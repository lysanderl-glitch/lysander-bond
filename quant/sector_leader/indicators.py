"""技术指标。

所有函数都返回与输入等长的序列，且**第 i 个值只使用 <= i 的数据**。
这条不变量是整个回测防前视的基础，`tests/test_indicators.py` 有专门校验。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, min_periods=window).mean()


def slope(s: pd.Series, window: int) -> pd.Series:
    """窗口内的相对斜率：(末值 - 首值) / 首值，用于判断均线走平还是拐头。"""
    prev = s.shift(window)
    return (s - prev) / prev.abs().replace(0, np.nan)


def amount_ratio(amount: pd.Series, window: int = 20) -> pd.Series:
    """当日成交额 / 前 window 日均额（不含当日，避免自我稀释）。"""
    base = amount.shift(1).rolling(window, min_periods=window).mean()
    return amount / base


def daily_return(close: pd.Series) -> pd.Series:
    return close.pct_change()


def rolling_return(close: pd.Series, window: int) -> pd.Series:
    return close / close.shift(window) - 1.0


def drawdown_from_peak(close: pd.Series) -> pd.Series:
    return close / close.cummax() - 1.0


def swing_low_index(close: pd.Series, lookback: int) -> pd.Series:
    """截至每一日、回看 lookback 日内最低点的位置（整数索引）。"""
    return close.rolling(lookback, min_periods=5).apply(
        lambda w: float(np.argmin(w.values)), raw=False
    )


def leg_up_and_retracement(close: pd.Series, lookback: int = 120) -> pd.DataFrame:
    """识别「起涨低点 → 波段高点 → 当前回调」的三点结构。

    返回列：
      leg_low     起涨低点价
      leg_high    该低点之后的最高价
      leg_gain    第一波涨幅
      retrace     当前自高点回撤占该波涨幅的比例（0 = 在高点，1 = 回到起涨点）
      days_since_high  距波段高点的交易日数
      leg_low_idx 起涨低点在原序列中的绝对位置（板块「启动日」）
      leg_high_idx 波段高点的绝对位置
    """
    n = len(close)
    vals = close.to_numpy(dtype=float)
    leg_low = np.full(n, np.nan)
    leg_high = np.full(n, np.nan)
    leg_gain = np.full(n, np.nan)
    retrace = np.full(n, np.nan)
    days_since_high = np.full(n, np.nan)
    leg_low_idx = np.full(n, np.nan)
    leg_high_idx = np.full(n, np.nan)

    for i in range(n):
        lo = max(0, i - lookback + 1)
        window = vals[lo: i + 1]
        if len(window) < 20:
            continue
        j = int(np.argmin(window))          # 窗口内最低点
        after = window[j:]
        k = int(np.argmax(after)) + j       # 低点之后的最高点
        low_px, high_px = window[j], window[k]
        if low_px <= 0:
            continue
        gain = high_px / low_px - 1.0
        leg_low[i], leg_high[i], leg_gain[i] = low_px, high_px, gain
        leg_low_idx[i], leg_high_idx[i] = lo + j, lo + k
        if high_px > low_px:
            retrace[i] = (high_px - vals[i]) / (high_px - low_px)
        days_since_high[i] = len(window) - 1 - k

    return pd.DataFrame(
        {"leg_low": leg_low, "leg_high": leg_high, "leg_gain": leg_gain,
         "retrace": retrace, "days_since_high": days_since_high,
         "leg_low_idx": leg_low_idx, "leg_high_idx": leg_high_idx},
        index=close.index,
    )


def cross_sectional_rps(returns: pd.DataFrame) -> pd.DataFrame:
    """相对强度 RPS：每一交易日在横截面上把区间涨幅排成 0~100 分位。

    输入 returns 的 index 为日期、columns 为股票代码。
    """
    return returns.rank(axis=1, pct=True) * 100.0
