#!/usr/bin/env python3
"""
migrate_astro_to_collections.py
Migrates 10 legacy .astro blog files from src/pages/blog/ to Content Collections (src/content/blog/zh/).
Uses Claude API to regenerate high-quality content with BLOG_PROMPT_V2 structure.
"""

import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

BOND_ROOT = Path("C:/Users/lysanderl_janusd/lysander-bond")
ZH_DIR = BOND_ROOT / "src" / "content" / "blog" / "zh"
PAGES_BLOG = BOND_ROOT / "src" / "pages" / "blog"

SYSTEM_PROMPT = """You are Lysander, the technical blogger of Synapse-PJ AI engineering team.
Your writing style: first-person, based on real experience, showing reasoning process not just conclusions.
Your readers: engineers and founders building AI Agent systems or n8n automation workflows.
Your credibility comes from: specific numbers, real filenames, showing mistakes made and thinking process.
Write in Chinese (Simplified) unless specified otherwise."""

BLOG_PROMPT_V2_TEMPLATE = """基于以下原始文章内容，用更高质量的结构重新撰写一篇技术博客文章。

原始标题：{title}
原始内容（HTML）：
{html_content}

## 强制结构（必须按此顺序，缺一不可）

输出格式：纯 HTML。使用元素：
- 段落：<p>
- 标题：<h2>（主节）、<h3>（子节）
- 代码块：<pre><code class="language-python">（或 yaml/bash）</code></pre>
- 关键要点：<div class="callout callout-insight"><p>...</p></div>
- 无序列表：<ul><li>
- 有序列表：<ol><li>

必须包含的节（缺一退回重写）：

1. TL;DR（位于正文最顶部）
<div class="tl-dr"><ul>
  <li>3-5条bullet，每条≤20字，让扫读者获得完整价值</li>
</ul></div>

2. 问题背景（H2，1-2段）
- 第一段：一个具体场景 + 至少1个具体数字
- 不假设读者了解 Synapse

3. 为什么难排查/为什么这个决策难做（H2，1-2段）
- 必须包含"我们一开始以为…但实际上…"的推理结构
- 禁止：直接给结论，跳过分析过程

4. 根因/核心设计决策（H2，含代码块）
- 必须包含至少1个 <pre><code> 代码块
- 内容：真实配置片段/伪代码/命令（仅使用素材中提及的，不编造路径）

5. 可移植的原则（H2）
- 第一条原则放入 callout-insight
- 其余用 <ol> 编号
- 每条格式：「如果你在[场景]，[具体行动原则]」

6. 结尾（1段）
- 关联文章具体技术问题的CTA
- 禁止：固定宣传模板语

## 强制约束
- 禁用词：革命性、未来可期、AI很强大、无限可能、日新月异
- 禁止：结论复述正文
- 禁止：使用素材未提及的文件路径或API字段名
- 长度：1200-2000字（中文）
- 只输出HTML内容本身，不要包含任何frontmatter或markdown包装
"""


def strip_html_tags(html: str) -> str:
    """Strip HTML tags and return plain text."""
    clean = re.sub(r'<[^>]+>', '', html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def extract_body_from_astro(content: str) -> tuple[str, str, str, str]:
    """
    Extract title, description, date, and HTML body from .astro file.
    Returns (title, description, date, html_body)
    """
    title = ""
    description = ""
    date = "2026-04-25"

    # Extract title from Layout title attribute
    title_match = re.search(r'title="([^"]+)\s*-\s*Lysander"', content)
    if title_match:
        title = title_match.group(1).strip()

    # Extract description
    desc_match = re.search(r'description="([^"]+)"', content)
    if desc_match:
        description = desc_match.group(1).strip()

    # Extract date
    date_match = re.search(r'<time[^>]*>(\d{4}-\d{2}-\d{2})<\/time>', content)
    if date_match:
        date = date_match.group(1)

    # Extract HTML body (everything inside the .prose div)
    body_match = re.search(
        r'<div class="prose prose-invert[^"]*"[^>]*>(.*?)</div>\s*\n\s*<footer',
        content,
        re.DOTALL
    )
    if body_match:
        html_body = body_match.group(1).strip()
    else:
        # Fallback: get everything between article content divs
        html_body = content

    return title, description, date, html_body


def call_claude_api(prompt: str, system: str) -> str:
    """Call Claude API using Anthropic SDK."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK not installed. Run: pip install anthropic") from e

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content:
        return ""
    first = response.content[0]
    return getattr(first, "text", str(first)).strip()


def structural_qa(html_content: str) -> tuple[bool, list[str]]:
    """
    Run structural QA checks on generated content.
    Returns (passed, list_of_issues)
    """
    issues = []

    # Check TL;DR
    if 'tl-dr' not in html_content and 'TL;DR' not in html_content and 'TL DR' not in html_content:
        issues.append("Missing TL;DR section")

    # Check H2 count >= 3
    h2_count = len(re.findall(r'<h2[^>]*>', html_content))
    if h2_count < 3:
        issues.append(f"Only {h2_count} H2 sections (need >= 3)")

    # Check code block
    if '<pre>' not in html_content and '<code' not in html_content:
        issues.append("Missing code block")

    # Check callout
    if 'callout' not in html_content:
        issues.append("Missing callout element")

    # Check word count (rough estimate for Chinese)
    text = strip_html_tags(html_content)
    char_count = len(text)
    if char_count < 600:
        issues.append(f"Too short: {char_count} chars (need >= 600)")
    elif char_count > 6000:
        issues.append(f"Too long: {char_count} chars (need <= 6000)")

    passed = len(issues) == 0
    return passed, issues


def build_frontmatter(title: str, description: str, date: str, slug: str) -> str:
    """Build YAML frontmatter for ZH content collection file."""
    # Clean title and description for YAML
    title_clean = title.replace('"', '\\"')
    desc_clean = description.replace('"', '\\"')

    # Map slug to pillar/priority
    pillar = "methodology"
    priority = "P2"

    if "n8n" in slug or "automation" in slug or "cron" in slug or "slack" in slug:
        pillar = "ops-practical"
    elif "fact-ssot" in slug or "knowledge" in slug or "decay" in slug:
        pillar = "methodology"
    elif "decision" in slug or "delegation" in slug:
        pillar = "multi-agent-case"
    elif "time" in slug or "illusion" in slug or "session" in slug:
        pillar = "methodology"
    elif "replacing" in slug or "outsourcing" in slug:
        pillar = "intelligence-evolution"

    return f'''---
title: "{title_clean}"
description: "{desc_clean}"
publishDate: {date}
slug: {slug}
lang: zh
hasEnglish: true
pillar: {pillar}
priority: {priority}
author: content_strategist
keywords:
  - "AI工程"
  - "Synapse"
  - "自动化"
---
'''


# Article definitions: (slug, astro_filename)
ARTICLES = [
    ("ai-agent-count-drift-fact-ssot-meta-rule", "ai-agent-count-drift-fact-ssot-meta-rule.astro"),
    ("ai-agent-decision-boundary-delegation", "ai-agent-decision-boundary-delegation.astro"),
    ("ai-knowledge-base-decay-fact-check", "ai-knowledge-base-decay-fact-check.astro"),
    ("ai-replacing-outsourcing-financial-leasing-synapse", "ai-replacing-outsourcing-financial-leasing-synapse.astro"),
    ("ai-session-time-awareness-illusion", "ai-session-time-awareness-illusion.astro"),
    ("ai-time-illusion-cross-day-conversation", "ai-time-illusion-cross-day-conversation.astro"),
    ("fact-ssot-meta-rule-for-ai-agent-systems", "fact-ssot-meta-rule-for-ai-agent-systems.astro"),
    ("n8n-replace-local-cron-intel-pipeline-migration", "n8n-replace-local-cron-intel-pipeline-migration.astro"),
    ("n8n-unified-slack-notification-routing-wf09", "n8n-unified-slack-notification-routing-wf09.astro"),
    ("n8n-unified-slack-notification-routing", "n8n-unified-slack-notification-routing.astro"),
]


def migrate_article(idx: int, slug: str, astro_filename: str) -> dict:
    """Migrate a single article. Returns result dict."""
    result = {
        "slug": slug,
        "qa_pass": False,
        "qa_issues": [],
        "zh_written": False,
        "en_exists": False,
        "en_frontmatter_ok": False,
        "astro_deleted": False,
        "error": None,
    }

    print(f"\n[{idx}/10] Processing: {slug}")

    astro_path = PAGES_BLOG / astro_filename
    zh_path = ZH_DIR / f"{slug}.md"
    en_path = BOND_ROOT / "src" / "content" / "blog" / "en" / f"{slug}.md"

    try:
        # Step 1: Read and extract from .astro file
        astro_content = astro_path.read_text(encoding="utf-8")
        title, description, date, html_body = extract_body_from_astro(astro_content)
        print(f"  Title: {title[:60]}...")
        print(f"  Date: {date}")

        # Step 2: Generate high-quality content via Claude API
        prompt = BLOG_PROMPT_V2_TEMPLATE.format(
            title=title,
            html_content=html_body[:8000]  # Limit to avoid token overflow
        )

        print(f"  Calling Claude API...")
        new_content = call_claude_api(prompt, SYSTEM_PROMPT)

        if not new_content:
            result["error"] = "Claude API returned empty response"
            print(f"  ERROR: {result['error']}")
            return result

        # Step 3: Structural QA
        qa_passed, qa_issues = structural_qa(new_content)
        result["qa_issues"] = qa_issues

        if not qa_passed:
            print(f"  QA FAILED: {qa_issues}")
            print(f"  Retrying...")
            time.sleep(2)
            new_content = call_claude_api(prompt, SYSTEM_PROMPT)
            qa_passed, qa_issues = structural_qa(new_content)
            result["qa_issues"] = qa_issues

        result["qa_pass"] = qa_passed
        print(f"  QA: {'PASS' if qa_passed else 'FAIL'} {qa_issues if qa_issues else ''}")

        # Step 4: Write ZH content collection file
        frontmatter = build_frontmatter(title, description, date, slug)
        full_content = frontmatter + "\n" + new_content

        ZH_DIR.mkdir(parents=True, exist_ok=True)
        zh_path.write_text(full_content, encoding="utf-8")
        result["zh_written"] = True
        print(f"  ZH written: {zh_path}")

        # Step 5: Verify EN file
        if en_path.exists():
            result["en_exists"] = True
            en_content = en_path.read_text(encoding="utf-8")
            # Check frontmatter has slug and publishDate/date
            if ("slug:" in en_content or "slug:" in en_content[:500]) and \
               ("publishDate:" in en_content[:500] or "date:" in en_content[:500]):
                result["en_frontmatter_ok"] = True
                print(f"  EN: exists + frontmatter OK")
            else:
                print(f"  EN: exists but frontmatter incomplete")
        else:
            print(f"  EN: NOT FOUND at {en_path}")

        # Step 6: Delete old .astro file
        astro_path.unlink()
        result["astro_deleted"] = True
        print(f"  Deleted: {astro_path}")

    except Exception as e:
        result["error"] = str(e)
        print(f"  ERROR: {e}")

    return result


def main():
    print("=" * 60)
    print("Blog Migration: .astro -> Content Collections")
    print("=" * 60)

    # Verify API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Verify directories
    if not PAGES_BLOG.exists():
        print(f"ERROR: {PAGES_BLOG} does not exist")
        sys.exit(1)

    ZH_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for idx, (slug, astro_filename) in enumerate(ARTICLES, 1):
        result = migrate_article(idx, slug, astro_filename)
        results.append(result)
        # Small delay between API calls
        if idx < len(ARTICLES):
            time.sleep(1)

    # Summary report
    print("\n" + "=" * 60)
    print("MIGRATION REPORT")
    print("=" * 60)
    print(f"{'slug':<55} {'QA':<6} {'ZH':<4} {'EN':<4} {'DEL':<4}")
    print("-" * 75)

    for r in results:
        qa = "PASS" if r["qa_pass"] else "FAIL"
        zh = "OK" if r["zh_written"] else "ERR"
        en = "OK" if (r["en_exists"] and r["en_frontmatter_ok"]) else ("EXISTS" if r["en_exists"] else "MISS")
        dl = "OK" if r["astro_deleted"] else "ERR"
        print(f"{r['slug']:<55} {qa:<6} {zh:<4} {en:<4} {dl:<4}")
        if r.get("error"):
            print(f"  ERROR: {r['error']}")
        if r.get("qa_issues"):
            print(f"  QA issues: {r['qa_issues']}")

    # Final check: only index.astro and [...slug].astro should remain
    print("\n--- Remaining files in src/pages/blog/ ---")
    remaining = list(PAGES_BLOG.glob("*.astro"))
    for f in remaining:
        print(f"  {f.name}")

    all_ok = remaining == [] or all(
        f.name in ("index.astro", "[...slug].astro") for f in remaining
    )
    if all_ok:
        print("  Route conflict resolved: only index.astro and [...slug].astro remain")
    else:
        extra = [f.name for f in remaining if f.name not in ("index.astro", "[...slug].astro")]
        print(f"  WARNING: unexpected files still present: {extra}")

    passed = sum(1 for r in results if r["zh_written"] and r["astro_deleted"])
    print(f"\nCompleted: {passed}/{len(ARTICLES)} articles migrated successfully")


if __name__ == "__main__":
    main()
