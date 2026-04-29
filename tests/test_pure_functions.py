"""Unit tests for pure functions in sync_from_source.py.

These tests import the module directly (no subprocess), which is possible
because resolve_paths() is now deferred to main().
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import sync_from_source as sfs


class TestParseFolderTimestamp(unittest.TestCase):
    def test_iso_date(self):
        result = sfs.parse_folder_timestamp('2026-04-28')
        self.assertEqual(result, datetime(2026, 4, 28, 0, 0))

    def test_iso_date_with_hour(self):
        result = sfs.parse_folder_timestamp('2026-04-28-16')
        self.assertEqual(result, datetime(2026, 4, 28, 16, 0))

    def test_compact_date(self):
        result = sfs.parse_folder_timestamp('20260428')
        self.assertEqual(result, datetime(2026, 4, 28, 0, 0))

    def test_compact_date_with_hour(self):
        result = sfs.parse_folder_timestamp('20260428-09')
        self.assertEqual(result, datetime(2026, 4, 28, 9, 0))

    def test_invalid_date(self):
        self.assertIsNone(sfs.parse_folder_timestamp('not-a-date'))

    def test_invalid_month(self):
        self.assertIsNone(sfs.parse_folder_timestamp('2026-13-01'))

    def test_iso_date_with_suffix(self):
        result = sfs.parse_folder_timestamp('2026-04-28-some-topic')
        self.assertEqual(result, datetime(2026, 4, 28, 0, 0))


class TestDetectKind(unittest.TestCase):
    def test_paper_summary(self):
        self.assertEqual(sfs.detect_kind('论文总结.md'), 'paper')

    def test_member_evolution(self):
        self.assertEqual(sfs.detect_kind('悠仁-能力进化.md'), 'member')

    def test_upgrade(self):
        self.assertEqual(sfs.detect_kind('升级迭代.md'), 'upgrade')

    def test_discussion(self):
        self.assertEqual(sfs.detect_kind('周会讨论.md'), 'discussion')

    def test_other(self):
        self.assertEqual(sfs.detect_kind('random-file.md'), 'other')

    def test_member_summary(self):
        self.assertEqual(sfs.detect_kind('五条悟-汇总.md'), 'other')


class TestMemberName(unittest.TestCase):
    def test_yujin(self):
        self.assertEqual(sfs.member_name('悠仁-能力进化.md'), '悠仁')

    def test_gojo(self):
        self.assertEqual(sfs.member_name('五条悟-能力进化.md'), '五条悟')

    def test_no_member(self):
        self.assertIsNone(sfs.member_name('论文总结.md'))


class TestParseScoreInfo(unittest.TestCase):
    def test_standard_score(self):
        text = '**综合评分：** 4.5/5'
        result = sfs.parse_score_info(text)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['score'], 4.5)

    def test_ten_scale(self):
        text = '**综合评分：8/10**'
        result = sfs.parse_score_info(text)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['score'], 4.0)

    def test_no_score(self):
        self.assertIsNone(sfs.parse_score_info('no score here'))


class TestFormatStarScore(unittest.TestCase):
    def test_integer(self):
        self.assertEqual(sfs.format_star_score(4.0), '4')

    def test_half(self):
        self.assertEqual(sfs.format_star_score(3.5), '3.5')


class TestScoreToStars(unittest.TestCase):
    def test_five_stars(self):
        result = sfs.score_to_stars(5.0)
        self.assertEqual(result.count('★'), 5)

    def test_three_and_half(self):
        result = sfs.score_to_stars(3.5)
        self.assertIn('★', result)


class TestExtractArxivId(unittest.TestCase):
    def test_standard_format(self):
        self.assertEqual(sfs.extract_arxiv_id('arXiv ID: 2604.08362'), '2604.08362')

    def test_url_format(self):
        self.assertEqual(sfs.extract_arxiv_id('https://arxiv.org/abs/2604.08362'), '2604.08362')

    def test_no_id(self):
        self.assertEqual(sfs.extract_arxiv_id('no arxiv here'), '')


class TestNormalizePaperKey(unittest.TestCase):
    def test_with_arxiv(self):
        result = sfs.normalize_paper_key('Some Paper Title', '2604.08362')
        self.assertEqual(result, '2604.08362')

    def test_without_arxiv(self):
        result = sfs.normalize_paper_key('Some Paper Title')
        self.assertIn('some', result.lower())


class TestMatchesKeywords(unittest.TestCase):
    def test_match(self):
        self.assertTrue(sfs.matches_keywords('Natural Language Processing', ['language', 'nlp']))

    def test_no_match(self):
        self.assertFalse(sfs.matches_keywords('Computer Vision', ['language', 'nlp']))

    def test_case_insensitive(self):
        self.assertTrue(sfs.matches_keywords('NLP Research', ['nlp']))


class TestCleanInlineText(unittest.TestCase):
    def test_removes_markdown(self):
        result = sfs.clean_inline_text('**bold** and *italic*')
        self.assertNotIn('**', result)
        self.assertNotIn('*', result)

    def test_plain_text(self):
        result = sfs.clean_inline_text('plain text')
        self.assertEqual(result.strip(), 'plain text')


class TestBuildTitle(unittest.TestCase):
    def test_paper_title_extraction(self):
        content = '# 论文总结\n\n**论文标题：** Test Paper Title'
        result = sfs.build_title('论文总结.md', content)
        self.assertIn('Test Paper Title', result)

    def test_heading_fallback(self):
        content = '# My Heading\n\nSome content here'
        result = sfs.build_title('random.md', content)
        self.assertIn('My Heading', result)


class TestClassifySessionType(unittest.TestCase):
    def test_paper(self):
        st, sl = sfs.classify_session_type('论文总结.md', '# 论文总结', 'paper')
        self.assertIsInstance(st, str)
        self.assertIsInstance(sl, str)

    def test_member(self):
        st, sl = sfs.classify_session_type('悠仁-能力进化.md', '# 悠仁', 'member')
        self.assertIsInstance(st, str)
        self.assertIsInstance(sl, str)


if __name__ == '__main__':
    unittest.main()
