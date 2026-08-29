"""规范 C / D —— 逐日事件驱动回测引擎。

时序约定（防前视的关键，任何改动都要守住）
------------------------------------------
    T 日收盘后：用 <= T 日的数据算信号，生成订单
    T+1 开盘：  订单以开盘价 ± 滑点成交，受涨跌停与停牌约束
    持仓期间：  硬止损在日内触发（用当日最低价判定），按止损价成交；
                均线/板块/逻辑类信号在收盘确认，次日开盘执行

真实约束
--------
- 100 股整手；不足一手的部分丢弃
- 涨停（≥+9.8%/+19.8%）当日不可买入，跌停不可卖出，顺延到下一日
- 停牌（无成交额）不可交易
- 费用：佣金万 2.5（最低 5 元）+ 过户费 + 卖出印花税 0.05% + 单边滑点
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .datasource.base import limit_threshold
from .market import MarketData
from .picker import select


@dataclass
class Position:
    code: str
    board: str
    shares: int = 0
    cost_basis: float = 0.0        # 累计买入成本（含费用）
    tranches_filled: int = 0
    planned_weight: float = 0.0
    entry_date: pd.Timestamp | None = None
    peak_price: float = 0.0
    reason: str = ""
    campaign_start: pd.Timestamp | None = None
    setup: str = "—"
    trimmed: bool = False

    @property
    def avg_cost(self) -> float:
        return self.cost_basis / self.shares if self.shares else 0.0


@dataclass
class Order:
    code: str
    board: str
    side: str                      # buy / sell
    quantity: int | None           # None = 全部
    reason: str
    planned_weight: float = 0.0
    tranche: int = 0
    meta: dict = field(default_factory=dict)


class Backtester:
    def __init__(self, md: MarketData, cfg: StrategyConfig):
        self.md = md
        self.cfg = cfg
        self.cash = cfg.initial_capital
        self.positions: dict[str, Position] = {}
        self.pending: list[Order] = []
        self.trades: list[dict] = []
        self.equity: list[dict] = []
        self.blocked: list[dict] = []      # 因涨跌停/停牌未能成交的记录
        self._precompute()

    # ------------------------------------------------------------------
    def _precompute(self) -> None:
        """把逐股逐日的入场条件向量化。"""
        md, cfg = self.md, self.cfg
        e = cfg.entry
        close, open_, amount = md.close, md.open, md.amount

        ma = md.ma_short
        amt5 = amount.rolling(5, min_periods=5).mean()
        near_ma = (close / ma - 1.0).abs() <= e.pullback_ma_tolerance
        shrink = amount < amt5 * e.pullback_volume_shrink
        stabilize = close >= open_
        self.pullback_entry = (near_ma & shrink & stabilize).fillna(False)

        prior_high = close.shift(1).rolling(10, min_periods=5).max()
        self.breakout_entry = (
            (close > prior_high) & (amount >= amt5 * e.breakout_confirm_volume)
        ).fillna(False)

        # 「跌破 20 日线」需要确认：连续 N 日收在均线下方 buffer 之外。
        # 不加确认会被日内噪音反复扫出场 —— 实测会把一批本可持有的仓位
        # 在买入次日就砍掉，显著拉低胜率且放大交易成本。
        below = close < ma * (1 - cfg.exit.ma_break_buffer)
        n = max(1, cfg.exit.ma_break_confirm_days)
        self.ma_break = (below.rolling(n, min_periods=n).sum() >= n).fillna(False)
        self.prev_close = close.shift(1)
        self.limit_pct = {c: limit_threshold(c, cfg.cost) for c in close.columns}
        # 板块级退出信号查表
        self.sector_exit = {b: s["sector_exit"] for b, s in md.sector_signals.items()}

    # ------------------------------------------------------------------
    def run(self, verbose: bool = False) -> "BacktestResult":
        cal = self.md.calendar
        warmup = max(self.cfg.sector.ma_long, self.cfg.pick.rps_window) + 5
        for i, date in enumerate(cal):
            self._execute_pending(date)
            self._manage_positions(date)
            if i >= warmup and i < len(cal) - 1:
                self._generate_orders(date)
            self._mark(date)
            if verbose and (i + 1) % 100 == 0:
                print(f"  {date.date()} 权益 {self.equity[-1]['equity']:,.0f} "
                      f"持仓 {len(self.positions)}")
        self._liquidate(cal[-1])
        return BacktestResult(self.cfg, self.md, pd.DataFrame(self.trades),
                              pd.DataFrame(self.equity), pd.DataFrame(self.blocked))

    # -- 成交 -----------------------------------------------------------
    def _execute_pending(self, date: pd.Timestamp) -> None:
        if not self.pending:
            return
        carry: list[Order] = []
        for order in self.pending:
            status = self._try_fill(order, date)
            if status == "blocked":
                self.blocked.append({"date": date, "code": order.code,
                                     "side": order.side, "reason": order.reason})
                carry.append(order)     # 顺延到下一交易日
        self.pending = carry

    def _try_fill(self, order: Order, date: pd.Timestamp) -> str:
        md, cost = self.md, self.cfg.cost
        code = order.code
        if code not in md.open.columns:
            return "skip"
        px_open = md.open.at[date, code]
        amt = md.amount.at[date, code] if code in md.amount.columns else np.nan
        if pd.isna(px_open) or not (amt > 0):
            return "blocked"            # 停牌

        prev = self.prev_close.at[date, code]
        limit = self.limit_pct.get(code, cost.limit_up_threshold)
        gap = (px_open / prev - 1.0) if pd.notna(prev) and prev > 0 else 0.0
        if order.side == "buy" and gap >= limit:
            return "blocked"            # 开盘涨停买不到
        if order.side == "sell" and gap <= -limit:
            return "blocked"            # 开盘跌停卖不掉

        if order.side == "buy":
            self._buy(order, date, px_open)
        else:
            self._sell(order, date, px_open, order.reason)
        return "filled"

    def _buy(self, order: Order, date: pd.Timestamp, px_open: float) -> None:
        cost = self.cfg.cost
        price = px_open * (1 + cost.slippage)
        equity = self._equity_value(date)
        target_value = equity * order.planned_weight * self.cfg.entry.tranches[order.tranche]
        target_value = min(target_value, self.cash * 0.98)
        raw_px = self._raw_price(date, order.code, price)
        shares = int(target_value // (raw_px * 100)) * 100
        if shares <= 0:
            return
        gross = shares * price
        fee = self._fee(gross, side="buy")
        if gross + fee > self.cash:
            shares = int((self.cash * 0.98) // (raw_px * 100)) * 100
            if shares <= 0:
                return
            gross = shares * price
            fee = self._fee(gross, side="buy")
        self.cash -= gross + fee
        pos = self.positions.get(order.code)
        if pos is None:
            pos = Position(code=order.code, board=order.board, entry_date=date,
                           reason=order.reason, planned_weight=order.planned_weight,
                           campaign_start=order.meta.get("campaign_start"),
                           setup=order.meta.get("setup", "—"))
            self.positions[order.code] = pos
        pos.shares += shares
        pos.cost_basis += gross + fee
        pos.tranches_filled = max(pos.tranches_filled, order.tranche + 1)
        pos.peak_price = max(pos.peak_price, price)

    def _sell(self, order: Order, date: pd.Timestamp, px: float, reason: str) -> None:
        pos = self.positions.get(order.code)
        if pos is None or pos.shares <= 0:
            return
        cost = self.cfg.cost
        price = px * (1 - cost.slippage)
        qty = pos.shares if order.quantity is None else min(order.quantity, pos.shares)
        qty = int(qty // 100) * 100 if qty < pos.shares else qty
        if qty <= 0:
            return
        gross = qty * price
        fee = self._fee(gross, side="sell")
        self.cash += gross - fee
        portion = qty / pos.shares
        cost_out = pos.cost_basis * portion
        pnl = gross - fee - cost_out
        self.trades.append({
            "code": pos.code, "board": pos.board,
            "board_name": self.md.board_names.get(pos.board, pos.board),
            "entry_date": pos.entry_date, "exit_date": date,
            "holding_days": int(np.busday_count(
                pos.entry_date.date(), date.date())) if pos.entry_date else 0,
            "shares": qty, "entry_price": cost_out / qty if qty else np.nan,
            "exit_price": price, "pnl": pnl,
            "return": pnl / cost_out if cost_out else np.nan,
            "entry_reason": pos.reason, "setup": pos.setup, "exit_reason": reason,
            "tranches": pos.tranches_filled,
        })
        pos.shares -= qty
        pos.cost_basis -= cost_out
        if pos.shares <= 0:
            self.positions.pop(pos.code, None)

    def _fee(self, gross: float, side: str) -> float:
        c = self.cfg.cost
        fee = max(gross * c.commission_rate, c.commission_min) + gross * c.transfer_fee
        if side == "sell":
            fee += gross * c.stamp_duty_sell
        return fee

    def _raw_price(self, date: pd.Timestamp, code: str, adj_price: float) -> float:
        """用未复权价决定「一手多少钱」，后复权价会严重高估最小买入金额。"""
        raw = self.md.raw_close.at[date, code] if code in self.md.raw_close.columns else np.nan
        adj = self.md.close.at[date, code]
        if pd.isna(raw) or pd.isna(adj) or adj <= 0:
            return adj_price
        return adj_price * (raw / adj)

    # -- 持仓管理（规范 D） ----------------------------------------------
    def _manage_positions(self, date: pd.Timestamp) -> None:
        ex = self.cfg.exit
        for code, pos in list(self.positions.items()):
            if code not in self.md.close.columns:
                continue
            close = self.md.close.at[date, code]
            low = self.md.low.at[date, code]
            high = self.md.high.at[date, code]
            if pd.isna(close):
                continue
            pos.peak_price = max(pos.peak_price, float(high) if pd.notna(high) else close)

            # D.1 硬止损：日内触发，按止损价成交（跌停则顺延）
            stop_px = pos.avg_cost * (1 - ex.hard_stop)
            if pd.notna(low) and low <= stop_px and pos.shares > 0:
                if self._can_sell_intraday(date, code):
                    fill = min(stop_px, self.md.open.at[date, code])
                    self._sell(Order(code, pos.board, "sell", None, "硬止损-8%"),
                               date, fill, "硬止损-8%")
                    continue
                self.blocked.append({"date": date, "code": code, "side": "sell",
                                     "reason": "跌停无法止损"})

            gain = close / pos.avg_cost - 1.0 if pos.avg_cost else 0.0

            # D.3 移动止盈
            if gain >= ex.trail_after_gain:
                if close <= pos.peak_price * (1 - ex.trail_drawdown):
                    self._queue_sell(code, pos, "移动止盈")
                    continue

            # D.1 跌破 20 日线
            if bool(self.ma_break.at[date, code]):
                self._queue_sell(code, pos, "跌破20日线")
                continue

            # D.4 板块级退出
            se = self.sector_exit.get(pos.board)
            if se is not None and date in se.index and bool(se.loc[date]):
                self._queue_sell(code, pos, "板块跌破60日线")
                continue

            # D.2 逻辑止损：已披露业绩转差 → 减仓一半（只做一次）
            if not pos.trimmed:
                improving = self.md.panel.asof(date, "improving", [code])
                if len(improving) and float(improving.iloc[0]) == 0.0 and gain < 0.15:
                    pos.trimmed = True
                    self._queue_sell(code, pos, "逻辑止损-业绩转差",
                                     qty=int(pos.shares * ex.logic_stop_trim // 100) * 100)
                    continue

            # 时间止损
            if pos.entry_date is not None:
                held = int(np.busday_count(pos.entry_date.date(), date.date()))
                if held >= ex.max_holding_days:
                    self._queue_sell(code, pos, "时间止损")

    def _can_sell_intraday(self, date: pd.Timestamp, code: str) -> bool:
        """只有全天封死跌停（最高价都在跌停位）才真正卖不掉。

        用「日内最低价触及跌停」来判定不可卖是错的 —— 盘中砸到跌停又拉回
        的票当天完全可以出货，那样会把一批本该止损成功的仓位错误地留到
        次日，人为放大亏损。
        """
        prev = self.prev_close.at[date, code]
        high = self.md.high.at[date, code]
        amt = self.md.amount.at[date, code]
        if not (amt > 0) or pd.isna(prev) or prev <= 0 or pd.isna(high):
            return False
        limit = self.limit_pct.get(code, self.cfg.cost.limit_up_threshold)
        return (high / prev - 1.0) > -limit + 1e-9

    def _queue_sell(self, code: str, pos: Position, reason: str, qty: int | None = None) -> None:
        if any(o.code == code and o.side == "sell" for o in self.pending):
            return
        self.pending.append(Order(code, pos.board, "sell", qty, reason))

    # -- 信号生成（规范 B + C） ------------------------------------------
    def _generate_orders(self, date: pd.Timestamp) -> None:
        cfg, md = self.cfg, self.md
        e = cfg.entry
        equity = self._equity_value(date)

        # 加仓：已有持仓、未满三笔、浮盈达标且当日突破
        for code, pos in self.positions.items():
            if pos.tranches_filled >= len(e.tranches) or code not in md.close.columns:
                continue
            close = md.close.at[date, code]
            if pd.isna(close) or not pos.avg_cost:
                continue
            gain = close / pos.avg_cost - 1.0
            if gain >= e.add_on_breakout_gain and bool(self.breakout_entry.at[date, code]):
                if not any(o.code == code for o in self.pending):
                    self.pending.append(Order(code, pos.board, "buy", None, pos.reason,
                                              pos.planned_weight, pos.tranches_filled,
                                              {"campaign_start": pos.campaign_start,
                                               "setup": pos.setup}))

        if len(self.positions) >= e.max_positions:
            return

        planned_value = equity * e.max_weight_per_stock
        board_weights = self._board_weights(date, equity)

        candidates: list[pd.DataFrame] = []
        for board, sig in md.sector_signals.items():
            if date not in sig.index or not bool(sig.at[date, "qualified"]):
                continue
            if board_weights.get(board, 0.0) >= e.max_weight_per_sector:
                continue
            c = select(md, cfg, board, date, planned_value)
            if not c.empty:
                candidates.append(c)
        if not candidates:
            return
        pool = pd.concat(candidates, ignore_index=True)
        # 交集信号优先，其次 RPS 高者优先
        pool["rank_key"] = pool["reason"].map({"both": 0, "momentum": 1, "fundamental": 2})
        pool = pool.sort_values(["rank_key", "rps"], ascending=[True, False])

        slots = e.max_positions - len(self.positions)
        for row in pool.itertuples():
            if slots <= 0:
                break
            code = row.code
            if code in self.positions or any(o.code == code for o in self.pending):
                continue
            if code not in md.close.columns:
                continue
            # C.1 买点：回调至均线缩量企稳 或 放量突破
            if not (bool(self.pullback_entry.at[date, code])
                    or bool(self.breakout_entry.at[date, code])):
                continue
            if board_weights.get(row.board, 0.0) + e.max_weight_per_stock * e.tranches[0] > e.max_weight_per_sector:
                continue
            self.pending.append(Order(code, row.board, "buy", None, row.reason,
                                      e.max_weight_per_stock, 0,
                                      {"campaign_start": row.campaign_start,
                                       "setup": getattr(row, "setup", "—")}))
            board_weights[row.board] = board_weights.get(row.board, 0.0) + \
                e.max_weight_per_stock * e.tranches[0]
            slots -= 1

    def _board_weights(self, date: pd.Timestamp, equity: float) -> dict[str, float]:
        out: dict[str, float] = {}
        for pos in self.positions.values():
            px = self.md.close.at[date, pos.code] if pos.code in self.md.close.columns else np.nan
            if pd.isna(px):
                continue
            out[pos.board] = out.get(pos.board, 0.0) + pos.shares * px / max(equity, 1.0)
        return out

    # -- 估值 -----------------------------------------------------------
    def _equity_value(self, date: pd.Timestamp) -> float:
        total = self.cash
        for pos in self.positions.values():
            if pos.code not in self.md.close.columns:
                continue
            px = self.md.close.at[date, pos.code]
            total += pos.shares * (px if pd.notna(px) else pos.avg_cost)
        return total

    def _mark(self, date: pd.Timestamp) -> None:
        self.equity.append({
            "date": date, "equity": self._equity_value(date),
            "cash": self.cash, "n_positions": len(self.positions),
        })

    def _liquidate(self, date: pd.Timestamp) -> None:
        for code, pos in list(self.positions.items()):
            px = self.md.close.at[date, code] if code in self.md.close.columns else np.nan
            if pd.isna(px):
                px = pos.avg_cost
            self._sell(Order(code, pos.board, "sell", None, "回测期末清算"),
                       date, float(px), "回测期末清算")
        if self.equity:
            self.equity[-1]["equity"] = self._equity_value(date)


@dataclass
class BacktestResult:
    config: StrategyConfig
    market: MarketData
    trades: pd.DataFrame
    equity: pd.DataFrame
    blocked: pd.DataFrame
