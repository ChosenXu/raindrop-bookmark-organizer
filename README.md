# raindrop-bookmark-organizer

[WorkBuddy](https://www.workbuddy.cn) skill that batch-organizes a Raindrop.io library with a proven three-step workflow: **命名（可选）→ 写描述 → 打标签**.

Battle-tested on a real 1,101-bookmark library — 37 batches, zero structural violations, every write verified by readback.

## What it does

For every untagged bookmark it produces:

- **Note** — 1–2 sentences: what it is + when you'll reach for it (40–80 字中文 / 30–60 words English)
- **Tags** — up to 6, from a controlled three-axis vocabulary:
  - **Domain** (1–2): 10 categories ≈ 37 leaves — 开发 / 设计 / AI / 产品效率 / 数码硬件 / 影音文化 / 阅读学习 / 科学 / 资讯 / 实用工具
  - **Type** (exactly 1): 16 types in 5 groups — 资产 / 交互 / 内容 / 检索 / 身份
  - **Status** (0–2, off by default): 待读 · 精华 · 免费 · 开源 · 付费 · 中文 · 英文
- **Title rewrite** — conservative, opt-in, default OFF; garbage titles only

Design principle: **metadata first**. Raindrop's list API returns title/link/domain/excerpt in bulk — no webpage fetching needed for ~90% of bookmarks. Deep-fetch is reserved for the low-confidence subset.

## Quick start

1. Get an API token: [app.raindrop.io/settings/integrations](https://app.raindrop.io/settings/integrations) → **For Developers** → Test tokens
2. Export it: `export RD_API_TOKEN=<your-token>` (never commit it anywhere)
3. In WorkBuddy, just ask: *"帮我整理 Raindrop 书签"* or *"organize my raindrop bookmarks"*

Optionally copy `references/vocabulary.custom.example.md` → `vocabulary.custom.md` to rename tags, add private domains, or enable the status axis.

## How a full-library run works

1. **pull** — sample untagged bookmarks (worklog-aware, resumable across sessions)
2. **classify** — structured records: `domain_tags` / `type` / `status` / `free` (roles are explicit, so leaf/type homonyms like 字体 never get confused)
3. **plan** — Before/After table for review, zero writes
4. **apply** — undo snapshot → conflict guard (skips already-tagged) → batches of 10 → readback verification → worklog advances (`applied` / `unverified` / `conflict-skip`)

```bash
python scripts/organize.py pull --sample 30     # fetch next batch
python scripts/organize.py plan --class <file>  # render review plan (no writes)
python scripts/organize.py apply --class <file> # verified write-back
python scripts/organize.py stats                # library progress
python scripts/rd_client.py --smoke             # client self-test with scratch data
```

## Safety model

- **Undo snapshot** before every write batch (`apply-*.undo.json`, stored outside the repo)
- **Readback verification** — the `deleted`/`updated` counts alone are never trusted (Raindrop's `delete_tags` lies about success; confirmed by probe)
- **Conflict guard** — bookmarks that already have tags are skipped, never overwritten
- **Idempotent** — re-running `apply` only picks up unprocessed records; safe after crashes (survived real SSL-flap outages)
- **Network retry** — 4 attempts with exponential backoff on transient failures

## Field notes (learned the hard way)

- MCP `update_bookmarks` tags object = incremental `{add, remove}` delta; REST `PUT /raindrop/{id}` tags array = full assignment. Bulk tagging → REST.
- Free Raindrop plans cannot use MCP semantic `search` — structural filters only.
- "Downloadable" ≠ "asset": book/manga libraries and mirror services are NOT `素材库` (they're content platforms / infrastructure). The vocabulary ships with an exclusion list.
- `待读` (to-read) applies to single articles only (`type=article` signal), never site-level bookmarks.
- Frozen vocabulary ≠ frozen data: after any vocabulary revision, re-validate all pending class records before applying.

## Requirements

- Python 3.10+ (stdlib only, no dependencies)
- A Raindrop.io API token (free plan works)
- WorkBuddy (for the skill workflow) — or use `scripts/` standalone

## License

MIT
