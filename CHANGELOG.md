# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-09-10

First release. Battle-tested end-to-end on a real 1,101-bookmark library (37 batches, 100% tagged + noted, zero structural violations).

### Added

- Project skeleton: SKILL.md (v1.0.0), scripts/, references/, docs/.
- Architecture: hybrid channels — REST API v1 for writes + bulk reads, MCP for content reads (`docs/decisions.md`).
- `scripts/rd_client.py`: REST client with verification readback, smoke test (`--smoke`), rate probe (`--rate-probe`), network retry (4 attempts, exponential backoff).
- `scripts/organize.py`: batch engine —
  - `pull`: untagged sampling, worklog-aware, resumable across sessions
  - `plan`: Before/After review table, zero writes, role-aware validation (tag cap, single type, 1–2 domains, mutual-exclusion pairs, status scoping, duplicate tags, domain membership)
  - `apply`: undo snapshot → conflict guard → batches of 10 → stop-on-failure → readback verification → worklog state machine (`classified-dryrun → applied / unverified / conflict-skip`)
  - `stats`: library progress
- Two-layer tag vocabulary: universal three-axis skeleton (`references/vocabulary.md`, zh/en) + optional personal extension (`vocabulary.custom.example.md` template) for private domains, renames, selective status tags, tag language and collection mapping. Hard cap 6 tags per bookmark.
- Type axis grouped into 5 semantic families (资产/交互/内容/检索/身份) with mutual-exclusion rules and boundary cases (作品集 vs 媒体刊物 vs 素材库; 工具网站 vs 官网).
- `docs/decisions.md`: 6 architecture decisions with rationale.

### Verified (2026-09-08 ~ 09-09, live)

- REST `PUT /raindrop/{id}` tags = full assignment/replace; MCP `update_bookmarks` tags object = incremental `{add, remove}` delta (probed with live seed + REST readback).
- Rate limit: 40 rapid list GETs → zero 429s.
- `delete_tags` lies about success (`deleted:N` on nonexistent tags) — every destructive op needs readback verification.
- Free-plan constraint: MCP semantic `search` is Pro-only; structural filters still work.
- Full-library run: 1,101/1,101 bookmarks tagged + noted across 37 batches; retry with backoff survived real SSL-flap outages; undo snapshots covered every write.
- Tier-2 deep-fetch round: 20/20 resolved via `fetch_bookmark_content` (5 corrections, incl. 2 material reclassifications).

### Known limitations

- MCP `search` parameters (semantic search, misplaced/mistagged detection) require Raindrop Pro.
- Pure JS-rendered sites may yield no parseable content even via `fetch_bookmark_content`.
- Title rewriting stays opt-in and off by default — original titles often carry valid information.

## [Unreleased]

_Nothing yet._
