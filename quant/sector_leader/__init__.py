"""行业景气度 + 板块动量 + 龙头 策略的可回测实现。

模块划分::

    config      策略全部可调参数（A/B/C/D 四组规范）
    datasource  行情/财务数据源适配层 + 本地缓存 + 合成数据
    indicators  技术指标与相对强度
    sector      规范 A：板块筛选
    picker      规范 B：个股选取
    backtest    规范 C/D：介入、仓位、风控、退出 —— 逐日事件驱动引擎
    metrics     胜率、盈亏比、期望收益、回撤等绩效统计
    report      Markdown 报告生成
"""

__version__ = "0.1.0"
