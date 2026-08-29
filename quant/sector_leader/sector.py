"""规范 A —— 板块筛选。

产出：每个板块一张与交易日等长的信号表，列含各条规则的布尔判定与
中间量。策略在回测里只做查表，不做重算，因此信号是「同一份代码同时
服务回测与实盘选股」——避免了研究与实盘两套逻辑漂移。

关于基本面三道门槛的现实情况
--------------------------
规范原文的三条是：①成分股增速环比改善占比 ②分析师盈利预测上调/下调
③行业中观数据（价格/订单/开工率/库存）。免费数据源只能覆盖 ①，另外
两条需要 Wind / Choice / 卓创等付费源。这里的处理是：

- 用业绩报表可算的三条量化门槛替代（广度、加速度、水平），
- 同时开放 `external_gates` 钩子，你接入付费数据后可直接注入布尔序列，
- 报告里如实标注实际启用了哪几道门槛 —— 不假装做了做不到的验证。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .fundamentals import FundamentalPanel
from .indicators import amount_ratio, daily_return, leg_up_and_retracement, sma, slope


class SectorScreener:
    def __init__(self, config: StrategyConfig, panel: FundamentalPanel):
        self.cfg = config
        self.panel = panel

    def build(
        self,
        board_code: str,
        board_name: str,
        daily: pd.DataFrame,
        members: list[str],
        external_gates: dict[str, pd.Series] | None = None,
    ) -> pd.DataFrame:
        r = self.cfg.sector
        df = daily.set_index("date").copy()
        close, amount = df["close"], df["amount"]

        # --- A.1 趋势结构 ---------------------------------------------
        df["ma_s"] = sma(close, r.ma_short)
        df["ma_l"] = sma(close, r.ma_long)
        df["ma_l_slope"] = slope(df["ma_l"], r.ma_long_slope_window)
        trend_ok = (close > df["ma_s"]) & (close > df["ma_l"]) & (df["ma_l_slope"] >= r.ma_long_slope_min)

        # --- A.2 反转确认：放量长阳 或 连续放量 -------------------------
        ret = daily_return(close)
        amt_ratio = amount_ratio(amount, 20)
        big_bull = (ret >= r.breakout_day_return) & (amt_ratio >= r.volume_surge_ratio)
        consecutive = (amt_ratio >= r.volume_surge_ratio).rolling(
            r.volume_surge_days, min_periods=r.volume_surge_days
        ).sum() >= r.volume_surge_days
        reversal_ok = (
            big_bull.rolling(r.breakout_lookback, min_periods=1).sum() > 0
        ) | (consecutive.rolling(r.breakout_lookback, min_periods=1).sum() > 0)

        # --- A.2 回调确认：第一波涨幅够、回撤不过半、缩量 ---------------
        legs = leg_up_and_retracement(close, lookback=120)
        legs.index = df.index
        amt5 = amount.rolling(5, min_periods=5).mean()
        peak_amt5 = amt5.shift(1).rolling(60, min_periods=5).max()
        volume_shrunk = amt5 < peak_amt5 * r.pullback_volume_ratio
        pullback_ok = (
            (legs["leg_gain"] >= r.leg_up_min_return)
            & (legs["retrace"] <= r.max_retracement)
            & (legs["retrace"] > 0.02)              # 已有实质回调，不是在高点
            & (legs["days_since_high"] >= 3)
            & volume_shrunk
        )

        if r.confirm_mode == "reversal":
            confirmed = reversal_ok
        elif r.confirm_mode == "pullback":
            confirmed = pullback_ok
        else:
            confirmed = reversal_ok | pullback_ok
        technical_ok = trend_ok & confirmed

        # --- A.3 基本面验证（可用门槛计数） ----------------------------
        breadth = pd.Series(
            [self.panel.improving_ratio(d, members) for d in df.index], index=df.index
        )
        med_growth = pd.Series(
            [_median(self.panel.asof(d, "growth", members)) for d in df.index], index=df.index
        )
        gate_breadth = breadth >= r.breadth_improving_ratio
        gate_accel = med_growth > med_growth.shift(63)     # 季度环比加速
        gate_level = med_growth > 0                         # 增速为正
        gates = pd.DataFrame({
            "gate_breadth": gate_breadth.fillna(False),
            "gate_accel": gate_accel.fillna(False),
            "gate_level": gate_level.fillna(False),
        })
        if external_gates:
            for name, series in external_gates.items():
                gates[f"gate_{name}"] = series.reindex(df.index).fillna(False).astype(bool)
        gate_count = gates.sum(axis=1)
        fundamental_ok = gate_count >= min(r.min_fundamental_gates, gates.shape[1])

        # --- A.4 排除 --------------------------------------------------
        excluded = any(tok and tok in board_name for tok in r.excluded_boards)

        out = pd.DataFrame(index=df.index)
        out["board_code"] = board_code
        out["board_name"] = board_name
        out["close"] = close
        out["ma_s"], out["ma_l"] = df["ma_s"], df["ma_l"]
        out["trend_ok"] = trend_ok.fillna(False)
        out["reversal_ok"] = reversal_ok.fillna(False)
        out["pullback_ok"] = pullback_ok.fillna(False)
        out["technical_ok"] = technical_ok.fillna(False)
        # 记录是哪条路径把这一天放进来的，供报告拆分两类买点各自的胜率
        out["setup"] = np.where(
            (reversal_ok & pullback_ok).fillna(False), "反转+回调",
            np.where(pullback_ok.fillna(False), "回调",
                     np.where(reversal_ok.fillna(False), "反转", "—")))
        out["breadth"] = breadth
        out["median_growth"] = med_growth
        out = pd.concat([out, gates], axis=1)
        out["gate_count"] = gate_count
        out["fundamental_ok"] = fundamental_ok
        out["qualified"] = out["technical_ok"] & out["fundamental_ok"] & (not excluded)
        # 板块启动日：当前波段的起涨低点，供规范 B/C 计算「启动以来涨幅」
        idx_pos = legs["leg_low_idx"].to_numpy(dtype=float)
        index_values = df.index.to_numpy()
        safe = np.nan_to_num(idx_pos, nan=0.0).astype(int).clip(0, len(index_values) - 1)
        start_dates = pd.Series(index_values[safe], index=df.index)
        out["campaign_start"] = start_dates.where(~np.isnan(idx_pos))
        out["leg_gain"] = legs["leg_gain"]
        out["retrace"] = legs["retrace"]
        out["sector_exit"] = close < sma(close, self.cfg.exit.sector_exit_ma)
        return out


def _median(s: pd.Series) -> float:
    return float(s.median()) if len(s) else float("nan")


def build_all(
    source, config: StrategyConfig, panel: FundamentalPanel, boards: pd.DataFrame,
    members_map: dict[str, list[str]], verbose: bool = False,
) -> dict[str, pd.DataFrame]:
    screener = SectorScreener(config, panel)
    signals: dict[str, pd.DataFrame] = {}
    for _, row in boards.iterrows():
        code, name = row["board_code"], row["board_name"]
        daily = source.sector_daily(name if source.name == "akshare" else code,
                                    config.start, config.end)
        if daily.empty or len(daily) < config.sector.ma_long + 20:
            continue
        signals[code] = screener.build(code, name, daily, members_map.get(code, []))
        if verbose:
            q = int(signals[code]["qualified"].sum())
            print(f"  {code} {name}: 合格交易日 {q}/{len(signals[code])}")
    return signals
