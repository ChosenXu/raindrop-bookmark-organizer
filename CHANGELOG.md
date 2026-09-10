# Changelog / 更新日志

All notable changes to this skill are documented in this file.
本文件记录本技能所有重要变更。

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).
格式参考 Keep a Changelog，版本号遵循语义化版本（SemVer）。

## [1.1.1] - 2026-09-10

### Changed / 变更

- README consistency unification across the three sibling repositories (`raindrop-bookmark-organizer`, `eagle-untagged-organizer`, `eagle-tag-governance`): the Install table now uses the shared two-column layout (user-level + project-level) with the fixed agent row order, and Codex CLI's user-level directory is corrected from `~/.codex/skills/` to `~/.agents/skills/` (the cross-agent directory the other two repositories document); the `~/.agents/skills/` interop tip is aligned with the other READMEs; the clone example targets `~/.agents/skills/`; the intro now says "Agent Skills-compatible" and links `https://agentskills.io` (was the invalid `agentskills.my`), and "Copilot" is written in full as "GitHub Copilot".
  三仓库（`raindrop-bookmark-organizer`、`eagle-untagged-organizer`、`eagle-tag-governance`）README 一致性统一：安装表改为通用双列布局（用户级 + 项目级），Agent 行序固定；Codex CLI 用户级目录由 `~/.codex/skills/` 修正为 `~/.agents/skills/`（另两仓记载的跨平台通用目录）；`~/.agents/skills/` 互操作提示与另两仓对齐；clone 示例指向 `~/.agents/skills/`；开篇改为 "Agent Skills-compatible" 定位并修正链接（原 `agentskills.my` 为无效地址）；"Copilot" 统一写全称 "GitHub Copilot"。

### Notes / 说明

- Version bumped 1.1.0 → 1.1.1 (PATCH: documentation only); no workflow or write-behavior changes.
  版本 1.1.0 → 1.1.1（PATCH：纯文档）；工作流与写入行为无任何变化。

## [1.1.0] - 2026-09-10

### Added / 新增

- Cross-agent portability: the skill now presents itself as a platform-neutral Agent Skill (SKILL.md open standard); the README documents install paths for Claude Code, Codex CLI, Gemini CLI, Copilot, Cursor and WorkBuddy.
  跨 Agent 可移植：Skill 以平台中立的 Agent Skill 定位呈现（SKILL.md 开放标准）；README 载明 Claude Code、Codex CLI、Gemini CLI、Copilot、Cursor 与 WorkBuddy 的安装路径。
- Portable state directory: default `~/.raindrop-organizer/`, overridable via `RD_ORGANIZER_STATE_DIR`; the legacy `~/.workbuddy/raindrop-organizer/` is still honored when it exists (with a one-time migration hint).
  状态目录可移植：默认 `~/.raindrop-organizer/`，可用 `RD_ORGANIZER_STATE_DIR` 覆盖；旧目录 `~/.workbuddy/raindrop-organizer/` 存在时仍沿用（附一次性迁移提示）。

### Changed / 变更

- SKILL.md description and architecture table now say "an optional Raindrop MCP server" instead of the WorkBuddy-specific "MCP connector" wording; frontmatter adds `license: MIT`; version bumped 1.0.0 → 1.1.0.
  SKILL.md 描述与架构表改用通用的 "an optional Raindrop MCP server" 表述，替代 WorkBuddy 专属的 "MCP connector"；frontmatter 增加 `license: MIT`；版本 1.0.0 → 1.1.0。

## [1.0.0] - 2026-09-10

First release. Battle-tested end-to-end on a real 1,101-bookmark library: 37 batches, 100% tagged + annotated, zero structural violations.
首个版本。在真实的 1101 条书签库上端到端实测：37 个批次，100% 打标 + 写描述，零结构违规。

### Added / 新增

- Project skeleton: SKILL.md (v1.0.0), scripts/, references/, docs/.
  项目骨架：SKILL.md（v1.0.0）、scripts/、references/、docs/。
- Architecture: hybrid channels — REST API v1 for writes + bulk reads, MCP for content reads (`docs/decisions.md`).
  架构：混合通道——REST API v1 负责写入与批量读取，MCP 负责内容读取（`docs/decisions.md`）。
- `scripts/rd_client.py`: REST client with verification readback, smoke test (`--smoke`), rate probe (`--rate-probe`), network retry (4 attempts, exponential backoff).
  `scripts/rd_client.py`：REST 客户端，内置回读核验、自测（`--smoke`）、限流探测（`--rate-probe`）与网络重试（4 次指数退避）。
- `scripts/organize.py`: batch engine — `pull` (untagged sampling, worklog-aware, resumable), `plan` (Before/After review table, zero writes, role-aware validation), `apply` (undo snapshot → conflict guard → batches of 10 → stop-on-failure → readback verification → worklog state machine), `stats` (library progress).
  `scripts/organize.py`：批处理引擎——`pull`（未打标抽样、worklog 感知、可断点续跑）、`plan`（Before/After 审阅表、零写入、角色感知校验）、`apply`（undo 快照 → 冲突防御 → 每 10 条一批 → 失败即停 → 回读核验 → worklog 状态机）、`stats`（库进度）。
- Two-layer tag vocabulary: universal three-axis skeleton (`references/vocabulary.md`, zh/en) + optional personal extension (`vocabulary.custom.example.md` template) for private domains, renames, selective status tags, tag language and collection mapping. Hard cap 6 tags per bookmark.
  两层标签词表：通用三轴骨架（`references/vocabulary.md`，中英）+ 可选个人扩展（`vocabulary.custom.example.md` 模板），支持私有领域、改名、选择性状态标签、标签语言与合集映射。每条书签上限 6 个标签。
- Type axis grouped into 5 semantic families (资产/交互/内容/检索/身份) with mutual-exclusion rules and boundary cases (作品集 vs 媒体刊物 vs 素材库; 工具网站 vs 官网).
  形态轴归组为 5 个语义族（资产/交互/内容/检索/身份），附互斥规则与边界个案（作品集 vs 媒体刊物 vs 素材库；工具网站 vs 官网）。
- `docs/decisions.md`: 6 architecture decisions with rationale.
  `docs/decisions.md`：6 条架构决策及理由。

### Verified / 实测验证（2026-09-08 ~ 09-09，真实库）

- REST `PUT /raindrop/{id}` tags = full assignment/replace; MCP `update_bookmarks` tags object = incremental `{add, remove}` delta (probed with live seed + REST readback).
  REST `PUT /raindrop/{id}` 的 tags 数组为全量赋值/替换；MCP `update_bookmarks` 的 tags object 为增量 `{add, remove}`（临时数据实测 + REST 回读确认）。
- Rate limit: 40 rapid list GETs → zero 429s.
  限流：40 次连发列表 GET 零 429。
- `delete_tags` lies about success (`deleted:N` on nonexistent tags) — every destructive op needs readback verification.
  `delete_tags` 会谎报成功（不存在的标签也返回 `deleted:N`）——所有破坏性操作必须回读核验。
- Free-plan constraint: MCP semantic `search` is Pro-only; structural filters still work.
  免费版限制：MCP 语义 `search` 为 Pro 专属；结构化过滤仍可用。
- Full-library run: 1,101/1,101 bookmarks tagged + noted across 37 batches; retry with backoff survived real SSL-flap outages; undo snapshots covered every write.
  全库执行：1101/1101 条书签跨 37 批完成打标 + 写描述；指数退避重试扛过真实 SSL 瞬断；每次写入均有 undo 快照覆盖。
- Tier-2 deep-fetch round: 20/20 resolved via `fetch_bookmark_content` (5 corrections, incl. 2 material reclassifications).
  Tier-2 深抓轮次：20/20 经 `fetch_bookmark_content` 解决（5 处修正，含 2 处实质性改判）。

### Known limitations / 已知限制

- MCP `search` parameters (semantic search, misplaced/mistagged detection) require Raindrop Pro.
  MCP 的 `search` 参数（语义搜索、错位/错标检测）需要 Raindrop Pro。
- Pure JS-rendered sites may yield no parseable content even via `fetch_bookmark_content`.
  纯 JS 渲染的站点即使通过 `fetch_bookmark_content` 也可能抓不到可解析内容。
- Title rewriting stays opt-in and off by default — original titles often carry valid information.
  重命名保持 opt-in 且默认关闭——原始标题往往含有有效信息。

## [Unreleased]

_Nothing yet._
_暂无。_
