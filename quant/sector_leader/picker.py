"""规范 B —— 个股选取：涨幅龙头 ∩ 业绩龙头。

关键实现细节：
- 「涨幅」一律从**板块启动日**（规范 A 识别出的起涨低点）起算，而不是
  固定回看 N 日。这样才对应「本轮行情的龙头」，而不是历史强势股。
- 「业绩」只用当日**已公告**的最新一期（点位时点面板），不用未来财报。
- 交集优先；无交集时各取 fallback_each 只，并在 `reason` 里标明来源，
  报告可以据此拆分两类信号各自的胜率 —— 这是后续做参数取舍的依据。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .market import MarketData


def select(md: MarketData, cfg: StrategyConfig, board: str, date: pd.Timestamp,
           planned_position_value: float) -> pd.DataFrame:
    sig = md.sector_signals.get(board)
    if sig is None or date not in sig.index:
        return _empty()
    row = sig.loc[date]
    if not bool(row["qualified"]):
        return _empty()

    members = [c for c in md.members.get(board, []) if c in md.close.columns]
    if not members:
        return _empty()

    tradable = md.tradable.loc[date, members]
    members = [c for c in members if bool(tradable.get(c, False))]
    if not members:
        return _empty()

    p = cfg.pick
    close_now = md.close.loc[date, members]

    # -- 流动性门槛：日均成交额 >= 计划持仓 * 倍数 -----------------------
    adv20 = md.amount[members].rolling(20, min_periods=10).mean().loc[date]
    liquid = adv20 >= planned_position_value * p.liquidity_multiple
    members = [c for c in members if bool(liquid.get(c, False))]
    if not members:
        return _empty()

    # -- B.1 涨幅龙头 ---------------------------------------------------
    start = row["campaign_start"]
    if pd.isna(start) or start not in md.close.index:
        return _empty()
    close_start = md.close.loc[start, members]
    gain = (md.close.loc[date, members] / close_start - 1.0).dropna()
    rps = md.rps.loc[date, members] if date in md.rps.index else pd.Series(dtype=float)
    momentum_pool = gain[rps.reindex(gain.index).fillna(-1) >= p.rps_min]
    momentum = momentum_pool.sort_values(ascending=False).head(p.momentum_top_n)

    # -- B.2 业绩龙头 ---------------------------------------------------
    rev = md.panel.asof(date, "revenue_yoy", members)
    npf = md.panel.asof(date, "net_profit_yoy", members)
    roe = md.panel.asof(date, "roe", members)
    fundamental = pd.Series(dtype=float)
    if len(rev) or len(npf):
        score = (rev.rank(pct=True).reindex(members).fillna(0)
                 + npf.rank(pct=True).reindex(members).fillna(0)) / 2.0
        if p.roe_above_sector_median and len(roe) >= 5:
            median_roe = float(roe.median())
            ok = roe.reindex(members) >= median_roe
            score = score[ok.fillna(False)]
        fundamental = score.sort_values(ascending=False).head(p.fundamental_top_n)

    # -- B.3 交集优先 ---------------------------------------------------
    both = [c for c in momentum.index if c in fundamental.index]
    rows: list[dict] = []
    setup = str(row.get("setup", "—"))
    if both:
        for c in both:
            rows.append(_row(c, board, date, "both", gain.get(c), rps.get(c),
                             fundamental.get(c), start, setup))
    else:
        for c in list(momentum.index)[: p.fallback_each]:
            rows.append(_row(c, board, date, "momentum", gain.get(c), rps.get(c),
                             fundamental.get(c), start, setup))
        for c in list(fundamental.index)[: p.fallback_each]:
            if c in {r["code"] for r in rows}:
                continue
            rows.append(_row(c, board, date, "fundamental", gain.get(c), rps.get(c),
                             fundamental.get(c), start, setup))

    # -- B.4 禁止追高（规范 C.4，在候选阶段剔除） -----------------------
    rows = [r for r in rows if _not_chasing(md, cfg, date, r)]
    return pd.DataFrame(rows) if rows else _empty()


def _not_chasing(md: MarketData, cfg: StrategyConfig, date: pd.Timestamp, row: dict) -> bool:
    """两种「追高」口径，见 EntryRules.chase_reference 的说明。"""
    e = cfg.entry
    if e.chase_reference == "campaign_start":
        g = row["gain_since_start"]
        return not (pd.notna(g) and g > e.max_chase_gain)
    code = row["code"]
    if date not in md.ma_short.index or code not in md.ma_short.columns:
        return True
    ma = md.ma_short.at[date, code]
    px = md.close.at[date, code]
    if pd.isna(ma) or pd.isna(px) or ma <= 0:
        return True
    return (px / ma - 1.0) <= e.max_ma_extension


def _row(code, board, date, reason, gain, rps, fscore, start, setup="—") -> dict:
    return {
        "date": date, "code": code, "board": board, "reason": reason, "setup": setup,
        "gain_since_start": float(gain) if gain is not None and pd.notna(gain) else np.nan,
        "rps": float(rps) if rps is not None and pd.notna(rps) else np.nan,
        "fundamental_score": float(fscore) if fscore is not None and pd.notna(fscore) else np.nan,
        "campaign_start": start,
    }


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["date", "code", "board", "reason", "setup",
                                 "gain_since_start", "rps", "fundamental_score",
                                 "campaign_start"])
