"""命令行入口。

    python -m sector_leader selftest  --source akshare
    python -m sector_leader backtest  --source synthetic --out output/
    python -m sector_leader backtest  --source akshare --start 2023-09-01 --end 2025-08-31
    python -m sector_leader sweep     --source synthetic
    python -m sector_leader walkforward --source synthetic
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from . import metrics, report
from .backtest import Backtester
from .config import StrategyConfig
from .datasource import get_source
from .market import load_market, rebuild_sector_signals, _derive


def _load(args) -> tuple[StrategyConfig, object, object]:
    cfg = StrategyConfig(start=args.start, end=args.end)
    if args.capital:
        cfg.initial_capital = args.capital
    if getattr(args, "chase", None):
        cfg.entry.chase_reference = args.chase
    if getattr(args, "confirm_mode", None):
        cfg.sector.confirm_mode = args.confirm_mode
    source = get_source(args.source, cfg.start, cfg.end)
    boards = source.sector_list()
    if getattr(args, "max_boards", None):
        boards = boards.head(args.max_boards)
    md = load_market(source, cfg, boards, verbose=args.verbose)
    return cfg, source, md


def cmd_backtest(args) -> None:
    cfg, source, md = _load(args)
    result = Backtester(md, cfg).run(verbose=args.verbose)
    bench = metrics.equal_weight_benchmark(md.close, cfg.initial_capital)
    summary = metrics.summarize(result, bench)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    text = report.build(result, summary)
    (out / "report.md").write_text(text, encoding="utf-8")
    result.trades.to_csv(out / "trades.csv", index=False)
    result.equity.to_csv(out / "equity.csv", index=False)
    print(text)
    print(f"\n[已写出] {out/'report.md'} / trades.csv / equity.csv")


def cmd_sweep(args) -> None:
    """参数敏感性：好策略的绩效应当是参数的连续函数，而不是几个孤立尖峰。"""
    cfg, source, md = _load(args)
    grid = {
        "sector.leg_up_min_return": [0.15, 0.20, 0.25, 0.30],
        "sector.max_retracement": [0.382, 0.50, 0.618],
        "sector.breadth_improving_ratio": [0.5, 0.6, 0.7],
        "pick.rps_min": [80.0, 85.0, 90.0, 95.0],
        "exit.hard_stop": [0.06, 0.08, 0.10, 0.12],
        "entry.max_ma_extension": [0.10, 0.15, 0.20, 0.30],
    }
    rows = []
    for path, values in grid.items():
        group, field = path.split(".")
        base = getattr(cfg, group)
        original = getattr(base, field)
        for v in values:
            setattr(base, field, v)
            # 板块层 / 派生量的参数改动必须触发重算，否则扫描出来的
            # 「不敏感」只是因为信号根本没跟着变。
            if group in ("sector", "exit"):
                rebuild_sector_signals(md, cfg)
            if group == "pick" and field == "rps_window":
                _derive(md, cfg)
            if group == "entry" and field == "pullback_to_ma":
                _derive(md, cfg)
            res = Backtester(md, cfg).run()
            st = metrics.trade_stats(res.trades)
            eq = metrics.equity_stats(res.equity, cfg.initial_capital)
            rows.append({
                "参数": path, "取值": v, "笔数": st.get("n_trades", 0),
                "胜率": round(st.get("win_rate", 0), 4),
                "盈亏比": round(st.get("payoff_ratio", 0), 2),
                "期望收益": round(st.get("expectancy", 0), 4),
                "年化": round(eq.get("cagr", 0), 4),
                "最大回撤": round(eq.get("max_drawdown", 0), 4),
            })
            print(f"  {path}={v}: 笔数 {st.get('n_trades',0)} "
                  f"胜率 {st.get('win_rate',0):.1%} 年化 {eq.get('cagr',0):.1%}")
        setattr(base, field, original)
        rebuild_sector_signals(md, cfg)
        _derive(md, cfg)

    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "sweep.csv", index=False)
    print("\n" + df.to_string(index=False))
    print(f"\n[已写出] {out/'sweep.csv'}")


def cmd_walkforward(args) -> None:
    """样本内 / 样本外切分：在前 60% 区间调参，后 40% 只验证，不回头改。"""
    cfg, source, md = _load(args)
    cal = md.calendar
    split = cal[int(len(cal) * 0.6)]
    print(f"样本内: {cal[0].date()} ~ {split.date()}　样本外: {split.date()} ~ {cal[-1].date()}\n")

    rows = []
    for label, (s, e) in {"样本内": (cal[0], split), "样本外": (split, cal[-1])}.items():
        sub = replace(cfg, start=str(s.date()), end=str(e.date()))
        sub_md = _slice_market(md, s, e)
        res = Backtester(sub_md, sub).run()
        st = metrics.trade_stats(res.trades)
        eq = metrics.equity_stats(res.equity, sub.initial_capital)
        boot = metrics.bootstrap_expectancy(res.trades)
        rows.append({
            "区间": label, "笔数": st.get("n_trades", 0),
            "胜率": f"{st.get('win_rate', 0):.1%}",
            "盈亏比": round(st.get("payoff_ratio", 0), 2),
            "期望收益": f"{st.get('expectancy', 0):.2%}",
            "年化": f"{eq.get('cagr', 0):.1%}",
            "最大回撤": f"{eq.get('max_drawdown', 0):.1%}",
            "期望为正概率": f"{boot.get('prob_positive_expectancy', float('nan')):.0%}",
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\n判读：样本外胜率/期望若较样本内大幅衰减，说明参数是拟合出来的，不是规律。")


def _slice_market(md, start, end):
    import copy
    sub = copy.copy(md)
    mask = (md.calendar >= start) & (md.calendar <= end)
    sub.calendar = md.calendar[mask]
    for attr in ("close", "open", "high", "low", "amount", "raw_close", "rps", "ma_short", "tradable"):
        df = getattr(md, attr)
        setattr(sub, attr, df.loc[sub.calendar] if not df.empty else df)
    sub.sector_signals = {b: s.loc[s.index.isin(sub.calendar)] for b, s in md.sector_signals.items()}
    return sub


def cmd_selftest(args) -> None:
    """在有网环境验证 provider 的字段映射，再开始大规模抓取。"""
    source = get_source(args.source, args.start, args.end)
    print(f"数据源: {source.name}　成分股是否点位时点: {source.members_are_point_in_time}")
    boards = source.sector_list()
    assert {"board_code", "board_name"} <= set(boards.columns), "sector_list 列名不符"
    print(f"✓ 板块 {len(boards)} 个，样例: {boards.head(3).to_dict('records')}")

    key = boards.board_name[0] if source.name == "akshare" else boards.board_code[0]
    sd = source.sector_daily(key, args.start, args.end)
    assert not sd.empty and {"date", "close", "amount"} <= set(sd.columns), "sector_daily 异常"
    print(f"✓ 板块日线 {len(sd)} 根，{sd.date.min().date()} ~ {sd.date.max().date()}")

    members = source.sector_members(key)
    print(f"✓ 成分股 {len(members)} 只，样例 {members[:5]}")

    sdd = source.stock_daily(members[0], args.start, args.end)
    assert not sdd.empty, "stock_daily 为空"
    print(f"✓ 个股日线 {len(sdd)} 根，含 raw_close: {'raw_close' in sdd.columns}")

    fin = source.financials(members[:30], args.start, args.end)
    if fin.empty:
        print("✗ 财务数据为空 —— 基本面门槛将全部失效，请先修好财务接口")
    else:
        assert fin["disclosure_date"].notna().all(), "存在缺公告日的财报记录（会引入前视偏差）"
        lag = (fin["disclosure_date"] - fin["report_period"]).dt.days
        print(f"✓ 财报 {len(fin)} 条，披露滞后中位数 {lag.median():.0f} 天 "
              f"(区间 {lag.min():.0f}~{lag.max():.0f})")
    print("\n自检通过。")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="sector_leader", description="板块动量+龙头策略回测")
    p.add_argument("--source", default="synthetic", choices=["synthetic", "akshare", "eastmoney"])
    p.add_argument("--start", default="2023-09-01")
    p.add_argument("--end", default="2025-08-31")
    p.add_argument("--capital", type=float, default=None)
    p.add_argument("--out", default="quant/output")
    p.add_argument("--max-boards", type=int, default=None, dest="max_boards")
    p.add_argument("--chase", choices=["ma_extension", "campaign_start"], default=None,
                   help="禁止追高的口径：乖离率 或 距板块启动涨幅")
    p.add_argument("--confirm-mode", dest="confirm_mode", default=None,
                   choices=["either", "reversal", "pullback"],
                   help="板块确认路径：原文的任一成立 / 只做反转启动 / 只做回调")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("command", choices=["backtest", "sweep", "walkforward", "selftest"])
    args = p.parse_args(argv)
    {"backtest": cmd_backtest, "sweep": cmd_sweep,
     "walkforward": cmd_walkforward, "selftest": cmd_selftest}[args.command](args)


if __name__ == "__main__":
    main()
