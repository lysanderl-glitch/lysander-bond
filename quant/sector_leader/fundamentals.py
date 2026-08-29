"""点位时点（point-in-time）财务面板。

这是整套回测里最容易出错、也最影响结论可信度的一块。

核心规则：一期财报只有在 **公告日 + lag** 之后才可以被策略看到。用报告期
（如 2024-03-31）当可用日期，等于让 4 月底才披露的数据在 3 月底就参与选股，
回测收益会被显著高估 —— 这正是「业绩爬坡策略」在纸面上特别好看的主因。

面板把每个字段展开成 [交易日 × 股票] 的宽表，按可用日前向填充，
引擎按日取一行即可，既快又不可能穿越。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class FundamentalPanel:
    FIELDS = ("revenue_yoy", "net_profit_yoy", "roe", "growth", "improving")

    def __init__(self, financials: pd.DataFrame, calendar: pd.DatetimeIndex, lag_days: int = 1):
        self.calendar = pd.DatetimeIndex(calendar)
        self.panels: dict[str, pd.DataFrame] = {}
        if financials is None or financials.empty:
            self.codes: list[str] = []
            for f in self.FIELDS:
                self.panels[f] = pd.DataFrame(index=self.calendar)
            return

        df = financials.copy()
        df["code"] = df["code"].astype(str).str.zfill(6)
        df["disclosure_date"] = pd.to_datetime(df["disclosure_date"])
        df["report_period"] = pd.to_datetime(df["report_period"])
        # 同一报告期可能多次修正公告，取最早可用的那一条
        df = df.sort_values(["code", "report_period", "disclosure_date"])
        df = df.drop_duplicates(["code", "report_period"], keep="first")

        # 综合增速 = 营收同比与净利同比的均值（净利缺失则退化为营收）
        df["growth"] = df[["revenue_yoy", "net_profit_yoy"]].mean(axis=1, skipna=True)
        # 「环比改善」= 本期综合增速高于上一期（按报告期顺序，不是按公告顺序）
        df["improving"] = (
            df.groupby("code")["growth"].diff() > 0
        ).astype(float)
        df.loc[df.groupby("code")["growth"].cumcount() == 0, "improving"] = np.nan

        df["available_date"] = df["disclosure_date"] + pd.Timedelta(days=lag_days)
        # 可用日对齐到下一个交易日
        pos = self.calendar.searchsorted(df["available_date"].to_numpy(), side="left")
        valid = pos < len(self.calendar)
        df = df.loc[valid].copy()
        df["available_date"] = self.calendar[pos[valid]]

        self.codes = sorted(df["code"].unique().tolist())
        for f in self.FIELDS:
            wide = df.pivot_table(index="available_date", columns="code", values=f, aggfunc="last")
            self.panels[f] = wide.reindex(self.calendar).ffill()

    def asof(self, date: pd.Timestamp, field: str, codes: list[str] | None = None) -> pd.Series:
        """取 date 当日可见的最新一期 field 值。"""
        panel = self.panels.get(field)
        if panel is None or panel.empty or date not in panel.index:
            return pd.Series(dtype=float)
        row = panel.loc[date]
        if codes is not None:
            row = row.reindex(codes)
        return row.dropna()

    def improving_ratio(self, date: pd.Timestamp, codes: list[str]) -> float:
        """板块内增速环比改善的成分股占比（分母为有数据的成分股）。"""
        vals = self.asof(date, "improving", codes)
        if vals.empty:
            return float("nan")
        return float(vals.mean())

    def coverage(self, date: pd.Timestamp, codes: list[str]) -> float:
        vals = self.asof(date, "growth", codes)
        return len(vals) / max(1, len(codes))
