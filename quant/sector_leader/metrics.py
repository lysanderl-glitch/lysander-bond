"""绩效统计。

「胜率」单独一个数字几乎没有决策价值 —— 一个 80% 胜率、盈亏比 0.2 的
策略是净亏的。这里始终把四个数放在一起看：

    期望收益/笔 = 胜率 × 平均盈利 − (1 − 胜率) × 平均亏损

再加上两件多数回测会漏掉的事：

1. **置信区间**。两年 A 股跑出来的样本通常只有几十到几百笔，胜率的
   标准误很大。这里用 bootstrap 给出期望收益的 95% 区间；如果区间跨过
   0，那么「这套策略有正期望」这句话在该样本上就不成立。
2. **基准对照**。板块动量策略天然吃 beta，牛市里随便买都赚。所以必须
   和「等权持有同一股票池」对比，看超额是否为正 —— 否则你只是买了个
   高换手、高成本的指数。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 244   # A 股年均交易日


def trade_stats(trades: pd.DataFrame) -> dict:
    if trades is None or trades.empty:
        return {"n_trades": 0}
    r = trades["return"].dropna()
    wins, losses = r[r > 0], r[r <= 0]
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(-losses.mean()) if len(losses) else 0.0
    win_rate = len(wins) / len(r) if len(r) else 0.0
    gross_profit = float(trades.loc[trades["pnl"] > 0, "pnl"].sum())
    gross_loss = float(-trades.loc[trades["pnl"] <= 0, "pnl"].sum())
    return {
        "n_trades": int(len(r)),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": avg_win / avg_loss if avg_loss > 0 else float("inf"),
        "expectancy": float(r.mean()),
        "expectancy_formula": win_rate * avg_win - (1 - win_rate) * avg_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else float("inf"),
        "median_return": float(r.median()),
        "best": float(r.max()),
        "worst": float(r.min()),
        "avg_holding_days": float(trades["holding_days"].mean()),
        "total_pnl": float(trades["pnl"].sum()),
    }


def concentration(trades: pd.DataFrame) -> dict:
    """收益集中度 —— 回测最常见的假象：总收益其实来自一两笔极端行情。

    如果剔除最好的 3 笔后策略就不赚钱了，那么「胜率」这个统计量描述的
    并不是你真实会遇到的分布，而是一次幸运的尾部事件。
    """
    if trades is None or trades.empty:
        return {}
    pnl = trades["pnl"].astype(float)
    total = float(pnl.sum())
    top = pnl.sort_values(ascending=False)
    out = {
        "top1_share": float(top.iloc[0] / total) if total > 0 else float("nan"),
        "top3_share": float(top.head(3).sum() / total) if total > 0 else float("nan"),
        "pnl_ex_top3": float(total - top.head(3).sum()),
        "profitable_ex_top3": bool(total - top.head(3).sum() > 0),
    }
    # 最大连续亏损笔数
    streak = worst = 0
    for r in trades.sort_values("exit_date")["return"]:
        streak = streak + 1 if r <= 0 else 0
        worst = max(worst, streak)
    out["max_consecutive_losses"] = int(worst)
    return out


def bootstrap_expectancy(trades: pd.DataFrame, n_boot: int = 5000,
                         seed: int = 7) -> dict:
    """对每笔收益率做 bootstrap，给出期望收益与胜率的 95% 置信区间。"""
    if trades is None or trades.empty:
        return {}
    r = trades["return"].dropna().to_numpy()
    if len(r) < 5:
        return {"note": "样本笔数过少（<5），不做区间估计"}
    rng = np.random.default_rng(seed)
    draws = rng.choice(r, size=(n_boot, len(r)), replace=True)
    means = draws.mean(axis=1)
    wins = (draws > 0).mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {
        "expectancy_ci95": (float(lo), float(hi)),
        "win_rate_ci95": tuple(float(x) for x in np.percentile(wins, [2.5, 97.5])),
        "prob_positive_expectancy": float((means > 0).mean()),
        "significant": bool(lo > 0),
    }


def equity_stats(equity: pd.DataFrame, initial: float) -> dict:
    if equity is None or equity.empty:
        return {}
    eq = equity.set_index("date")["equity"].astype(float)
    ret = eq.pct_change().dropna()
    days = len(eq)
    total = float(eq.iloc[-1] / initial - 1.0)
    years = days / TRADING_DAYS
    cagr = (1 + total) ** (1 / years) - 1 if years > 0 and total > -1 else float("nan")
    dd = eq / eq.cummax() - 1.0
    vol = float(ret.std() * np.sqrt(TRADING_DAYS)) if len(ret) > 1 else float("nan")
    downside = ret[ret < 0]
    dvol = float(downside.std() * np.sqrt(TRADING_DAYS)) if len(downside) > 1 else float("nan")
    mdd = float(dd.min())
    return {
        "total_return": total,
        "cagr": float(cagr),
        "volatility": vol,
        "sharpe": float(cagr / vol) if vol and vol == vol and vol > 0 else float("nan"),
        "sortino": float(cagr / dvol) if dvol and dvol == dvol and dvol > 0 else float("nan"),
        "max_drawdown": mdd,
        "calmar": float(cagr / abs(mdd)) if mdd < 0 else float("nan"),
        "final_equity": float(eq.iloc[-1]),
        "days": days,
        "exposure": float((equity["n_positions"] > 0).mean()),
    }


def equal_weight_benchmark(close: pd.DataFrame, initial: float) -> pd.DataFrame:
    """等权买入持有同一股票池 —— 剥离 beta 的对照组。"""
    ret = close.pct_change()
    daily = ret.mean(axis=1, skipna=True).fillna(0.0)
    eq = initial * (1 + daily).cumprod()
    return pd.DataFrame({"date": close.index, "equity": eq.to_numpy(),
                         "cash": 0.0, "n_positions": 1})


def group_stats(trades: pd.DataFrame, by: str) -> pd.DataFrame:
    if trades is None or trades.empty or by not in trades.columns:
        return pd.DataFrame()
    rows = []
    for key, grp in trades.groupby(by):
        st = trade_stats(grp)
        rows.append({by: key, "笔数": st["n_trades"], "胜率": st["win_rate"],
                     "平均盈利": st["avg_win"], "平均亏损": st["avg_loss"],
                     "盈亏比": st["payoff_ratio"], "期望收益": st["expectancy"],
                     "累计盈亏": st["total_pnl"]})
    return pd.DataFrame(rows).sort_values("累计盈亏", ascending=False).reset_index(drop=True)


def monthly_returns(equity: pd.DataFrame) -> pd.Series:
    if equity is None or equity.empty:
        return pd.Series(dtype=float)
    eq = equity.set_index("date")["equity"].astype(float)
    return eq.resample("ME").last().pct_change().dropna()


def summarize(result, benchmark_equity: pd.DataFrame | None = None) -> dict:
    cfg = result.config
    out = {
        "trade": trade_stats(result.trades),
        "concentration": concentration(result.trades),
        "bootstrap": bootstrap_expectancy(result.trades),
        "equity": equity_stats(result.equity, cfg.initial_capital),
        "by_entry_reason": group_stats(result.trades, "entry_reason"),
        "by_setup": group_stats(result.trades, "setup"),
        "by_exit_reason": group_stats(result.trades, "exit_reason"),
        "by_board": group_stats(result.trades, "board_name"),
        "monthly": monthly_returns(result.equity),
        "blocked_orders": int(len(result.blocked)) if result.blocked is not None else 0,
    }
    if benchmark_equity is not None and not benchmark_equity.empty:
        bench = equity_stats(benchmark_equity, cfg.initial_capital)
        out["benchmark"] = bench
        out["excess_return"] = out["equity"].get("total_return", np.nan) - bench.get("total_return", np.nan)
    return out
