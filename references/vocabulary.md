# Controlled Tag Vocabulary — 受控标签词表

This is the **default skeleton vocabulary**. It applies to any Raindrop.io library with zero configuration.

Personal overrides (private domains, collection mapping, status-axis on/off, language preference) live in a user-created `vocabulary.custom.md` — see `vocabulary.custom.example.md`. When a custom file exists, it **overrides and extends** this skeleton; when absent, this file alone governs.

Language of skeleton tags: explicit user instruction > invocation-language inheritance > default 简体中文. The English column below is the canonical translation; both refer to the same tag slot — never mix languages for the same tag on different bookmarks.

## Tag composition per bookmark（每条书签的标签配额）

| Axis | Count | Mandatory |
|---|---|---|
| 领域 Domain | 1–2 | yes |
| 形态 Type | 1 | yes |
| 状态 Status | 0–2 | no |
| 自由补充 Free | 0–2 | no |

**Hard cap: ≤6 tags per bookmark.** Never exceed; prefer dropping Free tags over dropping Domain/Type.

## Axis 1 · 领域 Domain（1–2 个）

Ten top-level domains, each usable as a tag on its own. Leaf tags are flat when written to Raindrop — the hierarchy below is only organizational.

| Domain | Leaf tags |
|---|---|
| 开发 dev | 前端 frontend · 后端 backend · 移动端 mobile · 组件库 ui-kit · 开发工具 dev-tools · 开源项目 open-source |
| 设计 design | UI 参考 ui-reference · 灵感集 inspiration · 图标 icons · 字体 fonts · 配色 color · 动效 motion · 排版 typography · 3D |
| AI | AI 工具 ai-tools · AI 资讯 ai-news · Agent · 模型评测 model-eval |
| 产品效率 productivity | 效率工具 tools · 笔记知识库 notes-pkm · 协作 collaboration · 自动化 automation |
| 数码硬件 hardware | 数码产品 gadgets · 智能家居 smart-home |
| 影音文化 media | 电影 film · 书籍 books · 游戏 games · 音乐 music |
| 阅读学习 learning | 教程 tutorial · 课程 courses · 语言学习 languages · 科普 science-pop |
| 科学 science | 科研 research · 数学 math |
| 资讯 news | 科技资讯 tech-news · 设计资讯 design-news · 周刊日报 newsletters |
| 实用工具 utilities | 查询计算 calculators · 安全隐私 privacy · 素材站点 assets |

Rules:
- Use a leaf tag when confident; fall back to the bare domain tag when not.
- Two Domain tags only when the bookmark genuinely spans both (e.g. 设计 + 开发 for a design-engineering blog).

## Axis 2 · 形态 Type（必选 1 个）

What the bookmark **is** — decides how it will be used again.

> 工具网站 tool · 组件 UI 库 ui-kit · 图标插画 icons · 字体 fonts · 模板 templates · 开源项目 open-source · 文章教程 article · 文档手册 docs · 视频 video · 书影记录 review · 清单导航 directory · 社区论坛 community · 数据报告 report

Rules:
- Exactly one Type per bookmark. Pick the dominant form.
- 书影记录 review covers Douban/IMDb-style pages for watched films and read books.

## Axis 3 · 状态 Status（可选 0–2 个；可通过 custom 文件整体关闭）

> 待读 to-read · 精华 starred · 免费 free · 开源 oss · 付费 paid · 中文 zh · 英文 en

待读/星级 are personal workflow tags; 免费/开源/付费/中文/英文 are property tags. Apply only when clearly true — when in doubt, omit.

## Free supplementary tags（自由补充标签，0–2 个）

For anything the skeleton cannot express: concrete tech names, project names, niches.

- Proper nouns keep original spelling, lowercase: `react` `figma` `mcp` `tailwind`
- Must not duplicate or paraphrase any skeleton tag
- ≤2 per bookmark

## Prohibitions（禁止事项）

- No tag outside Domain/Type/Status/Free roles
- No language mixing for the same skeleton tag across bookmarks
- No uppercase in Free tags (proper nouns excepted, keep original casing)
- No more than 6 tags total
- Never invent a new skeleton tag — a skeleton gap is solved by Free tags, and recurring gaps should be proposed as skeleton amendments in a new version
