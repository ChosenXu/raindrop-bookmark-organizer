#!/usr/bin/env python3
"""Selftests for scripts/organize.py (stdlib unittest, offline).

Run from the skill root:
    python3 -m unittest discover -s tests -v

Covers: markdown table cell escaping (_cell), the vocabulary gate
(_is_domain) and role-aware validate() rules, the vocabulary loader
(vocabulary.json + custom-file merge, json<->md consistency), worklog
tolerance, legacy flatten, pending-record terminal-state logic, and
artifact pruning.
"""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts")))

import organize as og  # noqa: E402


def flat(tags=(), type="文章教程", domain=("开发",), status=()):
    return {"tags": list(tags), "type": type, "domain": list(domain),
            "status": list(status)}


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
        # this repo's custom file enables 待读/精华; anything else is rejected
        issues = og.validate({}, f=flat(status=("精华", "废弃")))
        self.assertTrue(any(i.startswith("status-not-enabled") for i in issues))

    def test_workflow_status_requires_article_type(self):
        issues = og.validate({}, f=flat(type="开源项目", status=("待读",)))
        self.assertIn("workflow-not-single-article:['待读']", issues)

    def test_starred_also_requires_article_type(self):
        issues = og.validate({}, f=flat(type="媒体刊物", status=("精华",)))
        self.assertIn("workflow-not-single-article:['精华']", issues)

    def test_custom_vocab_enables_extra_status(self):
        vocab = dict(og.VOCAB)
        vocab["status_enabled"] = {"待读", "精华", "免费"}
        with mock.patch.object(og, "VOCAB", vocab):
            issues = og.validate({}, f=flat(type="工具网站", status=("免费",)))
        self.assertEqual(issues, [])


# --- vocabulary loader -------------------------------------------------------

CUSTOM_MD = """# my custom vocab

```markdown
status_tags: [待读, 精华, 免费]
domains_append:
  - domain: 求职招聘 career
    leaves: [简历 resume, 面试 interview]
# - domain: 健康生活 health
#   leaves: [健身 fitness]
domain_renames:
  数码硬件: 硬件
some unrelated line
```
"""


class VocabularyLoaderTests(unittest.TestCase):
    def _write(self, tmp: Path, name: str, text: str) -> Path:
        p = tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_no_custom_file_status_axis_off(self):
        with tempfile.TemporaryDirectory() as d:
            v = og.load_vocabulary(custom_path=Path(d) / "absent.md")
        self.assertEqual(v["status_enabled"], set())

    def test_custom_selective_enable(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, "custom.md", CUSTOM_MD)
            v = og.load_vocabulary(custom_path=tmp / "custom.md")
        self.assertEqual(v["status_enabled"], {"待读", "精华", "免费"})

    def test_custom_axis_enable_all(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, "custom.md", "status_axis_enabled: true\n")
            v = og.load_vocabulary(custom_path=tmp / "custom.md")
        self.assertEqual(v["status_enabled"], v["status_tags"])

    def test_status_tags_outside_vocabulary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, "custom.md", "status_tags: [待读, 付费之外乱写]\n")
            v = og.load_vocabulary(custom_path=tmp / "custom.md")
        self.assertEqual(v["status_enabled"], {"待读"})

    def test_custom_domains_and_renames_merge(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, "custom.md", CUSTOM_MD)
            v = og.load_vocabulary(custom_path=tmp / "custom.md")
        self.assertIn("求职招聘", v["domain_members"])   # zh alias of "求职招聘 career"
        self.assertIn("求职招聘 career", v["domain_members"])
        self.assertIn("简历", v["domain_members"])       # zh alias of "简历 resume"
        self.assertIn("硬件", v["domain_members"])       # rename target accepted
        self.assertIn("数码硬件", v["domain_members"])   # default kept
        self.assertNotIn("健康生活", v["domain_members"])  # commented out

    def test_commented_status_tags_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(tmp, "custom.md", "# status_tags: [付费]\n")
            v = og.load_vocabulary(custom_path=tmp / "custom.md")
        self.assertEqual(v["status_enabled"], set())

    def test_repo_default_vocab_respects_status_vocabulary(self):
        # The repo may or may not carry a local (gitignored) custom file
        # enabling 待读/精华 — CI sees none. Either way the merged result
        # must stay inside the vocabulary's status-tag set.
        self.assertLessEqual(og.VOCAB["status_enabled"], og.VOCAB["status_tags"])

    def test_caps_from_json(self):
        self.assertEqual(og.VOCAB["tag_cap"], 6)
        self.assertEqual(og.VOCAB["domain_cap"], 2)
        self.assertEqual(og.VOCAB["free_cap"], 2)


# --- json <-> markdown consistency ------------------------------------------

def _zh_parts(cell: str) -> list[str]:
    """'前端 frontend · 后端 backend' -> ['前端', '后端']; '3D' -> ['3D'].
    Mirrors the zh/en two-column convention of vocabulary.md: a trailing
    ASCII token is the English alias, everything before it is the tag."""
    parts = [p.strip() for p in cell.split("·") if p.strip()]
    out = []
    for p in parts:
        tokens = p.split()
        if len(tokens) > 1 and tokens[-1].isascii():
            out.append(" ".join(tokens[:-1]))
        else:
            out.append(p)
    return out


class VocabularyMarkdownConsistencyTests(unittest.TestCase):
    """Guards the json<->md pair: vocabulary.json is the machine source,
    vocabulary.md the human document — the test fails if either drifts."""

    @classmethod
    def setUpClass(cls):
        refs = og._VOCAB_PATH.parent
        cls.raw = json.loads(og._VOCAB_PATH.read_text(encoding="utf-8"))
        cls.md = (refs / "vocabulary.md").read_text(encoding="utf-8")

    def _table_rows(self, start: str, stop_prefix: str, skip_first_col: str):
        rows = []
        active = False
        for line in self.md.splitlines():
            if line.startswith(start):
                active = True
                continue
            if active:
                if line.startswith(stop_prefix):
                    break
                if line.startswith("|") and "---" not in line:
                    cells = [c.strip() for c in line.strip("|").split("|")]
                    if len(cells) >= 2 and cells[0] != skip_first_col:
                        rows.append(cells)
        return rows

    def test_domains_match(self):
        rows = self._table_rows("## Axis 1", "## Axis 2", "Domain")
        md_domains = {_zh_parts(c[0])[0] for c in rows}
        self.assertEqual(md_domains, set(self.raw["domains"]))

    def test_leaves_match(self):
        rows = self._table_rows("## Axis 1", "## Axis 2", "Domain")
        md_members = set()
        for c in rows:
            md_members.add(_zh_parts(c[0])[0])
            md_members.update(_zh_parts(c[1]))
        json_members = set(self.raw["domains"])
        for leaves in self.raw["domains"].values():
            json_members.update(leaves)
        self.assertEqual(md_members, json_members)

    def test_types_match(self):
        rows = self._table_rows("## Axis 2", "## Axis 3", "Type")
        md_types = {_zh_parts(c[0])[0] for c in rows}
        json_types = {t for ts in self.raw["type_groups"].values() for t in ts}
        self.assertEqual(md_types, json_types)
        # 17 was verified against vocabulary.md (SKILL.md/README said "16" —
        # a stale count this consistency check exists to catch)
        self.assertEqual(len(json_types), 17)

    def test_status_tags_match(self):
        for line in self.md.splitlines():
            if line.startswith("> 待读"):
                md_status = {_zh_parts(p.strip())[0]
                             for p in line.lstrip("> ").split("·")}
                break
        else:
            self.fail("status tag line not found in vocabulary.md")
        self.assertEqual(md_status, set(self.raw["status_tags"]))

    def test_mutex_entries_are_vocabulary_members(self):
        for leaf, typ in self.raw["mutex_leaf_type"].items():
            self.assertIn(leaf, og.VOCAB["domain_members"], leaf)
            self.assertIn(typ, og.VOCAB["types"], typ)
        for typ, st in self.raw["mutex_type_status"].items():
            self.assertIn(typ, og.VOCAB["types"])
            self.assertIn(st, self.raw["status_tags"])


# --- state machine helpers -----------------------------------------------------

class WorklogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.wl = Path(self.tmp.name) / "worklog.jsonl"
        self._orig = og.WORKLOG
        og.WORKLOG = self.wl
        self.addCleanup(setattr, og, "WORKLOG", self._orig)

    def test_missing_file_empty(self):
        self.assertEqual(og.load_worklog(), {})

    def test_corrupt_lines_skipped(self):
        self.wl.write_text(
            '{"id": 1, "status": "applied", "ts": "t"}\n'
            '{"id": 2, "stat\n'          # torn append mid-line
            'not json at all\n'
            '{"noid": 3}\n'
            '{"id": 4, "status": "applied"}\n',
            encoding="utf-8")
        out = og.load_worklog()
        self.assertEqual(out, {1: "applied", 4: "applied"})

    def test_latest_status_wins(self):
        self.wl.write_text(
            '{"id": 1, "status": "classified-dryrun"}\n'
            '{"id": 1, "status": "applied"}\n', encoding="utf-8")
        self.assertEqual(og.load_worklog(), {1: "applied"})


class FlattenLegacyTests(unittest.TestCase):
    def test_flat_tags_split_into_roles(self):
        f = og.flatten({"proposed_tags": ["开发", "开源项目", "待读", "react"]})
        self.assertEqual(f["domain"], ["开发"])
        self.assertEqual(f["type"], "开源项目")
        self.assertEqual(f["status"], ["待读"])
        self.assertEqual(f["free"], ["react"])

    def test_malformed_tags_degrade(self):
        f = og.flatten({"proposed_tags": "not-a-list"})
        self.assertEqual(f["tags"], [])
        self.assertEqual(f["type"], "")

    def test_structured_still_works(self):
        f = og.flatten({"domain_tags": ["设计"], "type": "模板",
                        "status": [], "free": ["figma"]})
        self.assertEqual(f["tags"], ["设计", "模板", "figma"])


class RecordPendingTests(unittest.TestCase):
    def test_pending_under_classified_dryrun(self):
        self.assertTrue(og._record_pending({"id": 7}, {7: "classified-dryrun"}))

    def test_terminal_states_not_pending(self):
        for s in ("applied", "unverified", "conflict-skip", "invalid-skip"):
            self.assertFalse(og._record_pending({"id": 7}, {7: s}), s)

    def test_string_id_matches_int_worklog_key(self):
        self.assertTrue(og._record_pending({"id": "7"}, {7: "classified-dryrun"}))

    def test_unparseable_id_uses_raw_key(self):
        self.assertTrue(og._record_pending({"id": "7/.."}, {"7/..": "classified-dryrun"}))
        self.assertFalse(og._record_pending({"id": "7/.."}, {}))

    def test_missing_id_never_pending(self):
        self.assertFalse(og._record_pending({}, {7: "classified-dryrun"}))


class PruneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._orig_state = og.STATE_DIR
        og.STATE_DIR = Path(self.tmp.name)
        self.addCleanup(setattr, og, "STATE_DIR", self._orig_state)

    def _touch(self, name, age_days):
        p = og.STATE_DIR / name
        p.write_text("x")
        old = time.time() - age_days * 86400
        os.utime(p, (old, old))
        return p

    def test_old_artifacts_pruned(self):
        old_sample = self._touch("sample-20200101-000000.json", 40)
        old_plan = self._touch("plan-20200101-000000.md", 40)
        removed = og.prune_artifacts()
        self.assertIn(old_sample.name, removed)
        self.assertIn(old_plan.name, removed)
        self.assertFalse(old_sample.exists())
        self.assertFalse(old_plan.exists())

    def test_new_artifacts_and_protected_files_survive(self):
        new_sample = self._touch("sample-20990101-000000.json", 1)
        undo = self._touch("apply-20200101-000000.undo.json", 400)
        worklog = self._touch("worklog.jsonl", 400)
        removed = og.prune_artifacts()
        self.assertEqual(removed, [])
        self.assertTrue(new_sample.exists())
        self.assertTrue(undo.exists())
        self.assertTrue(worklog.exists())


if __name__ == "__main__":
    unittest.main()
