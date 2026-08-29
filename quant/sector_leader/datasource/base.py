"""数据源接口与统一口径。

所有 provider 必须返回下列标准化 schema —— 回测引擎只认这套列名，
换数据源（akshare / 东方财富直连 / 本地落库 / 合成数据）不改策略代码。

口径约定（踩过坑的地方，务必遵守）
--------------------------------
1. **复权**：`stock_daily` 返回 **后复权(hfq)** 的 ohlc，用于计算收益与均线；
   同时返回 `raw_close` 未复权收盘价，用于判断涨跌停与最小买入金额。
   不要用前复权做回测——前复权序列会随未来分红被整体重写，等于把未来
   信息塞进历史价格。
2. **财报可用时点**：`financials` 必须带 `disclosure_date`（公告日）。
   引擎只在 `公告日 + lag` 之后才允许使用该期数据。用 `report_period`
   （报告期）当可用日期是最典型的前视偏差。
3. **成分股**：`sector_members(board, asof)` 理想情况按日期返回历史成分。
   若数据源只能给当前成分（akshare 即如此），会带来幸存者偏差 —— provider
   必须通过 `members_are_point_in_time` 属性如实声明，报告里会打警告。
"""

from __future__ import annotations

from typing import Protocol, Sequence

import pandas as pd

# ---- 标准 schema -------------------------------------------------------

DAILY_COLUMNS = [
    "date", "open", "high", "low", "close", "volume", "amount", "raw_close",
]
SECTOR_DAILY_COLUMNS = ["date", "open", "high", "low", "close", "volume", "amount"]
FINANCIAL_COLUMNS = [
    "code", "report_period", "disclosure_date",
    "revenue", "revenue_yoy", "net_profit", "net_profit_yoy", "roe",
]
META_COLUMNS = ["code", "name", "list_date", "board"]


class DataSource(Protocol):
    """行情 + 财务数据源。"""

    name: str
    members_are_point_in_time: bool

    def trading_calendar(self, start: str, end: str) -> pd.DatetimeIndex: ...

    def sector_list(self) -> pd.DataFrame:
        """→ columns: [board_code, board_name]"""

    def sector_daily(self, board: str, start: str, end: str) -> pd.DataFrame:
        """→ SECTOR_DAILY_COLUMNS"""

    def sector_members(self, board: str, asof: str | None = None) -> list[str]:
        """→ 成分股代码列表（6 位数字，不带交易所前缀）"""

    def stock_daily(self, code: str, start: str, end: str) -> pd.DataFrame:
        """→ DAILY_COLUMNS"""

    def stock_meta(self) -> pd.DataFrame:
        """→ META_COLUMNS"""

    def financials(self, codes: Sequence[str], start: str, end: str) -> pd.DataFrame:
        """→ FINANCIAL_COLUMNS，须含公告日 disclosure_date"""


def normalize_daily(df: pd.DataFrame) -> pd.DataFrame:
    """列名对齐 + 类型规整 + 按日期升序去重。"""
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    for col in ("open", "high", "low", "close", "volume", "amount", "raw_close"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "raw_close" not in out.columns:
        out["raw_close"] = out["close"]
    out = out.dropna(subset=["date", "close"])
    out = out.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    return out


def is_st(name: str) -> bool:
    upper = str(name).upper().replace(" ", "")
    return "ST" in upper or "退" in str(name)


def limit_threshold(code: str, cost) -> float:
    """按板块返回涨跌停幅度：科创(688)/创业板(30) 为 20cm，北交所 30cm 暂按 20cm 处理。"""
    code = str(code)
    if code.startswith(("688", "30", "8", "4")):
        return cost.limit_threshold_20cm
    return cost.limit_up_threshold
