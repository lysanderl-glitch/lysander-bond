"""回测报告（Markdown）。

报告刻意把「结论」和「这个结论能不能信」放在同等位置：置信区间、
基准对照、数据源缺陷都写进正文，而不是脚注。
"""

from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd


def _pct(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "—"
    return f"{x * 100:.{digits}f}%"


def _num(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "—"
    return f"{x:,.{digits}f}"


def build(result, summary: dict, data_warnings: list[str] | None = None) -> str:
    cfg = result.config
    t, e, b = summary["trade"], summary["equity"], summary.get("bootstrap", {})
    bench = summary.get("benchmark", {})
    md = result.market

    lines: list[str] = []
    A = lines.append

    A("# 板块动量 + 龙头策略 回测报告")
    A("")
    A(f"生成时间：{datetime.now():%Y-%m-%d %H:%M}　|　"
      f"区间：{cfg.start} ~ {cfg.end}　|　数据源：`{md.source_name}`")
    A("")

    if md.source_name == "synthetic":
        A("> ⚠️ **本次使用合成数据**。下列所有胜率与收益数字仅用于验证回测管线的")
        A("> 正确性（时序、成本、统计口径），**不具备任何投资参考价值**。真实结论")
        A("> 需以 `--source akshare` 或 `--source eastmoney` 抓取真实行情重跑。")
        A("")

    warnings = list(data_warnings or [])
    if not md.members_are_point_in_time:
        warnings.append(
            "**幸存者偏差**：数据源只提供板块的*当前*成分股，回测中被调出板块或已退市的"
            "个股不在样本内，历史胜率会被系统性高估。")
    if warnings:
        A("## 0. 结论可信度的前置声明")
        A("")
        for w in warnings:
            A(f"- {w}")
        A("")

    # -- 一、核心结论 ---------------------------------------------------
    A("## 1. 核心结论")
    A("")
    A("| 指标 | 数值 | 说明 |")
    A("|---|---:|---|")
    A(f"| 交易笔数 | {t.get('n_trades', 0)} | 样本量决定结论的稳健程度 |")
    A(f"| **胜率** | {_pct(t.get('win_rate'))} | 单独看没有意义，须与盈亏比同看 |")
    A(f"| 平均盈利 | {_pct(t.get('avg_win'))} | |")
    A(f"| 平均亏损 | {_pct(t.get('avg_loss'))} | |")
    A(f"| **盈亏比** | {_num(t.get('payoff_ratio'))} | 平均盈利 / 平均亏损 |")
    A(f"| **期望收益/笔** | {_pct(t.get('expectancy'))} | 胜率×均盈 −(1−胜率)×均亏 |")
    A(f"| 盈利因子 | {_num(t.get('profit_factor'))} | 总盈利 / 总亏损，>1 才有净收益 |")
    A(f"| 平均持有 | {_num(t.get('avg_holding_days'), 1)} 交易日 | |")
    A(f"| 最好 / 最差单笔 | {_pct(t.get('best'))} / {_pct(t.get('worst'))} | |")
    A("")
    A("| 账户指标 | 策略 | 等权基准 |")
    A("|---|---:|---:|")
    A(f"| 期间总收益 | {_pct(e.get('total_return'))} | {_pct(bench.get('total_return'))} |")
    A(f"| 年化收益 | {_pct(e.get('cagr'))} | {_pct(bench.get('cagr'))} |")
    A(f"| 年化波动 | {_pct(e.get('volatility'))} | {_pct(bench.get('volatility'))} |")
    A(f"| 最大回撤 | {_pct(e.get('max_drawdown'))} | {_pct(bench.get('max_drawdown'))} |")
    A(f"| 收益/回撤(Calmar) | {_num(e.get('calmar'))} | {_num(bench.get('calmar'))} |")
    A(f"| 夏普(无风险利率取0) | {_num(e.get('sharpe'))} | {_num(bench.get('sharpe'))} |")
    A(f"| 仓位暴露天数占比 | {_pct(e.get('exposure'))} | 100.00% |")
    if "excess_return" in summary:
        A(f"| **相对基准超额** | {_pct(summary['excess_return'])} | — |")
    A("")

    # -- 二、统计显著性 -------------------------------------------------
    A("## 2. 这个结果能不能信：统计显著性")
    A("")
    if b.get("expectancy_ci95"):
        lo, hi = b["expectancy_ci95"]
        wlo, whi = b["win_rate_ci95"]
        A(f"对 {t.get('n_trades')} 笔交易做 5000 次 bootstrap 重采样：")
        A("")
        A(f"- 期望收益/笔 95% 置信区间：**[{_pct(lo)}, {_pct(hi)}]**")
        A(f"- 胜率 95% 置信区间：**[{_pct(wlo)}, {_pct(whi)}]**")
        A(f"- 期望收益为正的概率：**{_pct(b.get('prob_positive_expectancy'))}**")
        A("")
        if b.get("significant"):
            A("✅ 置信区间下界大于 0：在本样本上「策略有正期望」这个说法站得住。")
        else:
            A("⚠️ **置信区间跨过 0**：以现有样本量，无法排除「这套策略的期望收益其实是 0」。")
            A("需要更长区间或更多标的来提高样本量，才能对胜率下结论。")
    else:
        A(b.get("note", "样本不足，未做区间估计。"))
    A("")

    # -- 二之二、收益集中度 ---------------------------------------------
    c = summary.get("concentration") or {}
    if c:
        A("### 收益集中度")
        A("")
        A(f"- 最赚的 1 笔贡献了总盈亏的 **{_pct(c.get('top1_share'))}**")
        A(f"- 最赚的 3 笔合计贡献 **{_pct(c.get('top3_share'))}**")
        A(f"- 剔除最好的 3 笔后，累计盈亏 = **{_num(c.get('pnl_ex_top3'), 0)}**"
          f"（{'仍为正' if c.get('profitable_ex_top3') else '转为负'}）")
        A(f"- 最大连续亏损：**{c.get('max_consecutive_losses')}** 笔（决定你需要多强的心理与资金承受力）")
        A("")
        if not c.get("profitable_ex_top3"):
            A("⚠️ **剔除三笔最佳交易后策略即不赚钱**：本次收益高度依赖极少数尾部行情，")
            A("「胜率 / 期望收益」的样本代表性存疑，不能据此推断未来。")
            A("")

    # -- 三、分组归因 ---------------------------------------------------
    A("## 3. 收益来自哪里")
    A("")
    for title, key in (("按入场信号类型", "by_entry_reason"),
                       ("按板块买点类型（反转启动 vs 回调）", "by_setup"),
                       ("按出场原因", "by_exit_reason"),
                       ("按板块（取前 10）", "by_board")):
        df = summary.get(key)
        if df is None or df.empty:
            continue
        A(f"### {title}")
        A("")
        show = df.head(10).copy()
        for col in ("胜率", "平均盈利", "平均亏损", "期望收益"):
            if col in show.columns:
                show[col] = show[col].map(lambda v: _pct(v))
        for col in ("盈亏比",):
            if col in show.columns:
                show[col] = show[col].map(lambda v: _num(v))
        if "累计盈亏" in show.columns:
            show["累计盈亏"] = show["累计盈亏"].map(lambda v: _num(v, 0))
        A(_md_table(show))
        A("")

    # -- 四、月度 -------------------------------------------------------
    monthly = summary.get("monthly")
    if monthly is not None and len(monthly):
        A("### 月度收益")
        A("")
        A("| 月份 | 收益 |")
        A("|---|---:|")
        for idx, val in monthly.items():
            A(f"| {idx:%Y-%m} | {_pct(val)} |")
        A("")

    # -- 五、执行摩擦 ---------------------------------------------------
    A("## 4. 执行摩擦")
    A("")
    A(f"- 因涨跌停 / 停牌未能按计划成交、被顺延的订单：**{summary.get('blocked_orders', 0)}** 次")
    A("- 已计入成本：佣金万 2.5（最低 5 元）、过户费、卖出印花税 0.05%、"
      f"单边滑点 {_pct(cfg.cost.slippage)}")
    A("- 成交价：T 日收盘出信号，**T+1 开盘**成交；硬止损按当日止损价成交")
    A("")

    # -- 六、参数 -------------------------------------------------------
    A("## 5. 本次参数（可复现）")
    A("")
    A("```json")
    A(json.dumps(_jsonable(cfg.to_dict()), ensure_ascii=False, indent=2))
    A("```")
    A("")
    return "\n".join(lines)


def _md_table(df: pd.DataFrame) -> str:
    """自己拼 Markdown 表，避免为一张表引入 tabulate 依赖。"""
    cols = list(df.columns)
    head = "| " + " | ".join(str(c) for c in cols) + " |"
    align = "|" + "|".join("---:" if df[c].dtype.kind in "if" else "---" for c in cols) + "|"
    rows = ["| " + " | ".join(str(v) for v in rec) + " |"
            for rec in df.itertuples(index=False, name=None)]
    return "\n".join([head, align, *rows])


def _jsonable(obj):
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj
