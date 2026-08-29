"""策略参数。

每个字段都直接对应交易规范里的一条，改参数就是改规范；回测报告会把
本对象整体序列化进去，保证「某个胜率数字」永远能追溯到产生它的参数集。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SectorRules:
    """规范 A —— 板块筛选。"""

    # A.1 趋势结构
    ma_short: int = 20
    ma_long: int = 60
    ma_long_slope_window: int = 20
    ma_long_slope_min: float = 0.0          # MA60 走平或拐头向上

    # A.2 反转确认
    breakout_lookback: int = 20             # 在最近 N 日内寻找放量长阳
    breakout_day_return: float = 0.03       # 单日涨幅 >= 3%
    volume_surge_ratio: float = 1.5         # 成交额 >= 前 20 日均值 * 1.5
    volume_surge_days: int = 3              # 或连续 3 日放量

    # A.2 回调确认
    leg_up_min_return: float = 0.20         # 第一波涨幅 >= 20%
    max_retracement: float = 0.50           # 回调不破该波涨幅 50% 位置
    pullback_volume_ratio: float = 0.70     # 回调需缩量：近 5 日额 < 波段峰值 5 日额 * 0.7

    # A.2 两条确认路径的组合方式。
    # 原规范是「反转确认 OR 回调确认」，但实测这个 OR 会让反转路径几乎
    # 完全吞掉回调路径：max_retracement 从 0.382 放宽到 0.8，回调成立的
    # 板块日 +81%，最终合格日只 +2%。也就是说「回调不破 50%」这条你视为
    # 核心风控的条款，在 OR 结构下几乎不起约束作用。
    # 拆成三种模式，才能分别统计两条路径各自的胜率。
    #   "either"   —— 规范原文：任一成立即可
    #   "reversal" —— 只做底部反转启动
    #   "pullback" —— 只做第一波后的回调
    confirm_mode: str = "either"

    # A.3 基本面验证（至少满足 min_fundamental_gates 条）
    min_fundamental_gates: int = 2
    breadth_improving_ratio: float = 0.60   # >60% 成分股增速环比改善
    estimate_revision_ratio: float = 1.50   # 上调家数 / 下调家数
    meso_improving_months: int = 2          # 中观数据连续改善月数

    # A.4 排除
    excluded_boards: tuple[str, ...] = ()   # 纯题材无业绩映射 / 政策强压行业


@dataclass
class PickRules:
    """规范 B —— 个股选取。"""

    momentum_top_n: int = 3                 # 涨幅龙头前三
    fundamental_top_n: int = 3              # 业绩龙头前三
    rps_min: float = 90.0                   # 相对强度 RPS >= 90
    rps_window: int = 120                   # RPS 计算窗口（交易日）
    roe_above_sector_median: bool = True
    fallback_each: int = 2                  # 无交集时各取 1~2 只
    # 硬性排除
    exclude_st: bool = True
    min_listed_days: int = 250              # 次新股剔除
    liquidity_multiple: float = 100.0       # 日均成交额 >= 计划持仓 * 100


@dataclass
class EntryRules:
    """规范 C —— 介入。"""

    pullback_to_ma: int = 20                # 回调至 20 日线附近
    pullback_ma_tolerance: float = 0.03     # 距均线 ±3% 视为「附近」
    pullback_volume_shrink: float = 0.80    # 缩量：当日额 < 5 日均额 * 0.8
    breakout_confirm_volume: float = 1.20   # 突破需放量
    tranches: tuple[float, ...] = (1 / 3, 1 / 3, 1 / 3)
    add_on_breakout_gain: float = 0.05      # 首笔浮盈 5% 且突破 → 加仓第二笔
    max_weight_per_stock: float = 0.20
    max_weight_per_sector: float = 0.40
    # 「禁止追高」的口径。实测发现按「距板块启动涨幅」度量时，规范 B.1
    # （选涨幅前三的龙头）与规范 C.4（涨幅 >50% 不建仓）直接冲突：龙头
    # 恰恰是涨幅最大的那批，98% 的龙头候选会被自己的风控条款否决，策略
    # 退化成纯业绩选股。因此提供两种口径，默认用乖离率。
    #   "campaign_start" —— 原文口径：距板块启动点涨幅 > max_chase_gain 不建仓
    #   "ma_extension"   —— 乖离率口径：收盘价高于 MA20 超过 max_ma_extension 不建仓
    chase_reference: str = "ma_extension"
    max_chase_gain: float = 0.50
    max_ma_extension: float = 0.15
    max_positions: int = 8


@dataclass
class ExitRules:
    """规范 D —— 风控与退出。"""

    hard_stop: float = 0.08                 # 跌破买入均价 8%
    stop_on_ma_break: int = 20              # 跌破 20 日线
    ma_break_confirm_days: int = 2          # 需连续 N 日收在均线下方才算「跌破」
    ma_break_buffer: float = 0.01           # 均线下方 1% 的缓冲，过滤盘中噪音
    logic_stop_trim: float = 0.50           # 逻辑止损减仓比例
    trail_after_gain: float = 0.50          # 涨幅超 50% 转移动止盈
    trail_drawdown: float = 0.15            # 自最高点回撤 15% 离场
    sector_exit_ma: int = 60                # 板块指数跌破 60 日线 → 清该板块
    max_holding_days: int = 120             # 时间止损，避免僵尸仓位


@dataclass
class CostModel:
    """A 股交易成本与可成交性约束。

    默认值按 2023-08-28 后的现行费率：印花税卖出单边 0.05%，佣金双边
    万分之二点五（最低 5 元），过户费万分之零点一。
    """

    commission_rate: float = 0.00025
    commission_min: float = 5.0
    stamp_duty_sell: float = 0.0005
    transfer_fee: float = 0.00001
    slippage: float = 0.001                 # 单边滑点，按开盘价成交价的比例
    limit_up_threshold: float = 0.098       # 涨停不可买（主板）
    limit_down_threshold: float = -0.098    # 跌停不可卖
    limit_threshold_20cm: float = 0.198     # 科创板/创业板 20cm


@dataclass
class StrategyConfig:
    start: str = "2023-09-01"
    end: str = "2025-08-31"
    initial_capital: float = 1_000_000.0
    benchmark: str = "000300"               # 沪深300
    rebalance_lag_days: int = 1             # T 日收盘选股，T+1 开盘执行
    fundamental_disclosure_lag_days: int = 1  # 财报公告日 +1 才可用
    sector: SectorRules = field(default_factory=SectorRules)
    pick: PickRules = field(default_factory=PickRules)
    entry: EntryRules = field(default_factory=EntryRules)
    exit: ExitRules = field(default_factory=ExitRules)
    cost: CostModel = field(default_factory=CostModel)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
