#!/usr/bin/env python3
"""Minimal selftest for scripts/organize.py (stdlib unittest, offline).

Run from the skill root:
    python3 -m unittest discover -s tests -v

Covers the pure helpers only: markdown table cell escaping (_cell — titles
must not inject table rows/columns), the domain vocabulary gate (_is_domain),
and the role-aware validate() rules driven by a pre-flattened record.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import organize as og  # noqa: E402


def flat(tags=(), type="文章教程", domain=("开发",), status=()):
    return {"tags": list(tags), "type": type, "domain": list(domain), "status": list(status)}


class CellEscapeTests(unittest.TestCase):
    def test_pipes_become_fullwidth(self):
        self.assertEqual(og._cell("a|b"), "a／b")

    def test_newlines_tabs_become_spaces(self):
        self.assertEqual(og._cell("a\nb\rc\td"), "a b c d")

    def test_none_becomes_empty(self):
        self.assertEqual(og._cell(None), "")


class IsDomainTests(unittest.TestCase):
    def test_known_members(self):
        for x in ("开发", "设计", "AI", "前端", "配色", "书籍"):
            self.assertTrue(og._is_domain(x), x)

    def test_unknown_rejected(self):
        for x in ("", "开发部", "design", "随便写的"):
            self.assertFalse(og._is_domain(x), x)


class ValidateTests(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(og.validate({}, f=flat(
            tags=("网页UI", "设计系统"), type="文章教程", domain=("开发", "设计"),
        )), [])

    def test_too_many_tags(self):
        issues = og.validate({}, f=flat(tags=tuple("abcdefgh"[:7])))
        self.assertIn("cap>6", issues)

    def test_duplicate_tags(self):
        issues = og.validate({}, f=flat(tags=("a", "a")))
        self.assertIn("duplicate-tags", issues)

    def test_invalid_type(self):
        issues = og.validate({}, f=flat(type="不存在的类型"))
        self.assertTrue(any(i.startswith("type-invalid") for i in issues))

    def test_domain_count_cap(self):
        issues = og.validate({}, f=flat(domain=("开发", "设计", "AI")))
        self.assertTrue(any(i.startswith("domain-count") for i in issues))

    def test_mutex_open_source_project_with_open_status(self):
        issues = og.validate({}, f=flat(type="开源项目", status=("开源",)))
        self.assertIn("mutex:开源项目+开源", issues)

    def test_status_not_enabled(self):
        # user's selective enablement: only 待读/精华 are active statuses
        issues = og.validate({}, f=flat(status=("精华", "废弃")))
        self.assertTrue(any(i.startswith("status-not-enabled") for i in issues))

    def test_daidu_requires_article_type(self):
        issues = og.validate({}, f=flat(type="开源项目", status=("待读",)))
        self.assertIn("待读-not-single-article", issues)


if __name__ == "__main__":
    unittest.main()
