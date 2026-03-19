from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / 'config.json'

DEFAULT_CONFIG = {
    'source_root': '/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/2026sci1/学术小龙虾',
    'project_root': '/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/学术小龙虾-web',
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding='utf-8') as f:
            return json.load(f)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    print(f'已生成默认配置文件: {CONFIG_PATH}')
    print(f'如需修改路径，请编辑 config.json 后重新运行。')
    return DEFAULT_CONFIG


def resolve_paths() -> tuple[Path, Path]:
    config = load_config()
    parser = argparse.ArgumentParser(description='从源目录同步内容并生成静态页面')
    parser.add_argument('--source', type=str, default=None, help='源内容目录路径')
    parser.add_argument('--project', type=str, default=None, help='网页项目输出目录路径')
    args = parser.parse_args()
    source = Path(args.source if args.source else config.get('source_root', DEFAULT_CONFIG['source_root']))
    project = Path(args.project if args.project else config.get('project_root', DEFAULT_CONFIG['project_root']))
    if not source.exists():
        print(f'错误: 源目录不存在 → {source}')
        print(f'请检查 config.json 中的 source_root 配置。')
        sys.exit(1)
    if not project.exists():
        print(f'错误: 项目目录不存在 → {project}')
        print(f'请检查 config.json 中的 project_root 配置。')
        sys.exit(1)
    return source, project


SOURCE_ROOT, PROJECT_ROOT = resolve_paths()

MEMBER_META = {
    '悠仁': {'image': 'yujin.jpg', 'accent': '#ff6b35', 'role': '跨领域追踪'},
    '野蔷薇': {'image': 'panda.jpg', 'accent': '#f97316', 'role': '批判性分析'},
    '惠': {'image': 'megumi.jpg', 'accent': '#27ae60', 'role': '写作与方法论'},
    '五条悟': {'image': 'gojo.jpg', 'accent': '#9b59b6', 'role': '前沿评审'},
}

SOURCE_PAGES = {
    'archive': {'file': 'archive.html', 'title': '全部记录', 'accent': '#ff6b35', 'desc': '源目录中的全部 Markdown 记录，按时间倒序自动汇总。'},
    'paper': {'file': 'papers.html', 'title': '论文总结', 'accent': '#ff8c42', 'desc': '源目录中的论文总结，按时间倒序自动汇总。'},
    'upgrade': {'file': 'upgrades.html', 'title': '升级迭代', 'accent': '#27ae60', 'desc': '源目录中的升级迭代记录，按时间倒序自动汇总。'},
    'meeting': {'file': 'meetings.html', 'title': '日会记录', 'accent': '#88ccff', 'desc': '源目录中的日会记录，按时间倒序自动汇总。'},
    'discussion': {'file': 'discussion.html', 'title': '团队讨论', 'accent': '#9b59b6', 'desc': '源目录中的团队讨论记录，按时间倒序自动汇总。'},
}

DOMAIN_META = {
    'AI': {'file': 'AI.html', 'accent': '#ff6b35', 'desc': '基于源目录中论文总结自动汇总的 AI 相关记录。'},
    'NLP': {'file': 'NLP.html', 'accent': '#ff8c42', 'desc': '基于关键词自动归类的语言与文本研究。'},
    'CV': {'file': 'CV.html', 'accent': '#ffa07a', 'desc': '基于关键词自动归类的视觉、图像、视频与 3D 研究。'},
    'ML': {'file': 'ML.html', 'accent': '#ffb366', 'desc': '基于关键词自动归类的训练、优化与模型方法研究。'},
    'HCI': {'file': 'HCI.html', 'accent': '#88ccff', 'desc': '基于关键词自动归类的人机交互与协作研究。'},
    'UX': {'file': 'UX.html', 'accent': '#cc88ff', 'desc': '基于关键词自动归类的体验与设计研究。'},
}

KEYWORDS = {
    'NLP': ['nlp', 'language', 'lingu', 'text', 'token', 'dialog', 'translation', 'cross-lingual', '语言', '文本', '对话', '跨语言', '翻译', '语义', '低资源'],
    'CV': ['vision', 'visual', 'image', 'video', '3d', 'geometry', 'diffusion', 'medical image', '视觉', '图像', '视频', '几何', '扩散', '影像', '超分', '光场'],
    'ML': ['learning', 'training', 'optimization', 'transformer', 'attention', 'routing', 'distill', 'continual', 'unlearning', '训练', '优化', '蒸馏', '持续学习', '遗忘', '路由', '注意力'],
    'HCI': ['hci', 'interaction', 'human-ai', 'user', 'gui', 'computer use', 'collaboration', 'interface', '交互', '用户', '协作', '界面', '人机'],
    'UX': ['ux', 'experience', 'design', 'usability', '体验', '设计', '可用性', '产品'],
}


def parse_folder_timestamp(folder_name: str) -> datetime | None:
    for fmt in ('%Y-%m-%d-%H', '%Y-%m-%d'):
        try:
            return datetime.strptime(folder_name, fmt)
        except ValueError:
            continue
    return None


def parse_content_timestamp(content: str, fallback: datetime) -> datetime:
    lines = [line.strip() for line in content.splitlines()]
    probe_lines = lines[:48] + lines[-24:]

    def normalize(line: str) -> str:
        line = re.sub(r'[*`_]+', '', line)
        return re.sub(r'\s+', ' ', line).strip()

    normalized = [normalize(line) for line in probe_lines if line.strip()]
    date_text = None
    time_text = None

    datetime_patterns = [
        r'(?:生成时间|更新时间|记录时间|整理时间|时间)\s*[:：]\s*(20\d{2}-\d{2}-\d{2})\s+(\d{2}:\d{2})',
        r'(20\d{2}-\d{2}-\d{2})\s+(\d{2}:\d{2})',
    ]
    date_patterns = [
        r'(?:整理日期|记录日期|日期)\s*[:：]\s*(20\d{2}-\d{2}-\d{2})',
    ]
    time_patterns = [
        r'(?:生成时间|更新时间|记录时间|整理时间|时间|会议结束)\s*[:：]\s*(\d{2}:\d{2})',
    ]

    for line in normalized:
        if '下次' in line:
            continue
        for pattern in datetime_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    return datetime.strptime(f'{match.group(1)} {match.group(2)}', '%Y-%m-%d %H:%M')
                except ValueError:
                    continue

    for line in normalized:
        if '下次' in line:
            continue
        if not date_text:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    date_text = match.group(1)
                    break
        if not time_text:
            for pattern in time_patterns:
                match = re.search(pattern, line)
                if match:
                    time_text = match.group(1)
                    break

    if date_text and time_text:
        try:
            return datetime.strptime(f'{date_text} {time_text}', '%Y-%m-%d %H:%M')
        except ValueError:
            pass
    if date_text:
        try:
            return datetime.strptime(f'{date_text} {fallback.strftime("%H:%M")}', '%Y-%m-%d %H:%M')
        except ValueError:
            pass
    return fallback


def detect_kind(file_name: str) -> str:
    if file_name == '论文总结.md':
        return 'paper'
    if file_name == '升级迭代.md':
        return 'upgrade'
    if file_name == '日会记录.md':
        return 'meeting'
    if file_name == '团队讨论.md':
        return 'discussion'
    if file_name.endswith('-能力进化.md'):
        return 'member'
    return 'other'


def extract_heading(content: str) -> str:
    match = re.search(r'^#\s+(.+)$', content, re.M)
    return match.group(1).strip() if match else '未命名记录'


def extract_paper_title(content: str) -> str:
    patterns = [
        r'\*\*论文标题\*\*[：:](.+)',
        r'\*\*标题\*\*[：:](.+)',
        r'\*\*论文\*\*[：:](.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip(' ：:')
    return extract_heading(content)


def first_meaningful_line(content: str) -> str:
    for line in content.splitlines():
        text = line.strip()
        if not text or text.startswith('#'):
            continue
        text = re.sub(r'[*_`>#-]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) >= 2:
            return text
    return ''


def member_name(file_name: str) -> str | None:
    match = re.match(r'(.+)-能力进化\.md$', file_name)
    return match.group(1) if match else None


def build_title(file_name: str, content: str) -> str:
    kind = detect_kind(file_name)
    if kind == 'paper':
        return extract_paper_title(content)
    return extract_heading(content)


def build_excerpt(file_name: str, content: str, folder_name: str) -> str:
    line = first_meaningful_line(content)
    if line:
        return f'来源：{folder_name}/{file_name} · {line}'
    return f'来源：{folder_name}/{file_name}'


def load_records() -> list[dict]:
    records = []
    for path in SOURCE_ROOT.rglob('*.md'):
        if 'html' in path.parts:
            continue
        rel = path.relative_to(SOURCE_ROOT)
        if len(rel.parts) < 2:
            continue
        folder_name = rel.parts[0]
        dt = parse_folder_timestamp(folder_name)
        if not dt:
            continue
        content = path.read_text(encoding='utf-8')
        actual_dt = parse_content_timestamp(content, dt)
        file_name = path.name
        record = {
            'date': actual_dt.strftime('%Y-%m-%d %H:%M'),
            'folder_name': folder_name,
            'file_name': file_name,
            'source_path': str(rel),
            'kind': detect_kind(file_name),
            'member': member_name(file_name),
            'title': build_title(file_name, content),
            'content': content,
            'excerpt': build_excerpt(file_name, content, folder_name),
            'timestamp': actual_dt,
            'source_dir': folder_name,
        }
        records.append(record)

    order = {'paper': 0, 'member': 1, 'upgrade': 2, 'meeting': 3, 'discussion': 4, 'other': 5}
    records.sort(key=lambda item: (item['timestamp'], -order.get(item['kind'], 9), item['file_name']), reverse=True)
    return records


def matches_keywords(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)


def domain_records(domain: str, papers: list[dict]) -> list[dict]:
    if domain == 'AI':
        return papers
    return [item for item in papers if matches_keywords(item['title'] + '\n' + item['content'], KEYWORDS[domain])]


def build_detail_page(title: str, subtitle: str, accent: str, entries: list[dict], cover_image: str | None = None) -> str:
    cover_markup = f'        <img class="sidebar-cover" src="{cover_image}" alt="{title} 封面" loading="lazy">\n' if cover_image else ''
    payload = [
        {
            'date': entry['date'],
            'title': entry['title'],
            'content': entry['content'],
            'excerpt': entry['excerpt'],
            'file_name': entry['file_name'],
            'source_dir': entry['source_dir'],
        }
        for entry in entries
    ]
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{subtitle}">
    <meta property="og:title" content="{title} - 咒术SCI高专">
    <meta property="og:description" content="{subtitle}">
    <meta property="og:image" content="logo.jpg">
    <meta property="og:type" content="website">
    <link rel="icon" href="logo.jpg" type="image/jpeg">
    <link rel="stylesheet" href="site.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>
</head>
<body class="detail-page" style="--accent:{accent};">
    <div class="nav-overlay" id="navOverlay"></div>
    <aside class="detail-sidebar" id="sidebar">
        <div class="sidebar-brand">
            <img class="sidebar-brand-mark" src="logo.jpg" alt="学术小龙虾 logo">
            <div class="brand-copy">
                <strong>学术小龙虾</strong>
                <span>{title}</span>
            </div>
        </div>
        <a class="sidebar-back" href="index.html">← 返回总览</a>
{cover_markup}        <div class="section-kicker">Source Driven</div>
        <h1 class="sidebar-heading">{title}</h1>
        <p class="sidebar-summary">{subtitle}</p>
        <div class="sidebar-metas">
            <span class="meta-chip" id="latestMeta">最新记录</span>
            <span class="meta-chip" id="totalMeta">0 条记录</span>
            <span class="meta-chip" id="currentMeta">当前 1/1</span>
        </div>
        <div class="search-wrap">
            <input id="filterInput" class="search-input" type="search" placeholder="筛选日期、标题或关键词">
            <div class="search-help" id="resultCount">共 0 条</div>
        </div>
        <ul class="detail-nav" id="navList"></ul>
    </aside>

    <main class="detail-main">
        <div class="mobile-bar">
            <div class="mobile-bar-copy">
                <strong>{title}</strong>
                <span>{subtitle}</span>
            </div>
            <div class="mobile-actions">
                <button class="menu-toggle" id="menuToggle" type="button">目录</button>
                <a class="ghost-link" href="index.html">首页</a>
            </div>
        </div>

        <div class="detail-main-inner">
            <div class="article-wrap">
                <div class="article-actions">
                    <button class="ghost-link" id="closeMenu" type="button">收起侧栏</button>
                </div>
                <div class="section-kicker">Reading Panel</div>
                <h1 class="article-title" id="articleTitle">载入中...</h1>
                <p class="article-intro" id="articleIntro">正在整理当前记录内容。</p>
                <div class="article-meta meta-row" id="articleMeta"></div>
                <article class="markdown-body" id="content"></article>
            </div>
        </div>
    </main>

    <script>
        var pageConfig = {json.dumps({'title': title, 'subtitle': subtitle}, ensure_ascii=False)};
        var entries = {json.dumps(payload, ensure_ascii=False, indent=2)};
    </script>
    <script src="site-detail.js"></script>
</body>
</html>
'''


def card_link(item: dict) -> str:
    if item['kind'] == 'paper':
        return 'papers.html'
    if item['kind'] == 'upgrade':
        return 'upgrades.html'
    if item['kind'] == 'meeting':
        return 'meetings.html'
    if item['kind'] == 'discussion':
        return 'discussion.html'
    if item['kind'] == 'member' and item['member']:
        return f"{item['member']}.html"
    return 'archive.html'


def render_entry_cards(items: list[dict]) -> str:
    html = []
    for item in items:
        html.append(f'''                    <article class="entry-card">
                        <div class="entry-date">{item['date']}</div>
                        <a class="entry-link" href="{card_link(item)}">
                            <h3 class="entry-title">{item['title']}</h3>
                            <div class="entry-meta">{item['excerpt']}</div>
                        </a>
                        <div class="entry-arrow">↗</div>
                    </article>''')
    return '\n'.join(html)


def render_topic_cards(items: list[dict]) -> str:
    html = []
    for item in items:
        html.append(f'''                    <a class="topic-card" href="{item['href']}" style="--accent:{item['accent']};">
                        <div class="topic-head">
                            <div>
                                <div class="topic-name">{item['name']}</div>
                                <div class="card-meta">{item['desc']}</div>
                            </div>
                            <div class="topic-count">{item['count']}</div>
                        </div>
                    </a>''')
    return '\n'.join(html)


def render_member_cards(items: list[dict]) -> str:
    html = []
    for item in items:
        html.append(f'''                <a class="member-card" href="{item['href']}">
                    <div class="member-head">
                        <div class="member-profile">
                            <img class="member-avatar" src="{item['image']}" alt="{item['name']}" width="56" height="56" loading="lazy">
                            <div>
                                <div class="member-name">{item['name']}</div>
                                <div class="member-role">{item['role']}</div>
                            </div>
                        </div>
                        <div class="member-count">{item['count']}</div>
                    </div>
                    <div class="member-snippet">{item['desc']}</div>
                </a>''')
    return '\n'.join(html)


def render_line_chart_card(title: str, subtitle: str, labels: list[str], series: list[dict], wide: bool = False) -> str:
    if not labels or not series:
        return ''

    width, height = 640, 220
    pad_left, pad_right, pad_top, pad_bottom = 26, 18, 18, 34
    plot_width = width - pad_left - pad_right
    plot_height = height - pad_top - pad_bottom
    max_value = max((value for item in series for value in item['values']), default=1) or 1

    grid_markup = []
    for step in range(5):
        y = pad_top + plot_height * step / 4
        value = round(max_value * (4 - step) / 4)
        grid_markup.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" stroke="rgba(148, 163, 184, 0.16)" stroke-width="1" />'
        )
        grid_markup.append(
            f'<text x="4" y="{y + 4:.1f}" fill="rgba(148, 163, 184, 0.78)" font-size="11">{value}</text>'
        )

    x_labels = []
    for index, label in enumerate(labels):
        x = pad_left + (plot_width * index / max(1, len(labels) - 1))
        x_labels.append(
            f'<text x="{x:.1f}" y="{height - 8}" text-anchor="middle" fill="rgba(148, 163, 184, 0.82)" font-size="11">{html.escape(label)}</text>'
        )

    line_markup = []
    for item in series:
        color = item['color']
        coords = []
        for index, value in enumerate(item['values']):
            x = pad_left + (plot_width * index / max(1, len(labels) - 1))
            y = pad_top + plot_height - (plot_height * value / max_value)
            coords.append((x, y, value))
        points = ' '.join(f'{x:.1f},{y:.1f}' for x, y, _ in coords)
        line_markup.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="{points}" />'
        )
        for x, y, _ in coords:
            line_markup.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" />'
            )
            line_markup.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="rgba(255,255,255,0.04)" stroke="{color}" stroke-opacity="0.35" stroke-width="1" />'
            )

    legend = ''.join(
        f'<div class="legend-item"><span class="legend-label"><span class="legend-swatch" style="background:{item["color"]};"></span>{html.escape(item["name"])}</span><span class="legend-value">近{len(labels)}期 {sum(item["values"])}</span></div>'
        for item in series
    )
    wide_class = ' wide' if wide else ''
    return f'''<article class="chart-card{wide_class}">
        <h3 class="chart-title">{html.escape(title)}</h3>
        <p class="chart-subtitle">{html.escape(subtitle)}</p>
        <div class="chart-holder">
            <svg class="chart-svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="{html.escape(title)}">
                {''.join(grid_markup)}
                {''.join(line_markup)}
                {''.join(x_labels)}
            </svg>
        </div>
        <div class="chart-legend">{legend}</div>
    </article>'''


def render_bar_chart_card(title: str, subtitle: str, items: list[dict]) -> str:
    if not items:
        return ''

    width, height = 360, 220
    pad_left, pad_right, pad_top, pad_bottom = 16, 16, 16, 42
    plot_width = width - pad_left - pad_right
    plot_height = height - pad_top - pad_bottom
    max_value = max((item['value'] for item in items), default=1) or 1
    slot_width = plot_width / max(1, len(items))
    bar_width = min(42, slot_width * 0.58)

    bars = [f'<line x1="{pad_left}" y1="{height - pad_bottom}" x2="{width - pad_right}" y2="{height - pad_bottom}" stroke="rgba(148, 163, 184, 0.2)" stroke-width="1" />']
    for index, item in enumerate(items):
        x = pad_left + slot_width * index + (slot_width - bar_width) / 2
        bar_height = 0 if item['value'] == 0 else max(10, plot_height * item['value'] / max_value)
        y = height - pad_bottom - bar_height
        label_x = x + bar_width / 2
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="12" fill="{item["color"]}" fill-opacity="0.92" />'
        )
        bars.append(
            f'<text x="{label_x:.1f}" y="{y - 6:.1f}" text-anchor="middle" fill="rgba(248, 250, 252, 0.92)" font-size="12">{item["value"]}</text>'
        )
        bars.append(
            f'<text x="{label_x:.1f}" y="{height - 14}" text-anchor="middle" fill="rgba(148, 163, 184, 0.82)" font-size="11">{html.escape(item["label"])}</text>'
        )

    legend = ''.join(
        f'<div class="legend-item"><span class="legend-label"><span class="legend-swatch" style="background:{item["color"]};"></span>{html.escape(item["label"])}</span><span class="legend-value">{item["value"]}</span></div>'
        for item in items
    )
    return f'''<article class="chart-card">
        <h3 class="chart-title">{html.escape(title)}</h3>
        <p class="chart-subtitle">{html.escape(subtitle)}</p>
        <div class="chart-holder">
            <svg class="chart-svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none" role="img" aria-label="{html.escape(title)}">
                {''.join(bars)}
            </svg>
        </div>
        <div class="chart-legend">{legend}</div>
    </article>'''



def render_rank_chart_card(title: str, subtitle: str, items: list[dict], note: str = "") -> str:
    if not items:
        return ''

    max_value = max((item['value'] for item in items), default=1) or 1
    rows = []
    for index, item in enumerate(items, start=1):
        width = max(18, round(item['value'] / max_value * 100))
        rows.append(
            f'''<div class="topic-rank-item">
            <div class="topic-rank-head">
                <span class="topic-rank-label"><span class="topic-rank-index">{index:02d}</span>{html.escape(item['label'])}</span>
                <span class="topic-rank-value">{item['value']}</span>
            </div>
            <div class="topic-rank-track"><span class="topic-rank-bar" style="--bar-color:{item['color']}; width:{width}%;"></span></div>
        </div>'''
        )

    note_markup = f'<div class="topic-rank-note">{html.escape(note)}</div>' if note else ''
    return f'''<article class="chart-card chart-card--rank">
        <h3 class="chart-title">{html.escape(title)}</h3>
        <p class="chart-subtitle">{html.escape(subtitle)}</p>
        <div class="topic-rank-list">{''.join(rows)}</div>
        {note_markup}
    </article>'''

def build_activity_chart(records: list[dict]) -> str:
    buckets: dict[str, dict[str, int]] = {}
    for item in records:
        if item['kind'] not in {'paper', 'member'}:
            continue
        day_key = item['timestamp'].strftime('%Y-%m-%d')
        bucket = buckets.setdefault(day_key, {'paper': 0, 'member': 0})
        bucket[item['kind']] += 1

    recent_days = sorted(buckets.keys())[-8:]
    labels = [datetime.strptime(day, '%Y-%m-%d').strftime('%m-%d') for day in recent_days]
    series = [
        {'name': '论文总结', 'values': [buckets[day]['paper'] for day in recent_days], 'color': '#ff8c42'},
        {'name': '成员进展', 'values': [buckets[day]['member'] for day in recent_days], 'color': '#9b59b6'},
    ]
    return render_line_chart_card('近期学术节奏', '展示最近 8 个更新日的论文总结与成员进展数量变化。', labels, series, wide=True)


def build_topic_chart(domain_cards: list[dict]) -> str:
    items = [
        {'label': item['name'], 'value': item['count'], 'color': item['accent']}
        for item in sorted(domain_cards, key=lambda card: card['count'], reverse=True)
        if item['count'] > 0
    ][:6]
    leader = items[0] if items else None
    note = f"当前最活跃方向：{leader['label']} · {leader['value']} 条" if leader else ''
    return render_rank_chart_card('研究主题分布', '改成首页更友好的主题排行视图，阅读更轻，判断更快。', items, note)


def build_member_activity_chart(member_cards: list[dict]) -> str:
    items = [
        {'label': item['name'], 'value': item['count'], 'color': item['accent']}
        for item in sorted(member_cards, key=lambda card: card['count'], reverse=True)
        if item['count'] > 0
    ]
    return render_bar_chart_card('成员活跃度', '按成员页自动汇总的记录量，方便在首页看到谁最近更新更密集。', items[:6])


def build_index(records: list[dict], papers: list[dict], source_cards: list[dict], domain_cards: list[dict], member_cards: list[dict]) -> str:
    academic_records = [item for item in records if item['kind'] in {'paper', 'member'}]
    latest = render_entry_cards(academic_records[:8])
    paper_card = next((item for item in source_cards if item['name'] == '论文总结'), None)
    archive_card = next((item for item in source_cards if item['name'] == '全部记录'), None)
    archive_link = archive_card['href'] if archive_card else 'archive.html'
    paper_count = paper_card['count'] if paper_card else len(papers)
    member_count = sum(1 for item in records if item['kind'] == 'member')
    topic_count = len(domain_cards)
    chart_markup = '\n'.join([
        build_activity_chart(records),
        build_topic_chart(domain_cards),
    ])

    focus_cards = [
        {
            'name': '论文总结',
            'href': 'papers.html',
            'count': paper_count,
            'accent': '#ff8c42',
            'desc': '汇总源目录中的论文总结，适合作为首页第一入口。'
        },
        {
            'name': '研究主题',
            'href': 'AI.html',
            'count': len(domain_cards),
            'accent': '#f59e0b',
            'desc': '从论文总结中自动归类出 AI、NLP、CV、ML、HCI、UX 等方向。'
        },
        {
            'name': '成员进展',
            'href': '惠.html',
            'count': member_count,
            'accent': '#9b59b6',
            'desc': '按成员查看能力进化记录，追踪个人研究与写作成长。'
        },
        {
            'name': '全部归档',
            'href': archive_link,
            'count': len(records),
            'accent': '#88ccff',
            'desc': '日会、升级迭代、团队讨论等归档仍然保留，但统一收进总归档页。'
        },
    ]

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>咒术SCI高专</title>
    <meta name="description" content="围绕论文追踪、主题沉淀与成员进化持续更新的学术协作主页。">
    <meta property="og:title" content="咒术SCI高专">
    <meta property="og:description" content="围绕论文追踪、主题沉淀与成员进化持续更新的学术协作主页。">
    <meta property="og:image" content="logo.jpg">
    <meta property="og:type" content="website">
    <link rel="icon" href="logo.jpg" type="image/jpeg">
    <link rel="stylesheet" href="site.css">
</head>
<body class="home-page">
    <div class="home-shell">
        <header class="topbar">
            <div class="brand">
                <img class="brand-mark" src="logo.jpg" alt="学术小龙虾 logo">
                <div class="brand-copy">
                    <strong>咒术SCI高专</strong>
                    <span>宗旨与简介</span>
                </div>
            </div>
            <div class="topbar-links">
                <a class="pill-link" href="#recent">最新更新</a>
                <a class="pill-link" href="#topics">研究主题</a>
                <a class="pill-link" href="#members">成员进展</a>
                <a class="pill-link" href="archive.html">全部归档</a>
            </div>
        </header>

        <section class="hero">
            <div class="hero-panel" style="--accent:#ff6b35;">
                <div class="section-kicker">Academic Front Page</div>
                <div class="hero-copy">
                    <h1>咒术SCI高专</h1>
                    <p>本主页以追踪前沿论文、沉淀研究主题、记录成员能力进化为核心，构建一个持续更新的学术协作场。我们希望把阅读、总结、讨论与写作连接成清晰可浏览的知识流，让每一次学习都能被积累、被连接、被推进。</p>
                </div>
                <div class="hero-actions">
                    <a class="action-link primary" href="papers.html">查看论文总结</a>
                    <a class="action-link secondary" href="archive.html">进入全部归档</a>
                </div>
                <div class="hero-tags">
                    <span class="hero-tag">论文总结 {paper_count}</span>
                    <span class="hero-tag">成员记录 {member_count}</span>
                    <span class="hero-tag">研究主题 {topic_count}</span>
                </div>
            </div>

            <div class="hero-side">
                <div class="hero-panel status-card" style="--accent:#88ccff;">
                    <div class="section-kicker">Snapshot</div>
                    <h2 class="section-title">当前学术概览</h2>
                    <p class="panel-subtitle">数据来自源目录实时扫描，按时间倒序组织。首页优先展示更适合学术浏览的内容层级。</p>
                    <div class="status-grid">
                        <div class="status-item"><div class="status-value">{len(records)}</div><div class="kpi-label">总记录</div></div>
                        <div class="status-item"><div class="status-value">{paper_count}</div><div class="kpi-label">论文总结</div></div>
                        <div class="status-item"><div class="status-value">{member_count}</div><div class="kpi-label">成员记录</div></div>
                        <div class="status-item"><div class="status-value">{records[0]['date'] if records else '-'}</div><div class="kpi-label">最新时间</div></div>
                    </div>
                </div>
            </div>
        </section>

        <section class="section-grid" style="margin-top:22px;">
            <div class="section-panel" style="--accent:#ff8c42;">
                <div class="section-kicker">Quick Access</div>
                <h2 class="section-title">核心学术入口</h2>
                <p class="panel-subtitle">首页保留最常用的学术浏览入口，并补回图表概览，让第一页既清爽也有信息密度。</p>
                <div class="topic-grid">
{render_topic_cards(focus_cards)}
                </div>
                <div class="chart-grid">
{chart_markup}
                </div>
            </div>
            <div class="section-panel" id="recent" style="--accent:#88ccff;">
                <div class="section-kicker">Latest Updates</div>
                <h2 class="section-title">最近更新</h2>
                <p class="panel-subtitle">按时间倒序提取的最新学术记录，优先展示你最近在看什么、写什么、总结了什么。</p>
                <div class="entry-list">
{latest}
                </div>
            </div>
        </section>

        <section class="section-panel" id="topics" style="margin-top:22px; --accent:#f59e0b;">
            <div class="section-kicker">Research Topics</div>
            <h2 class="section-title">按研究主题浏览</h2>
            <p class="panel-subtitle">这些主题页基于源目录中的 <code>论文总结.md</code> 自动归类，同样按时间倒序展示。</p>
            <div class="topic-grid">
{render_topic_cards(domain_cards)}
            </div>
        </section>

        <section class="section-panel" id="members" style="margin-top:22px; --accent:#9b59b6;">
            <div class="section-kicker">Members</div>
            <h2 class="section-title">按成员浏览</h2>
            <p class="panel-subtitle">成员页全部从对应的 <code>XX-能力进化.md</code> 自动拉取，并按时间倒序排列。</p>
            <div class="member-grid">
{render_member_cards(member_cards)}
            </div>
        </section>

        <p class="footer-note">首页已收敛为学术视图。日会、升级迭代、团队讨论等内容仍保留在 <a href="archive.html">全部归档</a> 中。</p>
    </div>
</body>
</html>
'''



def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def main() -> None:
    records = load_records()
    papers = [item for item in records if item['kind'] == 'paper']
    upgrades = [item for item in records if item['kind'] == 'upgrade']
    meetings = [item for item in records if item['kind'] == 'meeting']
    discussions = [item for item in records if item['kind'] == 'discussion']

    source_cards = [
        {'name': SOURCE_PAGES['archive']['title'], 'href': SOURCE_PAGES['archive']['file'], 'count': len(records), 'accent': SOURCE_PAGES['archive']['accent'], 'desc': SOURCE_PAGES['archive']['desc']},
        {'name': SOURCE_PAGES['paper']['title'], 'href': SOURCE_PAGES['paper']['file'], 'count': len(papers), 'accent': SOURCE_PAGES['paper']['accent'], 'desc': SOURCE_PAGES['paper']['desc']},
        {'name': SOURCE_PAGES['upgrade']['title'], 'href': SOURCE_PAGES['upgrade']['file'], 'count': len(upgrades), 'accent': SOURCE_PAGES['upgrade']['accent'], 'desc': SOURCE_PAGES['upgrade']['desc']},
        {'name': SOURCE_PAGES['meeting']['title'], 'href': SOURCE_PAGES['meeting']['file'], 'count': len(meetings), 'accent': SOURCE_PAGES['meeting']['accent'], 'desc': SOURCE_PAGES['meeting']['desc']},
        {'name': SOURCE_PAGES['discussion']['title'], 'href': SOURCE_PAGES['discussion']['file'], 'count': len(discussions), 'accent': SOURCE_PAGES['discussion']['accent'], 'desc': SOURCE_PAGES['discussion']['desc']},
    ]

    domain_cards = []
    for domain, meta in DOMAIN_META.items():
        items = domain_records(domain, papers)
        domain_cards.append({'name': domain, 'href': meta['file'], 'count': len(items), 'accent': meta['accent'], 'desc': meta['desc']})
        write_text(PROJECT_ROOT / meta['file'], build_detail_page(domain, f"{meta['desc']} 共 {len(items)} 条。", meta['accent'], items))

    member_cards = []
    for name, meta in MEMBER_META.items():
        items = [item for item in records if item['member'] == name]
        member_cards.append({'name': name, 'href': f'{name}.html', 'count': len(items), 'image': meta['image'], 'accent': meta['accent'], 'role': meta['role'], 'desc': f'来自源目录的 {len(items)} 条能力进化记录，按时间倒序排列。'})
        write_text(PROJECT_ROOT / f'{name}.html', build_detail_page(name, f'来自源目录的 {len(items)} 条能力进化记录，按时间倒序排列。', meta['accent'], items, cover_image=meta['image']))

    write_text(PROJECT_ROOT / SOURCE_PAGES['archive']['file'], build_detail_page(SOURCE_PAGES['archive']['title'], f"{SOURCE_PAGES['archive']['desc']} 共 {len(records)} 条。", SOURCE_PAGES['archive']['accent'], records))
    write_text(PROJECT_ROOT / SOURCE_PAGES['paper']['file'], build_detail_page(SOURCE_PAGES['paper']['title'], f"{SOURCE_PAGES['paper']['desc']} 共 {len(papers)} 条。", SOURCE_PAGES['paper']['accent'], papers))
    write_text(PROJECT_ROOT / SOURCE_PAGES['upgrade']['file'], build_detail_page(SOURCE_PAGES['upgrade']['title'], f"{SOURCE_PAGES['upgrade']['desc']} 共 {len(upgrades)} 条。", SOURCE_PAGES['upgrade']['accent'], upgrades))
    write_text(PROJECT_ROOT / SOURCE_PAGES['meeting']['file'], build_detail_page(SOURCE_PAGES['meeting']['title'], f"{SOURCE_PAGES['meeting']['desc']} 共 {len(meetings)} 条。", SOURCE_PAGES['meeting']['accent'], meetings))
    write_text(PROJECT_ROOT / SOURCE_PAGES['discussion']['file'], build_detail_page(SOURCE_PAGES['discussion']['title'], f"{SOURCE_PAGES['discussion']['desc']} 共 {len(discussions)} 条。", SOURCE_PAGES['discussion']['accent'], discussions))
    write_text(PROJECT_ROOT / 'index.html', build_index(records, papers, source_cards, domain_cards, member_cards))
    print(f'Generated {len(records)} records from {SOURCE_ROOT}')


if __name__ == '__main__':
    main()
