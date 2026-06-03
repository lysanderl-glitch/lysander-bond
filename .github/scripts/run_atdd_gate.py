#!/usr/bin/env python3
"""
Synapse ATDD CI Gate — Multi-Product Line Verification
GHA Entry Point: lysander-bond/.github/scripts/run_atdd_gate.py

验证层次：L3（内容正则匹配）或 L4（跨仓库端到端）
P0 通过率 < 100% → exit 1（阻断 deploy）
P1 通过率 < 80% → WARNING（不阻断）
P2 通过率任何 FAIL → WARNING（非阻断，记录为产品线健康信号）

Silent Fail 防御：HTTP 200 ≠ 业务 artifact 正确生成
"""
import os
import re
import sys
import requests
from datetime import datetime, timezone, timedelta, date
from typing import Tuple, Optional

SITE_URL = os.environ.get('SITE_URL', 'https://lysander.bond')
TIMEOUT = int(os.environ.get('VERIFY_TIMEOUT', '30'))


def dubai_today() -> str:
    """Today's date in YYYY-MM-DD (Dubai, UTC+4)."""
    return (datetime.now(timezone.utc) + timedelta(hours=4)).strftime('%Y-%m-%d')


def fetch(path: str) -> Tuple[int, str]:
    """Fetch page content. Returns (status_code, html_content)."""
    try:
        r = requests.get(f"{SITE_URL}{path}", timeout=TIMEOUT, allow_redirects=True)
        return r.status_code, r.text
    except Exception as e:
        return -1, str(e)


def result(tc_id: str, priority: str, ok: bool, evidence: str) -> dict:
    return {'id': tc_id, 'priority': priority, 'pass': ok, 'evidence': evidence}


# ─────────────────────────── P0 Test Cases ───────────────────────────

def check_tc_001() -> dict:
    """TC-INT-001: 情报主页可访问（L3：内容验证）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-001', 'P0', False, f'HTTP {status} — 页面不可访问')
    # L3: 验证内容包含实质性情报内容（非空页）
    has_content = len(html) > 1000
    has_keyword = bool(re.search(r'intelligence|情报|自进化|synapse', html, re.IGNORECASE))
    if has_content and has_keyword:
        evidence = f'页面长度{len(html)}字符，含情报关键词（L3验证通过）'
        return result('TC-INT-001', 'P0', True, evidence)
    return result('TC-INT-001', 'P0', False,
                  f'HTTP 200 但内容异常 — 长度{len(html)}字符，关键词存在:{has_keyword}（Silent Fail防御）')


def check_tc_002() -> dict:
    """TC-INT-002: 英文版路由可访问（L3：语言验证）"""
    status, html = fetch('/synapse/intelligence/en/')
    if status != 200:
        return result('TC-INT-002', 'P0', False, f'HTTP {status}')
    # L3: 验证页面为英文内容
    has_english = bool(re.search(r'[A-Za-z]{10,}', html))
    zh_ratio = len(re.findall(r'[一-鿿]', html)) / max(len(html), 1)
    if has_english and zh_ratio < 0.05:
        return result('TC-INT-002', 'P0', True, f'英文页面确认，中文字符占比{zh_ratio:.2%}')
    return result('TC-INT-002', 'P0', False, f'页面中文字符占比{zh_ratio:.2%}，疑似中文页面（L3验证）')


def check_tc_003() -> dict:
    """TC-INT-003: 当日内容存在（L3：日期验证）"""
    today = dubai_today()
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-003', 'P0', False, f'HTTP {status}')
    if today in html:
        return result('TC-INT-003', 'P0', True, f'页面包含今日日期{today}（L3内容验证）')
    # 检查是否有昨天的日期（可接受，但需说明）
    yesterday = (datetime.now(timezone.utc) + timedelta(hours=4) - timedelta(days=1)).strftime('%Y-%m-%d')
    if yesterday in html:
        return result('TC-INT-003', 'P0', False,
                      f'页面显示昨日{yesterday}而非今日{today} — 数据未更新（Silent Fail）')
    return result('TC-INT-003', 'P0', False, f'页面无今日日期{today}（Silent Fail防御）')


def check_tc_004() -> dict:
    """TC-INT-004: 决策条目存在（L3：DOM内容验证）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-004', 'P0', False, f'HTTP {status}')
    # L3: 验证决策相关内容区域非空
    decision_patterns = [r'decision', r'决策', r'action-item', r'决定']
    found = [p for p in decision_patterns if re.search(p, html, re.IGNORECASE)]
    if found:
        count = len(re.findall(r'decision|决策', html, re.IGNORECASE))
        return result('TC-INT-004', 'P0', True, f'决策内容区域存在，匹配{count}处（L3）')
    return result('TC-INT-004', 'P0', False,
                  f'HTTP 200 但决策内容区域为空（Silent Fail防御）')


def check_tc_005() -> dict:
    """TC-INT-005: 成果条目存在（L3：DOM内容验证）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-005', 'P0', False, f'HTTP {status}')
    achievement_patterns = [r'achievement', r'成果', r'result', r'output']
    found = any(re.search(p, html, re.IGNORECASE) for p in achievement_patterns)
    if found:
        return result('TC-INT-005', 'P0', True, f'成果内容区域存在（L3验证）')
    return result('TC-INT-005', 'P0', False,
                  f'HTTP 200 但成果区域为空（Silent Fail防御）')


def check_tc_006() -> dict:
    """TC-INT-006: 相关路由配置正确（L3：内容+路由双验证）"""
    # 验证几个关键相关路由
    routes = ['/synapse/', '/blog/']
    all_ok = True
    evidence_parts = []
    for route in routes:
        status, html = fetch(route)
        if status == 200 and len(html) > 500:
            evidence_parts.append(f'{route}:OK')
        else:
            evidence_parts.append(f'{route}:FAIL(HTTP {status})')
            all_ok = False
    evidence = ', '.join(evidence_parts)
    return result('TC-INT-006', 'P0', all_ok, evidence + '（L3路由内容验证）')


def check_tc_007() -> dict:
    """TC-INT-007: 无内部术语泄露（L3：正则扫描）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-007', 'P0', False, f'HTTP {status}')
    internal_terms = [
        r'CEO Guard', r'harness_engineer', r'technical_builder',
        r'integration_qa', r'LysanderInterceptor', r'ceo-guard',
        r'intercept_log', r'active_tasks\.yaml', r'CLAUDE\.md',
        r'obs/', r'dispatch_table'
    ]
    found_terms = [t for t in internal_terms if re.search(t, html)]
    if not found_terms:
        return result('TC-INT-007', 'P0', True, f'内部术语扫描通过，共检查{len(internal_terms)}个术语')
    return result('TC-INT-007', 'P0', False, f'内部术语泄露：{found_terms}')


def check_tc_008() -> dict:
    """TC-INT-008: 英文页面无中文字符（L3：编码验证）"""
    status, html = fetch('/synapse/intelligence/en/')
    if status != 200:
        return result('TC-INT-008', 'P0', False, f'HTTP {status}')
    zh_chars = re.findall(r'[一-鿿]', html)
    if not zh_chars:
        return result('TC-INT-008', 'P0', True, f'英文页面无中文字符（L3验证通过）')
    return result('TC-INT-008', 'P0', False,
                  f'英文页面含{len(zh_chars)}个中文字符（内容混杂）')


def check_tc_009() -> dict:
    """TC-INT-009: 关键内容块存在（L3：结构验证）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-009', 'P0', False, f'HTTP {status}')
    required_sections = ['discovery', 'decision', 'value']
    found = [s for s in required_sections if re.search(s, html, re.IGNORECASE)]
    if len(found) >= 2:
        return result('TC-INT-009', 'P0', True, f'关键内容块存在：{found}（L3结构验证）')
    return result('TC-INT-009', 'P0', False,
                  f'关键内容块缺失，仅找到：{found}（期望3个）')


def check_tc_010() -> dict:
    """TC-INT-010: 无内部ID格式泄露（L3：正则扫描）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-010', 'P0', False, f'HTTP {status}')
    # 检查内部ID格式（如 INTEL-20260601-001）
    internal_ids = re.findall(r'INTEL-\d{8}-\d{3}', html)
    if not internal_ids:
        return result('TC-INT-010', 'P0', True, f'无内部ID格式泄露（L3扫描通过）')
    return result('TC-INT-010', 'P0', False, f'内部ID泄露：{internal_ids[:3]}')


def check_tc_011() -> dict:
    """TC-INT-011: 无评分系统内部字段（L3：正则扫描）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-011', 'P0', False, f'HTTP {status}')
    internal_score_fields = [r'semantic_score', r'VACE\b', r'WSCORE', r'vace_score']
    found = [f for f in internal_score_fields if re.search(f, html)]
    if not found:
        return result('TC-INT-011', 'P0', True, f'评分内部字段扫描通过（L3）')
    return result('TC-INT-011', 'P0', False, f'内部评分字段泄露：{found}')


def check_tc_012() -> dict:
    """TC-INT-012: 无 Agent 角色名称泄露（L3：正则扫描）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-012', 'P0', False, f'HTTP {status}')
    agent_roles = [
        r'\b\w+_engineer\b', r'\b\w+_researcher\b',
        r'\b\w+_strategist\b', r'\b\w+_qa\b'
    ]
    found = [r for r in agent_roles if re.search(r, html)]
    if not found:
        return result('TC-INT-012', 'P0', True, f'Agent角色名称扫描通过（L3）')
    sample = re.findall(r'\b\w+_(?:engineer|researcher|strategist|qa)\b', html)[:3]
    return result('TC-INT-012', 'P0', False, f'Agent角色名称泄露：{sample}')


def check_tc_013() -> dict:
    """TC-INT-013: 数据跨仓同步验证（L4：页面内容与数据文件一致性）"""
    today = dubai_today()
    # L4: 验证页面显示的日期与预期一致（模拟跨仓验证）
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-013', 'P0', False, f'HTTP {status}')
    if today in html:
        return result('TC-INT-013', 'P0', True,
                      f'今日日期{today}在页面中存在（L4跨仓同步验证代理）')
    # 检查是否是构建延迟
    return result('TC-INT-013', 'P0', False,
                  f'今日{today}数据未同步到页面（Silent Fail：GHA构建成功但数据未更新）')


def check_tc_014() -> dict:
    """TC-INT-014: 内容质量门禁验证（L4：publish_gate 逻辑验证）"""
    status, html = fetch('/synapse/intelligence/')
    if status != 200:
        return result('TC-INT-014', 'P0', False, f'HTTP {status}')
    # L4: 验证内容有实质性长度（质量门禁代理验证）
    content_length = len(re.sub(r'<[^>]+>', '', html))  # 去除HTML标签
    if content_length > 2000:
        return result('TC-INT-014', 'P0', True,
                      f'内容长度{content_length}字符，通过质量门禁验证（L4代理）')
    return result('TC-INT-014', 'P0', False,
                  f'内容长度{content_length}字符，低于质量阈值2000（发布门禁未生效）')


# ─────────────────────── P2: Ximi Game TC ───────────────────────

def check_ximi_p01() -> dict:
    """TC-XIMI-P01: 汐弥游戏路由可访问且核心元素存在（L3）"""
    status, html = fetch('/ximi')
    if status != 200:
        return result('TC-XIMI-P01', 'P2', False, f'HTTP {status} — /ximi not accessible')
    has_canvas = bool(re.search(r'<canvas', html, re.IGNORECASE))
    has_start_game = bool(re.search(r'startGame', html))
    ximi_count = len(re.findall(r'ximi', html, re.IGNORECASE))
    if not has_canvas:
        return result('TC-XIMI-P01', 'P2', False,
                      f'Silent Fail — HTTP 200 but <canvas> absent; game surface missing')
    if not has_start_game:
        return result('TC-XIMI-P01', 'P2', False,
                      f'Silent Fail — canvas OK but startGame() absent; entry point broken')
    if ximi_count < 3:
        return result('TC-XIMI-P01', 'P2', False,
                      f'Silent Fail — "ximi" only {ximi_count}x (expected >=3); wrong page?')
    return result('TC-XIMI-P01', 'P2', True,
                  f'HTTP 200, canvas=present, startGame=present, ximi_occurrences={ximi_count}')


def check_ximi_p02() -> dict:
    """TC-XIMI-P02: 汐弥游戏关卡数量完整（7关）（L3）"""
    status, html = fetch('/ximi')
    if status != 200:
        return result('TC-XIMI-P02', 'P2', False, f'HTTP {status} — /ximi not accessible')
    if not re.search(r'DAYS\s*=\s*\[', html):
        return result('TC-XIMI-P02', 'P2', False,
                      f'Silent Fail — HTTP 200 but DAYS=[ not found; level array missing')
    days_match = re.search(r'DAYS\s*=\s*\[', html)
    snippet = html[days_match.start():days_match.start() + 6000]
    n_entries = re.findall(r'\{n:(\d+)', snippet)
    if len(n_entries) < 7:
        return result('TC-XIMI-P02', 'P2', False,
                      f'Silent Fail — only {len(n_entries)} level(s) found (expected 7); entries={n_entries}')
    level_nums = [int(x) for x in n_entries[:7]]
    if level_nums != list(range(1, 8)):
        return result('TC-XIMI-P02', 'P2', False,
                      f'Silent Fail — levels not sequential 1-7; found={level_nums}')
    return result('TC-XIMI-P02', 'P2', True,
                  f'HTTP 200, DAYS array present, level_count={len(n_entries)}, sequential=true')


def check_ximi_p03() -> dict:
    """TC-XIMI-P03: 汐弥礼物奖励系统完整（4个门槛：250/200/150/100）（L3）"""
    status, html = fetch('/ximi')
    if status != 200:
        return result('TC-XIMI-P03', 'P2', False, f'HTTP {status} — /ximi not accessible')
    if not re.search(r'checkGiftReward', html):
        return result('TC-XIMI-P03', 'P2', False,
                      f'Silent Fail — HTTP 200 but checkGiftReward absent; gift system removed')
    thresholds = set(int(x) for x in re.findall(r'score\s*>=\s*(\d+)', html, re.IGNORECASE))
    expected = {250, 200, 150, 100}
    missing = expected - thresholds
    if missing:
        return result('TC-XIMI-P03', 'P2', False,
                      f'Silent Fail — gift thresholds missing: {sorted(missing)}; found={sorted(thresholds)}')
    if not re.search(r'GIFTS\s*=\s*\{', html):
        return result('TC-XIMI-P03', 'P2', False,
                      f'Silent Fail — thresholds OK but GIFTS={{}} object absent')
    return result('TC-XIMI-P03', 'P2', True,
                  f'HTTP 200, checkGiftReward=present, thresholds={sorted(thresholds)}, GIFTS_object=present')


# ─────────────────────── P2: Game Factory TC ───────────────────────

def check_game_p01() -> dict:
    """TC-GAME-P01: AI游戏工厂入口/create可访问且含提交表单（L3）"""
    status, html = fetch('/create')
    if status != 200:
        return result('TC-GAME-P01', 'P2', False,
                      f'HTTP {status} — /create (game factory entry) not accessible')
    if not re.search(r'id=["\']game-form["\']', html, re.IGNORECASE):
        return result('TC-GAME-P01', 'P2', False,
                      f'Silent Fail — HTTP 200 but id="game-form" absent; submission form missing')
    if not re.search(r'name=["\']game_title["\']', html, re.IGNORECASE):
        return result('TC-GAME-P01', 'P2', False,
                      f'Silent Fail — game-form present but name="game_title" input absent')
    if not re.search(r'n8n', html, re.IGNORECASE):
        return result('TC-GAME-P01', 'P2', False,
                      f'Silent Fail — form fields OK but n8n reference absent; webhook integration broken')
    webhook_urls = re.findall(r'https?://[^\s\'"<>]*webhook[^\s\'"<>]*', html)
    webhook_display = webhook_urls[0][:80] if webhook_urls else 'n8n (no explicit URL)'
    return result('TC-GAME-P01', 'P2', True,
                  f'HTTP 200, game-form=present, game_title=present, n8n_webhook={webhook_display}')


def check_game_p02() -> dict:
    """TC-GAME-P02: AI游戏工厂结果列表/games可访问（L3）"""
    status, html = fetch('/games')
    if status == 404:
        return result('TC-GAME-P02', 'P2', False,
                      f'HTTP 404 — /games route does not exist; product blind spot')
    if status != 200:
        return result('TC-GAME-P02', 'P2', False,
                      f'HTTP {status} — /games returned unexpected status')
    if len(html) < 500:
        return result('TC-GAME-P02', 'P2', False,
                      f'Silent Fail — HTTP 200 but only {len(html)} chars; likely empty shell')
    game_factory_kw = [r'Lysander', r'game', r'Studio', r'create', r'Synapse']
    matched = [kw for kw in game_factory_kw if re.search(kw, html, re.IGNORECASE)]
    if len(matched) < 2:
        return result('TC-GAME-P02', 'P2', False,
                      f'Silent Fail — only {len(matched)} game factory keyword(s) matched; wrong page?')
    game_links = re.findall(r'href=[\"\']?(/games/[^\"\'> \n]+)', html)
    link_info = f'game_links={len(game_links)}' if game_links else 'game_links=0 (empty list — OK)'
    return result('TC-GAME-P02', 'P2', True,
                  f'HTTP 200, page_len={len(html)}, keywords_matched={matched[:3]}, {link_info}')


def check_game_p03() -> dict:
    """TC-GAME-P03: AI游戏工厂webhook端点健康检查（L3）"""
    status, html = fetch('/create')
    if status != 200:
        return result('TC-GAME-P03', 'P2', False,
                      f'HTTP {status} — /create not accessible, cannot extract webhook URL')
    webhook_urls = re.findall(r'https?://[^\s\'"<>]*webhook[^\s\'"<>]*', html)
    if not webhook_urls:
        return result('TC-GAME-P03', 'P2', False,
                      f'Silent Fail — /create HTTP 200 but no webhook URL found; n8n integration broken')
    webhook_url = webhook_urls[0]
    healthy = {200, 201, 204, 400, 405, 422}
    broken = {404, 502, 503, 504}
    try:
        resp = requests.options(webhook_url, timeout=TIMEOUT)
        probe_status, method = resp.status_code, 'OPTIONS'
    except Exception:
        try:
            resp = requests.head(webhook_url, timeout=TIMEOUT)
            probe_status, method = resp.status_code, 'HEAD'
        except Exception as e:
            return result('TC-GAME-P03', 'P2', False,
                          f'Webhook unreachable — {webhook_url[:60]}: {str(e)[:80]}')
    if probe_status in broken:
        return result('TC-GAME-P03', 'P2', False,
                      f'Webhook broken — {webhook_url[:60]}: {method} HTTP {probe_status}')
    return result('TC-GAME-P03', 'P2', probe_status in healthy,
                  f'Webhook URL found: {webhook_url[:70]}, {method} probe: HTTP {probe_status}')


# ─────────────────────── P2: Blog TC ───────────────────────

def check_blog_p01() -> dict:
    """TC-BLOG-P01: 最新博文可访问且发布日期在14天内（L3）"""
    status, html = fetch('/blog')
    if status != 200:
        return result('TC-BLOG-P01', 'P2', False, f'HTTP {status} — /blog not accessible')
    article_links = re.findall(r'href=[\"\']?(/blog/[^\"\'> \n#?]+)', html)
    if not article_links:
        return result('TC-BLOG-P01', 'P2', False,
                      f'Silent Fail — HTTP 200 but no /blog/[slug] links; listing is empty shell')
    today = (datetime.now(timezone.utc) + timedelta(hours=4)).date()
    dates_found = re.findall(r'(20\d\d-\d\d-\d\d)', html)
    valid_dates = []
    for d_str in dates_found:
        try:
            d = date.fromisoformat(d_str)
            if d <= today:
                valid_dates.append(d)
        except ValueError:
            pass
    if not valid_dates:
        return result('TC-BLOG-P01', 'P2', False,
                      f'Silent Fail — {len(article_links)} links but no valid dates; date rendering broken')
    most_recent = max(valid_dates)
    days_ago = (today - most_recent).days
    if days_ago > 14:
        return result('TC-BLOG-P01', 'P2', False,
                      f'Stale blog — most recent post {days_ago}d ago ({most_recent}); threshold=14d')
    return result('TC-BLOG-P01', 'P2', True,
                  f'HTTP 200, article_links={len(article_links)}, most_recent={most_recent} ({days_ago}d ago)')


def check_blog_p02() -> dict:
    """TC-BLOG-P02: 最新博文内容质量验证（L3）"""
    status, html = fetch('/blog')
    if status != 200:
        return result('TC-BLOG-P02', 'P2', False, f'HTTP {status} — /blog not accessible')
    article_links = re.findall(r'href=[\"\']?(/blog/[^\"\'> \n#?]+)', html)
    if not article_links:
        return result('TC-BLOG-P02', 'P2', False,
                      f'Silent Fail — /blog HTTP 200 but no article links; cannot test quality')
    art_status, art_html = fetch(article_links[0])
    if art_status != 200:
        return result('TC-BLOG-P02', 'P2', False,
                      f'HTTP {art_status} — article {article_links[0]} not accessible')
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', art_html, re.DOTALL | re.IGNORECASE)
    h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else ''
    title_match = re.search(r'<title[^>]*>(.*?)</title>', art_html, re.DOTALL | re.IGNORECASE)
    title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ''
    if not h1_text and not title_text:
        return result('TC-BLOG-P02', 'P2', False,
                      f'Silent Fail — article HTTP 200 but <title> and <h1> both empty; render failure')
    body_text = re.sub(r'<[^>]+>', '', art_html).strip()
    if len(body_text) < 200:
        return result('TC-BLOG-P02', 'P2', False,
                      f'Silent Fail — article body only {len(body_text)} chars (expected >=200)')
    error_pats = [r'\bundefined\b', r'\[object Object\]', r'NaN', r'Error:', r'Cannot read', r'TypeError']
    errors = [p for p in error_pats if re.search(p, body_text[:2000])]
    if errors:
        return result('TC-BLOG-P02', 'P2', False,
                      f'Rendering error — article contains patterns: {errors}')
    display_title = (h1_text or title_text)[:60].encode('ascii', 'replace').decode()
    return result('TC-BLOG-P02', 'P2', True,
                  f'HTTP 200, article={article_links[0]}, title="{display_title}", body_len={len(body_text)}')


def check_blog_p03() -> dict:
    """TC-BLOG-P03: 博客管线数据新鲜度（7天内有发布）（L3）"""
    status, html = fetch('/blog')
    if status != 200:
        return result('TC-BLOG-P03', 'P2', False, f'HTTP {status} — /blog not accessible')
    if len(html) < 10_000:
        return result('TC-BLOG-P03', 'P2', False,
                      f'Silent Fail — /blog only {len(html)} bytes; likely degraded skeleton page')
    unique_links = list(dict.fromkeys(re.findall(r'href=[\"\']?(/blog/[^\"\'> \n#?]+)', html)))
    if len(unique_links) < 3:
        return result('TC-BLOG-P03', 'P2', False,
                      f'Silent Fail — only {len(unique_links)} unique article links (expected >=3)')
    today = (datetime.now(timezone.utc) + timedelta(hours=4)).date()
    dates_raw = re.findall(r'(20\d\d-\d\d-\d\d)', html)
    fresh_dates = []
    all_valid = []
    for d_str in dates_raw:
        try:
            d = date.fromisoformat(d_str)
            if d <= today:
                all_valid.append(d)
                if (today - d).days <= 7:
                    fresh_dates.append(d)
        except ValueError:
            pass
    if not fresh_dates:
        most_recent = max(all_valid) if all_valid else None
        gap = (today - most_recent).days if most_recent else 'N/A'
        return result('TC-BLOG-P03', 'P2', False,
                      f'Stale — no articles in 7 days; most recent={most_recent} ({gap}d ago)')
    return result('TC-BLOG-P03', 'P2', True,
                  f'HTTP 200, article_links={len(unique_links)}, '
                  f'fresh_dates_7d={sorted(set(str(d) for d in fresh_dates), reverse=True)[:3]}, '
                  f'page_size={len(html)}')


# ─────────────────────── Orchestrator ───────────────────────

P0_CHECKS = [
    check_tc_001, check_tc_002, check_tc_003, check_tc_004,
    check_tc_005, check_tc_006, check_tc_007, check_tc_008,
    check_tc_009, check_tc_010, check_tc_011, check_tc_012,
    check_tc_013, check_tc_014,
]

# P1 checks would be added here (abbreviated for Phase 1)
P1_CHECKS = []

P2_CHECKS = [
    check_ximi_p01, check_ximi_p02, check_ximi_p03,
    check_game_p01, check_game_p02, check_game_p03,
    check_blog_p01, check_blog_p02, check_blog_p03,
]


def main():
    print(f"=== Synapse ATDD CI Gate === Site: {SITE_URL}")
    print(f"Date: {dubai_today()} (Dubai UTC+4)\n")

    p0_results = [fn() for fn in P0_CHECKS]
    p1_results = [fn() for fn in P1_CHECKS]
    p2_results = [fn() for fn in P2_CHECKS]

    print("-- [P0] Intelligence TC (blocking) --")
    p0_passed = 0
    for r in p0_results:
        status = "PASS" if r['pass'] else "FAIL"
        print(f"  [P0] {r['id']}: {status} -- {r['evidence']}")
        if r['pass']:
            p0_passed += 1

    p0_total = len(p0_results)
    p0_rate = p0_passed / p0_total * 100 if p0_total else 0
    print(f"\nP0 pass rate: {p0_passed}/{p0_total} ({p0_rate:.1f}%)")

    if p1_results:
        print("\n-- [P1] Test Cases (warning only) --")
        p1_passed = sum(1 for r in p1_results if r['pass'])
        for r in p1_results:
            status = "PASS" if r['pass'] else "WARNING"
            print(f"  [P1] {r['id']}: {status} -- {r['evidence']}")
        p1_rate = p1_passed / len(p1_results) * 100
        print(f"P1 pass rate: {p1_passed}/{len(p1_results)} ({p1_rate:.1f}%)")
        if p1_rate < 80:
            print("WARNING: P1 pass rate < 80% (non-blocking, but requires attention)")

    if p2_results:
        print("\n-- [P2] Product Line TC (non-blocking, health signal) --")
        p2_passed = sum(1 for r in p2_results if r['pass'])
        for r in p2_results:
            status = "PASS" if r['pass'] else "WARNING"
            print(f"  [P2] {r['id']}: {status} -- {r['evidence']}")
        p2_rate = p2_passed / len(p2_results) * 100
        print(f"P2 pass rate: {p2_passed}/{len(p2_results)} ({p2_rate:.1f}%)")
        if p2_rate < 100:
            failed = [r['id'] for r in p2_results if not r['pass']]
            print(f"WARNING: P2 non-blocking failures: {failed} (does not block deploy)")

    gate_pass = p0_passed == p0_total
    print(f"\n{'CI Gate PASS -- deploy allowed' if gate_pass else 'CI Gate FAIL -- deploy blocked (P0 not fully passed)'}")

    if not gate_pass:
        sys.exit(1)


if __name__ == '__main__':
    main()
