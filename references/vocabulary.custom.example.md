# Personal Vocabulary Extension — 个人词表扩展（模板）

Copy this file to `vocabulary.custom.md` in the same directory and edit it. Without a `vocabulary.custom.md`, the default `vocabulary.md` applies as-is.

Every field is optional. Anything omitted falls back to the default skeleton.

```markdown
## Language
# Skeleton tag language: zh (default) | en
tag_language: zh

## Status axis
# Set false to disable the whole Status axis
status_axis_enabled: true

## Private domains（私有领域大类）
# Append to the ten default domains; same two-level style, flat when written.
domains_append:
  - domain: 求职招聘 career
    leaves: [简历 resume, 面试 interview, 职位 jobs]
  # - domain: 健康生活 health
  #   leaves: [健身 fitness, 食谱 recipes]

## Domain renames（领域改名）
# Rename a default domain or leaf for personal taste; keys must match the default.
# domain_renames:
#   数码硬件: 硬件

## Collection mapping（合集映射，可选增强）
# When present, the skill additionally suggests a target collection for each
# bookmark (suggestion only — it never moves bookmarks on its own).
# Left side: tag (domain or leaf). Right side: your Raindrop collection name.
collection_mapping:
  设计: Design
  开发: Code
  AI: AI
  电影: Douban
  书籍: Douban
  游戏: Game
  数码硬件: Gadget
  实用工具: Site
  资讯: Information
  阅读学习: Study
  科学: Science
  影音文化: Watch
```

Notes:

- `collection_mapping` values must match collection titles exactly as they appear in your Raindrop.
- Renames and appends never delete default tags; they only change what gets written for you.
- Keep this file out of any public fork if it reveals personal workflow details.
