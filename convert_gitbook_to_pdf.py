#!/usr/bin/env python3
"""
GitBook to PDF Converter
========================
Convert GitBook markdown projects directly to a single, beautifully formatted
PDF book in one shot.

Features:
- Parses SUMMARY.md for exact chapter ordering and table of contents
- Dot-leader page numbers in Table of Contents (target-counter)
- Transforms GitBook-specific tags ({% hint %}, {% tabs %}, {% code %}, <figure>)
- SVG vector icons for callout boxes (no missing font glyphs)
- Custom badge for :1234: code analysis annotations
- Automatic resolution of local images (.gitbook/assets/...)
- Markdown parsing inside HTML containers (md_in_html)
- Syntax-highlighted code blocks with line numbers (Pygments)
- Elegant book layout: Cover Page, Table of Contents, Headers/Footers with page numbers
- PDF hierarchical bookmarks (Outlines) matching chapters
- Page break optimization to prevent awkward splits
"""

import os
import sys
import re
import html
import argparse
import datetime
import markdown
from pygments.formatters import HtmlFormatter
from weasyprint import HTML, CSS
from pypdf import PdfReader

# Base styling for GitBook PDF conversion
BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

@page {
  size: A4;
  margin: 22mm 18mm 22mm 18mm;
  @top-right {
    content: "엔트리로 파이썬 기초 입문하기";
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 8pt;
    color: #94a3b8;
  }
  @bottom-center {
    content: counter(page);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 8.5pt;
    color: #64748b;
  }
}

@page cover-page-style {
  margin: 0;
  @top-right { content: none; }
  @bottom-center { content: none; }
}

@page toc-page-style {
  @top-right { content: none; }
  @bottom-center {
    content: counter(page, lower-roman);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 8.5pt;
    color: #64748b;
  }
}

@page back-cover-style {
  margin: 0;
  @top-right { content: none; }
  @bottom-center { content: none; }
}

* {
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Pretendard", sans-serif;
  font-size: 10pt;
  line-height: 1.75;
  color: #1e293b;
  word-break: keep-all;
  overflow-wrap: break-word;
}

/* ================= Cover Page ================= */
.cover-container {
  page: cover-page-style;
  page-break-before: avoid;
  page-break-after: always;
  height: 297mm;
  padding: 50mm 25mm 30mm 25mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 60%, #0f766e 100%);
  color: #ffffff;
}

.cover-badge {
  display: inline-block;
  background: rgba(45, 212, 191, 0.15);
  border: 1px solid #2dd4bf;
  color: #2dd4bf;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 9.5pt;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 25px;
  text-transform: uppercase;
}

.cover-title {
  font-size: 32pt;
  font-weight: 800;
  line-height: 1.25;
  color: #ffffff;
  margin: 0 0 15px 0;
  letter-spacing: -0.02em;
}

.cover-subtitle {
  font-size: 14pt;
  font-weight: 400;
  color: #94a3b8;
  margin: 0 0 40px 0;
  line-height: 1.5;
}

.cover-divider {
  width: 60px;
  height: 4px;
  background: #2dd4bf;
  border-radius: 2px;
  margin-bottom: auto;
}

.cover-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  padding-top: 25px;
  font-size: 10pt;
  color: #cbd5e1;
  line-height: 1.8;
}

.cover-footer strong {
  color: #f8fafc;
}

/* ================= Table of Contents ================= */
.toc-page {
  page: toc-page-style;
  page-break-before: always;
  page-break-after: always;
  padding-top: 5mm;
}

.toc-heading {
  font-size: 20pt;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 2px solid #0f766e;
  padding-bottom: 8px;
  margin-bottom: 20px;
  bookmark-level: none;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-item {
  margin: 8px 0;
  line-height: 1.5;
}

.toc-item a {
  display: block;
  text-decoration: none;
}

.toc-item a::after {
  content: " " leader('.') " " target-counter(attr(href), page);
  float: right;
  color: #64748b;
  font-weight: 400;
  font-size: 8.5pt;
}

.toc-item-level-0 {
  font-weight: 700;
  font-size: 10pt;
  margin-top: 14px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 3px;
}

.toc-item-level-0 a {
  color: #0f172a;
}

.toc-item-level-1 {
  font-weight: 400;
  font-size: 9pt;
  padding-left: 18px;
}

.toc-item-level-1 a {
  color: #334155;
}

/* ================= Chapters & Headings ================= */
.chapter {
  page-break-before: always;
  padding-top: 4mm;
}

h1 {
  font-size: 18pt;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0.3em;
  margin-top: 0;
  margin-bottom: 0.8em;
  bookmark-level: 1;
  page-break-after: avoid;
}

h2 {
  font-size: 13pt;
  font-weight: 600;
  color: #1e293b;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 0.25em;
  margin-top: 1.5em;
  margin-bottom: 0.6em;
  bookmark-level: 2;
  page-break-after: avoid;
}

h3 {
  font-size: 11pt;
  font-weight: 600;
  color: #334155;
  margin-top: 1.2em;
  margin-bottom: 0.5em;
  bookmark-level: 3;
  page-break-after: avoid;
}

h4 {
  font-size: 10pt;
  font-weight: 600;
  color: #475569;
  margin-top: 1.1em;
  margin-bottom: 0.4em;
  page-break-after: avoid;
}

p {
  margin: 0.8em 0;
  line-height: 1.75;
}

strong {
  font-weight: 600;
  color: #0f172a;
}

em {
  color: #334155;
}

a {
  color: #0284c7;
  text-decoration: underline;
  text-underline-offset: 2px;
}

a strong, a em, strong a, em a {
  color: #0284c7;
}

blockquote {
  border-left: 3px solid #cbd5e1;
  padding: 6px 14px;
  margin: 1em 0;
  color: #475569;
  background: #f8fafc;
  border-radius: 0 4px 4px 0;
  font-style: italic;
  page-break-inside: avoid;
}

/* ================= Images & Figures ================= */
img {
  max-width: 100%;
  max-height: 380px;
  height: auto;
  display: block;
  margin: 0 auto;
  object-fit: contain;
}

img[data-size="line"] {
  display: inline-block !important;
  vertical-align: middle !important;
  max-height: 1.5em !important;
  width: auto !important;
  margin: 0 4px !important;
}

figure, .gb-figure {
  margin: 1.3em 0;
  text-align: center;
  page-break-inside: avoid;
}

figcaption {
  font-size: 8.5pt;
  color: #64748b;
  margin-top: 6px;
  text-align: center;
}

/* ================= GitBook Hints / Callouts ================= */
.gb-hint {
  border-left: 4px solid #3b82f6;
  background: #f0f9ff;
  padding: 10px 14px;
  border-radius: 4px;
  margin: 1.3em 0;
  page-break-inside: avoid;
}

.gb-hint-info { border-color: #0284c7; background: #f0f9ff; }
.gb-hint-warning { border-color: #f59e0b; background: #fffbeb; }
.gb-hint-danger { border-color: #ef4444; background: #fef2f2; }
.gb-hint-success { border-color: #10b981; background: #f0fdf4; }

.gb-hint-title {
  font-size: 9pt;
  font-weight: 700;
  color: #0369a1;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.gb-hint-warning .gb-hint-title { color: #b45309; }
.gb-hint-danger .gb-hint-title { color: #b91c1c; }
.gb-hint-success .gb-hint-title { color: #047857; }

.gb-hint-body p {
  margin: 0.4em 0;
  font-size: 9.5pt;
}

/* ================= GitBook Tabs ================= */
.gb-tabs-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin: 1.5em 0;
  background: #fafafa;
  overflow: hidden;
}

.gb-tab-item {
  border-bottom: 1px solid #e2e8f0;
  page-break-inside: avoid;
}

.gb-tab-item:last-child {
  border-bottom: none;
}

.gb-tab-header {
  background: #f1f5f9;
  padding: 6px 14px;
  font-size: 9pt;
  color: #1e293b;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
  page-break-after: avoid;
}

.gb-tab-badge {
  background: #0284c7;
  color: #ffffff;
  font-size: 7.5pt;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.gb-tab-body {
  padding: 12px 16px;
  background: #ffffff;
}

.gb-tab-body img {
  max-height: 300px;
}

/* ================= Code Blocks & Highlighting ================= */
.highlight {
  background: #f8fafc !important;
  border-radius: 6px;
  margin: 1em 0;
  overflow: hidden;
  page-break-inside: avoid;
  font-size: 8.5pt;
  border: 1px solid #e2e8f0;
}

.highlighttable {
  width: 100%;
  border-collapse: collapse;
  border-spacing: 0;
  margin: 0 !important;
  padding: 0 !important;
}

.linenos {
  width: 36px;
  background: #f1f5f9;
  border-right: 1px solid #e2e8f0;
  vertical-align: top !important;
  padding: 8px 8px 8px 4px !important;
  margin: 0 !important;
  user-select: none;
}

.code {
  vertical-align: top !important;
  padding: 8px 12px 8px 12px !important;
  margin: 0 !important;
}

.linenos pre,
.code pre {
  margin: 0 !important;
  padding: 0 !important;
  font-family: 'JetBrains Mono', Menlo, Monaco, Consolas, monospace !important;
  font-size: 8.5pt !important;
  line-height: 16pt !important;
  white-space: pre !important;
}

.linenos pre {
  color: #94a3b8;
  text-align: right;
}

.code pre {
  color: #1e293b;
}

.linenos pre span,
.code pre span,
.code pre code {
  font-family: inherit !important;
  font-size: inherit !important;
  line-height: inherit !important;
  vertical-align: baseline !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}

code:not(.code pre code) {
  background: #f1f5f9;
  color: #0f172a;
  padding: 1.5px 5.5px;
  border-radius: 4px;
  font-size: 8.5pt;
  font-family: 'JetBrains Mono', Menlo, Monaco, Consolas, monospace;
  border: 1px solid #e2e8f0;
}

/* Code line analysis icon */
.gb-code-explain-icon {
  display: inline-block;
  vertical-align: -3px;
  margin-right: 6px;
}

/* ================= Back Cover Page ================= */
.back-cover-container {
  page: back-cover-style;
  page-break-before: always;
  height: 297mm;
  padding: 40mm 25mm 25mm 25mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 60%, #0f766e 100%);
  color: #ffffff;
  box-sizing: border-box;
}

.back-badge {
  display: inline-block;
  background: rgba(45, 212, 191, 0.15);
  border: 1px solid #2dd4bf;
  color: #2dd4bf;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 9.5pt;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 25px;
  text-transform: uppercase;
}

.back-title {
  font-size: 22pt;
  font-weight: 700;
  line-height: 1.4;
  color: #ffffff;
  margin: 0 0 20px 0;
  letter-spacing: -0.02em;
}

.back-desc {
  font-size: 10.5pt;
  line-height: 1.8;
  color: #cbd5e1;
  margin-bottom: 25px;
  word-break: keep-all;
}

.back-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 35px;
}

.feature-item {
  background: rgba(255, 255, 255, 0.05);
  border-left: 3px solid #2dd4bf;
  padding: 12px 18px;
  border-radius: 0 8px 8px 0;
}

.feature-title {
  font-size: 10.5pt;
  font-weight: 600;
  color: #2dd4bf;
  margin-bottom: 4px;
}

.feature-text {
  font-size: 9.5pt;
  color: #cbd5e1;
  line-height: 1.5;
  margin: 0;
}

.back-target {
  border-top: 1px dashed rgba(255, 255, 255, 0.2);
  padding-top: 15px;
  font-size: 9.5pt;
  color: #cbd5e1;
}

.back-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  font-size: 9.5pt;
  color: #cbd5e1;
}

.barcode-box {
  background: #ffffff;
  color: #0f172a;
  padding: 8px 14px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 8.5pt;
  text-align: center;
  line-height: 1.2;
}

.barcode-lines {
  font-size: 18pt;
  letter-spacing: 2px;
  font-family: 'Courier New', monospace;
}

/* ================= Tables ================= */
table:not(.highlighttable) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.3em 0;
  font-size: 9pt;
  page-break-inside: avoid;
}

table:not(.highlighttable) th, table:not(.highlighttable) td {
  border: 1px solid #cbd5e1;
  padding: 7px 10px;
  text-align: left;
  vertical-align: middle;
}

table:not(.highlighttable) th {
  background: #f8fafc;
  font-weight: 600;
  color: #0f172a;
  text-align: center;
}

table:not(.highlighttable) td img {
  max-height: 42px;
  width: auto;
  display: block;
  margin: 0 auto;
}

/* ================= Sponsor Block ================= */
.sponsor-box {
  margin: 2em 0 1em 0;
  padding: 14px 18px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  text-align: center;
  page-break-inside: avoid;
}

.sponsor-title {
  font-size: 10pt;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.sponsor-grid {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.sponsor-card {
  text-align: center;
}

.sponsor-card img {
  width: 150px;
  height: auto;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
}

.sponsor-card span {
  display: block;
  margin-top: 6px;
  font-size: 8.5pt;
  color: #475569;
}
"""

# Vector SVG icons for hints
SVG_ICONS = {
    "info": '<svg width="15" height="15" viewBox="0 0 24 24" fill="#0284c7" style="vertical-align: -2px;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
    "warning": '<svg width="15" height="15" viewBox="0 0 24 24" fill="#f59e0b" style="vertical-align: -2px;"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>',
    "danger": '<svg width="15" height="15" viewBox="0 0 24 24" fill="#ef4444" style="vertical-align: -2px;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11H7v-2h10v2z"/></svg>',
    "success": '<svg width="15" height="15" viewBox="0 0 24 24" fill="#10b981" style="vertical-align: -2px;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>'
}

def parse_summary(summary_path, workspace_dir):
    """
    Parse SUMMARY.md to obtain chapter hierarchy and file paths.
    """
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"SUMMARY.md not found at {summary_path}")

    with open(summary_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    chapters = []
    pattern = re.compile(r"^(\s*)[*-]\s*\[(.*?)\]\((.*?)\)")

    for line in lines:
        match = pattern.match(line)
        if match:
            indent, title, rel_path = match.groups()
            level = len(indent) // 2
            # Skip external or anchor-only links
            if rel_path.startswith("http://") or rel_path.startswith("https://") or rel_path.startswith("#"):
                continue

            full_path = os.path.normpath(os.path.join(workspace_dir, rel_path))
            chapters.append({
                "level": level,
                "title": title.strip(),
                "rel_path": rel_path.strip(),
                "full_path": full_path
            })

    return chapters


def preprocess_gitbook_markdown(md_content, file_dir, workspace_dir):
    """
    Transform GitBook markdown tags into standard HTML components.
    """
    # 1. Resolve include tag ({% include "..." %})
    def replace_include(match):
        toss_path = os.path.join(workspace_dir, "pub/imgs/toss.jpg")
        kakao_path = os.path.join(workspace_dir, "pub/imgs/kakao.jpg")
        if os.path.exists(toss_path) and os.path.exists(kakao_path):
            return f"""
<div class="sponsor-box">
  <div class="sponsor-title">여러분의 후원은 컨텐트 제작에 큰 힘이 됩니다!</div>
  <div class="sponsor-grid">
    <div class="sponsor-card">
      <img src="file://{toss_path}" alt="Toss 후원" />
      <span>토스</span>
    </div>
    <div class="sponsor-card">
      <img src="file://{kakao_path}" alt="카카오페이 후원" />
      <span>카카오페이</span>
    </div>
  </div>
</div>
"""
        return ""

    md_content = re.sub(r'\{%\s*include\s*"[^"]+"\s*%\}', replace_include, md_content)

    # 2. Fix HTML entities and escaped markdown characters
    md_content = md_content.replace("&#x20;", " ").replace("&#x26;", "&").replace("&nbsp;", " ")
    md_content = md_content.replace(r"\~", "~")

    # 2-1. Convert HTML <pre class="language-..."> tags to standard fenced code blocks
    def convert_pre_tags_to_fenced(text):
        def repl(m):
            lang = m.group(1) or 'python'
            code = m.group(2)
            clean_code = re.sub(r'</?[a-zA-Z][^>]*>', '', code)
            clean_code = html.unescape(clean_code)
            clean_code = clean_code.replace('&#x3C;', '<').replace('&#x3E;', '>')
            return f"\n\n```{lang}\n{clean_code.strip()}\n```\n\n"

        pattern = r'<pre\s+class="language-([^"]*)"[^>]*><code[^>]*>(.*?)</code></pre>'
        return re.sub(pattern, repl, text, flags=re.DOTALL)

    md_content = convert_pre_tags_to_fenced(md_content)

    # 3. Replace emoji shortcode :1234: with styled code-analysis icon (code tag </> icon)
    code_explain_icon = (
        '<svg class="gb-code-explain-icon" width="16" height="16" viewBox="0 0 20 20" fill="none">'
        '<circle cx="10" cy="10" r="9.5" fill="#0284c7"/>'
        '<path d="M6.5 7.5L4 10L6.5 12.5M13.5 7.5L16 10L13.5 12.5M11.5 6L8.5 14" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    md_content = md_content.replace(":1234:", code_explain_icon)

    # 4. Strip empty anchor tags like <a href="#id" id="id"></a>
    md_content = re.sub(r'<a\s+[^>]*id="[^"]*"[^>]*>\s*</a>', '', md_content)

    # Inner markdown parser for hints and tabs
    inner_md_parser = markdown.Markdown(
        extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'attr_list'],
        extension_configs={
            'codehilite': {
                'linenums': True,
                'css_class': 'highlight',
                'guess_lang': False
            }
        }
    )

    # 5. GitBook Tabs: {% tabs %} ... {% tab title="..." %} ... {% endtab %} ... {% endtabs %}
    def replace_tabs(match):
        tabs_inner = match.group(1)
        tab_pattern = r'\{%\s*tab\s+title="([^"]+)"\s*%\}(.*?)\{%\s*endtab\s*%\}'
        rendered_tabs = []
        for tab_match in re.finditer(tab_pattern, tabs_inner, re.DOTALL):
            tab_title = tab_match.group(1)
            tab_body = tab_match.group(2).strip()
            inner_md_parser.reset()
            parsed_tab_body = inner_md_parser.convert(tab_body)
            rendered_tabs.append(
                f'<div class="gb-tab-item">\n'
                f'  <div class="gb-tab-header"><span class="gb-tab-badge">탭</span> <strong>{tab_title}</strong></div>\n'
                f'  <div class="gb-tab-body">\n{parsed_tab_body}\n  </div>\n'
                f'</div>'
            )
        return f'<div class="gb-tabs-card">\n' + "\n".join(rendered_tabs) + '\n</div>'

    md_content = re.sub(r'\{%\s*tabs\s*%\}(.*?)\{%\s*endtabs\s*%\}', replace_tabs, md_content, flags=re.DOTALL)

    # 6. GitBook Hints: {% hint style="..." %} ... {% endhint %}
    def replace_hint(match):
        style = match.group(1).lower()
        content = match.group(2).strip()
        icon_svg = SVG_ICONS.get(style, SVG_ICONS["info"])
        title = style.upper()
        inner_md_parser.reset()
        parsed_content = inner_md_parser.convert(content)
        return (
            f'<div class="gb-hint gb-hint-{style}">\n'
            f'  <div class="gb-hint-title">{icon_svg} <span>{title}</span></div>\n'
            f'  <div class="gb-hint-body">\n{parsed_content}\n  </div>\n'
            f'</div>'
        )

    md_content = re.sub(r'\{%\s*hint\s+style="([^"]+)"\s*%\}(.*?)\{%\s*endhint\s*%\}', replace_hint, md_content, flags=re.DOTALL)

    # 7. GitBook Code blocks: {% code lineNumbers="true" %}
    md_content = re.sub(r'\{%\s*code\s*(?:lineNumbers="([^"]+)")?\s*%\}', '', md_content)
    md_content = re.sub(r'\{%\s*endcode\s*%\}', '', md_content)

    # 8. Resolve local image paths (both <img src="..."> and ![alt](src))
    def resolve_path(src):
        src = src.strip().strip('<>')
        if src.startswith("http://") or src.startswith("https://") or src.startswith("file://") or src.startswith("data:"):
            return src
        abs_path = os.path.normpath(os.path.join(file_dir, src))
        if os.path.exists(abs_path):
            return f"file://{abs_path}"
        return src

    def fix_img_tag(match):
        prefix = match.group(1)
        src = match.group(2)
        suffix = match.group(3)
        return f'{prefix}{resolve_path(src)}{suffix}'

    md_content = re.sub(r'(<img\s+[^>]*src=")([^"]+)(")', fix_img_tag, md_content)

    def fix_md_img(match):
        alt = match.group('alt')
        src = match.group('src_angle') or match.group('src_normal')
        return f'![{alt}]({resolve_path(src)})'

    pattern = r'!\[(?P<alt>[^\]]*)\]\((?:<(?P<src_angle>[^>]+)>|(?P<src_normal>[^)]+(?:\([^)]*\)[^)]*)*))\)'
    md_content = re.sub(pattern, fix_md_img, md_content)

    return md_content


def build_full_html(chapters, workspace_dir, meta, include_front_cover=True, include_back_cover=True):
    """
    Compile all chapters, cover, and TOC into a unified HTML document.
    """
    pygments_css = HtmlFormatter(style='vs').get_style_defs('.highlight')

    # Markdown renderer with Pygments codehilite and md_in_html
    md_parser = markdown.Markdown(
        extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'attr_list', 'md_in_html'],
        extension_configs={
            'codehilite': {
                'linenums': True,
                'css_class': 'highlight',
                'guess_lang': False
            }
        }
    )

    # 1. Generate Cover Page
    current_date = datetime.datetime.now().strftime("%Y년 %m월")
    cover_html = f"""
<div class="cover-container">
  <div>
    <span class="cover-badge">Python 입문 가이드</span>
    <h1 class="cover-title">{meta['title']}</h1>
    <p class="cover-subtitle">{meta['subtitle']}</p>
    <div class="cover-divider"></div>
  </div>
  <div class="cover-footer">
    <p><strong>저자:</strong> {meta['author']}</p>
    <p><strong>발행일:</strong> {current_date}</p>
    <p><strong>라이선스:</strong> Creative Commons BY-NC-SA 4.0</p>
  </div>
</div>
"""

    # 2. Generate TOC Items and Chapter Content
    toc_items = []
    chapter_sections = []

    for idx, chap in enumerate(chapters):
        chap_id = f"chap-{idx}"
        chap_level = chap["level"]
        chap_title = chap["title"]
        file_path = chap["full_path"]

        toc_class = f"toc-item toc-item-level-{chap_level}"
        toc_items.append(f'<li class="{toc_class}"><a href="#{chap_id}">{chap_title}</a></li>')

        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} not found, skipping content.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            raw_md = f.read()

        processed_md = preprocess_gitbook_markdown(raw_md, os.path.dirname(file_path), workspace_dir)
        md_parser.reset()
        body_html = md_parser.convert(processed_md)

        # Wrap chapter in section with anchor
        chapter_sections.append(
            f'<section class="chapter" id="{chap_id}">\n{body_html}\n</section>'
        )

    toc_html = f"""
<div class="toc-page">
  <h2 class="toc-heading">목차 (Table of Contents)</h2>
  <ul class="toc-list">
    {"".join(toc_items)}
  </ul>
</div>
"""

    # 3. Generate Back Cover Page
    back_cover_html = f"""
<div class="back-cover-container">
  <div>
    <span class="back-badge">ENTRY-PYTHON GUIDE</span>
    <h2 class="back-title">블록 코딩에서 텍스트 코딩으로 나아가는<br>가장 확실한 첫걸음</h2>
    <p class="back-desc">
      엔트리의 친숙한 블록 환경을 통해 파이썬의 핵심 문법과 프로그래밍 개념을
      자연스럽게 체득할 수 있도록 구성된 실전 입문 가이드입니다.
      블록 코딩 교육 이후 학습자의 텍스트 코딩으로의 원활한 전환을 돕고자 하는 교육자와,
      실전 개발 언어를 처음 배우고자 하는 입문자 모두를 위한 도서입니다.
    </p>

    <div class="back-features">
      <div class="feature-item">
        <div class="feature-title">✔ 1:1 비교를 통한 직관적 학습</div>
        <p class="feature-text">실행결과, 블록코딩, 엔트리-파이썬 코드를 한눈에 비교하여 코드 구조를 자연스럽게 이해합니다.</p>
      </div>
      <div class="feature-item">
        <div class="feature-title">✔ 파이썬 핵심 기초 문법 완벽 정복</div>
        <p class="feature-text">변수, 입출력, 조건문, 반복문, 리스트, 난수, 사용자 정의 함수까지 단계별로 체득합니다.</p>
      </div>
      <div class="feature-item">
        <div class="feature-title">✔ 현대 프로그래밍 패러다임 이해</div>
        <p class="feature-text">순차/병렬 처리, 이벤트 주도형, 객체 지향 프로그래밍의 핵심 개념을 기초부터 다룹니다.</p>
      </div>
    </div>

    <div class="back-target">
      <strong>대상 독자:</strong> 블록 코딩을 익힌 후 파이썬에 입문하려는 초·중·고 학습자 및 소프트웨어 교육자
    </div>
  </div>

  <div class="back-footer">
    <div>
      <p style="margin:0 0 4px 0;"><strong>저자:</strong> {meta['author']}</p>
      <p style="margin:0;"><strong>라이선스:</strong> Creative Commons BY-NC-SA 4.0</p>
    </div>
    <div class="barcode-box">
      <div class="barcode-lines">||| | |||| | |||</div>
      <div>ENTRY-PYTHON</div>
    </div>
  </div>
</div>
"""

    cover_section = cover_html if include_front_cover else ""
    back_cover_section = back_cover_html if include_back_cover else ""

    full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{meta['title']}</title>
<style>
{BASE_CSS}
{pygments_css}
</style>
</head>
<body>
{cover_section}
{toc_html}
{"".join(chapter_sections)}
{back_cover_section}
</body>
</html>"""

    return fix_img_attributes(full_html)


def fix_img_attributes(html_content):
    """
    Ensure WeasyPrint strictly respects HTML 'width' and 'height' attributes on <img> tags
    by mapping them to inline CSS styles (e.g., style="width: 275px;").
    """
    def replace_img(match):
        tag = match.group(0)
        w_match = re.search(r"""\bwidth=["\']([^"\']+)["\']""", tag)
        h_match = re.search(r"""\bheight=["\']([^"\']+)["\']""", tag)
        style_match = re.search(r"""\bstyle=["\']([^"\']*)["\']""", tag)

        style_val = style_match.group(1).rstrip("; ") if style_match else ""
        new_styles = []
        if style_val:
            new_styles.append(style_val)

        if w_match and "width" not in style_val:
            w = w_match.group(1).strip()
            if w.isdigit() or not any(w.endswith(u) for u in ["px", "%", "em", "rem", "pt"]):
                new_styles.append(f"width: {w}px")
            else:
                new_styles.append(f"width: {w}")

        if h_match and "height" not in style_val:
            h = h_match.group(1).strip()
            if h.isdigit() or not any(h.endswith(u) for u in ["px", "%", "em", "rem", "pt"]):
                new_styles.append(f"height: {h}px")
            else:
                new_styles.append(f"height: {h}")

        if not new_styles:
            return tag

        merged_style = "; ".join(new_styles) + ";"
        if style_match:
            tag = re.sub(r"""\bstyle=["\'][^"\']*["\']""", f'style="{merged_style}"', tag)
        else:
            tag = f'<img style="{merged_style}" ' + tag[5:]

        return tag

    return re.sub(r'<img\b[^>]*>', replace_img, html_content)



def convert_gitbook_to_pdf(summary_path="SUMMARY.md",
                           output_path="pub/pdf/Entry-Python_by_JJ.pdf",
                           title="엔트리로 파이썬 기초 입문하기",
                           subtitle="블록 코딩에서 텍스트 코딩으로의 원활한 전환 가이드",
                           author="JJ (comseong@gmail.com)",
                           include_front_cover=True,
                           include_back_cover=True,
                           html_only=False,
                           keep_html=False):
    """
    Main conversion routine.
    """
    workspace_dir = os.path.abspath(os.path.dirname(summary_path) or ".")
    abs_summary = os.path.abspath(summary_path)
    abs_output = os.path.abspath(output_path)

    os.makedirs(os.path.dirname(abs_output), exist_ok=True)

    meta = {
        "title": title,
        "subtitle": subtitle,
        "author": author
    }

    print("=" * 60)
    print(" GitBook to PDF 1-Shot Converter")
    print("=" * 60)
    print(f"• SUMMARY File : {abs_summary}")
    print(f"• Output PDF   : {abs_output}")
    print(f"• Workspace    : {workspace_dir}")
    print(f"• Front Cover  : {'Included' if include_front_cover else 'Excluded'}")
    print(f"• Back Cover   : {'Included' if include_back_cover else 'Excluded'}")
    print("-" * 60)

    # 1. Parse SUMMARY.md
    print("1. Parsing SUMMARY.md...")
    chapters = parse_summary(abs_summary, workspace_dir)
    print(f"   Found {len(chapters)} chapter entries.")

    # 2. Build Unified HTML
    print("2. Preprocessing GitBook markdown & building HTML...")
    full_html = build_full_html(
        chapters, workspace_dir, meta,
        include_front_cover=include_front_cover,
        include_back_cover=include_back_cover
    )

    html_path = os.path.splitext(abs_output)[0] + ".html"
    if html_only or keep_html:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"   HTML saved to: {html_path}")
        if html_only:
            print("Finished (HTML-only mode).")
            return

    # 3. Render PDF via WeasyPrint
    print("3. Rendering PDF via WeasyPrint engine...")
    start_time = datetime.datetime.now()

    weasy_doc = HTML(string=full_html, base_url=workspace_dir)
    weasy_doc.write_pdf(abs_output)

    duration = (datetime.datetime.now() - start_time).total_seconds()
    print(f"   PDF generated in {duration:.1f}s.")

    # 4. Verify Generated PDF
    if os.path.exists(abs_output):
        reader = PdfReader(abs_output)
        page_count = len(reader.pages)
        file_size_mb = os.path.getsize(abs_output) / (1024 * 1024)
        print("-" * 60)
        print(f"🎉 SUCCESS: PDF generated successfully!")
        print(f"• File Path   : {abs_output}")
        print(f"• Total Pages : {page_count} pages")
        print(f"• File Size   : {file_size_mb:.2f} MB")
        print("=" * 60)
    else:
        print(f"Error: Expected output {abs_output} was not created.", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Convert GitBook project directly to a single PDF book.")
    parser.add_argument("--summary", default="SUMMARY.md", help="Path to SUMMARY.md (default: SUMMARY.md)")
    parser.add_argument("--output", default="pub/pdf/Entry-Python_by_JJ.pdf", help="Output PDF path (default: pub/pdf/Entry-Python_by_JJ.pdf)")
    parser.add_argument("--title", default="엔트리로 파이썬 기초 입문하기", help="Book title")
    parser.add_argument("--subtitle", default="블록 코딩에서 텍스트 코딩으로의 원활한 전환 가이드", help="Book subtitle")
    parser.add_argument("--author", default="JJ (comseong@gmail.com)", help="Author info")
    parser.add_argument("--no-cover", action="store_true", help="Exclude both front and back covers")
    parser.add_argument("--no-front-cover", action="store_true", help="Exclude front cover only")
    parser.add_argument("--no-back-cover", action="store_true", help="Exclude back cover only")
    parser.add_argument("--html-only", action="store_true", help="Generate HTML only without rendering PDF")
    parser.add_argument("--keep-html", action="store_true", help="Keep intermediate HTML alongside PDF")

    args = parser.parse_args()

    include_front_cover = not (args.no_cover or args.no_front_cover)
    include_back_cover = not (args.no_cover or args.no_back_cover)

    convert_gitbook_to_pdf(
        summary_path=args.summary,
        output_path=args.output,
        title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        include_front_cover=include_front_cover,
        include_back_cover=include_back_cover,
        html_only=args.html_only,
        keep_html=args.keep_html
    )


if __name__ == "__main__":
    main()
