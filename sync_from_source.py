from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / 'config.json'
LOCAL_CONFIG_PATH = SCRIPT_DIR / 'config.local.json'

DEFAULT_CONFIG = {
    'source_root': '/Users/zijian/Library/Mobile Documents/com~apple~CloudDocs/SCI/2026sci1/学术小龙虾',
    'project_root': '.',
    'obsidian_vault': '',
    'obsidian_folder': '',
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding='utf-8') as f:
            config = json.load(f)
        if LOCAL_CONFIG_PATH.exists():
            with open(LOCAL_CONFIG_PATH, encoding='utf-8') as f:
                config.update(json.load(f))
        return config
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    print(f'已生成默认配置文件: {CONFIG_PATH}')
    print(f'如需修改路径，请编辑 config.json 后重新运行。')
    return DEFAULT_CONFIG


def path_from_config(value: str, *, base: Path = SCRIPT_DIR) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return base / path


def resolve_paths() -> tuple[Path, Path, dict]:
    config = load_config()
    parser = argparse.ArgumentParser(description='从源目录同步内容并生成静态页面')
    parser.add_argument('--source', type=str, default=None, help='源内容目录路径')
    parser.add_argument('--project', type=str, default=None, help='网页项目输出目录路径')
    args = parser.parse_args()
    source = Path(args.source).expanduser() if args.source else path_from_config(config.get('source_root', DEFAULT_CONFIG['source_root']))
    project = Path(args.project).expanduser() if args.project else path_from_config(config.get('project_root', DEFAULT_CONFIG['project_root']))
    if not source.exists():
        print(f'错误: 源目录不存在 → {source}')
        print(f'请检查 config.json 或 config.local.json 中的 source_root 配置。')
        sys.exit(1)
    if not project.exists():
        print(f'错误: 项目目录不存在 → {project}')
        print(f'请检查 config.json 或 config.local.json 中的 project_root 配置。')
        sys.exit(1)
    return source, project, config


SOURCE_ROOT, PROJECT_ROOT, APP_CONFIG = resolve_paths()
IGNORED_SOURCE_PARTS = {'html', 'legacy-html', 'attachments', 'inbox', '__pycache__'}

MEMBER_META = {
    '悠仁': {'image': 'yujin.jpg', 'accent': '#ff6b35', 'role': '跨领域追踪'},
    '野蔷薇': {'image': 'panda.jpg', 'accent': '#f97316', 'role': '批判性分析'},
    '惠': {'image': 'megumi.jpg', 'accent': '#27ae60', 'role': '写作与方法论'},
    '五条悟': {'image': 'gojo.jpg', 'accent': '#9b59b6', 'role': '前沿评审'},
}

SOURCE_PAGES = {
    'archive': {'file': 'archive.html', 'title': '全部记录', 'accent': '#ff6b35', 'desc': '源目录中的全部 Markdown 记录，按时间倒序自动汇总。'},
    'paper': {'file': 'papers.html', 'title': '论文总结', 'accent': '#ff8c42', 'desc': '源目录中的论文总结，按时间倒序自动汇总。'},
    'starred': {'file': 'starred.html', 'title': '高星论文', 'accent': '#ffd166', 'desc': '汇总各角色打星过的论文，按综合星级和角色数排序。'},
    'upgrade': {'file': 'upgrades.html', 'title': '升级迭代', 'accent': '#27ae60', 'desc': '源目录中的升级迭代记录，按时间倒序自动汇总。'},
    'discussion': {'file': 'discussion.html', 'title': '周会讨论', 'accent': '#9b59b6', 'desc': '源目录中的周会讨论记录，按时间倒序自动汇总。'},
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
    # Try YYYY-MM-DD format first (e.g. "2026-04-28")
    match = re.match(r'^(20\d{2}-\d{2}-\d{2})(?:-(\d{2}))?(?:-.+)?$', folder_name)
    if match:
        hour = match.group(2) or '00'
        try:
            return datetime.strptime(f'{match.group(1)} {hour}:00', '%Y-%m-%d %H:%M')
        except ValueError:
            return None
    # Try YYYYMMDD format (e.g. "20260428")
    match2 = re.match(r'^(20\d{2})(\d{2})(\d{2})(?:-(\d{2}))?(?:-.+)?$', folder_name)
    if match2:
        hour = match2.group(4) or '00'
        try:
            return datetime.strptime(f'{match2.group(1)}-{match2.group(2)}-{match2.group(3)} {hour}:00', '%Y-%m-%d %H:%M')
        except ValueError:
            return None
    return None


def record_context(path: Path) -> tuple[str, datetime] | None:
    rel = path.relative_to(SOURCE_ROOT)
    parts = rel.parts
    if any(part in IGNORED_SOURCE_PARTS for part in parts) or not path.name.endswith('.md'):
        return None

    if len(parts) >= 6 and parts[0] == 'records':
        year, month, day, slot = parts[1:5]
        if not re.fullmatch(r'20\d{2}', year) or not re.fullmatch(r'\d{2}', month) or not re.fullmatch(r'\d{2}', day):
            return None
        hour = slot if re.fullmatch(r'\d{2}', slot) else '00'
        try:
            # Supports both legacy records/YYYY/MM/DD/HH/file.md and
            # Hermes records/YYYY/MM/DD/HH/<paper-key>/file.md records.
            return '/'.join(parts[:-1]), datetime.strptime(f'{year}-{month}-{day} {hour}:00', '%Y-%m-%d %H:%M')
        except ValueError:
            return None

    if len(parts) >= 2:
        # Determine which part contains the date: in YYYYMMDD/HH/<key>/ format it's parts[1],
        # in YYYY/MM/DD/HH/ format it's parts[0] (the date folder is parts[1]='YYYY' which doesn't parse)
        candidate = parse_folder_timestamp(parts[1])
        folder_name = parts[1] if candidate else parts[0]
        dt = parse_folder_timestamp(folder_name)
        if dt:
            # Support YYYYMMDD/HH/<key>/file.md format (5 parts)
            # Return full path prefix including slot hour
            if len(parts) >= 4 and re.fullmatch(r'20\d{6}', parts[1]):
                # parts: records, YYYYMMDD, HH, key, file.md
                # Rebuild dt with correct hour from parts[2]
                year = parts[1][:4]
                month = parts[1][4:6]
                day = parts[1][6:8]
                slot = parts[2]
                hour = slot if re.fullmatch(r'\d{2}', slot) else '00'
                dt = datetime.strptime(f'{year}-{month}-{day} {hour}:00', '%Y-%m-%d %H:%M')
                return f"records/{parts[1]}/{parts[2]}/{parts[3]}", dt
            return folder_name, dt

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
    if file_name in {'团队讨论.md', '深度讨论.md', '周会讨论.md'}:
        return 'discussion'
    if file_name.endswith('-能力进化.md'):
        return 'member'
    return 'other'


def classify_session_type(file_name: str, content: str, kind: str) -> tuple[str, str]:
    text = f'{file_name}\n{content}'
    if kind == 'discussion' or any(keyword in text for keyword in ('周会', '每周交流', '团队讨论', '深度讨论')):
        return 'weekly', '周会讨论'
    if kind == 'upgrade' or any(keyword in text for keyword in ('评审', '升级迭代', '评审把控', '最终评审')):
        return 'review', '评审会'
    return '', ''


def extract_heading(content: str) -> str:
    match = re.search(r'^#\s+(.+)$', content, re.M)
    return match.group(1).strip() if match else '未命名记录'


def extract_paper_title(content: str) -> str:
    patterns = [
        r'\*\*论文标题\s*[：:]\*\*(.+)',
        r'\*\*论文标题\*\*[：:](.+)',
        r'\*\*标题\s*[：:]\*\*(.+)',
        r'\*\*标题\*\*[：:](.+)',
        r'\*\*论文\s*[：:]\*\*(.+)',
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


def detail_content(content: str) -> str:
    lines = content.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)

    if lines and re.match(r'^#\s+', lines[0].strip()):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)

    metadata_pattern = re.compile(
        r'^(?:论文标题|标题|论文|作者|会议/期刊|会议|期刊|来源|arxiv(?:\s*id)?|doi|url|日期|领域标签|综合评分)\s*[：:]',
        re.I,
    )
    while lines:
        text = lines[0].strip()
        if not text:
            lines.pop(0)
            continue
        if re.match(r'^#{2,6}\s+', text):
            break
        plain_text = re.sub(r'^[-*]\s*', '', text)
        plain_text = re.sub(r'[`*_]+', '', plain_text).strip()
        if metadata_pattern.match(plain_text):
            lines.pop(0)
            continue
        break

    return '\n'.join(lines).strip() or content


def clean_inline_text(text: str) -> str:
    text = re.sub(r'[`*_>#-]+', ' ', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_arxiv_id(text: str) -> str:
    match = re.search(r'(?i)(?:arxiv(?:\s*id)?\s*[:：]?\s*)?`?((?:19|20|21|22|23|24|25|26)\d{2}\.\d{4,5})`?', text)
    return match.group(1) if match else ''


def clean_external_url(url: str) -> str:
    return url.strip().strip('.,，。；;>)）】]')


def extract_doi(text: str) -> str:
    match = re.search(r'\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b', text, re.I)
    return match.group(1).rstrip('.,，。；;') if match else ''


def extract_original_link(content: str) -> tuple[str, str]:
    url_pattern = re.compile(r'https?://[^\s<>)）】]+', re.I)
    preferred_keywords = ('原文', '论文链接', '论文地址', '来源', 'url', 'doi', 'arxiv', 'paper', 'link')

    for raw_line in content.splitlines():
        line = raw_line.strip()
        urls = url_pattern.findall(line)
        if not urls:
            continue
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in preferred_keywords):
            url = clean_external_url(urls[0])
            if 'doi.org' in url.lower():
                return url, 'DOI'
            if 'arxiv.org' in url.lower():
                return url, 'arXiv'
            return url, '原文'

    doi = extract_doi(content)
    if doi:
        return f'https://doi.org/{doi}', 'DOI'

    arxiv_id = extract_arxiv_id(content)
    if arxiv_id:
        return f'https://arxiv.org/abs/{arxiv_id}', 'arXiv'

    urls = url_pattern.findall(content)
    for raw_url in urls:
        url = clean_external_url(raw_url)
        lower_url = url.lower()
        if 'doi.org' in lower_url:
            return url, 'DOI'
        if 'arxiv.org' in lower_url:
            return url, 'arXiv'
    if urls:
        return clean_external_url(urls[0]), '原文'

    return '', ''


def parse_score_info(text: str) -> dict | None:
    preferred_patterns = [
        r'(?:综合推荐指数|综合评分|综合推荐|综合|悟评|评分|打星|星级)[^\n|]{0,40}?((?:10|[0-9])(?:\.\d+)?)\s*/\s*(5|10)',
        r'→\s*\*{0,2}\s*综合\s*((?:10|[0-9])(?:\.\d+)?)\s*/?\s*(5|10)?',
        r'\|\s*\*{0,2}综合\*{0,2}\s*\|\s*\*{0,2}((?:10|[0-9])(?:\.\d+)?)\s*/\s*(5|10)',
        r'(?:综合推荐指数|综合评分|综合推荐|综合)\s*[:：]?\s*((?:10|[0-9])(?:\.\d+)?)\b',
    ]
    for pattern in preferred_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            raw_score = float(match.group(1))
            scale = int(match.group(2)) if match.lastindex and match.lastindex >= 2 and match.group(2) else (10 if raw_score > 5 else 5)
            if scale == 10:
                return {
                    'score': raw_score / 2,
                    'display': f'{format_star_score(raw_score)}/10',
                    'scale': 10,
                }
            return {
                'score': raw_score,
                'display': f'{format_star_score(raw_score * 2)}/10',
                'scale': 5,
            }

    keyword_lines = [
        line for line in text.splitlines()
        if any(keyword in line for keyword in ('悟评', '综合', '评分', '打星', '星级', '推荐指数'))
    ]
    for line in keyword_lines:
        match = re.search(r'((?:10|[0-9])(?:\.\d+)?)\s*/\s*(5|10)', line)
        if match:
            raw_score = float(match.group(1))
            scale = int(match.group(2))
            return {
                'score': raw_score / 2 if scale == 10 else raw_score,
                'display': f'{format_star_score(raw_score if scale == 10 else raw_score * 2)}/10',
                'scale': scale,
            }
        star_match = re.search(r'([★⭐☆]{3,5})', line)
        if star_match:
            stars = star_match.group(1)
            score = float(stars.count('★') + stars.count('⭐'))
            return {
                'score': score,
                'display': f'{format_star_score(score * 2)}/10',
                'scale': 5,
            }
    return None


def parse_star_score(text: str) -> float | None:
    score_info = parse_score_info(text)
    return score_info['score'] if score_info else None


def format_star_score(score: float) -> str:
    return f'{score:.1f}'.rstrip('0').rstrip('.')


def score_to_stars(score: float) -> str:
    rounded = max(0, min(5, round(score)))
    return '★' * rounded + '☆' * (5 - rounded)


def format_ten_point_score(score: float) -> str:
    return f'{format_star_score(score * 2)}/10'


def normalize_paper_key(title: str, arxiv_id: str = '') -> str:
    if arxiv_id:
        return arxiv_id.lower()
    normalized = clean_inline_text(title).lower()
    normalized = re.sub(r'^[^a-z0-9\u4e00-\u9fff]+', '', normalized)
    normalized = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', normalized)
    return re.sub(r'\s+', ' ', normalized).strip()


def clean_section_heading(title: str) -> str:
    title = clean_inline_text(title)
    title = re.sub(r'^(?:课题|论文)\s*[A-Za-z0-9一二三四五六七八九十]+\s*[：:]\s*', '', title)
    title = title.lstrip('📄📚💡🔬🔥🚨⭐ ')
    return title.strip()


def extract_paper_title_from_text(text: str, fallback: str = '') -> str:
    patterns = [
        r'(?:^|\n)-\s*\*\*论文\*\*\s*[:：]\s*(.+)',
        r'(?:^|\n)\*\*论文标题\*\*\s*[:：]\s*(.+)',
        r'(?:^|\n)\*\*论文\*\*\s*[:：]\s*(.+)',
        r'(?:^|\n)论文\s*[:：]\s*(.+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            candidate = clean_inline_text(match.group(1).split('—')[-1].split('--')[-1])
            if candidate:
                return candidate
    return clean_section_heading(fallback)


def extract_rating_excerpt(text: str) -> str:
    for raw_line in text.splitlines():
        line = clean_inline_text(raw_line)
        if not line:
            continue
        if any(keyword in line for keyword in ('论文', '来源', '评分', '综合', '时间', '状态', '训练类型', '身份', 'ArXiv', 'arXiv')):
            continue
        if len(line) >= 12:
            return line[:140]
    return ''


def split_level3_sections(content: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r'^###\s+(.+)$', content, re.M))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        heading = match.group(1).strip()
        block = content[match.start():end].strip()
        sections.append((heading, block))
    return sections


def extract_star_candidates_from_member(record: dict) -> list[dict]:
    candidates: list[dict] = []
    member = record.get('member') or '成员'
    content = record['content']
    sections = split_level3_sections(content)

    for heading, block in sections:
        score = parse_star_score(block)
        if score is None:
            continue
        title = extract_paper_title_from_text(block, heading)
        heading_clean = clean_section_heading(heading)
        has_paper_marker = any(token in block for token in ('**论文', '- **来源**', 'arXiv', 'ArXiv'))
        if not title or title in {'论文信息', '自评结果', '筛选理由', '核心收获', '反思与改进', '下一步研究方向'}:
            continue
        if not has_paper_marker and heading_clean == title and not re.match(r'^(?:课题|论文|📄)', heading):
            continue
        candidates.append({
            'title': title,
            'arxiv_id': extract_arxiv_id(block),
            'score': score,
            'role': member,
            'date': record['date'],
            'timestamp': record['timestamp'],
            'excerpt': extract_rating_excerpt(block),
            'source_dir': record['source_dir'],
            'source_file': record['file_name'],
            'source_page': f'{member}.html',
        })

    if not candidates:
        score = parse_star_score(content)
        title = extract_paper_title_from_text(content)
        if score is not None and title:
            candidates.append({
                'title': title,
                'arxiv_id': extract_arxiv_id(content),
                'score': score,
                'role': member,
                'date': record['date'],
                'timestamp': record['timestamp'],
                'excerpt': extract_rating_excerpt(content),
                'source_dir': record['source_dir'],
                'source_file': record['file_name'],
                'source_page': f'{member}.html',
            })

    deduped: list[dict] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for item in candidates:
        key = (
            item['role'],
            normalize_paper_key(item['title'], item['arxiv_id']),
            item['date'],
            item['source_file'],
            format_star_score(item['score']),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def build_starred_markdown(title: str, arxiv_id: str, ratings: list[dict], average_score: float) -> str:
    overview = [
        f'# {title}',
        '',
        '## 星级概览',
        f'- 综合星级：**{format_star_score(average_score)}/5 {score_to_stars(average_score)}**',
        f'- 打星角色：**{len(ratings)} 位**',
        f'- 最近更新时间：**{ratings[0]["date"]}**',
    ]
    if arxiv_id:
        overview.append(f'- arXiv：`{arxiv_id}`')

    table = [
        '',
        '## 角色打星',
        '| 角色 | 星级 | 时间 | 来源 |',
        '| --- | --- | --- | --- |',
    ]
    for rating in ratings:
        table.append(
            f'| {rating["role"]} | {format_star_score(rating["score"])}/5 {score_to_stars(rating["score"])} | {rating["date"]} | [{rating["source_dir"]}/{rating["source_file"]}]({rating["source_page"]}) |'
        )

    quotes = ['', '## 角色摘录']
    for rating in ratings:
        quotes.append(f'### {rating["role"]} · {format_star_score(rating["score"])}/5')
        if rating['excerpt']:
            quotes.append(f'> {rating["excerpt"]}')
        quotes.append(f'- 来源记录：[{rating["source_dir"]}/{rating["source_file"]}]({rating["source_page"]})')
        quotes.append('')

    return '\n'.join(overview + table + quotes).strip()


def build_starred_entries(records: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    for record in records:
        if record['kind'] == 'member' and record.get('member'):
            candidates.extend(extract_star_candidates_from_member(record))

    grouped: dict[str, dict] = {}
    for item in candidates:
        key = normalize_paper_key(item['title'], item['arxiv_id'])
        if not key:
            continue
        bucket = grouped.setdefault(key, {
            'title': item['title'],
            'arxiv_id': item['arxiv_id'],
            'ratings': [],
        })
        if item['arxiv_id'] and not bucket['arxiv_id']:
            bucket['arxiv_id'] = item['arxiv_id']
        if len(item['title']) > len(bucket['title']):
            bucket['title'] = item['title']
        bucket['ratings'].append(item)

    entries: list[dict] = []
    for bucket in grouped.values():
        ratings = sorted(bucket['ratings'], key=lambda item: (item['score'], item['timestamp']), reverse=True)
        average_score = round(sum(item['score'] for item in ratings) / len(ratings), 1)
        latest = max(ratings, key=lambda item: item['timestamp'])
        rating_summary = ' / '.join(
            f'{item["role"]} {format_star_score(item["score"])}'
            for item in sorted(ratings, key=lambda entry: (entry['score'], entry['timestamp']), reverse=True)[:4]
        )
        content = build_starred_markdown(bucket['title'], bucket['arxiv_id'], ratings, average_score)
        entries.append({
            'date': latest['date'],
            'folder_name': latest['source_dir'],
            'file_name': '角色打星汇总',
            'source_path': latest['source_file'],
            'kind': 'other',
            'member': None,
            'title': bucket['title'],
            'content': content,
            'excerpt': f'综合 {format_star_score(average_score)}/5 · {len(ratings)} 位角色打星 · {rating_summary}',
            'timestamp': latest['timestamp'],
            'source_dir': latest['source_dir'],
            'session_type': '',
            'session_label': f'{format_star_score(average_score)}★ · {len(ratings)}人',
        })

    entries.sort(key=lambda item: (float(re.search(r'([0-5](?:\.\d+)?)', item['session_label']).group(1)), item['timestamp']), reverse=True)
    return entries


def load_records() -> list[dict]:
    records = []
    for path in SOURCE_ROOT.rglob('*.md'):
        rel = path.relative_to(SOURCE_ROOT)
        context = record_context(path)
        if not context:
            continue
        source_dir, dt = context
        content = path.read_text(encoding='utf-8')
        actual_dt = parse_content_timestamp(content, dt)
        file_name = path.name
        kind = detect_kind(file_name)
        original_url, original_label = extract_original_link(content)
        session_type, session_label = classify_session_type(file_name, content, kind)
        record = {
            'date': actual_dt.strftime('%Y-%m-%d %H:%M'),
            'folder_name': source_dir,
            'file_name': file_name,
            'source_path': str(rel),
            'kind': kind,
            'member': member_name(file_name),
            'title': build_title(file_name, content),
            'content': content,
            'excerpt': build_excerpt(file_name, content, source_dir),
            'original_url': original_url,
            'original_label': original_label,
            'timestamp': actual_dt,
            'source_dir': source_dir,
            'session_type': session_type,
            'session_label': session_label,
        }
        records.append(record)

    order = {'paper': 0, 'member': 1, 'upgrade': 2, 'discussion': 3, 'other': 4}
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
    obsidian_config = {
        'vault': APP_CONFIG.get('obsidian_vault', ''),
        'folder': APP_CONFIG.get('obsidian_folder', ''),
    }
    payload = [
        {
            'date': entry['date'],
            'title': entry['title'],
            'content': detail_content(entry['content']),
            'excerpt': entry['excerpt'],
            'file_name': entry['file_name'],
            'source_dir': entry['source_dir'],
            'original_url': entry.get('original_url', ''),
            'original_label': entry.get('original_label', ''),
            'session_type': entry.get('session_type', ''),
            'session_label': entry.get('session_label', ''),
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
    <link rel="stylesheet" href="site.css?v=20260427-quiet-detail1">
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
            <div class="filter-tabs" id="filterTabs" aria-label="记录类型筛选"></div>
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
            <div class="reader-tools" id="readerTools" hidden>
                <div class="reader-tools-head">
                    <span class="section-kicker">段落导航</span>
                    <span class="reader-tools-count" id="readerToolsCount"></span>
                </div>
                <nav class="reader-toc" id="readerToc" aria-label="正文快速定位"></nav>
            </div>
            <div class="article-wrap">
                <h1 class="article-title" id="articleTitle">载入中...</h1>
                <div class="article-tool-row">
                    <a class="article-tool-link" id="originalLink" href="#" target="_blank" rel="noopener noreferrer" hidden>原文链接</a>
                    <button class="article-tool-link" id="obsidianButton" type="button">复制到 Obsidian</button>
                    <span class="obsidian-status" id="obsidianStatus" aria-live="polite"></span>
                </div>
                <article class="markdown-body" id="content"></article>
            </div>
        </div>
    </main>

    <script>
        var pageConfig = {json.dumps({'title': title, 'subtitle': subtitle, 'obsidian': obsidian_config}, ensure_ascii=False)};
        var entries = {json.dumps(payload, ensure_ascii=False, indent=2)};
    </script>
    <script src="site-detail.js?v=20260427-quiet-detail1"></script>
</body>
</html>
'''


def card_link(item: dict) -> str:
    if item['kind'] == 'paper':
        return 'papers.html'
    if item['kind'] == 'upgrade':
        return 'upgrades.html'
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


def paper_package_key(record: dict) -> str:
    return record['source_dir'] if record['kind'] == 'paper' else ''


def member_package_key(record: dict) -> str:
    if record['kind'] != 'member':
        return ''
    parts = record['source_dir'].split('/')
    if len(parts) >= 6 and parts[0] == 'records':
        return record['source_dir']
    return ''


def build_research_packages(records: list[dict]) -> list[dict]:
    buckets: dict[str, dict] = {}

    for record in records:
        if record['kind'] == 'paper':
            key = paper_package_key(record)
            if not key:
                continue
            bucket = buckets.setdefault(key, {'paper': None, 'members': []})
            bucket['paper'] = record

    for record in records:
        key = member_package_key(record)
        if not key or key not in buckets:
            continue
        buckets[key]['members'].append(record)

    packages = []
    for key, bucket in buckets.items():
        paper = bucket['paper']
        if not paper:
            continue
        members = sorted(bucket['members'], key=lambda item: (item.get('member') or '', item['timestamp']))
        packages.append({
            'key': key,
            'paper': paper,
            'members': members,
            'date': paper['date'],
            'timestamp': paper['timestamp'],
            'title': paper['title'],
        })

    packages.sort(key=lambda item: item['timestamp'], reverse=True)
    return packages


def extract_package_keys_from_summary_heading(key_text: str) -> set[str]:
    keys = set()
    for token in re.findall(r'[A-Za-z0-9][A-Za-z0-9_.-]*', key_text):
        token = token.strip('._-').lower()
        if '-' in token or re.match(r'\d{4}\.\d+', token):
            keys.add(token)
    return keys


def extract_gojo_summary_ratings(records: list[dict]) -> dict[str, dict]:
    ratings: dict[str, dict] = {}
    heading_pattern = re.compile(r'^###\s+.+?[（(]([^）)]+)[）)]\s*$', re.M)

    for record in records:
        marker = f"{record['file_name']}\n{record['title']}\n{record['content']}"
        if '五条悟' not in marker or '汇总' not in marker:
            continue

        matches = list(heading_pattern.finditer(record['content']))
        for index, match in enumerate(matches):
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(record['content'])
            section = record['content'][match.end():section_end]
            score_info = parse_score_info(section)
            if not score_info:
                continue
            item = {
                'score': score_info['score'],
                'display_score': score_info['display'],
                'source_label': '五条老师评定',
                'date': record['date'],
                'timestamp': record['timestamp'],
            }
            for key in extract_package_keys_from_summary_heading(match.group(1)):
                current = ratings.get(key)
                if not current or item['timestamp'] >= current['timestamp']:
                    ratings[key] = item

    return ratings


def render_research_package_cards(packages: list[dict]) -> str:
    if not packages:
        return '<div class="empty-state">还没有可展示的论文研究包。</div>'

    cards = []
    for package in packages:
        paper = package['paper']
        members = package['members']
        member_names = [item['member'] for item in members if item.get('member')]
        member_label = '、'.join(member_names[:4]) if member_names else '暂无角色短评'
        if len(member_names) > 4:
            member_label += f' 等 {len(member_names)} 位'
        member_count = len(members)
        member_count_label = f'角色短评 {member_count}' if member_count else '等待短评'
        tags = []
        for domain in DOMAIN_META:
            if domain_records(domain, [paper]):
                tags.append(domain)
        tags_markup = ''.join(f'<span class="research-chip">{html.escape(tag)}</span>' for tag in tags[:4])
        cards.append(f'''                    <article class="research-package-card">
                        <div class="research-package-date">{html.escape(package['date'])}</div>
                        <a class="research-package-title" href="papers.html?search={quote(paper['title'])}">{html.escape(paper['title'])}</a>
                        <div class="research-package-meta">来源：{html.escape(package['key'])} · {member_count_label}</div>
                        <div class="research-package-roles">{html.escape(member_label)}</div>
                        <div class="research-chip-row">
                            {tags_markup}
                            <a class="research-chip link-chip" href="archive.html?search={quote(package['key'])}">查看研究包</a>
                        </div>
                    </article>''')
    return '\n'.join(cards)


def gojo_rating_for_package(package: dict) -> dict | None:
    ratings = []
    for member in package['members']:
        if member.get('member') != '五条悟':
            continue
        score_info = parse_score_info(member['content'])
        if not score_info:
            continue
        ratings.append({
            'score': score_info['score'],
            'display_score': score_info['display'],
            'source_label': '五条老师评定',
            'date': member['date'],
            'timestamp': member['timestamp'],
        })
    if not ratings:
        return None
    return max(ratings, key=lambda item: (item['score'], item['timestamp']))


def package_rating_keys(package: dict) -> list[str]:
    key = package['key'].lower()
    return [
        key,
        key.rstrip('/').split('/')[-1],
        normalize_paper_key(package['title']),
    ]


def ranking_rating_for_package(package: dict, gojo_summary_ratings: dict[str, dict] | None = None) -> dict | None:
    gojo_rating = gojo_rating_for_package(package)
    if gojo_rating:
        return gojo_rating

    if gojo_summary_ratings:
        for key in package_rating_keys(package):
            rating = gojo_summary_ratings.get(key)
            if rating:
                return rating

    paper_score = parse_score_info(package['paper']['content'])
    if paper_score:
        return {
            'score': paper_score['score'],
            'display_score': paper_score['display'],
            'source_label': '综合评分',
            'date': package['paper']['date'],
            'timestamp': package['paper']['timestamp'],
        }

    role_scores = []
    for member in package['members']:
        score_info = parse_score_info(member['content'])
        if not score_info:
            continue
        role_scores.append({
            'score': score_info['score'],
            'display_score': score_info['display'],
            'source_label': f'{member.get("member") or "角色"}评分',
            'date': member['date'],
            'timestamp': member['timestamp'],
        })
    if not role_scores:
        return None
    return max(role_scores, key=lambda item: (item['score'], item['timestamp']))


def build_gojo_recent_rankings(packages: list[dict], *, days: int = 3, gojo_summary_ratings: dict[str, dict] | None = None) -> list[dict]:
    if not packages:
        return []

    latest = max(package['timestamp'] for package in packages)
    cutoff = latest - timedelta(days=days)
    ranked = []

    for package in packages:
        if package['timestamp'] < cutoff:
            continue
        rating = ranking_rating_for_package(package, gojo_summary_ratings)
        ranked.append({
            **package,
            'gojo_rating': rating,
            'gojo_score': rating['score'] if rating else None,
        })

    ranked.sort(
        key=lambda item: (
            item['gojo_score'] is not None,
            item['gojo_score'] or 0,
            item['timestamp'],
        ),
        reverse=True,
    )
    return ranked


def package_domain_tags(paper: dict) -> list[str]:
    tags = []
    for domain in DOMAIN_META:
        if domain_records(domain, [paper]):
            tags.append(domain)
    return tags


def ranking_reason(package: dict, tags: list[str], rating: dict | None) -> str:
    if rating:
        tag_text = ' / '.join(tags[:2]) if tags else '前沿'
        return f'五条老师给到 {format_ten_point_score(rating["score"])}，适合作为 {tag_text} 方向的灵感线索。'
    if tags:
        return f'已进入近 3 天资讯池，可先按 {" / ".join(tags[:2])} 方向暂存观察。'
    return '已进入近 3 天资讯池，等待五条老师补充前沿判断。'


def ranking_next_action(rating: dict | None) -> str:
    if not rating:
        return '下一步：等待五条老师评定'
    if rating['score'] >= 4.5:
        return '下一步：优先精读，提炼可迁移研究问题'
    if rating['score'] >= 4:
        return '下一步：加入候选池，观察是否能连接现有课题'
    return '下一步：暂存归档，保留为背景材料'


def render_gojo_ranking_cards(packages: list[dict]) -> str:
    if not packages:
        return '<div class="empty-state">近 3 天还没有可展示的论文研究包。</div>'

    cards = []
    for index, package in enumerate(packages, start=1):
        paper = package['paper']
        rating = package.get('gojo_rating')
        score_label = f"{rating.get('source_label', '综合评分')} {rating.get('display_score', format_ten_point_score(rating['score']))}" if rating else '待五条老师评定'
        score_stars = score_to_stars(rating['score']) if rating else '未评分'
        tags = package_domain_tags(paper)
        next_action = ranking_next_action(rating)
        tags_markup = ''.join(f'<span class="research-chip">{html.escape(tag)}</span>' for tag in tags[:3])
        cards.append(f'''                    <article class="research-package-card ranking-card">
                        <div class="ranking-head">
                            <div class="ranking-position">#{index}</div>
                            <div>
                                <div class="research-package-date">{html.escape(package['date'])}</div>
                                <div class="ranking-score">{html.escape(score_label)} · {html.escape(score_stars)}</div>
                            </div>
                        </div>
                        <a class="research-package-title" href="papers.html?search={quote(paper['title'])}">{html.escape(paper['title'])}</a>
                        <div class="ranking-action">{html.escape(next_action)}</div>
                        <div class="research-chip-row">
                            {tags_markup}
                            <a class="research-chip link-chip" href="papers.html?search={quote(paper['title'])}">阅读</a>
                        </div>
                    </article>''')
    return '\n'.join(cards)


def render_topic_cards(items: list[dict]) -> str:
    html = []
    for item in items:
        html.append(f'''                    <a class="topic-card focus-link" href="{item['href']}" style="--accent:{item['accent']};">
                        <div class="topic-head">
                            <div>
                                <div class="topic-name">{item['name']}</div>
                                <div class="card-meta">{item['desc']}</div>
                            </div>
                            <div class="topic-count">{item['count']}</div>
                        </div>
                    </a>''')
    return '\n'.join(html)


def render_compact_topic_cards(items: list[dict]) -> str:
    cards = []
    for item in items:
        cards.append(f'''                        <a class="direction-card" href="{item['href']}" style="--accent:{item['accent']};">
                            <div>
                                <div class="direction-name">{html.escape(item['name'])}</div>
                                <div class="direction-desc">{html.escape(item['desc'])}</div>
                            </div>
                            <div class="direction-count">{item['count']}</div>
                        </a>''')
    return '\n'.join(cards)


def build_domain_track_cards(domain_cards: list[dict]) -> list[dict]:
    lookup = {item['name']: item for item in domain_cards}
    hci_count = lookup.get('HCI', {}).get('count', 0)
    ux_count = lookup.get('UX', {}).get('count', 0)
    tracks: list[dict] = []

    for name in ('AI', 'NLP', 'CV', 'ML'):
        item = lookup.get(name)
        if item:
            tracks.append(item)

    if hci_count or ux_count:
        tracks.append({
            'name': 'UX / HCI',
            'href': 'papers.html?search=UX%20/%20HCI',
            'count': max(hci_count, ux_count),
            'accent': '#88ccff',
            'desc': '合并人机交互、用户体验、界面理解和设计方法相关材料。',
        })

    return sorted(tracks, key=lambda item: item['count'], reverse=True)


def build_trend_filter_cards(papers: list[dict], *, days: int = 14) -> list[dict]:
    if not papers:
        return []

    latest = max(paper['timestamp'] for paper in papers)
    recent_cutoff = latest - timedelta(days=days)
    previous_cutoff = latest - timedelta(days=days * 2)
    recent_papers = [paper for paper in papers if paper['timestamp'] >= recent_cutoff]
    previous_papers = [paper for paper in papers if previous_cutoff <= paper['timestamp'] < recent_cutoff]

    candidates: list[dict] = []
    for name, meta in PROBLEM_LENSES.items():
        recent_count = sum(1 for paper in recent_papers if matches_keywords(f"{paper['title']}\n{paper['content']}", meta['keywords']))
        previous_count = sum(1 for paper in previous_papers if matches_keywords(f"{paper['title']}\n{paper['content']}", meta['keywords']))
        if not recent_count:
            continue
        delta = recent_count - previous_count
        candidates.append({
            'name': name,
            'href': f'papers.html?search={quote(name)}',
            'count': recent_count,
            'delta': delta,
            'accent': meta['accent'],
            'desc': meta['desc'],
            'kind': '问题',
            'score': recent_count * 2 + max(delta, 0),
        })

    for item in build_domain_track_cards([
        {
            'name': name,
            'href': meta['file'],
            'count': len(domain_records(name, recent_papers)),
            'accent': meta['accent'],
            'desc': meta['desc'],
        }
        for name, meta in DOMAIN_META.items()
    ]):
        previous_count = 0
        if item['name'] == 'UX / HCI':
            previous_count = max(len(domain_records('HCI', previous_papers)), len(domain_records('UX', previous_papers)))
        else:
            previous_count = len(domain_records(item['name'], previous_papers))
        if not item['count']:
            continue
        delta = item['count'] - previous_count
        candidates.append({
            **item,
            'delta': delta,
            'kind': '方向',
            'score': item['count'] * 2 + max(delta, 0),
        })

    deduped: dict[str, dict] = {}
    for item in candidates:
        current = deduped.get(item['name'])
        if not current or (item['score'], item['count'], item['delta']) > (current['score'], current['count'], current['delta']):
            deduped[item['name']] = item

    merged = list(deduped.values())
    merged.sort(key=lambda item: (item['score'], item['count'], item['delta']), reverse=True)
    return merged[:8]


def render_trend_filter_cards(items: list[dict]) -> str:
    if not items:
        return '<div class="empty-state">暂无可展示的热点趋势。</div>'

    cards = []
    for item in items:
        if item['delta'] > 0:
            delta_label = f"+{item['delta']}"
        elif item['delta'] < 0:
            delta_label = str(item['delta'])
        else:
            delta_label = '持平'
        cards.append(f'''                    <a class="trend-chip" href="{item['href']}" style="--accent:{item['accent']};">
                        <span class="trend-kind">{html.escape(item['kind'])}</span>
                        <strong>{html.escape(item['name'])}</strong>
                        <span>近 14 天 {item['count']} · {html.escape(delta_label)}</span>
                    </a>''')
    return '\n'.join(cards)


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


def render_home_filter_tags(items: list[dict]) -> str:
    markup = []
    for item in items:
        markup.append(f'''                    <a class="quick-filter-chip" href="{item['href']}" style="--accent:{item['accent']};">
                        <span class="quick-filter-label">{html.escape(item['label'])}</span>
                        <strong>{item['count']}</strong>
                    </a>''')
    return '\n'.join(markup)


PROBLEM_LENSES = {
    'Agent': {
        'keywords': ['agent', 'agentic', 'multi-agent', 'tool use', 'workflow', '智能体', '代理', '工具调用'],
        'accent': '#f97316',
        'desc': '自主规划、工具调用、多 Agent 协作与执行链路。'
    },
    'UX / HCI': {
        'keywords': ['hci', 'ux', 'interaction', 'user', 'interface', 'usability', 'experience', '交互', '用户', '体验', '界面'],
        'accent': '#88ccff',
        'desc': '用户体验、人机协作、界面理解与设计方法。'
    },
    'Evaluation': {
        'keywords': ['benchmark', 'evaluation', 'dataset', 'metric', '评估', '基准', '数据集', '指标'],
        'accent': '#ffd166',
        'desc': '基准、指标、可复现性和评测方法。'
    },
    'Fairness': {
        'keywords': ['fairness', 'bias', 'accountability', 'ethic', 'trust', '公平', '偏见', '问责', '伦理', '信任'],
        'accent': '#27ae60',
        'desc': '公平性、信任、问责与敏感场景边界。'
    },
    'Multimodal': {
        'keywords': ['multimodal', 'vision-language', 'visual', 'image', 'video', '多模态', '视觉', '图像'],
        'accent': '#cc88ff',
        'desc': '多模态理解、视觉语言模型与跨模态推理。'
    },
}


def build_problem_lens_cards(papers: list[dict]) -> list[dict]:
    cards = []
    for name, meta in PROBLEM_LENSES.items():
        matches = [paper for paper in papers if matches_keywords(f"{paper['title']}\n{paper['content']}", meta['keywords'])]
        if not matches:
            continue
        cards.append({
            'name': name,
            'href': f'papers.html?search={quote(name)}',
            'count': len(matches),
            'accent': meta['accent'],
            'desc': meta['desc'],
        })
    cards.sort(key=lambda item: item['count'], reverse=True)
    return cards


def home_search_label(item: dict) -> str:
    if item['kind'] == 'paper':
        return '论文总结'
    if item['kind'] == 'member':
        return f"{item['member']} · 成员进展" if item.get('member') else '成员进展'
    if item['kind'] == 'upgrade':
        return item.get('session_label') or '评审会'
    if item['kind'] == 'discussion':
        return item.get('session_label') or '周会讨论'
    return '全部归档'


def home_search_href(item: dict, query: str | None = None) -> str:
    base = card_link(item)
    if not query:
        return base
    connector = '&' if '?' in base else '?'
    return f'{base}{connector}search={quote(query)}'


def build_home_search_payload(records: list[dict], starred_entries: list[dict]) -> list[dict]:
    payload = []
    seen: set[tuple[str, str, str]] = set()

    for item in starred_entries:
        title = item['title'].strip()
        key = ('starred', title.lower(), item['date'])
        if key in seen:
            continue
        seen.add(key)
        payload.append({
            'title': title,
            'date': item['date'],
            'excerpt': item['excerpt'],
            'label': '高星论文',
            'href': home_search_href({'kind': 'other'}, title),
            'keywords': f"{title} {item['excerpt']} {clean_inline_text(item['content'])[:3200]} 高星论文 打星 综合星级 角色评分",
        })

    for item in records:
        title = item['title'].strip()
        key = (item['kind'], title.lower(), item['date'])
        if key in seen:
            continue
        seen.add(key)
        payload.append({
            'title': title,
            'date': item['date'],
            'excerpt': item['excerpt'],
            'label': home_search_label(item),
            'href': home_search_href(item, title),
            'keywords': f"{title} {item['excerpt']} {clean_inline_text(item['content'])[:3200]} {item['file_name']} {item['source_dir']} {item.get('member') or ''} {item.get('session_label') or ''}",
        })

    payload.sort(key=lambda item: item['date'], reverse=True)
    return payload


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

    subtitle_markup = f'\n        <p class="chart-subtitle">{html.escape(subtitle)}</p>' if subtitle else ''
    note_markup = f'<div class="topic-rank-note">{html.escape(note)}</div>' if note else ''
    return f'''<article class="chart-card chart-card--rank">
        <h3 class="chart-title">{html.escape(title)}</h3>{subtitle_markup}
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
    return render_rank_chart_card('研究主题分布', '', items, note)


def build_member_activity_chart(member_cards: list[dict]) -> str:
    items = [
        {'label': item['name'], 'value': item['count'], 'color': item['accent']}
        for item in sorted(member_cards, key=lambda card: card['count'], reverse=True)
        if item['count'] > 0
    ]
    return render_bar_chart_card('成员活跃度', '按成员页自动汇总的记录量，方便在首页看到谁最近更新更密集。', items[:6])


def build_index(records: list[dict], papers: list[dict], source_cards: list[dict], domain_cards: list[dict], member_cards: list[dict], starred_entries: list[dict]) -> str:
    research_packages = build_research_packages(records)
    gojo_summary_ratings = extract_gojo_summary_ratings(records)
    gojo_rankings = build_gojo_recent_rankings(research_packages, days=3, gojo_summary_ratings=gojo_summary_ratings)
    gojo_ranking_markup = render_gojo_ranking_cards(gojo_rankings[:5])
    problem_lenses = build_problem_lens_cards(papers)
    problem_lens_markup = render_compact_topic_cards(problem_lenses[:6])
    domain_tracks = build_domain_track_cards(domain_cards)
    domain_topic_markup = render_compact_topic_cards(domain_tracks)
    trend_filter_markup = render_trend_filter_cards(build_trend_filter_cards(papers, days=14))
    paper_card = next((item for item in source_cards if item['name'] == '论文总结'), None)
    archive_card = next((item for item in source_cards if item['name'] == '全部记录'), None)
    archive_link = archive_card['href'] if archive_card else 'archive.html'
    paper_count = paper_card['count'] if paper_card else len(papers)
    member_count = sum(1 for item in records if item['kind'] == 'member')
    topic_count = len(domain_cards)
    package_count = len(research_packages)
    activity_chart_markup = build_activity_chart(records)
    topic_chart_markup = build_topic_chart(domain_cards)
    quick_filters = [
        {
            'label': '周会讨论',
            'href': 'archive.html?filter=weekly',
            'count': sum(1 for item in records if item.get('session_type') == 'weekly'),
            'accent': '#9b59b6',
        },
        {
            'label': '每日评审',
            'href': 'archive.html?filter=review',
            'count': sum(1 for item in records if item.get('session_type') == 'review'),
            'accent': '#27ae60',
        },
    ]
    search_payload = build_home_search_payload(records, starred_entries)

    focus_cards = [
        {
            'name': '论文资讯',
            'href': 'papers.html',
            'count': paper_count,
            'accent': '#ff8c42',
            'desc': '先快速扫最近收集了什么。'
        },
        {
            'name': '精选论文',
            'href': '#recent',
            'count': len(starred_entries),
            'accent': '#88ccff',
            'desc': '看五条榜单和高星库，决定先读哪篇。'
        },
        {
            'name': '研究方向雷达',
            'href': '#directions',
            'count': len(domain_tracks),
            'accent': '#f59e0b',
            'desc': '把主题、问题和热点合在一起找方向。'
        },
        {
            'name': '成员判断',
            'href': '#members',
            'count': member_count,
            'accent': '#9b59b6',
            'desc': '只在需要追溯判断来源时进入。'
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
            <form class="topbar-search" id="homeSearchForm" role="search">
                <div class="topbar-search-shell">
                    <input id="homeSearchInput" class="topbar-search-input" type="search" placeholder="搜索论文、成员、主题或讨论关键词" aria-label="首页搜索">
                    <button class="topbar-search-button" type="submit" aria-label="提交搜索">
                        <img class="topbar-search-icon" src="search-icon.svg" alt="" aria-hidden="true">
                    </button>
                </div>
            </form>
            <div class="topbar-links">
                <a class="pill-link" href="#recent">最新更新</a>
                <a class="pill-link" href="#directions">研究方向</a>
                <a class="pill-link" href="{SOURCE_PAGES['starred']['file']}">高星论文</a>
                <a class="pill-link" href="#members">成员进展</a>
                <a class="pill-link" href="archive.html">全部归档</a>
            </div>
        </header>

        <section class="hero">
            <div class="hero-panel" style="--accent:#ff6b35;">
                <div class="section-kicker">Research Dashboard</div>
                <div class="hero-copy">
                    <h1>咒术SCI高专</h1>
                    <p>本主页以追踪前沿论文、沉淀研究主题、记录成员能力进化为核心，构建一个持续更新的学术协作场。我们希望把阅读、总结、讨论与写作连接成清晰可浏览的知识流，让每一次学习都能被积累、被连接、被推进。</p>
                </div>
                <div class="hero-actions">
                    <a class="action-link primary" href="#recent">查看论文排行榜</a>
                    <a class="action-link secondary" href="{SOURCE_PAGES['starred']['file']}">进入高星论文</a>
                </div>
                <div class="hero-tags">
                    <span class="hero-tag">研究包 {package_count}</span>
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
                        <div class="status-item"><div class="status-value">{package_count}</div><div class="kpi-label">研究包</div></div>
                        <div class="status-item"><div class="status-value">{member_count}</div><div class="kpi-label">成员记录</div></div>
                        <div class="status-item"><div class="status-value">{records[0]['date'] if records else '-'}</div><div class="kpi-label">最新时间</div></div>
                    </div>
                </div>
            </div>
        </section>

        <section class="section-grid" style="margin-top:22px;">
            <div class="section-panel focus-panel" style="--accent:#ff8c42;">
                <div class="section-kicker">Quick Access</div>
                <h2 class="section-title">核心学术入口</h2>
                <p class="panel-subtitle">按你的实际使用路径组织：先看资讯，再找灵感，最后沉淀成可追踪的研究方向。</p>
                <div class="topic-grid focus-link-list">
{render_topic_cards(focus_cards)}
                </div>
                <a class="focus-archive-link" href="{archive_link}">查看全部 {len(records)} 条归档</a>
            </div>
            <div class="section-panel ranking-panel" id="recent" style="--accent:#88ccff;">
                <div class="section-kicker">Gojo Ranking</div>
                <h2 class="section-title">近 3 天论文排行榜</h2>
                <p class="panel-subtitle">只显示前五篇。评分决定优先级，未评分论文排在后面等待判断。</p>
                <div class="research-package-list">
{gojo_ranking_markup}
                </div>
            </div>
        </section>

        <section class="section-panel direction-radar" id="directions" style="margin-top:22px; --accent:#f59e0b;">
            <div class="section-kicker">Research Radar</div>
            <h2 class="section-title">研究方向雷达</h2>
            <div class="section-kicker" style="margin-top:18px;">Trend Filters</div>
            <h3 class="direction-group-title">热点筛选</h3>
            <div class="trend-filter-strip">
{trend_filter_markup}
            </div>
            <div class="direction-radar-grid">
                <div class="direction-chart">
{topic_chart_markup}
                </div>
                <div class="direction-groups">
                    <div class="direction-group">
                        <div class="section-kicker">Idea Lenses</div>
                        <h3 class="direction-group-title">按问题找灵感</h3>
                        <div class="direction-card-list">
{problem_lens_markup}
                        </div>
                    </div>
                    <div class="direction-group">
                        <div class="section-kicker">Topic Tracks</div>
                        <h3 class="direction-group-title">按主题找积累</h3>
                        <div class="direction-card-list">
{domain_topic_markup}
                        </div>
                    </div>
                </div>
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

        <p class="footer-note">首页已收敛为学术视图。周会、升级迭代等内容仍保留在 <a href="archive.html">全部归档</a> 中。</p>
    </div>
    <script>
        var homeSearchIndex = {json.dumps(search_payload, ensure_ascii=False, indent=2)};
    </script>
    <script src="site-index.js"></script>
</body>
</html>
'''



def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def main() -> None:
    records = load_records()
    papers = [item for item in records if item['kind'] == 'paper']
    starred_entries = build_starred_entries(records)
    upgrades = [item for item in records if item['kind'] == 'upgrade']
    discussions = [item for item in records if item['kind'] == 'discussion']

    source_cards = [
        {'name': SOURCE_PAGES['archive']['title'], 'href': SOURCE_PAGES['archive']['file'], 'count': len(records), 'accent': SOURCE_PAGES['archive']['accent'], 'desc': SOURCE_PAGES['archive']['desc']},
        {'name': SOURCE_PAGES['paper']['title'], 'href': SOURCE_PAGES['paper']['file'], 'count': len(papers), 'accent': SOURCE_PAGES['paper']['accent'], 'desc': SOURCE_PAGES['paper']['desc']},
        {'name': SOURCE_PAGES['upgrade']['title'], 'href': SOURCE_PAGES['upgrade']['file'], 'count': len(upgrades), 'accent': SOURCE_PAGES['upgrade']['accent'], 'desc': SOURCE_PAGES['upgrade']['desc']},
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
    write_text(PROJECT_ROOT / SOURCE_PAGES['starred']['file'], build_detail_page(SOURCE_PAGES['starred']['title'], f"{SOURCE_PAGES['starred']['desc']} 当前共 {len(starred_entries)} 篇。", SOURCE_PAGES['starred']['accent'], starred_entries))
    write_text(PROJECT_ROOT / SOURCE_PAGES['upgrade']['file'], build_detail_page(SOURCE_PAGES['upgrade']['title'], f"{SOURCE_PAGES['upgrade']['desc']} 共 {len(upgrades)} 条。", SOURCE_PAGES['upgrade']['accent'], upgrades))
    write_text(PROJECT_ROOT / SOURCE_PAGES['discussion']['file'], build_detail_page(SOURCE_PAGES['discussion']['title'], f"{SOURCE_PAGES['discussion']['desc']} 共 {len(discussions)} 条。", SOURCE_PAGES['discussion']['accent'], discussions))
    write_text(PROJECT_ROOT / 'index.html', build_index(records, papers, source_cards, domain_cards, member_cards, starred_entries))
    print(f'Generated {len(records)} records from {SOURCE_ROOT}')


if __name__ == '__main__':
    main()
