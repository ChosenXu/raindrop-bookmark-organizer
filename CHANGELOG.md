# Changelog / 更新日志

All notable changes to this skill are documented in this file.
本文件记录本技能所有重要变更。

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).
格式参考 Keep a Changelog，版本号遵循语义化版本（SemVer）。

## [1.2.0] - 2026-09-23

### Added / 新增

- Rate-limit resilience in `rd_client`: HTTP 429 responses are now retried with exponential backoff (honoring the `Retry-After` header when present) instead of aborting immediately, and the inter-request pacing adapts upward after a 429 so subsequent calls slow down automatically.
  `rd_client` 的限流韧性：HTTP 429 响应改为指数退避重试（有 `Retry-After` 头时遵循之），不再立即中止；且 429 之后请求间隔自动调大，后续调用随之减速。
- Connection reuse: the REST client keeps one persistent HTTPS connection per run (`http.client`), so a full-library pagination no longer pays a TCP+TLS handshake per request. Stale/broken connections are rebuilt transparently and retried.
  连接复用：REST 客户端每次运行维持一条 HTTPS 长连接（`http.client`），全库分页拉取不再为每个请求付出 TCP+TLS 握手开销；失效连接透明重建并重试。

### Changed / 变更

- State files (`sample-*.json`, `plan-*.md`, undo snapshots, `worklog.jsonl`) are now created with owner-only permissions (0600) and fsync'd on write — they carry full bookmark metadata and are no longer readable by other local users under a permissive umask. Existing files created 0644 by earlier versions are healed to 0600 automatically on the next write.
  状态文件（`sample-*.json`、`plan-*.md`、undo 快照、`worklog.jsonl`）改为属主专属权限（0600）创建并强制 fsync——这些文件含全量书签元数据，不再因宽松 umask 而被本机其他用户读取。旧版本创建的 0644 文件会在下次写入时自动愈合为 0600。
- A torn/corrupt worklog line (e.g. after a crash mid-append) is skipped with a warning instead of crashing every subcommand (`pull`/`apply`/`stats`).
  崩溃导致的半行/损坏 worklog 记录改为警告并跳过，不再让所有子命令（`pull`/`apply`/`stats`）集体崩溃。
- Markdown plan tables escape newlines, tabs and pipes in every cell (title, note, tags, tier…), so a bookmark title can no longer inject rows or columns into the review plan.
  Markdown 计划表的所有单元格（标题、备注、标签、层级……）统一转义换行、制表符与竖线，书签标题再也无法向审阅计划注入行或列。
- `apply --limit` and `pull --sample` validate their values up front (`--limit >= 0`, `--sample >= 1`); `--sample 0` no longer crashes with ZeroDivisionError and a negative limit no longer silently truncates from the tail.
  `apply --limit` 与 `pull --sample` 改为入口校验（`--limit >= 0`、`--sample >= 1`）；`--sample 0` 不再触发除零崩溃，负 limit 不再静默从尾部截断。
- Regenerable review artifacts (`sample-*.json`, `plan-*.md`) older than 30 days are pruned automatically on `pull`/`stats`. Undo snapshots and the worklog are never pruned.
  可再生的审阅产物（`sample-*.json`、`plan-*.md`）超过 30 天后在 `pull`/`stats` 时自动清理。undo 快照与 worklog 永不清理。
- Minor efficiency: classification records are flattened once per record and shared between validation and plan rendering (previously computed twice); `list_all` stops as soon as the reported total count is reached (no extra empty page when the library size is an exact multiple of the page size).
  轻量提速：每条分类记录只展开一次，供校验与计划渲染共用（原先计算两遍）；`list_all` 在达到响应报告的总数后立即停止（库大小恰为页大小整数倍时不再多发一次空页）。

### Notes / 说明

- Follow-up to the 2026-09-22 security review: implements the P2 (low-severity) findings. The per-write readback verification and 3-calls-per-item pattern are unchanged by design (they are this skill's core safety guarantee); the TOCTOU window in the conflict guard is now documented as a known limitation (run `apply` while no other client is writing).
  系 2026-09-22 安全审查的 P2（低危）跟进。逐条写入的读回核验与每条 3 次调用的模式**有意保持不变**（它们是本 skill 的核心安全保证）；冲突护栏的 TOCTOU 窗口改为文档化已知限制（请在无其他客户端写入时运行 `apply`）。
- No breaking changes: command-line interfaces, worklog format and state file locations are unchanged.
  无破坏性变更：命令行接口、worklog 格式与状态文件位置均不变。

## [1.1.3] - 2026-09-23

### Fixed / 修复

- `apply --what` values are now validated up front: unknown or empty values (e.g. `--what tag`) exit with an error before any API call, instead of silently sending an empty PUT and recording a false `applied` status in the worklog for bookmarks that were never written.
  `apply --what` 取值改为入口处校验：未知或空值（如 `--what tag`）在发出任何 API 请求前即报错退出，不再静默发送空 PUT、把从未写入的书签以假 `applied` 状态记进 worklog。
- Bookmark ids from the class file are coerced to integers and non-int ids are skipped (`invalid-skip`); `rd_client` read/write methods (`get`/`update`/`list_page`/`delete_collection`) now reject non-integer ids before URL interpolation. This closes the API path-injection surface where a crafted class file (e.g. a string id like `"123/.."`) could steer requests to arbitrary endpoints. Resume matching now prefers the int-normalized worklog key, so records keyed by a string id are correctly recognized as done and unparseable ids become terminal instead of re-reporting on every run.
  class 文件中的书签 id 强制转为整数，非整数 id 直接跳过（`invalid-skip`）；`rd_client` 的读写方法（`get`/`update`/`list_page`/`delete_collection`）在拼接 URL 前拒绝非整数 id。由此封堵 API 路径注入面——被构造的 class 文件（如字符串 id `"123/.."`）原本可能把请求导向任意端点。断点续跑匹配改为优先整数化的 worklog 键：字符串 id 的记录能被正确识别为已完成，无法解析的 id 成为终态，不再每次重跑都重复报 skip。
- `apply` now re-runs `validate()` on every record before writing (previously only `plan` validated): records edited after the plan step can no longer bypass the controlled-vocabulary rules (tag cap, mutual exclusion, domain membership) and write illegal tags directly into the library.
  `apply` 写入前对每条记录复跑 `validate()`（原先仅 `plan` 校验）：plan 之后被再编辑的 class 文件再也无法绕过受控词表规则（标签上限、互斥、领域成员资格）把非法标签直写进库。
- The undo snapshot is now flushed to disk BEFORE every single write instead of every 10 items: an interrupted run (Ctrl-C, kill) can no longer leave the most recent ≤9 written bookmarks without rollback data.
  undo 快照改为每条写入**之前**即落盘（原先每 10 条才落盘一次）：中断的执行（Ctrl-C、kill）不会再让最近 ≤9 条已写入的书签失去回滚数据。
- `rd_client.update()` refuses to send an update when all fields are None (empty-payload guard), and `flatten()` degrades safely on malformed input (non-list `proposed_tags`, non-string `type`) so `validate()` can flag the record instead of crashing.
  `rd_client.update()` 在三个字段全为 None 时拒绝发送更新（空载荷防护）；`flatten()` 对畸形输入（`proposed_tags` 非列表、`type` 非字符串）安全降级，让 `validate()` 能标红该记录而不是直接崩溃。

### Notes / 说明

- Security review follow-up (4 medium findings fixed; report of 2026-09-22). New worklog state `invalid-skip` is terminal, like `conflict-skip`: reclassify the item and re-run the plan→apply cycle. No workflow changes for valid inputs.
  系安全审查跟进（修复 4 项中危发现；审查报告 2026-09-22）。新增 worklog 状态 `invalid-skip` 与 `conflict-skip` 一样为终态：重新分类该条目并重跑 plan→apply 循环即可。对合法输入而言工作流无任何变化。

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
