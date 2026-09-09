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


def cmd_plan(cls_path: Path, out: Path | None) -> int:
    """Render classification JSON into a review plan. Zero writes."""
    records = json.loads(cls_path.read_text())
    out = out or (STATE_DIR / f"plan-{time.strftime('%Y%m%d-%H%M%S')}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = sum(1 for r in records if r.get("tier") != "manual")
    by_tier: dict[str, int] = {}
    for r in records:
        by_tier[r.get("tier", "?")] = by_tier.get(r.get("tier", "?"), 0) + 1
    lines = [
        "# Dry-run plan (NO writes performed)",
        f"- items: {len(records)} · classifiable: {n_ok} · by tier: {by_tier}",
        "",
        "| id | title | domain | proposed note | proposed tags | conf | tier |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in records:
        t = (r.get("proposed_note") or "").replace("|", "／")
        tags = ", ".join(r.get("proposed_tags") or [])
        title = (r.get("title") or "")[:36]
        lines.append(
            f"| {r['id']} | {title} | {r.get('domain','')[:24]} "
            f"| {t} | {tags} | {r.get('confidence','')} | {r.get('tier','')} |")
    manual = [r for r in records if r.get("tier") == "manual"]
    if manual:
        lines += ["", "## Manual list (needs human decision)", ""]
        lines += [f"- {r['id']} {r.get('title','')[:60]} — {r.get('reason','')}" for r in manual]
    out.write_text("\n".join(lines) + "\n")
    print(f"plan -> {out} ({len(records)} items, tiers={by_tier})")
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
