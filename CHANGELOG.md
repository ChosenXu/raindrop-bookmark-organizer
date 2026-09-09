# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Project skeleton: SKILL.md (v1.0.0), scripts/, references/, docs/.
- Architecture decision: hybrid channels — REST API v1 for writes + bulk reads, MCP for content reads (docs/decisions.md).
- `scripts/rd_client.py`: REST client with verification readback, smoke test (`--smoke`), rate probe (`--rate-probe`).
- Two-layer tag vocabulary: universal three-axis skeleton (`references/vocabulary.md`, zh/en) + optional personal extension file (`vocabulary.custom.example.md` template) for private domains, renames, status-axis toggle, tag language and collection mapping. Tag cap: 6 per bookmark.

### Verified (2026-09-08)

- REST `PUT /raindrop/{id}` tags = full assignment/replace semantics; update+readback loop verified on scratch data.
- MCP `update_bookmarks` tags object = incremental delta `{add: [...], remove: [...]}` (probed with live seed + REST readback).
- Rate limit: 40 rapid list GETs → zero 429s; per-request latency ~1.7s observed.

## [1.0.0]

_Pending — not yet released. Will be tagged after Phase 6 (full-library run) passes acceptance._
