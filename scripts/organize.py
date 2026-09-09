#!/usr/bin/env python3
"""organize.py — batch engine for raindrop-bookmark-organizer.

State dir: ~/.workbuddy/raindrop-organizer/  (outside the repo, persistent)
  worklog.jsonl   one line per processed bookmark: {"id":..,"status":..,"ts":..}
  plan-*.md       dry-run plans (review artifacts)

Modes (all read-only against Raindrop unless --apply, which is Phase 4):
  pull   --sample N [--out FILE]    emit an evenly-spaced sample of untagged
                                    bookmarks as JSON for classification
  plan   --class FILE [--out FILE]  render a classification JSON into a
                                    Before/After markdown plan (zero writes)
  stats                             worklog + library tagging progress
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rd_client import RaindropClient, RaindropError  # noqa: E402

STATE_DIR = Path.home() / ".workbuddy" / "raindrop-organizer"
WORKLOG = STATE_DIR / "worklog.jsonl"
DEFAULT_OUT = STATE_DIR


def log_state(rid: int, status: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(WORKLOG, "a") as f:
        f.write(json.dumps({"id": rid, "status": status,
                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


def load_worklog() -> set[int]:
    if not WORKLOG.exists():
        return set()
    return {json.loads(l)["id"] for l in WORKLOG.read_text().splitlines() if l.strip()}


def pull_untagged(rc: RaindropClient) -> list[dict]:
    """All untagged, non-trashed bookmarks with classification-relevant fields."""
    items = rc.list_all(0)
    out = []
    for it in items:
        if it.get("tags"):
            continue
        out.append({
            "id": it["_id"],
            "title": (it.get("title") or "").strip(),
            "link": it.get("link") or "",
            "domain": it.get("domain") or "",
            "excerpt": (it.get("excerpt") or "").strip(),
            "note": (it.get("note") or "").strip(),
            "collection": (it.get("collection") or {}).get("title", ""),
            "created": it.get("created", ""),
            "type": it.get("type", "link"),
        })
    return out


def cmd_pull(sample: int, out: Path | None) -> int:
    rc = RaindropClient()
    done = load_worklog()
    cands = [x for x in pull_untagged(rc) if x["id"] not in done]
    print(f"untagged candidates: {len(cands)} (worklog done: {len(done)})")
    if not cands:
        print("nothing to do")
        return 0
    cands.sort(key=lambda x: x["id"])
    stride = max(1, len(cands) // sample)
    sample_items = cands[::stride][:sample]
    out = out or (STATE_DIR / f"sample-{time.strftime('%Y%m%d-%H%M%S')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sample_items, ensure_ascii=False, indent=1))
    print(f"sampled {len(sample_items)} -> {out}")
    for x in sample_items[:3]:
        print(f"  e.g. {x['id']} {x['title'][:40]} [{x['domain']}]")
    return 0


GROUPS = {  # type member -> semantic group
    "组件 UI 库": "A", "图标插画": "A", "字体": "A", "模板": "A", "素材库": "A",
    "工具网站": "B", "开源项目": "B",
    "媒体刊物": "C", "文章教程": "C", "文档手册": "C", "视频": "C", "书影记录": "C", "数据报告": "C",
    "清单导航": "D", "社区论坛": "D",
    "作品集": "E", "官网": "E",
}
MUTEX_LEAF_TYPE = {"字体": "字体", "图标": "图标插画", "组件库": "组件 UI 库"}


def flatten(rec: dict) -> dict:
    """Normalize a class record: accept structured (domain_tags/type/status/free)
    or legacy flat proposed_tags, return dict with roles + flat tags.
    Note: rec["domain"] (site domain string) is source metadata, never tags."""
    if "type" in rec:  # structured
        dom = list(rec.get("domain_tags") or [])
        st = list(rec.get("status") or [])
        free = list(rec.get("free") or [])
        typ = rec["type"]
        return {"domain": dom, "type": typ, "status": st, "free": free,
                "tags": [*dom, typ, *st, *free]}
    # legacy flat: infer type = first tag belonging to a group
    t = rec.get("proposed_tags", [])
    typ = next((x for x in t if x in GROUPS), "")
    st = [x for x in t if x in {"待读", "精华", "免费", "开源", "付费", "中文", "英文"}]
    dom = [x for x in t if x != typ and x not in st and _is_domain(x)]
    free = [x for x in t if x != typ and x not in st and x not in dom]
    return {"domain": dom, "type": typ, "status": st, "free": free, "tags": t}


def _is_domain(x: str) -> bool:
    return x in {"开发", "设计", "AI", "产品效率", "数码硬件", "影音文化",
                 "阅读学习", "科学", "资讯", "实用工具"} or x in {
        "前端", "后端", "移动端", "组件库", "开发工具", "UI 参考", "灵感集", "图标",
        "配色", "动效", "排版", "3D", "AI 工具", "AI 资讯", "Agent", "模型评测",
        "效率工具", "笔记知识库", "协作", "自动化", "数码产品", "智能家居",
        "电影", "书籍", "游戏", "音乐", "课程", "语言学习", "科普",
        "科研", "数学", "科技资讯", "设计资讯", "周刊日报", "查询计算", "安全隐私"}


def validate(rec: dict) -> list[str]:
    """Role-aware rule check. Returns list of issue strings (empty = pass)."""
    f = flatten(rec)
    issues = []
    if len(f["tags"]) > 6:
        issues.append("cap>6")
    if not f["type"] or f["type"] not in GROUPS:
        issues.append(f"type-invalid:{f['type']!r}")
    if not 1 <= len(f["domain"]) <= 2:
        issues.append(f"domain-count:{f['domain']}")
    for leaf, typ in MUTEX_LEAF_TYPE.items():
        if leaf in f["domain"] and f["type"] == typ:
            issues.append(f"mutex:{leaf}+{typ}")
    if f["type"] == "开源项目" and "开源" in f["status"]:
        issues.append("mutex:开源项目+开源")
    if "待读" in f["status"] and f["type"] != "文章教程":
        issues.append("待读-not-single-article")
    allowed_status = {"待读", "精华"}  # user's selective enablement
    bad = set(f["status"]) - allowed_status
    if bad:
        issues.append(f"status-not-enabled:{sorted(bad)}")
    return issues


def cmd_plan(cls_path: Path, out: Path | None) -> int:
    """Render classification JSON into a review plan. Zero writes."""
    records = json.loads(cls_path.read_text())
    out = out or (STATE_DIR / f"plan-{time.strftime('%Y%m%d-%H%M%S')}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = sum(1 for r in records if r.get("tier") != "manual")
    by_tier: dict[str, int] = {}
    all_issues = {}
    for r in records:
        by_tier[r.get("tier", "?")] = by_tier.get(r.get("tier", "?"), 0) + 1
        v = validate(r)
        if v:
            all_issues[r["id"]] = v
    lines = [
        "# Dry-run plan (NO writes performed)",
        f"- items: {len(records)} · classifiable: {n_ok} · by tier: {by_tier}",
        f"- validation: {'ALL PASS' if not all_issues else all_issues}",
        "",
        "| id | title | domain | proposed note | proposed tags | conf | tier |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in records:
        f = flatten(r)
        t = (r.get("proposed_note") or r.get("note_draft") or "").replace("|", "／")
        tags = ", ".join(f["tags"])
        title = (r.get("title") or "")[:36]
        lines.append(
            f"| {r['id']} | {title} | {r.get('domain','')[:24]} "
            f"| {t} | {tags} | {r.get('confidence','')} | {r.get('tier','')} |")
    manual = [r for r in records if r.get("tier") == "manual"]
    if manual:
        lines += ["", "## Manual list (needs human decision)", ""]
        lines += [f"- {r['id']} {r.get('title','')[:60]} — {r.get('reason','')}" for r in manual]
    out.write_text("\n".join(lines) + "\n")
    print(f"plan -> {out} ({len(records)} items, tiers={by_tier}, "
          f"validation={'ALL PASS' if not all_issues else all_issues})")
    return 0


def cmd_stats() -> int:
    rc = RaindropClient()
    u = rc.user()["statistics"]["bookmarks"]
    done = load_worklog()
    print(f"library: total={u['total']} has_tags={u['has_tags']} lacks_tags={u['lacks_tags']}")
    print(f"worklog entries: {len(done)}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("pull")
    sp.add_argument("--sample", type=int, default=30)
    sp.add_argument("--out", type=Path, default=None)
    cp = sub.add_parser("plan")
    cp.add_argument("--class", dest="cls", type=Path, required=True)
    cp.add_argument("--out", type=Path, default=None)
    sub.add_parser("stats")
    a = p.parse_args()
    try:
        if a.cmd == "pull":
            return cmd_pull(a.sample, a.out)
        if a.cmd == "plan":
            return cmd_plan(a.cls, a.out)
        if a.cmd == "stats":
            return cmd_stats()
    except RaindropError as e:
        print(f"API error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
