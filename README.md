# Raindrop Bookmark Organizer

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

A [WorkBuddy](https://www.workbuddy.cn/) skill that batch-organizes a [Raindrop.io](https://raindrop.io/) library with a proven three-step workflow — **name (optional) → annotate → tag**. Battle-tested end-to-end on a real 1,101-bookmark library: 37 batches, 100% tagged + annotated, zero structural violations.

## What it does

For every untagged bookmark it produces:

1. **Note** — 1–2 sentences: what it is + when you'll reach for it (40–80 characters in Chinese, 30–60 words in English)
2. **Tags** — up to 6, selected verbatim from a controlled three-axis vocabulary:
   - **Domain** (1–2): 10 categories ≈ 37 leaves — Dev / Design / AI / Productivity / Hardware / Media & Culture / Learning / Science / News / Utilities
   - **Type** (exactly 1): 16 types in 5 semantic groups — Assets / Interactive / Content / Discovery / Identity
   - **Status** (0–2, off by default): to-read · starred · free · oss · paid · zh · en
3. **Title rewrite** — conservative, opt-in, default OFF; garbage titles only

Design principle: **metadata first**. Raindrop's list API returns title/link/domain/excerpt in bulk — no webpage fetching needed for ~90% of bookmarks. Deep-fetch (`fetch_bookmark_content`) is reserved for the low-confidence subset.

Tag output language is configurable: the skeleton ships with Simplified Chinese and English canonical columns, and the custom vocabulary file can rename any tag or switch the tag language per library.

## Highlights

1. **Metadata first, fetch only when unsure** — bulk list API returns title/link/domain/excerpt/type per bookmark; webpage fetching is a tier-2 fallback for the low-confidence subset, not the default path.
2. **Structured, reusable, and on-track** — tags are selected verbatim from a controlled two-layer vocabulary (universal skeleton + optional personal extension), with mutual-exclusion rules and boundary cases written down. The result is a consistent library whose tag taxonomy never drifts out of control.
3. **Safety first: preview before writing** — every batch is surfaced as a Before/After plan for review; before any write, one command snapshots every bookmark's current note/tags to an undo file; after writing, each item is read back and verified — it never silently mutates your library.
4. **Scales to large libraries** — checkpointed batches with a worklog state machine, resumable across sessions; 1,100+ bookmarks were processed this way without a single duplicate write.
5. **Idempotent and retry-hardened** — re-running `apply` only picks up unprocessed records; transient network/SSL failures are retried with exponential backoff (survived real outages mid-run).
6. **Honest about limits** — free Raindrop plans have no semantic search; pure JS-rendered sites may yield no parseable content; title rewriting stays opt-in because original titles often carry valid information.

## Install

Clone this repository into your WorkBuddy skills directory:

```bash
git clone https://github.com/ChosenXu/raindrop-bookmark-organizer.git \
  ~/.workbuddy/skills/raindrop-bookmark-organizer
```

Or copy the folder manually into `~/.workbuddy/skills/`.

## Prerequisites

- A Raindrop.io API token (free plan works): [app.raindrop.io/settings/integrations](https://app.raindrop.io/settings/integrations) → **For Developers** → Test tokens
- Export it before running: `export RD_API_TOKEN=<your-token>` — never commit it anywhere

## Usage

Mention Raindrop with an intent like "organize my Raindrop bookmarks" or "tidy up my bookmark library" (Chinese trigger phrases work as well), and the skill drives the workflow. See [`SKILL.md`](SKILL.md) for the full workflow (pull → classify → plan → apply → verify).

The batch engine is also usable standalone:

```bash
python scripts/organize.py pull --sample 30      # fetch next untagged batch
python scripts/organize.py plan --class <file>   # render Before/After plan (no writes)
python scripts/organize.py apply --class <file>  # verified write-back with undo snapshot
python scripts/organize.py stats                 # library progress
python scripts/rd_client.py --smoke              # client self-test with scratch data
```

Optionally copy `references/vocabulary.custom.example.md` → `vocabulary.custom.md` to rename tags, add private domains, or enable the status axis — no custom file needed to get started.

## Field notes (learned the hard way)

- MCP `update_bookmarks` tags object = incremental `{add, remove}` delta; REST `PUT /raindrop/{id}` tags array = full assignment. Bulk tagging → REST.
- `delete_tags` lies about success (`deleted:N` on nonexistent tags) — every destructive op needs readback verification.
- "Downloadable" ≠ "asset": book/manga libraries and mirror services are NOT tagged `asset-library` (they're content platforms / infrastructure). The vocabulary ships with an exclusion list.
- The `to-read` status applies to single articles only (the `type=article` signal), never site-level bookmarks.
- Frozen vocabulary ≠ frozen data: after any vocabulary revision, re-validate all pending class records before applying.

## Structure

```
SKILL.md                            # skill definition & workflow
README.md / README.zh-CN.md         # this file (English / Simplified Chinese)
CHANGELOG.md                        # bilingual changelog
LICENSE                             # MIT
docs/
  decisions.md                      # architecture decisions & rationale
references/
  vocabulary.md                     # universal three-axis skeleton (zh/en, normative)
  vocabulary.custom.example.md      # template for the personal extension layer
scripts/
  rd_client.py                      # REST client: bulk reads, verified writes, self-test
  organize.py                       # batch engine: pull / plan / apply / stats
```

## License

[MIT](LICENSE)
