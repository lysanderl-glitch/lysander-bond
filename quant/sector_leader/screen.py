"""单只个股的规范体检 —— 把 A/B/C/D 四组规范逐条打分。

这个模块**不给买卖建议**，只回答一件事：截至某个交易日，这只票在你自己
定下的规范里，哪几条过、哪几条不过、实际数值离阈值有多远。

判断留给你，依据摆在桌面上。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .datasource.base import is_st
from .market import MarketData


@dataclass
class Check:
    group: str          # 规范 A / B / C / D
    rule: str           # 规范条款
    requirement: str    # 要求
    actual: str         # 实际
    passed: bool | None  # None = 数据缺失，无法判定

    @property
    def mark(self) -> str:
        return {True: "✅", False: "❌", None: "⚠️"}[self.passed]


def _fmt(x, pct: bool = False, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "无数据"
    return f"{x * 100:.{digits}f}%" if pct else f"{x:,.{digits}f}"


def evaluate(md: MarketData, cfg: StrategyConfig, code: str,
             date: pd.Timestamp, board: str) -> list[Check]:
    checks: list[Check] = []
    A = checks.append
    sig = md.sector_signals.get(board)
    if sig is None or date not in sig.index:
        return [Check("数据", "板块信号", "需要板块指数日线", "缺失", None)]
    row = sig.loc[date]
    s, p, e, x = cfg.sector, cfg.pick, cfg.entry, cfg.exit

    # ---------------- 规范 A：板块 ----------------
    A(Check("A 板块", "A.1 站上 20/60 日均线",
            f"收盘 > MA20 且 > MA60",
            f"收盘 {_fmt(row['close'])} / MA20 {_fmt(row['ma_s'])} / MA60 {_fmt(row['ma_l'])}",
            bool(row["close"] > row["ma_s"] and row["close"] > row["ma_l"])))
    A(Check("A 板块", "A.1 MA60 走平或向上",
            f"{s.ma_long_slope_window} 日斜率 ≥ {s.ma_long_slope_min}",
            _fmt(row.get("ma_l_slope"), pct=True),
            None if pd.isna(row.get("ma_l_slope"))
            else bool(row["ma_l_slope"] >= s.ma_long_slope_min)))
    A(Check("A 板块", "A.2 反转确认（放量长阳/连续放量）",
            f"{s.breakout_lookback} 日内出现单日涨 ≥{s.breakout_day_return:.0%} 且量比 ≥{s.volume_surge_ratio}",
            "成立" if row["reversal_ok"] else "不成立", bool(row["reversal_ok"])))
    A(Check("A 板块", "A.2 回调确认（幅度/回撤/缩量）",
            f"第一波涨幅 ≥{s.leg_up_min_return:.0%}，回撤 ≤{s.max_retracement:.0%}，且缩量",
            f"本波涨幅 {_fmt(row.get('leg_gain'), pct=True)}，"
            f"当前回撤 {_fmt(row.get('retrace'), pct=True)}",
            bool(row["pullback_ok"])))
    A(Check("A 板块", "A.2 买点类型", "反转 或 回调",
            str(row.get("setup", "—")), None if row.get("setup") == "—" else True))
    A(Check("A 板块", "A.3 成分股增速环比改善广度",
            f"≥ {s.breadth_improving_ratio:.0%}", _fmt(row.get("breadth"), pct=True),
            bool(row.get("gate_breadth"))))
    A(Check("A 板块", "A.3 板块增速加速（季度环比）", "本季增速中位数 > 上季",
            f"增速中位数 {_fmt(row.get('median_growth'), pct=True)}",
            bool(row.get("gate_accel"))))
    A(Check("A 板块", "A.3 板块增速为正", "增速中位数 > 0",
            _fmt(row.get("median_growth"), pct=True), bool(row.get("gate_level"))))
    A(Check("A 板块", "A.3 基本面门槛合计",
            f"至少满足 {s.min_fundamental_gates} 条", f"满足 {int(row.get('gate_count', 0))} 条",
            bool(row.get("fundamental_ok"))))
    A(Check("A 板块", "板块总判定", "技术面 且 基本面 同时成立",
            "合格" if row["qualified"] else "不合格", bool(row["qualified"])))

    # ---------------- 规范 B：个股 ----------------
    members = [c for c in md.members.get(board, []) if c in md.close.columns]
    start = row.get("campaign_start")

    if pd.notna(start) and start in md.close.index and code in md.close.columns:
        gains = (md.close.loc[date, members] / md.close.loc[start, members] - 1.0).dropna()
        rank = int((gains > gains.get(code, -9)).sum()) + 1
        A(Check("B 个股", "B.1 涨幅龙头（板块启动以来）",
                f"板块内前 {p.momentum_top_n} 名",
                f"第 {rank}/{len(gains)} 名，涨幅 {_fmt(gains.get(code), pct=True)}"
                f"（启动日 {pd.Timestamp(start).date()}）",
                rank <= p.momentum_top_n))
    else:
        A(Check("B 个股", "B.1 涨幅龙头", "板块启动日可识别", "无法定位启动日", None))

    rps = md.rps.loc[date, code] if (date in md.rps.index and code in md.rps.columns) else np.nan
    A(Check("B 个股", "B.1 相对强度 RPS", f"≥ {p.rps_min:.0f}",
            _fmt(rps, digits=1), None if pd.isna(rps) else bool(rps >= p.rps_min)))

    rev = md.panel.asof(date, "revenue_yoy", members)
    npf = md.panel.asof(date, "net_profit_yoy", members)
    roe = md.panel.asof(date, "roe", members)
    if code in rev.index or code in npf.index:
        score = (rev.rank(pct=True).reindex(members).fillna(0)
                 + npf.rank(pct=True).reindex(members).fillna(0)) / 2.0
        frank = int((score > score.get(code, -9)).sum()) + 1
        A(Check("B 个股", "B.2 业绩龙头（营收+净利增速综合）",
                f"板块内前 {p.fundamental_top_n} 名",
                f"第 {frank}/{len(score)} 名，营收同比 {_fmt(rev.get(code), pct=True)}，"
                f"净利同比 {_fmt(npf.get(code), pct=True)}",
                frank <= p.fundamental_top_n))
        med = float(roe.median()) if len(roe) else np.nan
        A(Check("B 个股", "B.2 ROE 高于板块中位数", f"ROE ≥ {_fmt(med, pct=True)}",
                _fmt(roe.get(code), pct=True),
                None if pd.isna(med) or code not in roe.index
                else bool(roe.get(code) >= med)))
    else:
        A(Check("B 个股", "B.2 业绩龙头", "需已公告财报", "该日无已披露财报数据", None))

    name = ""
    hit = md.meta[md.meta["code"] == code]
    if not hit.empty:
        name = str(hit.iloc[0]["name"])
    A(Check("B 个股", "B.4 排除 ST / 退市风险", "非 ST、非退市整理",
            name or "无名称数据", None if not name else not is_st(name)))

    adv20 = md.amount[code].rolling(20, min_periods=10).mean().loc[date] \
        if code in md.amount.columns else np.nan
    A(Check("B 个股", "B.4 流动性",
            f"日均成交额 ≥ 计划持仓 × {p.liquidity_multiple:.0f}",
            f"20 日均额 {_fmt(adv20 / 1e8)} 亿元 → 可容纳单笔持仓上限约 "
            f"{_fmt(adv20 / p.liquidity_multiple / 1e4)} 万元",
            None if pd.isna(adv20) else True))
    A(Check("B 个股", "B.4 质押 / 减持 / 违规",
            "大股东无高质押、近期无重要股东减持、无监管处罚",
            "本工具不覆盖，须人工查公告", None))

    # ---------------- 规范 C：介入 ----------------
    close = md.close.at[date, code] if code in md.close.columns else np.nan
    ma20 = md.ma_short.at[date, code] if code in md.ma_short.columns else np.nan
    ext = close / ma20 - 1.0 if pd.notna(close) and pd.notna(ma20) and ma20 > 0 else np.nan
    if e.chase_reference == "campaign_start":
        gain_since = (close / md.close.loc[start, code] - 1.0) \
            if pd.notna(start) and start in md.close.index else np.nan
        A(Check("C 介入", "C.4 禁止追高（距启动涨幅）",
                f"≤ {e.max_chase_gain:.0%}", _fmt(gain_since, pct=True),
                None if pd.isna(gain_since) else bool(gain_since <= e.max_chase_gain)))
    else:
        A(Check("C 介入", "C.4 禁止追高（对 MA20 乖离率）",
                f"≤ {e.max_ma_extension:.0%}", _fmt(ext, pct=True),
                None if pd.isna(ext) else bool(ext <= e.max_ma_extension)))

    amt = md.amount.at[date, code] if code in md.amount.columns else np.nan
    amt5 = md.amount[code].rolling(5, min_periods=5).mean().loc[date] \
        if code in md.amount.columns else np.nan
    near = abs(ext) <= e.pullback_ma_tolerance if pd.notna(ext) else False
    shrink = amt < amt5 * e.pullback_volume_shrink if pd.notna(amt) and pd.notna(amt5) else False
    op = md.open.at[date, code] if code in md.open.columns else np.nan
    stabilize = close >= op if pd.notna(close) and pd.notna(op) else False
    A(Check("C 介入", "C.1 买点一：回调至 MA20 缩量企稳",
            f"|乖离| ≤{e.pullback_ma_tolerance:.0%}、量 < 5日均量×{e.pullback_volume_shrink}、收阳",
            f"乖离 {_fmt(ext, pct=True)}、量比 {_fmt(amt / amt5 if pd.notna(amt5) and amt5 else np.nan)}、"
            f"{'收阳' if stabilize else '收阴'}",
            bool(near and shrink and stabilize)))

    prior_high = md.close[code].shift(1).rolling(10, min_periods=5).max().loc[date] \
        if code in md.close.columns else np.nan
    brk = (close > prior_high) and (amt >= amt5 * e.breakout_confirm_volume) \
        if pd.notna(prior_high) and pd.notna(amt5) else False
    A(Check("C 介入", "C.1 买点二：放量突破回调期高点",
            f"收盘 > 前 10 日高点 且 量 ≥ 5日均量×{e.breakout_confirm_volume}",
            f"前高 {_fmt(prior_high)}、现价 {_fmt(close)}", bool(brk)))

    A(Check("C 介入", "C.2/C.3 仓位纪律",
            f"首笔 ≤ 计划仓位 {e.tranches[0]:.0%}；单股 ≤{e.max_weight_per_stock:.0%}、"
            f"单板块 ≤{e.max_weight_per_sector:.0%}",
            "由你执行，工具不代管", None))

    # ---------------- 规范 D：预设退出 ----------------
    if pd.notna(close):
        A(Check("D 风控", "D.1 硬止损位（若此刻买入）",
                f"买入价 −{x.hard_stop:.0%}", f"约 {_fmt(close * (1 - x.hard_stop))} 元",
                None))
        A(Check("D 风控", "D.1 均线止损位",
                f"连续 {x.ma_break_confirm_days} 日收在 MA20×(1−{x.ma_break_buffer:.0%}) 下方",
                f"当前 MA20 {_fmt(ma20)} → 触发线约 {_fmt(ma20 * (1 - x.ma_break_buffer))} 元",
                None))
        risk = x.hard_stop
        A(Check("D 风控", "风险回报预估",
                f"止损 {risk:.0%}，需盈亏比 ≥2 才值得进",
                f"目标价至少 {_fmt(close * (1 + 2 * risk))} 元（+{2 * risk:.0%}）", None))
    A(Check("D 风控", "D.4 板块级退出信号",
            f"板块指数跌破 MA{x.sector_exit_ma} 即清仓该板块",
            "已跌破" if bool(row.get("sector_exit")) else "未跌破",
            not bool(row.get("sector_exit"))))
    return checks


def render(checks: list[Check], code: str, name: str, board_name: str,
           date: pd.Timestamp, source_name: str) -> str:
    lines: list[str] = []
    A = lines.append
    A(f"\n{'=' * 78}")
    A(f" 规范体检：{code} {name}　|　所属板块：{board_name}")
    A(f" 截至交易日：{date:%Y-%m-%d}　|　数据源：{source_name}")
    A(f"{'=' * 78}\n")

    group = None
    for c in checks:
        if c.group != group:
            group = c.group
            A(f"\n【{group}】")
        A(f" {c.mark} {c.rule}")
        A(f"      要求：{c.requirement}")
        A(f"      实际：{c.actual}")

    scored = [c for c in checks if c.passed is not None]
    passed = sum(1 for c in scored if c.passed)
    failed = [c for c in scored if not c.passed]
    unknown = [c for c in checks if c.passed is None]

    A(f"\n{'-' * 78}")
    A(f" 可判定条款 {len(scored)} 条，通过 {passed} 条，未通过 {len(failed)} 条，"
      f"另有 {len(unknown)} 条需人工核实")
    if failed:
        A("\n 未通过的条款：")
        for c in failed:
            A(f"   ❌ {c.rule} —— {c.actual}")
    A("")
    A(" 本输出是规范打分表，不是买卖建议。规范全部通过也不代表这笔交易会赚钱；")
    A(" 只代表它符合你事先定下的纪律。任何一条不通过，按你自己规范 E 的要求，")
    A(" 强行进场都应记为违规交易 —— 哪怕最后赚了。")
    A(f"{'=' * 78}\n")
    return "\n".join(lines)
