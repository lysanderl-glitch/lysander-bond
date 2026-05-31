#!/usr/bin/env python3
"""
gen_eval_summaries.py — backfill evaluation summary files in
src/content/intelligence/decisions/ from existing results files.

Each output file is named {date}.md and carries the new schema:
  date, publishDate, title, topIntel, executeCount, inboxCount,
  deferredCount, totalCount, topScore, truthfulness, lang, tags, source

DE-2 (INTEL-PIPELINE-REMEDIATION v3 Phase 3, 2026-05-31)
--------------------------------------------------------
A day on which the pipeline genuinely produced nothing (no execute / inbox /
deferred items AND no actionsCount) is an HONEST-EMPTY day. It must be rendered
as an explicit "今日无新情报" state with ``truthfulness: empty`` — NOT as a
``totalCount: 0`` shell that looks like a real scoring day with zero results.
A day with real items carries ``truthfulness: genuine``. This kills the
"empty-as-real" presentation half of the 21-day fabrication incident.
"""

import re
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "src" / "content" / "intelligence" / "results"
DECISIONS_DIR = Path(__file__).parent.parent / "src" / "content" / "intelligence" / "decisions"

SCORE_RE = re.compile(r'\*{1,2}(\d+)(?:/\d+)?\*{1,2}')


def parse_matrix(raw: str):
    """Extract execute/inbox/deferred counts and top score from body text.

    Table format: | title | S | P | T | F | **score** | action_emoji action_word |
    """
    # Find the scoring matrix section
    matrix_match = re.search(r'专家评估矩阵.*', raw, re.DOTALL)
    section = matrix_match.group(0) if matrix_match else raw

    execute_items = []
    inbox_items   = []
    defer_items   = []

    for line in section.splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.split('|')]
        # cols[0] is empty (before first |), cols[-1] is empty (after last |)
        # Data columns: cols[1]=title, cols[2..5]=scores, cols[6]=score_bold, cols[7]=action
        if len(cols) < 7:
            continue
        title  = cols[1].strip()
        action = cols[-2].strip().lower()   # last data column = action
        # Skip header/separator rows
        if not title or title in ('情报',) or set(title) <= set('-'):
            continue
        if '战略' in title or '产品' in title:
            continue
        # Classify by action column content
        if any(tok in action for tok in ['execute', '⚡', '✅']):
            execute_items.append(title)
        elif any(tok in action for tok in ['inbox', '📥', '🟡', '🟢', 'monitor']):
            inbox_items.append(title)
        elif any(tok in action for tok in ['deferred', '⏸', '⏳', 'defer']):
            defer_items.append(title)

    # Scores in the matrix (bold numbers like **18** or **18/20**)
    scores = [int(s) for s in SCORE_RE.findall(section) if int(s) <= 20]

    return {
        "execute":  execute_items,
        "inbox":    inbox_items,
        "deferred": defer_items,
        "scores":   scores,
    }


def generate(results_file: Path, overwrite: bool = False):
    raw = results_file.read_text(encoding="utf-8")

    # Extract date from frontmatter
    fm_match = re.search(r'^---\n(.*?)\n---', raw, re.DOTALL)
    date = ""
    top_score_fm = None
    if fm_match:
        fm = fm_match.group(1)
        d = re.search(r'^date:\s*"?(\d{4}-\d{2}-\d{2})', fm, re.MULTILINE)
        date = d.group(1) if d else ""
        ts = re.search(r'^actionsCount:\s*(\d+)', fm, re.MULTILINE)

    if not date:
        dm = re.search(r'(\d{4}-\d{2}-\d{2})', results_file.name)
        date = dm.group(1) if dm else "unknown"

    out_path = DECISIONS_DIR / f"{date}.md"
    if out_path.exists() and not overwrite:
        print(f"[SKIP] {out_path.name} already exists")
        return False

    data = parse_matrix(raw)
    execute_items = data["execute"]
    inbox_items   = data["inbox"]
    deferred_items= data["deferred"]
    scores        = data["scores"]

    # Derive top score
    top_score = max(scores) if scores else None

    # Top intel = first execute item, or first inbox, or generic
    all_items = execute_items + inbox_items
    top_intel = all_items[0] if all_items else f"{date} 情报评估"
    # Clean markdown/table artefacts from top_intel
    top_intel = re.sub(r'[\*\`]', '', top_intel).strip()
    if len(top_intel) > 60:
        top_intel = top_intel[:60] + "…"

    parsed_count = len(execute_items) + len(inbox_items) + len(deferred_items)
    total_count = parsed_count
    if total_count == 0:
        # Fallback: use actionsCount from frontmatter
        total_re = re.search(r'actionsCount:\s*(\d+)', raw)
        total_count = int(total_re.group(1)) if total_re else 0

    month_tag = date[:7]
    top_score_line = f"\ntopScore: {top_score}" if top_score else ""

    # DE-2: an honest-empty day = nothing scored AND no actions recorded. Render an
    # explicit "今日无新情报" state, NOT a totalCount:0 shell that mimics a real day.
    honest_empty = (total_count == 0)

    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)

    if honest_empty:
        title = f"{date} 情报评分裁定 — 今日无新情报"
        content = f"""---
date: "{date}"
publishDate: {date}T10:00:00.000Z
title: "{title}"
topIntel: "今日无新情报"
executeCount: 0
inboxCount: 0
deferredCount: 0
totalCount: 0
truthfulness: empty
lang: zh
tags:
  - 执行决策
  - 评分裁定
  - 诚实空态
  - {month_tag}
source: intel-action-agent
---

# {date} 情报评分裁定

**评估日期**：{date}
**评分结果**：今日无新情报

---

> 今日情报管线未产出可信的可执行情报（诚实空态，未以任何虚构内容填充）。
"""
        out_path.write_text(content, encoding="utf-8")
        print(f"[OK] {out_path.name}  HONEST-EMPTY (truthfulness=empty, totalCount=0)")
        return True

    # ── Genuine scoring day ──
    title = f"{date} 情报评分裁定 — {len(execute_items)} 执行 / {len(inbox_items)} 跟踪 / {len(deferred_items)} 延迟"

    # Build body — reuse the scoring matrix section from the results file
    matrix_section = ""
    mat_match = re.search(r'(## 专家评估矩阵.*?)(?=\n## |\Z)', raw, re.DOTALL)
    if mat_match:
        matrix_section = mat_match.group(1).strip()

    content = f"""---
date: "{date}"
publishDate: {date}T10:00:00.000Z
title: "{title}"
topIntel: "{top_intel}"
executeCount: {len(execute_items)}
inboxCount: {len(inbox_items)}
deferredCount: {len(deferred_items)}
totalCount: {total_count}{top_score_line}
truthfulness: genuine
lang: zh
tags:
  - 执行决策
  - 评分裁定
  - {month_tag}
source: intel-action-agent
---

# {date} 情报评分裁定

**评估日期**：{date}
**评分结果**：⚡ {len(execute_items)} 执行 · 📥 {len(inbox_items)} 跟踪 · ⏸ {len(deferred_items)} 延迟
**最高评分**：{top_score}/20

---

{matrix_section if matrix_section else "_评分矩阵数据请查看对应执行结果报告_"}

---

> 完整行动任务清单见 [执行结果报告 {date}](/intelligence/results/{date})
"""

    out_path.write_text(content, encoding="utf-8")
    print(f"[OK] {out_path.name}  execute={len(execute_items)} inbox={len(inbox_items)} deferred={len(deferred_items)} topScore={top_score} truthfulness=genuine")
    return True


def main():
    overwrite = "--overwrite" in sys.argv
    files = sorted(RESULTS_DIR.glob("*.md"))
    print(f"Processing {len(files)} results files -> {DECISIONS_DIR}")
    ok = 0
    for f in files:
        if generate(f, overwrite=overwrite):
            ok += 1
    print(f"Generated {ok} evaluation summary file(s)")


if __name__ == "__main__":
    main()
