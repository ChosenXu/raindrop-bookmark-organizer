# Controlled Tag Vocabulary — 受控标签词表

This is the **default skeleton vocabulary**. It applies to any Raindrop.io library with zero configuration.

Personal overrides (private domains, collection mapping, status-axis on/off, language preference) live in a user-created `vocabulary.custom.md` — see `vocabulary.custom.example.md`. When a custom file exists, it **overrides and extends** this skeleton; when absent, this file alone governs.

Language of skeleton tags: explicit user instruction > invocation-language inheritance > default 简体中文. The English column below is the canonical translation; both refer to the same tag slot — never mix languages for the same tag on different bookmarks.

## Tag composition per bookmark（每条书签的标签配额）

| Axis | Count | Mandatory |
|---|---|---|
| 领域 Domain | 1–2 | yes |
| 形态 Type | 1 | yes |
| 状态 Status | 0–2（默认关闭，经 custom 文件开启） | no |
| 自由补充 Free | 0–2 | no |

**Hard cap: ≤6 tags per bookmark.** Never exceed; prefer dropping Free tags over dropping Domain/Type.

## Axis 1 · 领域 Domain（1–2 个）

Ten top-level domains, each usable as a tag on its own. Leaf tags are flat when written to Raindrop — the hierarchy below is only organizational.

| Domain | Leaf tags |
|---|---|
| 开发 dev | 前端 frontend · 后端 backend · 移动端 mobile · 组件库 ui-kit · 开发工具 dev-tools |
| 设计 design | UI 参考 ui-reference · 灵感集 inspiration · 图标 icons · 字体 fonts · 配色 color · 动效 motion · 排版 typography · 3D |
| AI | AI 工具 ai-tools · AI 资讯 ai-news · Agent · 模型评测 model-eval |
| 产品效率 productivity | 效率工具 tools · 笔记知识库 notes-pkm · 协作 collaboration · 自动化 automation |
| 数码硬件 hardware | 数码产品 gadgets · 智能家居 smart-home |
| 影音文化 media | 电影 film · 书籍 books · 游戏 games · 音乐 music |
| 阅读学习 learning | 课程 courses · 语言学习 languages · 科普 science-pop |
| 科学 science | 科研 research · 数学 math |
| 资讯 news | 科技资讯 tech-news · 设计资讯 design-news · 周刊日报 newsletters |
| 实用工具 utilities | 查询计算 calculators · 安全隐私 privacy |

Rules:
- Use a leaf tag when confident; fall back to the bare domain tag when not.
- Two Domain tags only when the bookmark genuinely spans both (e.g. 设计 + 开发 for a design-engineering blog).
- Domain leaves answer **"关于什么"**；形态 Type answers **"它是什么东西"**。当一个领域叶与某个 Type 同名（图标/字体/组件库）时，两者不得同时打——见下方互斥规则。

## Axis 2 · 形态 Type（必选 1 个）

What the bookmark **is** — decides how it will be used again. 16 types in 5 semantic groups; classify by group first ("是拿来用的 / 看的 / 取的 / 找的 / 认人的"), then pick the member. Tags are flat when written.

### A · 资产类 — 拿来取用的东西

| Type | Definition |
|---|---|
| 组件 UI 库 ui-kit | 可复用的界面组件集合 |
| 图标插画 icons-illustrations | 图标、插画素材页面 |
| 字体 fonts | 字型文件与字族展示页 |
| 模板 templates | 可套用的成品框架（网页、演示、简历、动效模板） |
| 素材库 assets-library | 多件可下载资产的集合（纹理、照片、音效、UI kit 等设计/创作素材） |

**素材库边界**：素材 = 供设计/创作**取用**的材料。面向消费的内容库（书库、漫画库、古籍库、游戏资源站）与基础设施服务（软件镜像源、代码托管）**不属于素材库**——前者按内容领域归类、形态用 `清单导航`（浏览/下载型）或对应内容形态，后者用 `工具网站`/`官网`。

### B · 交互类 — 拿来操作的东西

| Type | Definition |
|---|---|
| 工具网站 tool | 可操作的交互式工具：计算器、转换器、生成器、网页小游戏。**仅此而已**——营销官网、博客、杂志都不是工具网站 |
| 开源项目 open-source | 代码仓库与项目主页 |

### C · 内容类 — 拿来消费的东西

| Type | Definition |
|---|---|
| 媒体刊物 media | 持续发布内容的编辑型站点：新闻网站、杂志、**个人博客**。首页/栏目页/单篇文章都属此形态 |
| 文章教程 article | **单篇**可一口气读完的文章或教程页面 |
| 文档手册 docs | 参考文档、手册、百科、API 文档 |
| 视频 video | 视频内容页 |
| 书影记录 review | 条目型书影页面（豆瓣/IMDb 风格），记录看过的作品 |
| 数据报告 report | 报告、榜单、调研与数据集 |

### D · 检索类 — 帮你找到别的东西

| Type | Definition |
|---|---|
| 清单导航 directory | 指向别处的链接/条目汇编（导航站、榜单、片单、聚合页） |
| 社区论坛 community | 讨论与问答社区 |

### E · 身份类 — 认识"这是谁做的"

| Type | Definition |
|---|---|
| 作品集 portfolio | 个人或团队的自我展示与作品陈列（个人主页、studio 作品页） |
| 官网 official-site | 公司或产品的官方网站（含产品的营销首页） |

### Boundary rules（形态轴内部边界）

- **个人博客 vs 作品集**：博客是持续发内容的出版物 → `媒体刊物`（看内容）；主页是自我介绍与作品陈列 → E 组（看人看作品）。同一作者两者都有时，按**存的那一页**判。
- **官网 vs 工具网站**：描述工具的营销首页 → `官网`；工具本体（打开即用的 web app）→ `工具网站`。
- **作品集 vs 素材库**：陈列**自己的**作品 → `作品集`；第三方可取用资产的**集合** → `素材库`。灵感向的作品聚合站（收集多人的作品）→ `清单导航` 或 `素材库`，不打 `作品集`。
- Type=开源项目 时不加状态标签"开源"（若状态轴开启）。
- 判据提示：Raindrop 自动识别的单篇文章 `type=article`、URL 含 /blog/ /post/ /2024/ 式路径、摘要为正文开头——指向 `文章教程`；域名根路径/首页、about/work 类栏目——指向 E 组；正文式长摘要+持续更新感——指向 `媒体刊物`。

## Axis 3 · 状态 Status（可选 0–2 个；**默认关闭，按标签选择性开启**）

> 待读 to-read · 精华 starred · 免费 free · 开源 oss · 付费 paid · 中文 zh · 英文 en

**Default: the whole axis is off.** Enable via `vocabulary.custom.md` in one of two ways:

- `status_axis_enabled: true` — all seven tags active;
- `status_tags: [...]` — a selective list, e.g. `[待读, 精华]`.

**Selective-enable rule:** 工作流标签（待读/精华）只适用于**单篇文章页**（形态 = 文章教程，且是具体某一篇，可通过 Raindrop `type=article`、文章式 URL 路径、正文式摘要识别）。**站点级书签——新闻网站、杂志首页、专栏、博客首页——一律不打待读/精华**，无论其内容多值得读。属性标签（免费/开源/付费/中文/英文）适用于任何形态。开启的标签仍按"明确为真才打，存疑不打"执行。

## Free supplementary tags（自由补充标签，0–2 个）

For anything the skeleton cannot express: concrete tech names, project names, niches.

- Proper nouns keep original spelling, lowercase: `react` `figma` `mcp` `tailwind`
- Must not duplicate or paraphrase any skeleton tag
- ≤2 per bookmark

## Mutual-exclusion rules（轴间互斥规则）

同名/近义标签不得跨轴重复打。每条规则给出"打哪个"的判据：

| 冲突对 | 规则 |
|---|---|
| Domain 叶 `图标` / `字体` / `组件库` ↔ Type `图标插画` / `字体` / `组件 UI 库` | **资产本体打 Type，话题内容打 Domain 叶。** 图标站/字体站/组件库站：Type 承载形式，Domain 只打到 `设计` / `开发` 大类。图标/字体/组件类的**文章、教程、资讯**：Type 是文章/视频等，用 Domain 叶表达主题 |
| Domain ~~开源项目~~ ↔ Type `开源项目` | Domain 叶已删除。GitHub 仓库等直接 Type=开源项目，领域按内容打（开发/设计/AI…） |
| Domain ~~素材站点~~ ↔ Type `素材库` | Domain 叶已删除。素材站按内容领域打（设计/影音文化…），形式打 Type=素材库 |
| Domain ~~教程~~ ↔ Type `文章教程` | Domain 叶已删除。教程类内容 Type=文章教程/视频，是否学习用途由领域（阅读学习）或自由标签表达 |
| Status `开源` ↔ Type `开源项目` | 状态轴开启时也不并列，Type 已含此义 |

## Prohibitions（禁止事项）

- No tag outside Domain/Type/Status/Free roles
- No language mixing for the same skeleton tag across bookmarks
- No uppercase in Free tags (proper nouns excepted, keep original casing)
- No more than 6 tags total
- No tag pair listed in the mutual-exclusion table
- Never invent a new skeleton tag — a skeleton gap is solved by Free tags, and recurring gaps should be proposed as skeleton amendments in a new version
