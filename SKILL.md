---
name: raindrop-bookmark-organizer
description: Use when the user wants to organize, tag, annotate, or rename bookmarks in their Raindrop.io library (via the Raindrop REST API and an optional Raindrop MCP server). Triggers on mentions of Raindrop, raindrop.io, 书签, bookmarks, 收藏 combined with a batch-organize intent (打标签 / 写描述 / 整理 / tag / annotate / organize). Produces a structured note and three-axis controlled tags for each bookmark; title rewriting is a conservative opt-in step. Supports checkpointed batch processing across sessions for libraries of 1000+ bookmarks.
agent_created: true
version: 1.3.0
license: MIT
---

# Raindrop Bookmark Organizer

## Overview

Batch-organize Raindrop.io bookmarks with a three-step workflow:

1. **命名 (title)** — conservative rewrite of garbage titles only (opt-in, default OFF)
2. **写描述 (note)** — one structured note per bookmark: 1–2 sentences, "what it is + key highlight / when to reach for it", 40–80 字 (Chinese) / ~30–60 words (English); same language as skeleton tags; no marketing fluff, no repeating the title verbatim.
3. **打标签 (tags)** — three-axis controlled vocabulary

Design principle: **metadata first**. The Raindrop list API returns title/link/domain/excerpt/type per bookmark in bulk — no webpage fetching needed for classification. Deep-fetch (`fetch_bookmark_content`) is reserved for a low-confidence subset (≤30%).

## Architecture

**Hybrid channels** (see `docs/decisions.md`):

| Channel | Used for |
|---|---|
| Raindrop REST API v1 (`api.raindrop.io/rest/v1/...`) | all writes (note/tags) + bulk reads + verification readback |
| Raindrop MCP server (optional) | semantic-adjacent reads only: `fetch_bookmark_content`, `fetch_popular_keywords`, `search_help_docs` |

Free-plan constraint: MCP `search` parameters are Pro-only — never rely on them.

## Credentials

- API token from `env RD_API_TOKEN` (or ask the user at runtime). **Never hardcode, never write into any repo file.**
- Token belongs to the user's Raindrop account; treat every write as destructive-capable.

## Workflow (per batch, 30-50 items)

1. **Resume check** — load checkpoint file; skip processed items.
2. **Fetch metadata** — REST list per collection (50/page), includes excerpt.
3. **Domain clustering** — same-domain items share context in one batch.
4. **Classify** — load the custom vocabulary file first if present, else the default skeleton; assign tags per the composition rules; output confidence per item.
5. **Deep fetch (Tier 2)** — only for low-confidence items; single retry on failure, then mark `manual`.
6. **Write** — order: note → tags. Title opt-in. Small batches (≤10), stop on first failure.
7. **Verify** — readback after every write; report `requested / verified_ok`; failures listed as `UNVERIFIED`.
8. **Checkpoint** — persist state (JSONL worklog) after every batch.

## Safety rules

- `delete_tags` lies about success (it reports `deleted:N` even for tags that do not exist). Every delete is followed by readback verification; the `deleted` count alone is never trusted.
- `delete_bookmarks` is soft-delete (moves to Trash). The skill never deletes bookmarks; it only adds metadata.
- Before any write: snapshot original state (title/note/tags) into an undo mapping file. The snapshot is flushed to disk before every single write, so an interrupted run never loses undo data.
- `apply` re-validates every record against the vocabulary rules before writing (invalid records are skipped as `invalid-skip`; rules derive from `references/vocabulary.json` merged with the user's `vocabulary.custom.md`), coerces ids to integers (path-safety), and rejects unknown `--what` values up front.
- State files (samples, plans, undo snapshots, worklog) are written with owner-only permissions (0600) and fsync'd; a torn worklog line after a crash is skipped with a warning instead of breaking the tool.
- The REST client reuses one HTTPS connection per run, retries 429s with backoff (honoring `Retry-After`) and adapts its pacing after a 429; network errors rebuild the connection and retry.
- Regenerable review artifacts (`sample-*.json`, `plan-*.md`) older than 30 days are pruned automatically on `pull`/`stats`; undo snapshots and the worklog are never pruned.
- Known limitation (TOCTOU): the conflict guard is a pre-write GET — tags added by another client between check and write would be replaced. Run `apply` while no other client is writing.
- All reports go to `/tmp/`, never into the repo.

## Vocabulary & language

Tags are selected verbatim from the controlled vocabulary in `references/vocabulary.md` (normative): three axes — Domain (1–2), Type (exactly 1, picked from the 5 semantic groups), Status (0–2, **off by default**) — plus up to 2 free supplementary tags, hard cap 6 per bookmark. Workflow status tags (待读/精华) apply only to single-article pages, never site-level bookmarks. Never tag both sides of a conflicting pair; never invent skeleton tags. Read the vocabulary file before tagging; never mix languages for the same tag across bookmarks.

Machine authority: `references/vocabulary.json` drives the batch validator in `scripts/organize.py`; `vocabulary.md` is its human-readable twin, kept in sync by a unit test. Loading order: if `references/vocabulary.custom.md` exists (user-created from the provided example template), read it first — it overrides/extends the skeleton (tag language, status-axis enablement, private domains, renames, optional collection mapping), and the validator merges the same file. Otherwise defaults apply.

Skeleton tag language: explicit user instruction > invocation-language inheritance > default 简体中文. `vocabulary.md` carries the canonical zh/en columns.

If a collection mapping exists in the custom file, additionally output a suggested target collection per bookmark — suggestion only, never move bookmarks.

## Supporting Files

Load only when needed:

- `references/vocabulary.md` — default skeleton vocabulary (always load before tagging)
- `references/vocabulary.json` — machine-authoritative vocabulary consumed by the validator
- `references/vocabulary.custom.example.md` — template for the user's personal extension file
- `scripts/organize.py` — batch engine: candidate pull, checkpoint worklog, dry-run plan rendering
- `docs/decisions.md` — architecture decisions and their rationale
- `scripts/rd_client.py` — REST client: paginated reads, batched writes, verification readback

## Out of scope

- Skeleton languages beyond the built-in zh/en columns
- Collection restructuring, highlights processing
- Tag merge/dedup governance (needs tag stock first)
- Full-library deep fetching beyond the 30% confidence budget
