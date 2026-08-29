"""全市场数据容器：一次装载，回测里按日切片。

把所有个股日线拼成 [交易日 × 代码] 的宽表。宽表让横截面计算（RPS、
涨幅排名、流动性过滤）变成一次向量化操作，回测 485 个交易日 × 750 只
股票在秒级完成；逐票循环则要几分钟。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .datasource.base import is_st
from .fundamentals import FundamentalPanel
from .indicators import cross_sectional_rps, rolling_return, sma


@dataclass
class MarketData:
    calendar: pd.DatetimeIndex
    close: pd.DataFrame
    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    amount: pd.DataFrame
    raw_close: pd.DataFrame
    meta: pd.DataFrame
    panel: FundamentalPanel
    sector_signals: dict[str, pd.DataFrame]
    members: dict[str, list[str]]
    board_names: dict[str, str]
    sector_daily_cache: dict[str, pd.DataFrame] = field(default_factory=dict)
    rps: pd.DataFrame = field(default_factory=pd.DataFrame)
    ma_short: pd.DataFrame = field(default_factory=pd.DataFrame)
    tradable: pd.DataFrame = field(default_factory=pd.DataFrame)
    source_name: str = ""
    members_are_point_in_time: bool = False

    @property
    def codes(self) -> list[str]:
        return list(self.close.columns)

    def board_of(self, code: str) -> str | None:
        for board, mem in self.members.items():
            if code in mem:
                return board
        return None


def load_market(source, config: StrategyConfig, boards: pd.DataFrame,
                verbose: bool = False) -> MarketData:
    from .sector import SectorScreener

    calendar = pd.DatetimeIndex(source.trading_calendar(config.start, config.end))
    members: dict[str, list[str]] = {}
    board_names: dict[str, str] = {}
    for row in boards.itertuples():
        key = row.board_name if source.name == "akshare" else row.board_code
        members[row.board_code] = source.sector_members(key)
        board_names[row.board_code] = row.board_name

    all_codes = sorted({c for mem in members.values() for c in mem})
    if verbose:
        print(f"[载入] 板块 {len(members)} 个，去重个股 {len(all_codes)} 只")

    frames: dict[str, dict[str, pd.Series]] = {k: {} for k in
                                               ("close", "open", "high", "low", "amount", "raw_close")}
    for i, code in enumerate(all_codes):
        d = source.stock_daily(code, config.start, config.end)
        if d.empty:
            continue
        d = d.set_index("date")
        for k in frames:
            if k in d.columns:
                frames[k][code] = d[k]
        if verbose and (i + 1) % 200 == 0:
            print(f"  行情载入 {i + 1}/{len(all_codes)}")

    def wide(key: str) -> pd.DataFrame:
        if not frames[key]:
            return pd.DataFrame(index=calendar)
        return pd.DataFrame(frames[key]).reindex(calendar)

    close, open_, high, low = wide("close"), wide("open"), wide("high"), wide("low")
    amount, raw_close = wide("amount"), wide("raw_close")

    meta = source.stock_meta()
    meta["code"] = meta["code"].astype(str).str.zfill(6)
    meta = meta[meta["code"].isin(close.columns)].reset_index(drop=True)

    fin = source.financials(all_codes, config.start, config.end)
    panel = FundamentalPanel(fin, calendar, config.fundamental_disclosure_lag_days)

    sector_daily_cache: dict[str, pd.DataFrame] = {}
    for board, name in board_names.items():
        key = name if source.name == "akshare" else board
        daily = source.sector_daily(key, config.start, config.end)
        if daily.empty or len(daily) < config.sector.ma_long + 20:
            continue
        sector_daily_cache[board] = daily

    md = MarketData(
        calendar=calendar, close=close, open=open_, high=high, low=low,
        amount=amount, raw_close=raw_close, meta=meta, panel=panel,
        sector_signals={}, members=members, board_names=board_names,
        sector_daily_cache=sector_daily_cache,
        source_name=source.name,
        members_are_point_in_time=getattr(source, "members_are_point_in_time", False),
    )
    rebuild_sector_signals(md, config)
    _derive(md, config)
    return md


def rebuild_sector_signals(md: MarketData, config: StrategyConfig) -> None:
    """用当前参数重算板块信号。

    参数扫描时必须调用 —— 板块信号是预计算的，只改 config 而不重算，
    板块层的参数会「看起来完全没有影响」，扫描结果就是假的。
    """
    from .sector import SectorScreener

    screener = SectorScreener(config, md.panel)
    md.sector_signals = {
        board: screener.build(board, md.board_names[board], daily, md.members[board])
        for board, daily in md.sector_daily_cache.items()
    }


def _derive(md: MarketData, config: StrategyConfig) -> None:
    """预计算横截面派生量。"""
    md.rps = cross_sectional_rps(rolling_return(md.close, config.pick.rps_window))
    md.ma_short = md.close.rolling(config.entry.pullback_to_ma,
                                  min_periods=config.entry.pullback_to_ma).mean()

    # 可交易性：有行情（非停牌）+ 非 ST + 上市满 N 日
    has_quote = md.close.notna() & md.amount.fillna(0).gt(0)
    st_codes = set()
    if config.pick.exclude_st and "name" in md.meta.columns:
        st_codes = {r.code for r in md.meta.itertuples() if is_st(r.name)}
    listed_enough = pd.DataFrame(True, index=md.close.index, columns=md.close.columns)
    list_dates: dict[str, pd.Timestamp] = {}
    if "list_date" in md.meta.columns:
        list_dates = dict(zip(md.meta["code"], pd.to_datetime(md.meta["list_date"], errors="coerce")))
    # 上市满 min_listed_days 个自然日折算（约 1.45 个自然日 ≈ 1 个交易日）
    unknown_list_date = []
    for code in md.close.columns:
        ld = list_dates.get(code)
        if pd.notna(ld):
            cutoff = ld + pd.Timedelta(days=int(config.pick.min_listed_days * 1.45))
            listed_enough[code] = md.close.index >= cutoff
        else:
            unknown_list_date.append(code)
    # 仅对缺上市日的标的退化为「样本内已积累足够 K 线」；否则会把开头一整段
    # 交易日全部作废，白白缩短回测区间。
    if unknown_list_date:
        need = min(config.pick.min_listed_days, len(md.calendar) // 3)
        bars_so_far = has_quote[unknown_list_date].cumsum()
        listed_enough[unknown_list_date] &= bars_so_far >= need

    tradable = has_quote & listed_enough
    for code in st_codes:
        if code in tradable.columns:
            tradable[code] = False
    md.tradable = tradable
