"""东方财富公开接口直连 provider（只依赖 requests，不装 akshare）。

akshare 本质上也是包这些接口，直连的好处是依赖轻、可控频控与重试。
代价是接口非官方文档、字段可能变动。

⚠️ 本 provider 的字段映射是按东财接口现行返回结构写的，但**没有在本
沙箱里对活接口验证过**（网络策略封禁了 push2his.eastmoney.com）。首次在
有网环境使用时，请先跑 `python -m sector_leader.cli selftest --source eastmoney`，
它会拉一段样本并校验 schema，再开始大规模抓取。
"""

from __future__ import annotations

import time
from typing import Any, Sequence

import pandas as pd

from .base import normalize_daily
from .cache import Cache

PUSH2 = "https://push2.eastmoney.com/api/qt/clist/get"
PUSH2HIS = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
DATACENTER = "https://datacenter-web.eastmoney.com/api/data/v1/get"
UT = "fa5fd1943c7b386f172d6893dbfba10b"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://quote.eastmoney.com/",
}
# kline fields2 的顺序即返回字符串按逗号切分后的语义
KLINE_FIELDS = ["date", "open", "close", "high", "low", "volume", "amount",
                "amplitude", "pct_change", "change", "turnover"]


class EastmoneySource:
    name = "eastmoney"
    members_are_point_in_time = False

    def __init__(self, cache: Cache | None = None, sleep: float = 0.25, retries: int = 3):
        import requests

        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cache = cache or Cache()
        self.sleep = sleep
        self.retries = retries

    def _get(self, url: str, params: dict[str, Any]) -> dict:
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                time.sleep(self.sleep)
                r = self.session.get(url, params=params, timeout=20)
                r.raise_for_status()
                return r.json()
            except Exception as exc:  # 网络抖动/频控 → 指数退避
                last = exc
                time.sleep(2 ** attempt)
        raise RuntimeError(f"east money request failed: {url} {params}") from last

    # -- 板块 ------------------------------------------------------------
    def sector_list(self) -> pd.DataFrame:
        def fetch() -> pd.DataFrame:
            js = self._get(PUSH2, {
                "pn": 1, "pz": 500, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                "fid": "f3", "fs": "m:90 t:2 f:!50", "fields": "f12,f14", "ut": UT,
            })
            rows = (js.get("data") or {}).get("diff") or []
            return pd.DataFrame(
                {"board_code": [r["f12"] for r in rows], "board_name": [r["f14"] for r in rows]}
            )

        return self.cache.get_or_fetch("sector_list", "em_industry", fetch)

    def sector_daily(self, board: str, start: str, end: str) -> pd.DataFrame:
        key = f"em|{board}|{start}|{end}"

        def fetch() -> pd.DataFrame:
            return self._kline(f"90.{board}", start, end, fqt=1)

        return normalize_daily(self.cache.get_or_fetch("sector_daily", key, fetch))

    def sector_members(self, board: str, asof: str | None = None) -> list[str]:
        def fetch() -> pd.DataFrame:
            js = self._get(PUSH2, {
                "pn": 1, "pz": 1000, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                "fid": "f3", "fs": f"b:{board} f:!50", "fields": "f12,f14", "ut": UT,
            })
            rows = (js.get("data") or {}).get("diff") or []
            return pd.DataFrame({"code": [str(r["f12"]).zfill(6) for r in rows]})

        return self.cache.get_or_fetch("sector_members", f"em|{board}", fetch)["code"].tolist()

    # -- 个股 ------------------------------------------------------------
    def stock_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        key = f"em|{code}|{start}|{end}"

        def fetch() -> pd.DataFrame:
            secid = _secid(code)
            hfq = self._kline(secid, start, end, fqt=2)   # 后复权
            raw = self._kline(secid, start, end, fqt=0)   # 不复权
            if hfq.empty:
                return hfq
            if not raw.empty:
                hfq = hfq.merge(
                    raw[["date", "close"]].rename(columns={"close": "raw_close"}),
                    on="date", how="left",
                )
            return hfq

        return normalize_daily(self.cache.get_or_fetch("stock_daily", key, fetch))

    def _kline(self, secid: str, start: str, end: str, fqt: int) -> pd.DataFrame:
        js = self._get(PUSH2HIS, {
            "secid": secid, "ut": UT,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": 101, "fqt": fqt,
            "beg": start.replace("-", ""), "end": end.replace("-", ""),
        })
        klines = (js.get("data") or {}).get("klines") or []
        if not klines:
            return pd.DataFrame()
        rows = [dict(zip(KLINE_FIELDS, line.split(","))) for line in klines]
        df = pd.DataFrame(rows)
        return df[["date", "open", "high", "low", "close", "volume", "amount"]]

    def stock_meta(self) -> pd.DataFrame:
        def fetch() -> pd.DataFrame:
            rows: list[dict] = []
            page = 1
            while True:
                js = self._get(PUSH2, {
                    "pn": page, "pz": 200, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                    "fid": "f3", "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
                    "fields": "f12,f14", "ut": UT,
                })
                diff = (js.get("data") or {}).get("diff") or []
                if not diff:
                    break
                rows.extend(diff)
                page += 1
                if page > 40:
                    break
            return pd.DataFrame(
                {"code": [str(r["f12"]).zfill(6) for r in rows],
                 "name": [r["f14"] for r in rows], "list_date": pd.NaT, "board": ""}
            )

        return self.cache.get_or_fetch("stock_meta", "em_all", fetch)

    # -- 财务 ------------------------------------------------------------
    def financials(self, codes: Sequence[str], start: str, end: str) -> pd.DataFrame:
        from .akshare_ds import _report_periods

        frames = []
        for period in _report_periods(start, end):
            iso = f"{period[:4]}-{period[4:6]}-{period[6:]}"

            def fetch(iso=iso) -> pd.DataFrame:
                rows: list[dict] = []
                page = 1
                while True:
                    js = self._get(DATACENTER, {
                        "reportName": "RPT_LICO_FN_CPD", "columns": "ALL",
                        "filter": f"(REPORTDATE='{iso}')",
                        "pageNumber": page, "pageSize": 500,
                        "sortColumns": "UPDATE_DATE", "sortTypes": -1,
                    })
                    data = (js.get("result") or {}).get("data") or []
                    if not data:
                        break
                    rows.extend(data)
                    if page >= ((js.get("result") or {}).get("pages") or 1):
                        break
                    page += 1
                return pd.DataFrame(rows)

            raw = self.cache.get_or_fetch("financials", f"em|{period}", fetch)
            if raw is None or raw.empty:
                continue
            frames.append(pd.DataFrame({
                "code": raw["SECURITY_CODE"].astype(str).str.zfill(6),
                "report_period": pd.Timestamp(iso),
                "disclosure_date": pd.to_datetime(raw.get("NOTICE_DATE"), errors="coerce"),
                "revenue": pd.to_numeric(raw.get("TOTAL_OPERATE_INCOME"), errors="coerce"),
                "revenue_yoy": pd.to_numeric(raw.get("YSTZ"), errors="coerce") / 100.0,
                "net_profit": pd.to_numeric(raw.get("PARENTNETPROFIT"), errors="coerce"),
                "net_profit_yoy": pd.to_numeric(raw.get("SJLTZ"), errors="coerce") / 100.0,
                "roe": pd.to_numeric(raw.get("WEIGHTAVG_ROE"), errors="coerce") / 100.0,
            }).dropna(subset=["disclosure_date"]))
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        wanted = {str(c).zfill(6) for c in codes}
        return out[out["code"].isin(wanted)].reset_index(drop=True)

    def trading_calendar(self, start: str, end: str) -> pd.DatetimeIndex:
        """用沪深300指数的交易日作为日历。"""
        df = normalize_daily(self._kline("1.000300", start, end, fqt=1))
        return pd.DatetimeIndex(df["date"])


def _secid(code: str) -> str:
    code = str(code).zfill(6)
    market = "1" if code.startswith(("6", "5", "9")) else "0"
    return f"{market}.{code}"
