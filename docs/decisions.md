# Architecture & Design Decisions

## D1 · Hybrid channels: REST v1 for writes, MCP for content reads (2026-09-08)

**Decision.** All writes (note/tags) and bulk reads go through the Raindrop REST API v1 (`https://api.raindrop.io/rest/v1/...`) using a thin Python client (`scripts/rd_client.py`). The `raindrop` MCP connector is used only for content reads: `fetch_bookmark_content`, `fetch_popular_keywords`, `search_help_docs`.

**Rationale.**

1. MCP `update_bookmarks` requires a `tags` **object** whose semantics were unverified at design time (possibly replace-style `{"old":"new"}` rather than assignment). REST `PUT /raindrop/{id}` natively accepts a tags **array** — verified 2026-09-08.
2. MCP error messages double as schema hints, but field names differ from REST (`link` vs `url`; `create_collections` requires `parent_id`). One canonical schema (REST) reduces mapping bugs.
3. REST bulk list returns `excerpt/domain/type/tags` per item in pages of 50 — the metadata-first classification route needs exactly this and nothing more.
4. Both channels share the same Bearer token, so mixing them has no extra credential cost.

**Consequence.** MCP tool behavior must still be re-tested if the server changes (protocol 2024-11-05, stateless Streamable HTTP, no session id).

## D2 · Write order: note → tags → title(opt-in) (2026-09-08)

**Rationale.** The library has 0 tags and ~0 notes, so note+tags carry all the value with near-zero destructiveness. Title rewriting touches meaningful user data (official product names, bilingual titles), is hard to spot-check at 1100 items, and titles are the primary search key — a bad mass rename degrades the library. Titles are therefore: default OFF, allow-list only (default SEO slugs / bare URLs / mojibake), opt-in flag, undo mapping mandatory.

## D3 · Checkpointed batch processing is a P0 requirement (2026-09-08)

**Rationale.** 1101 bookmarks exceed what a single agent session can process. State lives in a JSONL worklog (one line per item: id, status, tags, confidence, tier, timestamps). Every batch append-checkpoints; restart resumes from the last checkpoint; `is_tagged`-style filters skip processed items. Idempotency over convenience.

## D4 · Trust no write count blindly (2026-09-08)

**Evidence.** MCP `delete_tags` returned `{"deleted":1}` (and later `{"deleted":2}`) for tags that did not exist — fake success, same failure shape as the eagle `tag_merge` incident (affectedItems:0).

**Rule.** After every mutating call, read back the affected item(s) via REST and count `verified_ok` against `requested`. Any mismatch → item marked `UNVERIFIED`, processing stops at batch end.

## D5 · Token hygiene (2026-09-08)

The Raindrop API token grants full read/write to the library. It is injected via `RD_API_TOKEN` at runtime. It must never appear in repo files, skill files, logs, or reports. Reports go to `/tmp/` only.
