"""akshare 数据源（推荐的真实数据 provider）。

需要有网环境：`pip install akshare`。本仓库的沙箱网络策略封禁了所有
A 股行情域名，所以这个 provider 在 CI 里不会被调用，请在本地运行。

涉及的 akshare 接口
-------------------
- `stock_board_industry_name_em()`      东财行业板块列表
- `stock_board_industry_hist_em()`      板块指数日线
- `stock_board_industry_cons_em()`      板块成分股（**仅当前成分**，见幸存者偏差警告）
- `stock_zh_a_hist(adjust="hfq"/"")`    个股日线（后复权 / 不复权）
- `stock_info_a_code_name()`            全市场代码与名称
- `stock_yjbb_em(date="YYYYMMDD")`      业绩报表，**含公告日期**，点位时点的关键
"""

from __future__ import annotations

import time
from typing import Sequence

import pandas as pd

from .base import normalize_daily
from .cache import Cache


class AkshareSource:
    name = "akshare"
    # akshare 的成分股接口只返回「当前」成分，无法回溯历史调入调出。
    members_are_point_in_time = False

    def __init__(self, cache: Cache | None = None, sleep: float = 0.3):
        try:
            import akshare as ak  # noqa: F401
        except ImportError as exc:  # pragma: no cover - 环境相关
            raise ImportError(
                "需要 akshare：pip install akshare（本沙箱网络策略禁止访问行情源，请在本地运行）"
            ) from exc
        import akshare as ak

        self.ak = ak
        self.cache = cache or Cache()
        self.sleep = sleep
        self._name_to_code: dict[str, str] = {}

    # -- 日历 ------------------------------------------------------------
    def trading_calendar(self, start: str, end: str) -> pd.DatetimeIndex:
        df = self.cache.get_or_fetch(
            "calendar", "tool_trade_date_hist_sina", lambda: self.ak.tool_trade_date_hist_sina()
        )
        dates = pd.to_datetime(df["trade_date"])
        mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
        return pd.DatetimeIndex(sorted(dates[mask]))

    # -- 板块 ------------------------------------------------------------
    def sector_list(self) -> pd.DataFrame:
        def fetch() -> pd.DataFrame:
            df = self.ak.stock_board_industry_name_em()
            return pd.DataFrame(
                {"board_code": df["板块代码"].astype(str), "board_name": df["板块名称"].astype(str)}
            )

        out = self.cache.get_or_fetch("sector_list", "industry_em", fetch)
        self._name_to_code = dict(zip(out["board_name"], out["board_code"]))
        return out

    def sector_daily(self, board: str, start: str, end: str) -> pd.DataFrame:
        key = f"{board}|{start}|{end}"

        def fetch() -> pd.DataFrame:
            time.sleep(self.sleep)
            df = self.ak.stock_board_industry_hist_em(
                symbol=board,
                start_date=start.replace("-", ""),
                end_date=end.replace("-", ""),
                period="日k",
                adjust="",
            )
            return pd.DataFrame(
                {
                    "date": df["日期"],
                    "open": df["开盘"], "high": df["最高"],
                    "low": df["最低"], "close": df["收盘"],
                    "volume": df["成交量"], "amount": df["成交额"],
                }
            )

        return normalize_daily(self.cache.get_or_fetch("sector_daily", key, fetch))

    def sector_members(self, board: str, asof: str | None = None) -> list[str]:
        """注意：asof 被忽略 —— 数据源只有当前成分，回测存在幸存者偏差。"""
        def fetch() -> pd.DataFrame:
            time.sleep(self.sleep)
            df = self.ak.stock_board_industry_cons_em(symbol=board)
            return pd.DataFrame({"code": df["代码"].astype(str).str.zfill(6)})

        return self.cache.get_or_fetch("sector_members", board, fetch)["code"].tolist()

    # -- 个股 ------------------------------------------------------------
    def stock_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        key = f"{code}|{start}|{end}"

        def fetch() -> pd.DataFrame:
            time.sleep(self.sleep)
            s, e = start.replace("-", ""), end.replace("-", "")
            hfq = self.ak.stock_zh_a_hist(
                symbol=code, period="daily", start_date=s, end_date=e, adjust="hfq"
            )
            raw = self.ak.stock_zh_a_hist(
                symbol=code, period="daily", start_date=s, end_date=e, adjust=""
            )
            if hfq is None or hfq.empty:
                return pd.DataFrame()
            out = pd.DataFrame(
                {
                    "date": hfq["日期"],
                    "open": hfq["开盘"], "high": hfq["最高"],
                    "low": hfq["最低"], "close": hfq["收盘"],
                    "volume": hfq["成交量"], "amount": hfq["成交额"],
                }
            )
            if raw is not None and not raw.empty:
                raw_close = pd.DataFrame({"date": raw["日期"], "raw_close": raw["收盘"]})
                out = out.merge(raw_close, on="date", how="left")
            return out

        return normalize_daily(self.cache.get_or_fetch("stock_daily", key, fetch))

    def stock_meta(self) -> pd.DataFrame:
        def fetch() -> pd.DataFrame:
            df = self.ak.stock_info_a_code_name()
            return pd.DataFrame(
                {"code": df["code"].astype(str).str.zfill(6), "name": df["name"], "list_date": pd.NaT}
            )

        out = self.cache.get_or_fetch("stock_meta", "a_code_name", fetch)
        if "board" not in out.columns:
            out["board"] = ""
        return out

    # -- 财务：点位时点的核心 --------------------------------------------
    def financials(self, codes: Sequence[str], start: str, end: str) -> pd.DataFrame:
        """按报告期逐期拉业绩报表，保留公告日期用于防前视。"""
        frames = []
        for period in _report_periods(start, end):
            def fetch(period=period) -> pd.DataFrame:
                time.sleep(self.sleep)
                return self.ak.stock_yjbb_em(date=period)

            df = self.cache.get_or_fetch("financials", period, fetch)
            if df is None or df.empty:
                continue
            frames.append(_normalize_yjbb(df, period))
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        wanted = set(str(c).zfill(6) for c in codes)
        return out[out["code"].isin(wanted)].reset_index(drop=True)


def _report_periods(start: str, end: str) -> list[str]:
    """回测区间前推一年（需要同比基数与上一期环比）内的所有报告期。"""
    s = pd.Timestamp(start) - pd.DateOffset(years=1)
    e = pd.Timestamp(end)
    periods = []
    for year in range(s.year, e.year + 1):
        for md in ("0331", "0630", "0930", "1231"):
            d = pd.Timestamp(f"{year}{md}")
            if s <= d <= e:
                periods.append(f"{year}{md}")
    return periods


def _normalize_yjbb(df: pd.DataFrame, period: str) -> pd.DataFrame:
    def col(*names):
        for n in names:
            if n in df.columns:
                return df[n]
        return pd.Series([pd.NA] * len(df))

    out = pd.DataFrame(
        {
            "code": col("股票代码").astype(str).str.zfill(6),
            "report_period": pd.Timestamp(period),
            "disclosure_date": pd.to_datetime(col("最新公告日期"), errors="coerce"),
            "revenue": pd.to_numeric(col("营业收入-营业收入"), errors="coerce"),
            "revenue_yoy": pd.to_numeric(col("营业收入-同比增长"), errors="coerce") / 100.0,
            "net_profit": pd.to_numeric(col("净利润-净利润"), errors="coerce"),
            "net_profit_yoy": pd.to_numeric(col("净利润-同比增长"), errors="coerce") / 100.0,
            "roe": pd.to_numeric(col("净资产收益率"), errors="coerce") / 100.0,
        }
    )
    # 没有公告日的记录不可用（宁可丢数据，不可引入前视）
    return out.dropna(subset=["disclosure_date"])
