# Raindrop Bookmark Organizer

[English](README.md) | 简体中文

一个跨平台的 [Agent Skill](https://agentskills.my/)，用经过实战验证的三步工作流批量整理 [Raindrop.io](https://raindrop.io/) 书签库——**命名（可选）→ 写描述 → 打标签**。可在任何支持 SKILL.md 标准的 Agent 中使用（Claude Code、Codex CLI、Gemini CLI、Copilot、Cursor、WorkBuddy…）。已在真实的 1101 条书签库上端到端跑通：37 个批次，100% 打标 + 写描述，零结构违规。

## 它能做什么

针对每条未打标签的书签，它会产出：

1. **描述（note）** —— 1–2 句话：是什么 + 什么时候用得上（中文 40–80 字 / 英文 30–60 词）
2. **标签** —— 最多 6 个，从三轴受控词表中逐字原样选取：
   - **领域**（1–2 个）：10 大类 ≈ 37 叶——开发 / 设计 / AI / 产品效率 / 数码硬件 / 影音文化 / 阅读学习 / 科学 / 资讯 / 实用工具
   - **形态**（恰好 1 个）：5 组 16 类——资产 / 交互 / 内容 / 检索 / 身份
   - **状态**（0–2 个，默认关闭）：待读 · 精华 · 免费 · 开源 · 付费 · 中文 · 英文
3. **命名（title）** —— 保守的 opt-in，默认关闭；只改垃圾标题

设计原则：**元数据优先**。Raindrop 批量列表 API 自带 title/link/domain/excerpt——约 90% 的书签无需抓取网页；深抓（`fetch_bookmark_content`）只留给低置信度子集。

## 核心优势

1. **元数据优先，拿不准才深抓** —— 批量列表 API 一次返回 title/link/domain/excerpt/type；抓网页只是低置信度子集的 tier-2 兜底，不是默认路径。
2. **结构化、可复用、不跑偏** —— 标签从两层受控词表（通用骨架 + 可选个人扩展）中逐字原样选取，互斥规则与边界个案白纸黑字写进词表。整理出来的库风格统一，标签体系不会越滚越乱。
3. **安全第一，先预览后写入** —— 每批都以 Before/After 计划呈现供你审阅；写入前一条命令把每条书签当前的 note/标签快照进 undo 文件；写完逐条回读校验——不会悄无声息地乱改你的库。
4. **大库也能扛** —— 带 worklog 状态机的断点续跑分批处理，可跨会话接力；1100+ 条书签就是这样跑完的，没有一次重复写入。
5. **幂等 + 重试加固** —— 重跑 `apply` 只拾取未处理记录；瞬时网络/SSL 故障按指数退避自动重试（真实断网中途恢复过）。
6. **坦诚说明限制** —— 免费版 Raindrop 没有语义搜索；纯 JS 渲染的站点可能抓不到可解析内容；重命名保持 opt-in，因为原始标题往往含有有效信息。

## 安装

将本仓库克隆到你所用 Agent 的 skills 目录：

```bash
git clone https://github.com/ChosenXu/raindrop-bookmark-organizer.git \
  <skills-dir>/raindrop-bookmark-organizer
```

| Agent | skills 目录 |
|---|---|
| Claude Code | `~/.claude/skills/`（个人级）或 `.claude/skills/`（项目级） |
| Codex CLI | `~/.codex/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| GitHub Copilot | `.github/skills/` |
| Cursor | `.cursor/skills/`（仅项目级） |
| WorkBuddy | `~/.workbuddy/skills/` |

> `.agents/skills/` 可作为大多数 Agent 的通用回退目录。

## 前置条件

- Raindrop.io API token（免费版可用）：[app.raindrop.io/settings/integrations](https://app.raindrop.io/settings/integrations) → **For Developers** → Test tokens
- 运行前导出：`export RD_API_TOKEN=<你的token>` —— 绝不提交到任何仓库

## 使用

在对话中提到 Raindrop / 书签并带上整理意图，如"帮我整理 Raindrop 书签" / "organize my raindrop bookmarks"，Skill 会驱动整个工作流。完整流程（pull → classify → plan → apply → verify）见 [`SKILL.md`](SKILL.md)。

批处理引擎也可以独立使用：

```bash
python scripts/organize.py pull --sample 30      # 拉取下一批未打标书签
python scripts/organize.py plan --class <文件>    # 渲染 Before/After 审阅计划（零写入）
python scripts/organize.py apply --class <文件>   # 带快照的核验写回
python scripts/organize.py stats                 # 库进度
python scripts/rd_client.py --smoke              # 客户端自测（临时数据）
```

可选：把 `references/vocabulary.custom.example.md` 复制为 `vocabulary.custom.md` 来改名标签、追加私有领域或开启状态轴——不建 custom 文件也能直接上手。

## 实战笔记（踩坑换来的）

- MCP `update_bookmarks` 的 tags object 是增量语义 `{add, remove}`；REST `PUT /raindrop/{id}` 的 tags 数组是全量赋值。批量打标 → 走 REST。
- `delete_tags` 会谎报成功（不存在的标签也返回 `deleted:N`）——所有破坏性操作都要回读核验。
- "可下载" ≠ "素材"：书库/漫画库和镜像源不是 `素材库`（它们是内容平台 / 基础设施）。词表里附带了排除清单。
- `待读` 只用于单篇文章页（看 `type=article` 信号），站点级书签绝不打。
- 词表冻结 ≠ 分类数据冻结：词表任何修订后，apply 前要对所有待写分类记录重新校验。

## 目录结构

```
SKILL.md                            # Skill 定义与工作流
README.md / README.zh-CN.md         # 本文件（英文 / 简体中文）
CHANGELOG.md                        # 双语更新日志
LICENSE                             # MIT
docs/
  decisions.md                      # 架构决策与理由
references/
  vocabulary.md                     # 通用三轴骨架词表（中英，规范目标）
  vocabulary.custom.example.md      # 个人扩展层模板
scripts/
  rd_client.py                      # REST 客户端：批量读、核验写、自测
  organize.py                       # 批处理引擎：pull / plan / apply / stats
```

## 许可证

[MIT](LICENSE)
