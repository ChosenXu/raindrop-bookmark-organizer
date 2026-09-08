---
name: raindrop-bookmark-organizer
description: Use when the user wants to organize, tag, annotate, or rename bookmarks in their Raindrop.io library (via the raindrop MCP connector or the Raindrop REST API). Triggers on mentions of Raindrop, raindrop.io, 书签, bookmarks, 收藏 combined with a batch-organize intent (打标签 / 写描述 / 整理 / tag / annotate / organize). Produces a structured note and three-axis controlled tags for each bookmark; title rewriting is a conservative opt-in step. Supports checkpointed batch processing across sessions for libraries of 1000+ bookmarks.
agent_created: true
version: 1.0.0
---

# Raindrop Bookmark Organizer

## Overview

Batch-organize Raindrop.io bookmarks with the three-step workflow proven in `eagle-untagged-organizer`:

1. **命名 (title)** — conservative rewrite of garbage titles only (opt-in, default OFF)
2. **写描述 (note)** — one structured note per bookmark
3. **打标签 (tags)** — three-axis controlled vocabulary

Design principle: **metadata first**. The Raindrop list API returns title/link/domain/excerpt/type per bookmark in bulk — no webpage fetching needed for classification. Deep-fetch (`fetch_bookmark_content`) is reserved for a low-confidence subset (≤30%).

## Architecture

**Hybrid channels** (decided 2026-09-08, see `docs/decisions.md`):

| Channel | Used for |
|---|---|
| Raindrop REST API v1 (`api.raindrop.io/rest/v1/...`) | all writes (note/tags) + bulk reads + verification readback |
| `raindrop` MCP connector | semantic-adjacent reads only: `fetch_bookmark_content`, `fetch_popular_keywords`, `search_help_docs` |

Free-plan constraint: MCP `search` parameters are Pro-only — never rely on them.

## Credentials

- API token from `env RD_API_TOKEN` (or ask the user at runtime). **Never hardcode, never write into any repo file.**
- Token belongs to the user's Raindrop account; treat every write as destructive-capable.

## Workflow (per batch, 30-50 items)

1. **Resume check** — load checkpoint file; skip processed items.
2. **Fetch metadata** — REST list per collection (50/page), includes excerpt.
3. **Domain clustering** — same-domain items share context in one batch.
4. **Classify** — assign tags from `references/vocabulary.md` (user-frozen); output confidence per item.
5. **Deep fetch (Tier 2)** — only for low-confidence items; single retry on failure, then mark `manual`.
6. **Write** — order: note → tags. Title opt-in. Small batches (≤10), stop on first failure.
7. **Verify** — readback after every write; report `requested / verified_ok`; failures listed as `UNVERIFIED`.
8. **Checkpoint** — persist state (JSONL worklog) after every batch.

## Safety rules

- `delete_tags` lies about success (`deleted:N` on nonexistent tags — confirmed 2026-09-08). Every delete is followed by readback verification; the `deleted` count alone is never trusted.
- `delete_bookmarks` is soft-delete (moves to Trash). The skill never deletes bookmarks; it only adds metadata.
- Before any write: snapshot original state (title/note/tags) into an undo mapping file.
- All reports go to `/tmp/`, never into the repo.

## Supporting Files

Load only when needed:

- `references/vocabulary.md` — controlled three-axis tag vocabulary (frozen by user before any full run)
- `docs/decisions.md` — architecture decisions and their rationale
- `scripts/rd_client.py` — REST client: paginated reads, batched writes, verification readback

## Out of scope (v1.0.0)

- Multilingual outputs (Chinese only in v1)
- Collection restructuring, highlights processing
- Tag merge/dedup governance (needs tag stock first)
- Full-library deep fetching beyond the 30% confidence budget
