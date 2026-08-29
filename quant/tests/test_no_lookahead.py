"""防前视偏差测试 —— 这是整个回测里唯一必须证明的东西。

回测结果好看有一万种可能，其中大部分是穿越。所以这些测试不测「策略赚不
赚钱」，只测「策略在 T 日有没有偷看 T 日之后的数据」。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sector_leader import indicators as ind
from sector_leader.config import StrategyConfig
from sector_leader.fundamentals import FundamentalPanel


def _series(n=200, seed=1) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))


def test_indicators_are_causal():
    """把序列截断后重算，历史部分的指标值必须与全序列时完全一致。

    只要有一个指标用到了未来数据（比如居中滚动、全样本标准化），
    截断前后就会出现差异。
    """
    s = _series(300)
    cut = 200
    funcs = {
        "sma20": lambda x: ind.sma(x, 20),
        "slope20": lambda x: ind.slope(x, 20),
        "amount_ratio": lambda x: ind.amount_ratio(x, 20),
        "rolling_return60": lambda x: ind.rolling_return(x, 60),
        "drawdown": lambda x: ind.drawdown_from_peak(x),
    }
    for name, f in funcs.items():
        full = f(s).iloc[:cut]
        truncated = f(s.iloc[:cut])
        pd.testing.assert_series_equal(full, truncated, check_names=False,
                                       obj=f"{name} 使用了未来数据")


def test_leg_structure_is_causal():
    s = _series(300, seed=5)
    cut = 220
    full = ind.leg_up_and_retracement(s, lookback=120).iloc[:cut]
    trunc = ind.leg_up_and_retracement(s.iloc[:cut], lookback=120)
    pd.testing.assert_frame_equal(full, trunc, obj="波段识别使用了未来数据")


def test_fundamentals_respect_disclosure_date():
    """财报在公告日之前必须不可见。"""
    cal = pd.bdate_range("2024-01-01", "2024-12-31")
    fin = pd.DataFrame([
        {"code": "600000", "report_period": pd.Timestamp("2024-03-31"),
         "disclosure_date": pd.Timestamp("2024-04-25"),
         "revenue_yoy": 0.5, "net_profit_yoy": 0.6, "roe": 0.12},
        {"code": "600000", "report_period": pd.Timestamp("2024-06-30"),
         "disclosure_date": pd.Timestamp("2024-08-20"),
         "revenue_yoy": 0.9, "net_profit_yoy": 1.0, "roe": 0.15},
    ])
    panel = FundamentalPanel(fin, pd.DatetimeIndex(cal), lag_days=1)

    # 报告期已过但尚未公告 → 不可见
    assert panel.asof(pd.Timestamp("2024-04-10"), "revenue_yoy", ["600000"]).empty, \
        "一季报在公告日之前就被策略看到了（典型前视偏差）"
    # 公告日当天 +lag 之后 → 可见，且是一季报的值
    v = panel.asof(pd.Timestamp("2024-05-06"), "revenue_yoy", ["600000"])
    assert not v.empty and abs(float(v.iloc[0]) - 0.5) < 1e-9

    # 中报公告前，看到的仍应是一季报
    v = panel.asof(pd.Timestamp("2024-08-01"), "revenue_yoy", ["600000"])
    assert abs(float(v.iloc[0]) - 0.5) < 1e-9, "中报提前泄露"
    v = panel.asof(pd.Timestamp("2024-09-02"), "revenue_yoy", ["600000"])
    assert abs(float(v.iloc[0]) - 0.9) < 1e-9


def test_improving_flag_uses_report_order_not_disclosure_order():
    """增速环比改善必须按报告期顺序比较，晚公告的旧报告期不能颠倒顺序。"""
    cal = pd.bdate_range("2024-01-01", "2025-06-30")
    fin = pd.DataFrame([
        {"code": "600000", "report_period": pd.Timestamp("2024-03-31"),
         "disclosure_date": pd.Timestamp("2024-04-25"),
         "revenue_yoy": 0.10, "net_profit_yoy": 0.10, "roe": 0.1},
        {"code": "600000", "report_period": pd.Timestamp("2024-06-30"),
         "disclosure_date": pd.Timestamp("2024-08-25"),
         "revenue_yoy": 0.30, "net_profit_yoy": 0.30, "roe": 0.1},
    ])
    panel = FundamentalPanel(fin, pd.DatetimeIndex(cal), lag_days=1)
    v = panel.asof(pd.Timestamp("2024-09-10"), "improving", ["600000"])
    assert float(v.iloc[0]) == 1.0, "10% → 30% 应判定为增速改善"


def test_rps_is_cross_sectional_only():
    """RPS 只在同一交易日的横截面上排名，不得跨期借用信息。"""
    df = pd.DataFrame({"a": [0.1, 0.2], "b": [0.3, 0.05], "c": [0.2, 0.4]})
    rps = ind.cross_sectional_rps(df)
    assert list(rps.iloc[0].rank()) == list(df.iloc[0].rank())
    # 改动第二行不应影响第一行
    df2 = df.copy()
    df2.iloc[1] = [9.0, 9.0, 9.0]
    pd.testing.assert_series_equal(ind.cross_sectional_rps(df2).iloc[0], rps.iloc[0])
