from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SyncFromSourceHermesTests(unittest.TestCase):
    def test_config_local_and_hermes_paper_key_records_generate_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            source = root / 'source'
            project.mkdir()

            shutil.copy2(REPO_ROOT / 'sync_from_source.py', project / 'sync_from_source.py')
            (project / 'config.json').write_text(
                json.dumps({
                    'source_root': str(root / 'missing-source'),
                    'project_root': str(project),
                }),
                encoding='utf-8',
            )
            (project / 'config.local.json').write_text(
                json.dumps({'source_root': str(source)}),
                encoding='utf-8',
            )

            paper_dir = source / 'records' / '2026' / '04' / '27' / '16' / '2604.08362'
            paper_dir.mkdir(parents=True)
            (paper_dir / '论文总结.md').write_text(
                '\n'.join([
                    '# 论文总结',
                    '',
                    '**论文标题：** Hermes Paper Contract',
                    '**arXiv ID：** 2604.08362',
                    '**领域标签：** HCI, Agent',
                    '**综合评分：** 4.5/5',
                    '',
                    '## 1. 研究什么？',
                    '测试 Hermes 深层目录契约。',
                ]),
                encoding='utf-8',
            )
            (paper_dir / '五条悟-能力进化.md').write_text(
                '\n'.join([
                    '# 五条悟短评',
                    '',
                    '**时间：** 2026-04-27 16:10',
                    '',
                    '### Hermes Paper Contract',
                    '综合 4.5/5，只保留批判、关系和下一步动作。',
                ]),
                encoding='utf-8',
            )
            (paper_dir / '野蔷薇-论文总结.md').write_text(
                '# 不应作为 canonical 论文总结\n\n这份历史式命名不应增加论文计数。',
                encoding='utf-8',
            )

            result = subprocess.run(
                [sys.executable, 'sync_from_source.py'],
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Generated 3 records', result.stdout)
            self.assertIn('Hermes Paper Contract', (project / 'papers.html').read_text(encoding='utf-8'))
            self.assertIn('records/2026/04/27/16/2604.08362', (project / 'papers.html').read_text(encoding='utf-8'))
            self.assertIn('五条悟短评', (project / '五条悟.html').read_text(encoding='utf-8'))
            self.assertIn('研究包 1', (project / 'index.html').read_text(encoding='utf-8'))

    def test_home_page_groups_papers_and_role_notes_into_research_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'project'
            source = root / 'source'
            project.mkdir()

            shutil.copy2(REPO_ROOT / 'sync_from_source.py', project / 'sync_from_source.py')
            (project / 'config.json').write_text(
                json.dumps({'source_root': str(source), 'project_root': str(project)}),
                encoding='utf-8',
            )

            first = source / 'records' / '2026' / '04' / '27' / '17' / 'mta-agent'
            first.mkdir(parents=True)
            (first / '论文总结.md').write_text(
                '\n'.join([
                    '# 论文总结',
                    '',
                    '**论文标题：** MTA-Agent: An Open Recipe for Multimodal Deep Search Agents',
                    '**作者：** Salesforce AI Research',
                    '**领域标签：** AI, Agent, Multimodal',
                    '',
                    '## 1. 研究什么？',
                    '研究多模态深度搜索 Agent。',
                ]),
                encoding='utf-8',
            )
            (first / '五条悟-能力进化.md').write_text(
                '# 五条悟 · 前沿评审\n\n综合 4.7/5，适合放入高优先级 Agent 研究包。',
                encoding='utf-8',
            )

            second = source / 'records' / '2026' / '04' / '27' / '16' / 'wiserui-bench'
            second.mkdir(parents=True)
            (second / '论文总结.md').write_text(
                '\n'.join([
                    '# 论文总结',
                    '',
                    '**论文标题：** WiserUI-Bench',
                    '**领域标签：** UX, HCI, Benchmark',
                    '',
                    '## 1. 研究什么？',
                    '研究 UI/UX 行为理解。',
                ]),
                encoding='utf-8',
            )

            result = subprocess.run(
                [sys.executable, 'sync_from_source.py'],
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            index = (project / 'index.html').read_text(encoding='utf-8')
            self.assertIn('近 3 天论文排行榜', index)
            self.assertIn('MTA-Agent: An Open Recipe for Multimodal Deep Search Agents', index)
            self.assertIn('五条老师评定 4.7/5', index)
            self.assertIn('待五条老师评定', index)
            self.assertIn('问题索引', index)
            self.assertIn('Agent', index)
            self.assertIn('UX / HCI', index)
            self.assertIn('research-package-card', index)
            self.assertIn('ranking-card', index)
            self.assertNotIn('<article class="entry-card">', index)
            self.assertLess(
                index.index('MTA-Agent: An Open Recipe for Multimodal Deep Search Agents'),
                index.index('WiserUI-Bench'),
            )


if __name__ == '__main__':
    unittest.main()
