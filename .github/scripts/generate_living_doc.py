#!/usr/bin/env python3
"""
P3-A4: Living Documentation Generator
Synapse ATDD CI Gate — Automated TC Status Report

Reads CI Gate stdout (passed via stdin or ATDD_GATE_OUTPUT file) and generates
a Markdown report for Living Documentation.

Usage (GHA):
    python .github/scripts/run_atdd_gate.py 2>&1 | \
        python .github/scripts/generate_living_doc.py /tmp/qa-report-$(date +%Y-%m-%d).md

Or via env var:
    ATDD_GATE_OUTPUT=/tmp/gate_output.txt python .github/scripts/generate_living_doc.py report.md
"""
import os
import re
import sys
from datetime import datetime, timezone, timedelta


def dubai_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=4)).strftime('%Y-%m-%d')


def parse_gate_output(raw: str) -> dict:
    """
    Parse run_atdd_gate.py stdout into structured result dict.
    Returns: {
        'date': str,
        'site_url': str,
        'p0_results': list[dict],
        'p1_results': list[dict],
        'p2_results': list[dict],
        'p0_passed': int, 'p0_total': int,
        'p1_passed': int, 'p1_total': int,
        'p2_passed': int, 'p2_total': int,
        'gate_pass': bool,
        'run_id': str,
    }
    """
    result = {
        'date': dubai_today(),
        'site_url': '',
        'p0_results': [],
        'p1_results': [],
        'p2_results': [],
        'p0_passed': 0, 'p0_total': 0,
        'p1_passed': 0, 'p1_total': 0,
        'p2_passed': 0, 'p2_total': 0,
        'gate_pass': False,
        'run_id': os.environ.get('GITHUB_RUN_ID', 'local'),
    }

    # Extract site URL
    site_m = re.search(r'Site:\s*(https?://\S+)', raw)
    if site_m:
        result['site_url'] = site_m.group(1)

    # Parse TC result lines: "  [P0] TC-INT-001: PASS -- evidence"
    tc_pattern = re.compile(
        r'\[(P[012])\]\s+(TC-[\w-]+):\s+(PASS|FAIL|WARNING)\s+--\s+(.*)'
    )
    for m in tc_pattern.finditer(raw):
        priority, tc_id, status_str, evidence = m.groups()
        passed = status_str == 'PASS'
        entry = {'id': tc_id, 'priority': priority, 'pass': passed,
                 'status': status_str, 'evidence': evidence.strip()}
        key = f'p{priority[1]}_results'
        result[key].append(entry)

    # Recalculate pass counts
    for p in ('p0', 'p1', 'p2'):
        entries = result[f'{p}_results']
        result[f'{p}_total'] = len(entries)
        result[f'{p}_passed'] = sum(1 for e in entries if e['pass'])

    # Gate pass/fail
    result['gate_pass'] = 'CI Gate PASS' in raw

    return result


def generate_markdown(data: dict) -> str:
    date_str = data['date']
    run_id = data['run_id']
    site_url = data['site_url'] or 'https://lysander.bond'
    gate_badge = '✅ PASS' if data['gate_pass'] else '❌ FAIL'

    lines = [
        f"---",
        f"date: '{date_str}'",
        f"type: qa-auto-report",
        f"generated_by: CI Gate P3-A4 Living Documentation",
        f"github_run_id: '{run_id}'",
        f"site_url: '{site_url}'",
        f"gate_result: {'PASS' if data['gate_pass'] else 'FAIL'}",
        f"p0_pass_rate: '{data['p0_passed']}/{data['p0_total']}'",
        f"p1_pass_rate: '{data['p1_passed']}/{data['p1_total']}'",
        f"p2_pass_rate: '{data['p2_passed']}/{data['p2_total']}'",
        f"stale_after: '{(datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d')}'",
        f"---",
        f"",
        f"# Synapse Intelligence TC 自动执行报告 — {date_str}",
        f"",
        f"> **CI Gate 结论：** {gate_badge}  ",
        f"> **站点：** {site_url}  ",
        f"> **GHA Run ID：** [{run_id}](https://github.com/lysanderl-glitch/lysander-bond/actions/runs/{run_id})  ",
        f"> **生成时间（Dubai UTC+4）：** {datetime.now(timezone.utc) + timedelta(hours=4):%Y-%m-%d %H:%M}",
        f"",
    ]

    # P0 table
    if data['p0_results']:
        p0_rate = data['p0_passed'] / data['p0_total'] * 100 if data['p0_total'] else 0
        p0_badge = '✅' if data['p0_passed'] == data['p0_total'] else '❌'
        lines += [
            f"## P0 核心验收 — {p0_badge} {data['p0_passed']}/{data['p0_total']} ({p0_rate:.0f}%)",
            f"",
            f"> **门禁标准：P0 必须 100% PASS，否则阻断部署**",
            f"",
            f"| TC-ID | 状态 | 实证摘要 |",
            f"|-------|------|---------|",
        ]
        for r in data['p0_results']:
            icon = '✅ PASS' if r['pass'] else '❌ FAIL'
            evidence = r['evidence'][:120]
            lines.append(f"| `{r['id']}` | {icon} | {evidence} |")
        lines.append(f"")

    # P1 table
    if data['p1_results']:
        p1_rate = data['p1_passed'] / data['p1_total'] * 100 if data['p1_total'] else 0
        p1_badge = '✅' if p1_rate >= 80 else '⚠️'
        lines += [
            f"## P1 重要功能 — {p1_badge} {data['p1_passed']}/{data['p1_total']} ({p1_rate:.0f}%)",
            f"",
            f"> **门禁标准：P1 通过率 ≥ 80%（低于此值为警告，不阻断部署）**",
            f"",
            f"| TC-ID | 状态 | 实证摘要 |",
            f"|-------|------|---------|",
        ]
        for r in data['p1_results']:
            icon = '✅ PASS' if r['pass'] else '⚠️ WARNING'
            evidence = r['evidence'][:120]
            lines.append(f"| `{r['id']}` | {icon} | {evidence} |")
        lines.append(f"")

    # P2 table
    if data['p2_results']:
        p2_rate = data['p2_passed'] / data['p2_total'] * 100 if data['p2_total'] else 0
        lines += [
            f"## P2 产品线健康信号 — {data['p2_passed']}/{data['p2_total']} ({p2_rate:.0f}%)",
            f"",
            f"> **非阻断：P2 失败记录为产品线健康信号，列入下一迭代 backlog**",
            f"",
            f"| TC-ID | 产品线 | 状态 | 实证摘要 |",
            f"|-------|--------|------|---------|",
        ]
        for r in data['p2_results']:
            icon = '✅ PASS' if r['pass'] else '⚠️ WARNING'
            # Infer product line from TC-ID prefix
            tc_id = r['id']
            if tc_id.startswith('TC-XIMI'):
                product = '汐弥游戏'
            elif tc_id.startswith('TC-GAME'):
                product = 'AI游戏工厂'
            elif tc_id.startswith('TC-BLOG'):
                product = '博客管线'
            else:
                product = '情报系统'
            evidence = r['evidence'][:100]
            lines.append(f"| `{tc_id}` | {product} | {icon} | {evidence} |")
        lines.append(f"")

    # Summary box
    total_tcs = data['p0_total'] + data['p1_total'] + data['p2_total']
    total_passed = data['p0_passed'] + data['p1_passed'] + data['p2_passed']
    lines += [
        f"## 汇总",
        f"",
        f"| 维度 | 数值 |",
        f"|------|------|",
        f"| 总 TC 数 | {total_tcs} |",
        f"| 总通过数 | {total_passed} |",
        f"| P0 通过率 | {data['p0_passed']}/{data['p0_total']} |",
        f"| P1 通过率 | {data['p1_passed']}/{data['p1_total']} |",
        f"| P2 通过率 | {data['p2_passed']}/{data['p2_total']} |",
        f"| CI Gate | {'PASS ✅' if data['gate_pass'] else 'FAIL ❌'} |",
        f"",
        f"---",
        f"",
        f"*自动生成 by P3-A4 Living Documentation · "
        f"GHA Run [{run_id}](https://github.com/lysanderl-glitch/lysander-bond/actions/runs/{run_id}) · "
        f"Synapse ATDD Standard v1.1*",
    ]

    return '\n'.join(lines)


def main():
    # Read gate output: from file env var, or stdin
    gate_output_path = os.environ.get('ATDD_GATE_OUTPUT', '')
    if gate_output_path and os.path.isfile(gate_output_path):
        with open(gate_output_path, encoding='utf-8') as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        # Minimal fallback report when no output provided
        raw = f"=== Synapse ATDD CI Gate === Site: unknown\nDate: {dubai_today()}\nCI Gate FAIL -- no output"

    data = parse_gate_output(raw)
    report = generate_markdown(data)

    # Determine output path
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Living Documentation written to: {output_path}", file=sys.stderr)
    else:
        print(report)


if __name__ == '__main__':
    main()
