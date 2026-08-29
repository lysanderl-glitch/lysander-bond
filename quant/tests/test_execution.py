"""成交与成本测试：T+1、涨跌停、整手、费率。

回测里最容易「偷偷多赚」的地方就是成交假设。这些测试把每一条约束
钉死，改引擎时如果不小心放松了约束，测试会立刻失败。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sector_leader.backtest import Backtester, Order, Position
from sector_leader.config import StrategyConfig
from sector_leader.fundamentals import FundamentalPanel
from sector_leader.market import MarketData


def make_market(closes, opens=None, highs=None, lows=None, code="600000") -> MarketData:
    n = len(closes)
    cal = pd.DatetimeIndex(pd.bdate_range("2024-01-01", periods=n))
    opens = opens if opens is not None else closes
    highs = highs if highs is not None else [max(a, b) for a, b in zip(opens, closes)]
    lows = lows if lows is not None else [min(a, b) for a, b in zip(opens, closes)]

    def wide(vals):
        return pd.DataFrame({code: vals}, index=cal, dtype=float)

    md = MarketData(
        calendar=cal, close=wide(closes), open=wide(opens), high=wide(highs),
        low=wide(lows), amount=wide([1e9] * n), raw_close=wide(closes),
        meta=pd.DataFrame([{"code": code, "name": "测试股", "list_date": pd.NaT, "board": ""}]),
        panel=FundamentalPanel(pd.DataFrame(), cal, 1),
        sector_signals={}, members={"BK0001": [code]}, board_names={"BK0001": "测试板块"},
    )
    md.rps = pd.DataFrame({code: [50.0] * n}, index=cal)
    md.ma_short = md.close.rolling(20, min_periods=1).mean()
    md.tradable = pd.DataFrame({code: [True] * n}, index=cal)
    return md


def test_order_fills_at_next_open_not_signal_day_close():
    """T 日挂单必须以 T+1 的开盘价成交 —— 用 T 日收盘价成交等于穿越。"""
    # T 日(index 1)收盘价 10，T+1 日(index 2)开盘价 10.5（+5%，未涨停）
    md = make_market(closes=[10, 10, 11, 11, 11], opens=[10, 10, 10.5, 11, 11])
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.pending = [Order("600000", "BK0001", "buy", None, "test", 0.2, 0)]
    bt._execute_pending(md.calendar[2])
    pos = bt.positions["600000"]
    # 成交价应贴近 10.5（+滑点），而不是信号日收盘价 10、也不是当日收盘价 11
    assert 10.5 < pos.avg_cost < 10.6, f"应以 T+1 开盘价 10.5 成交，实际 {pos.avg_cost:.4f}"


def test_round_trip_at_same_price_loses_exactly_the_costs():
    """同价买入卖出，亏损应等于双边费用 + 双边滑点，不多不少。"""
    md = make_market(closes=[10.0] * 5, opens=[10.0] * 5)
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.pending = [Order("600000", "BK0001", "buy", None, "test", 0.2, 0)]
    bt._execute_pending(md.calendar[1])
    pos = bt.positions["600000"]
    shares = pos.shares
    bt._sell(Order("600000", "BK0001", "sell", None, "test"), md.calendar[2], 10.0, "test")

    trade = bt.trades[0]
    c = cfg.cost
    gross_buy = shares * 10.0 * (1 + c.slippage)
    gross_sell = shares * 10.0 * (1 - c.slippage)
    expected_fees = (max(gross_buy * c.commission_rate, c.commission_min)
                     + gross_buy * c.transfer_fee
                     + max(gross_sell * c.commission_rate, c.commission_min)
                     + gross_sell * c.transfer_fee
                     + gross_sell * c.stamp_duty_sell)
    expected_pnl = gross_sell - gross_buy - expected_fees
    assert abs(trade["pnl"] - expected_pnl) < 1e-6, \
        f"费用计算不符：实际 {trade['pnl']:.2f} 预期 {expected_pnl:.2f}"
    assert trade["pnl"] < 0, "同价往返必然亏损（费用+滑点）"


def test_cannot_buy_on_limit_up_open():
    """开盘一字涨停时买单必须落空并顺延，而不是假装成交。"""
    md = make_market(closes=[10, 11.0, 11.0], opens=[10, 11.0, 11.0])
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.pending = [Order("600000", "BK0001", "buy", None, "test", 0.2, 0)]
    bt._execute_pending(md.calendar[1])       # +10% 开盘 → 涨停
    assert "600000" not in bt.positions, "涨停开盘不应买到货"
    assert len(bt.pending) == 1, "未成交的买单应顺延到下一交易日"
    assert bt.blocked and bt.blocked[0]["reason"] == "test"


def test_cannot_sell_on_limit_down_open():
    md = make_market(closes=[10, 9.0, 9.0], opens=[10, 9.0, 9.0],
                     highs=[10, 9.0, 9.0], lows=[10, 9.0, 9.0])
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.positions["600000"] = Position("600000", "BK0001", shares=1000,
                                      cost_basis=10000.0, entry_date=md.calendar[0])
    bt.pending = [Order("600000", "BK0001", "sell", None, "止损")]
    bt._execute_pending(md.calendar[1])       # -10% 开盘 → 跌停
    assert bt.positions["600000"].shares == 1000, "跌停开盘不应卖得掉"
    assert len(bt.pending) == 1, "未成交的卖单应顺延"


def test_can_still_sell_when_limit_down_is_only_touched_intraday():
    """盘中砸到跌停又拉回 → 当天卖得掉，不能当成卖不掉。"""
    md = make_market(closes=[10, 9.5], opens=[10, 9.6], highs=[10, 9.8], lows=[10, 9.0])
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.positions["600000"] = Position("600000", "BK0001", shares=1000,
                                      cost_basis=10000.0, entry_date=md.calendar[0],
                                      peak_price=10.0)
    bt._manage_positions(md.calendar[1])
    assert bt.trades, "盘中触及跌停但收在跌停上方，应能止损成交"


def test_shares_are_round_lots():
    md = make_market(closes=[7.77] * 3, opens=[7.77] * 3)
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.pending = [Order("600000", "BK0001", "buy", None, "test", 0.2, 0)]
    bt._execute_pending(md.calendar[1])
    assert bt.positions["600000"].shares % 100 == 0, "A 股必须按 100 股整手交易"


def test_cash_never_goes_negative():
    md = make_market(closes=[10.0] * 6, opens=[10.0] * 6)
    cfg = StrategyConfig(initial_capital=50_000)
    cfg.entry.max_weight_per_stock = 1.0
    bt = Backtester(md, cfg)
    for i in range(1, 5):
        bt.pending = [Order("600000", "BK0001", "buy", None, "test", 1.0, 0)]
        bt._execute_pending(md.calendar[i])
        assert bt.cash >= 0, f"第 {i} 笔买入后现金为负：{bt.cash}"


def test_hard_stop_exits_at_stop_price_not_at_close():
    """日内跌破止损位应按止损价成交，而不是等到收盘价（收盘可能更低）。"""
    # 次日：开 9.7、最低 9.1（跌 9%，未封死跌停）、收 9.3；止损位 = 10*(1-8%) = 9.2
    md = make_market(closes=[10, 9.3], opens=[10, 9.7], highs=[10, 9.75], lows=[10, 9.1])
    cfg = StrategyConfig(initial_capital=1_000_000)
    bt = Backtester(md, cfg)
    bt.positions["600000"] = Position("600000", "BK0001", shares=1000,
                                      cost_basis=10000.0, entry_date=md.calendar[0],
                                      peak_price=10.0)
    bt._manage_positions(md.calendar[1])
    assert bt.trades, "触发止损位却没有成交"
    exit_px = bt.trades[0]["exit_price"]
    stop_px = 10.0 * (1 - cfg.exit.hard_stop)   # 9.2
    expected = stop_px * (1 - cfg.cost.slippage)
    assert abs(exit_px - expected) < 1e-9, \
        f"止损应按止损价 {expected:.4f} 成交（而非收盘价 9.3），实际 {exit_px:.4f}"
