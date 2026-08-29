"""合成 A 股市场 —— 用于在无网环境验证整条回测管线的正确性。

⚠️ 用途边界：合成数据只能证明「代码逻辑跑得通、没有前视偏差、统计口径
正确」。**它产生的胜率与收益没有任何投资参考价值**，因为数据生成过程
是我写的，策略在其中的表现只反映生成器的假设。真实结论必须用
AkshareSource / EastmoneySource 抓真实数据重跑。

生成器刻意包含了几类现实结构，用来检验策略的过滤能力：
- **真景气板块**：股价先动，业绩滞后约一个季度爬坡（策略应能抓到）
- **纯题材板块**：股价同样放量拉升，但业绩始终不兑现（A.3 基本面门槛应过滤掉）
- **下跌中继陷阱**：第一波上涨后回调直接跌破起涨点（策略的最大失效场景）
- 龙头结构：板块内少数个股 beta 与 alpha 更高
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import normalize_daily


@dataclass
class SyntheticSpec:
    n_sectors: int = 30
    stocks_per_sector: int = 25
    theme_ratio: float = 0.30      # 纯题材板块占比
    trap_ratio: float = 0.35       # 第一波后直接破位的陷阱占比
    seed: int = 20240101


class SyntheticSource:
    name = "synthetic"
    members_are_point_in_time = True   # 合成市场没有成分变动，无幸存者偏差

    def __init__(self, start: str, end: str, spec: SyntheticSpec | None = None):
        self.spec = spec or SyntheticSpec()
        self.rng = np.random.default_rng(self.spec.seed)
        self.dates = _calendar(start, end)
        self._build()

    # -- 市场生成 --------------------------------------------------------
    def _build(self) -> None:
        n_days = len(self.dates)
        spec = self.spec
        rng = self.rng

        market = rng.normal(0.0, 0.010, n_days)   # 大盘因子：零漂移，不送免费beta

        self.boards: list[dict] = []
        self.sector_px: dict[str, pd.DataFrame] = {}
        self.stock_px: dict[str, pd.DataFrame] = {}
        self.members: dict[str, list[str]] = {}
        self.fundamental_regime: dict[str, np.ndarray] = {}
        self.names: dict[str, str] = {}

        for si in range(spec.n_sectors):
            board_code = f"BK{9000 + si}"
            is_theme = rng.random() < spec.theme_ratio
            board_name = ("题材" if is_theme else "行业") + f"板块{si:02d}"
            self.boards.append({"board_code": board_code, "board_name": board_name})

            drift, phase, boom = self._campaign_schedule(n_days, is_theme)
            sector_ret = 0.9 * market + drift + rng.normal(0, 0.011, n_days)
            sector_close = 1000 * np.exp(np.cumsum(sector_ret))
            self.sector_px[board_code] = _ohlc(self.dates, sector_close, sector_ret, phase, rng)
            self.fundamental_regime[board_code] = boom

            codes = []
            for k in range(spec.stocks_per_sector):
                code = f"{600000 + si * 100 + k:06d}"
                codes.append(code)
                self.names[code] = f"{board_name[:2]}股{k:02d}"
                is_leader = k < 4                       # 每板块 4 只结构性龙头
                beta = rng.uniform(1.2, 1.7) if is_leader else rng.uniform(0.6, 1.2)
                # 龙头溢价：这是被检验的假设本身，所以只植入很小的一点
                # （行情期日均 3bp），足以让「龙头是否更强」可被统计，
                # 又不至于让策略靠生成器的馈赠取胜。
                alpha = (rng.normal(0.0003, 0.0004) if is_leader
                         else rng.normal(-0.0001, 0.0004))
                idio = rng.normal(0, rng.uniform(0.012, 0.022), n_days)
                ret = beta * sector_ret + alpha * (drift != 0) + idio
                close = rng.uniform(5, 60) * np.exp(np.cumsum(ret))
                self.stock_px[code] = _ohlc(self.dates, close, ret, phase, rng, per_stock=True)
            self.members[board_code] = codes

        self._build_financials()

    def _campaign_schedule(self, n_days: int, is_theme: bool):
        """构造若干轮「启动→第一波→回调→二波 or 破位」的板块行情。"""
        rng = self.rng
        drift = np.zeros(n_days)
        phase = np.zeros(n_days, dtype=int)   # 0 平静 1 启动放量 2 主升 3 回调 4 二波/破位
        boom = np.zeros(n_days)               # 基本面景气强度（滞后于股价）

        day = int(rng.integers(20, 90))
        while day < n_days - 60:
            leg1 = int(rng.integers(20, 45))
            pull = int(rng.integers(8, 25))
            leg2 = int(rng.integers(15, 50))
            is_trap = rng.random() < self.spec.trap_ratio

            up = rng.uniform(0.004, 0.010)
            _fill(drift, phase, day, min(3, leg1), up * 1.6, 1)
            _fill(drift, phase, day + 3, leg1 - 3, up, 2)

            p0 = day + leg1
            _fill(drift, phase, p0, pull, -up * rng.uniform(0.5, 0.9), 3)

            p1 = p0 + pull
            if is_trap:  # 下跌中继：二波变成破位下跌
                _fill(drift, phase, p1, leg2, -up * rng.uniform(0.6, 1.1), 4)
            else:
                _fill(drift, phase, p1, leg2, up * rng.uniform(0.7, 1.2), 4)

            if not is_theme and not is_trap:
                # 真景气：业绩自启动后约一个季度开始爬坡，持续到二波结束
                b0 = day + 60
                boom[b0: p1 + leg2] = np.linspace(0, 1, max(1, p1 + leg2 - b0))

            day = p1 + leg2 + int(rng.integers(30, 120))

        # 关键：把 campaign 漂移去均值。否则「涨段多于跌段」会让生成器凭空
        # 注入年化几十个点的正收益，任何做多策略都稳赚，回测就失去了检验
        # 意义 —— 波段结构应当只提供「形状」，不提供「免费收益」。
        if drift.any():
            drift -= drift.mean()
        return drift, phase, boom

    def _build_financials(self) -> None:
        """按季度生成业绩，公告日 = 报告期后 30~110 天（模拟真实披露节奏）。"""
        rng = self.rng
        rows = []
        periods = pd.date_range(
            pd.Timestamp(self.dates[0]) - pd.DateOffset(years=1),
            self.dates[-1], freq="QE",
        )
        idx = pd.DatetimeIndex(self.dates)
        for board, codes in self.members.items():
            boom = self.fundamental_regime[board]
            for period in periods:
                pos = idx.searchsorted(period)
                strength = float(boom[min(pos, len(boom) - 1)]) if pos < len(boom) else 0.0
                lag = int(rng.integers(30, 110))
                disclosure = period + pd.Timedelta(days=lag)
                for code in codes:
                    base = rng.normal(-0.02, 0.18)
                    growth = base + strength * rng.uniform(0.25, 0.75)
                    rows.append({
                        "code": code,
                        "report_period": period,
                        "disclosure_date": disclosure,
                        "revenue": float(rng.uniform(1e8, 5e10)),
                        "revenue_yoy": growth,
                        "net_profit": float(rng.uniform(1e6, 5e9)),
                        "net_profit_yoy": growth * rng.uniform(0.8, 1.8),
                        "roe": float(np.clip(rng.normal(0.09, 0.05) + strength * 0.04, -0.2, 0.5)),
                    })
        self._financials = pd.DataFrame(rows)

    # -- DataSource 接口 -------------------------------------------------
    def trading_calendar(self, start: str, end: str) -> pd.DatetimeIndex:
        idx = pd.DatetimeIndex(self.dates)
        return idx[(idx >= pd.Timestamp(start)) & (idx <= pd.Timestamp(end))]

    def sector_list(self) -> pd.DataFrame:
        return pd.DataFrame(self.boards)

    def sector_daily(self, board: str, start: str, end: str) -> pd.DataFrame:
        return _slice(self.sector_px[board], start, end)

    def sector_members(self, board: str, asof: str | None = None) -> list[str]:
        return list(self.members[board])

    def stock_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        return _slice(self.stock_px[code], start, end)

    def stock_meta(self) -> pd.DataFrame:
        rows = [{"code": c, "name": n, "list_date": self.dates[0] - pd.Timedelta(days=800),
                 "board": ""} for c, n in self.names.items()]
        return pd.DataFrame(rows)

    def financials(self, codes, start: str, end: str) -> pd.DataFrame:
        wanted = set(codes)
        return self._financials[self._financials["code"].isin(wanted)].reset_index(drop=True)


# -- 工具 ----------------------------------------------------------------

def _calendar(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.bdate_range(start, end)
    return pd.DatetimeIndex([d for d in days if not _is_cn_holiday(d)])


def _is_cn_holiday(d: pd.Timestamp) -> bool:
    """粗略的 A 股休市近似：元旦、春节周、清明、五一、十一周。"""
    md = (d.month, d.day)
    if d.month == 1 and d.day <= 3:
        return True
    if d.month == 2 and 9 <= d.day <= 17:
        return True
    if md in ((4, 4), (4, 5), (4, 6)):
        return True
    if d.month == 5 and d.day <= 3:
        return True
    if d.month == 10 and d.day <= 7:
        return True
    return False


def _fill(drift, phase, start, length, value, tag) -> None:
    end = min(len(drift), start + max(0, length))
    if start >= end:
        return
    drift[start:end] = value
    phase[start:end] = tag


def _ohlc(dates, close, ret, phase, rng, per_stock: bool = False) -> pd.DataFrame:
    n = len(close)
    open_ = close / np.exp(ret) * np.exp(rng.normal(0, 0.004, n))
    span = np.abs(ret) + rng.uniform(0.004, 0.016, n)
    high = np.maximum(open_, close) * (1 + span * rng.uniform(0.2, 0.8, n))
    low = np.minimum(open_, close) * (1 - span * rng.uniform(0.2, 0.8, n))
    # 成交额：启动/主升放量，回调缩量 —— 让规范 A.2 的量能条件真正可被检验
    vol_mult = np.ones(n)
    vol_mult[phase == 1] = 2.2
    vol_mult[phase == 2] = 1.5
    vol_mult[phase == 3] = 0.65
    vol_mult[phase == 4] = 1.3
    base = rng.uniform(2e8, 4e9) if not per_stock else rng.uniform(3e7, 2e9)
    amount = base * vol_mult * np.exp(rng.normal(0, 0.35, n)) * (1 + 3 * np.abs(ret))
    return normalize_daily(pd.DataFrame({
        "date": dates, "open": open_, "high": high, "low": low, "close": close,
        "volume": amount / close, "amount": amount, "raw_close": close,
    }))


def _slice(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    m = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    return df.loc[m].reset_index(drop=True)
