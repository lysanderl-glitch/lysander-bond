from .base import DataSource, normalize_daily, is_st, limit_threshold
from .cache import Cache
from .synthetic import SyntheticSource, SyntheticSpec


def get_source(name: str, start: str, end: str, **kwargs):
    """按名称构造 provider：synthetic / akshare / eastmoney。"""
    name = name.lower()
    if name == "synthetic":
        return SyntheticSource(start, end, **kwargs)
    if name == "akshare":
        from .akshare_ds import AkshareSource
        return AkshareSource(**kwargs)
    if name == "eastmoney":
        from .eastmoney import EastmoneySource
        return EastmoneySource(**kwargs)
    raise ValueError(f"未知数据源: {name}")


__all__ = ["DataSource", "Cache", "SyntheticSource", "SyntheticSpec",
           "get_source", "normalize_daily", "is_st", "limit_threshold"]
