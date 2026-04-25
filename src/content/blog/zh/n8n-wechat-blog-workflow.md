---
title: "n8n 微信公众号博客发布工作流开发复盘"
slug: n8n-wechat-blog-workflow
description: "通过 n8n 工作流将个人网站博客内容自动发布到微信公众号草稿箱，完整记录踩坑过程与解决方案"
lang: zh
hasEnglish: true
pillar: ops-practical
priority: P3
publishDate: 2026-04-06
author: content_strategist
keywords:
  - "n8n"
  - "微信公众号"
  - "工作流"
---
## 背景

个人网站使用 Astro + Tailwind CSS 构建，发布的博客文章采用 Tailwind class 样式。
        需要将这些博客文章自动化发布到微信公众号草稿箱，供后续编辑发布。

微信公众号只支持有限的 HTML 子集，不支持：

- 所有 `class` 属性（Tailwind 的核心）
- `div`, `section`, `article` 等容器标签
- 外部 CSS 和 `style` 属性（部分支持）

## 工作流设计

```
Manual Trigger
      |
      v
+---------------+
| Fetch Article |  HTTP GET 抓取博客 HTML
+---------------+
      |
      v
+---------------+
| Get Token     |  获取 access_token
+---------------+
      |
      v
+---------------+
| Convert HTML  |  核心：HTML 清洗 + 样式转换
| Build Request |
+---------------+
      |
      v
+---------------+
| Create Draft  |  HTTP POST 到草稿箱 API
+---------------+
```

## 挑战一：微信公众号 HTML 限制

微信公众号支持的 HTML 核心标签非常有限：

支持的标签

`p`, `br`, `span`, `strong`, `em`,
          `u`, `h1`-`h4`, `ul`, `ol`,
          `li`, `blockquote`, `pre`, `code`, `img`

Tailwind 输出的 HTML 如 `<h1 class="text-2xl font-bold">` 会全部失效，变成无样式纯文本。

### 解决方案：内联样式转换

在 Code 节点中使用 JavaScript 将 Tailwind class 转换为内联样式：

```
// 示例：Tailwind 转内联样式
articleHtml = articleHtml
  // 移除 class 属性
  .replace(/\s*class="[^"]*"/gi, '')

  // 转换代码块样式
  .replace(/<code>/gi, '<code style="background:f4f4f4;padding:2px 6px;border-radius:3px;">')

  // 转换标题样式
  .replace(/

## ]*>/gi, '

')
  .replace(/<\/h2>/gi, '

')

  // 转换段落样式
  .replace(/

]*)>/gi, function(m, attrs) &#123;
    if (attrs.includes('style=')) return m;
    return '<p style="margin:14px 0;line-height:1.9;">';
  &#125;);
```

      <h2 class="text-2xl font-bold text-white mt-12">挑战二：access_token 传递问题

      <p>
        这是踩坑最多的地方。微信公众号 API 要求 `access_token` 作为查询参数传递，
        但 n8n HTTP Request 节点的表达式处理有特殊规则。

### 错误方式

```
// 错误：access_token 放在 URL 中
url: "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=&#123;&#123; $json.access_token &#125;&#125;"

// 错误：sendQuery 配合 bodyParameters
```

### 正确方式

```
// 正确配置
&#123;
  method: "POST",
  url: "https://api.weixin.qq.com/cgi-bin/draft/add",
  sendQuery: true,
  queryParameters: &#123;
    parameters: [&#123;
      name: "access_token",
      value: "=&#123;&#123; $json.access_token &#125;&#125;"
    &#125;]
  &#125;,
  sendBody: true,
  specifyBody: "string",
  contentType: "raw",
  rawContentType: "application/json",
  body: "=&#123;&#123; $json.body &#125;&#125;"
&#125;
```

关键发现

`sendQuery: true` 时，URL 中不应包含已有的 query string，
          token 必须通过 `queryParameters` 单独传递。

## 挑战三：文章内容边界提取

博客文章 HTML 中包含导航栏、侧边栏、footer 等非文章内容。
        最初使用正则表达式匹配 `
` 边界，但遇到嵌套标签时容易匹配错误。

### 错误方式

```
// 错误：正则匹配遇到嵌套 div 会提前终止
const proseMatch = html.match(/class="prose"[\s\S]*?<\/div>/);
// 导致 content 字段只包含标题，内容被截断
```

### 正确方式：精确位置计算

```
// 正确：使用 indexOf/lastIndexOf 精确计算边界
const articleStart = html.indexOf('');

// 找到 prose 类的开始位置
const proseClassIndex = html.indexOf('class="prose', articleStart);
const proseOpenTagEnd = html.indexOf('>', proseClassIndex) + 1;

// 找到 footer 的开始位置（在 prose 区域内）
const footerStartInArticle = html.indexOf('
        <summary class="cursor-pointer text-white/60 hover:text-white text-sm">[ 点击展开微信版思维导图 ]</summary>

          <div style="font-family: Georgia, serif; line-height: 2; white-space: pre-wrap;">═══════════════════════════════════
     ◆  n8n 微信公众号博客发布工作流  ◆
       自动化 · 零手动 · 草稿箱直达
═══════════════════════════════════

  ▼ 四大核心节点

    ① 抓取博客 HTML
       └─ HTTP GET → 源站文章页面

    ② 获取 access_token
       └─ 微信 API → client_credential

    ③ HTML 样式转换
       └─ Tailwind → 内联样式 · 内容清洗

    ④ 创建草稿箱
       └─ POST API → media_id 封面关联

───────────────────────────────────

  ★ 三大核心挑战 → 解决方案

    ⚡ 挑战一：HTML 标签限制
       问题：微信公众号不支持 class/style 标签
       解决：Tailwind class → 内联 style 属性

    ⚡ 挑战二：access_token 传递
       问题：URL 参数被表达式覆盖
       解决：sendQuery + queryParameters 组合

    ⚡ 挑战三：内容边界提取
       问题：嵌套 div 正则匹配提前终止
       解决：indexOf/lastIndexOf 精确位置计算

───────────────────────────────────

  ⚙ 关键配置参数
     AppID:    wx964591c526715c17
     API:      api.weixin.qq.com
     sendQuery: true (必须)
     thumb_media_id: 永久素材ID

      </details>

## 踩坑总结

1. n8n sendQuery 模式

使用 `sendQuery: true` 时，token 必须通过 `queryParameters` 传递，不能放在 URL 里。

2. body 类型选择

发送 JSON body 时，使用 `specifyBody: "string"` + `rawContentType: "application/json"`，而非 `jsonBody`。

3. HTML 提取

遇到嵌套标签时，位置计算（`indexOf`）比正则表达式更可靠。

4. thumb_media_id 必填

微信公众号草稿箱 API 要求必须上传封面图获取 `media_id`，不能留空。

## 最终结果

工作流成功创建，草稿箱文章包含完整内容：

- 标题提取
- 正文完整提取
- 代码块保留
- 内联样式转换
- 封面图关联
