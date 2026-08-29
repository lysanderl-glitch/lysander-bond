"""本地 CSV 缓存。

抓 A 股全市场两年日线是几千次 HTTP 请求，接口都有频控；缓存是必需品而
不是优化。缓存键 = 数据种类 + 标的 + 区间，命中即不发请求。
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Callable

import pandas as pd

DEFAULT_CACHE_DIR = Path(os.environ.get("SECTOR_LEADER_CACHE", "quant/.cache"))


class Cache:
    def __init__(self, root: Path | str = DEFAULT_CACHE_DIR, enabled: bool = True):
        self.root = Path(root)
        self.enabled = enabled
        if enabled:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, kind: str, key: str) -> Path:
        digest = hashlib.md5(key.encode("utf-8")).hexdigest()[:16]
        folder = self.root / kind
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{digest}.csv"

    def get_or_fetch(
        self, kind: str, key: str, fetch: Callable[[], pd.DataFrame]
    ) -> pd.DataFrame:
        if not self.enabled:
            return fetch()
        path = self._path(kind, key)
        if path.exists():
            return pd.read_csv(path, dtype={"code": str})
        df = fetch()
        if df is not None and not df.empty:
            df.to_csv(path, index=False)
        return df if df is not None else pd.DataFrame()

    def clear(self, kind: str | None = None) -> int:
        target = self.root / kind if kind else self.root
        if not target.exists():
            return 0
        removed = 0
        for p in target.rglob("*.csv"):
            p.unlink()
            removed += 1
        return removed
