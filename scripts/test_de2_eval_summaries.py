#!/usr/bin/env python3
"""
test_de2_eval_summaries.py — DE-2 probes (INTEL-PIPELINE-REMEDIATION v3 Phase 3, PR-5)

Proves gen_eval_summaries.py renders an HONEST-EMPTY day correctly:

    PR-5a  a results file with zero scored items AND zero actionsCount → the
           generated decision is truthfulness:empty + "今日无新情报", NOT a
           totalCount:0 / "共 0 条情报" shell that mimics a real scoring day.
    PR-5b  a results file with genuine scored items → truthfulness:genuine, with
           the real execute/inbox/deferred counts.

Pure-Python: crafted fixtures in temp dirs, deterministic parsing only. NO network.

Run:
    python -m unittest test_de2_eval_summaries -v
    # or:
    python scripts/test_de2_eval_summaries.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SCRIPT_DIR = Path(__file__).resolve().parent

# Load gen_eval_summaries as a module so we can repoint its RESULTS_DIR / DECISIONS_DIR.
_spec = importlib.util.spec_from_file_location(
    "gen_eval_summaries", _SCRIPT_DIR / "gen_eval_summaries.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


_EMPTY_RESULTS = """---
title: "2026-05-31 执行行动报告"
date: "2026-05-31"
publishDate: 2026-05-31T10:00:00.000Z
summary: "本日情报管线未产出可信的可执行情报"
actionsCount: 0
completedCount: 0
lang: zh
source: intel-action-agent
---

# 情报行动报告 2026-05-31

今日无新情报。
"""

_GENUINE_RESULTS = """---
title: "2026-05-31 执行行动报告"
date: "2026-05-31"
publishDate: 2026-05-31T10:00:00.000Z
summary: "评估完成"
actionsCount: 2
completedCount: 1
lang: zh
source: intel-action-agent
---

# 情报行动报告 2026-05-31

## 专家评估矩阵

| 情报 | S | P | T | F | 评分 | 行动 |
|------|---|---|---|---|------|------|
| Anthropic 发布新模型 | 5 | 5 | 4 | 4 | **18** | ⚡ execute |
| 某 Agent 框架更新 | 3 | 3 | 3 | 3 | **12** | 📥 inbox |
"""


class _GenMixin(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.results_dir = root / "results"
        self.decisions_dir = root / "decisions"
        self.results_dir.mkdir()
        self.decisions_dir.mkdir()
        self._patches = [
            mock.patch.object(gen, "RESULTS_DIR", self.results_dir),
            mock.patch.object(gen, "DECISIONS_DIR", self.decisions_dir),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def _write_results(self, name: str, body: str) -> Path:
        p = self.results_dir / name
        p.write_text(body, encoding="utf-8")
        return p


class TestHonestEmpty(_GenMixin):

    def test_empty_day_is_truthfulness_empty(self):
        """PR-5a: zero-item day → truthfulness:empty + 今日无新情报, not 0-shell."""
        rf = self._write_results("2026-05-31.md", _EMPTY_RESULTS)
        ok = gen.generate(rf, overwrite=True)
        self.assertTrue(ok)
        out = (self.decisions_dir / "2026-05-31.md").read_text(encoding="utf-8")
        self.assertIn("truthfulness: empty", out)
        self.assertIn("今日无新情报", out)
        self.assertIn("totalCount: 0", out)
        # It must NOT pretend to be a real scoring day:
        self.assertNotIn("共 0 条情报", out)
        self.assertNotIn("最高评分", out)  # no fake score line

    def test_genuine_day_is_truthfulness_genuine(self):
        """PR-5b: real items → truthfulness:genuine with the parsed counts."""
        rf = self._write_results("2026-05-31.md", _GENUINE_RESULTS)
        ok = gen.generate(rf, overwrite=True)
        self.assertTrue(ok)
        out = (self.decisions_dir / "2026-05-31.md").read_text(encoding="utf-8")
        self.assertIn("truthfulness: genuine", out)
        self.assertNotIn("今日无新情报", out)
        self.assertIn("executeCount: 1", out)
        self.assertIn("inboxCount: 1", out)
        # totalCount reflects the genuine matrix, never collapsed to 0.
        self.assertIn("totalCount: 2", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
