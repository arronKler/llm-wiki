# Wiki 整合契约

## 先匹配再创建

依次检查：

1. 人工维护的 `wiki/_index.md`；
2. 生成的 `_catalog.md`、`_sources.md`、`_backlinks.json`；
3. title、`aliases`、旧 `also`、properties 与正文搜索；
4. 相关页面的一到两跳 wikilinks/backlinks。

把同一实体的别名并入现有页。仅在主题是 durable link target、跨来源重复出现、对一个来源非常核心或能写出至少一个有证据的完整段落时创建新页。不要为一处顺带提及建立空 stub。

## 使用标准 Markdown Properties

新知识页至少使用 `title`、`type`、`created`、`updated` 和 `sources`，并按需使用完整 schema：

```yaml
---
title: 页面标题
aliases: [Alternate name]
type: concept
domains: [work]
status: current
classification: internal
created: YYYY-MM-DD
updated: YYYY-MM-DD
as_of: YYYY-MM-DD
review_after: YYYY-MM-DD
confidence: medium
sources: [src-web-0123456789ab]
---
```

采用 schema 中定义的 controlled values。YAML frontmatter 是通用契约，并同时兼容 Obsidian Properties。让文件名尽量使用稳定的 lowercase kebab-case，让中文或多语言名称放在 `title` 和 `aliases`。让 `[[wikilinks]]` 通过 title/aliases 解析。

遇到旧页时：

- 保留 `also` 并把它用于别名匹配；除非显式迁移，不删除或批量改写它；
- 保留 `last_updated`；更新页面时可同时增加/更新现代 `updated`，不得令旧消费者失效；
- 保留旧 source ID，例如 `text-b185a6a06928`；不要只为格式统一而换 ID；
- 保留人工 `_index.md` 的组织、摘要和注释，只增量更新受影响条目。

## 按主张引用原始证据

让事实、数字、决定、个人陈述和时间敏感结论直接追到 raw source ID：

```markdown
支付转化率在 2026-06-30 为 18.4%。[^src-report-a1b2-p12] ^claim-7f3a

[^src-report-a1b2-p12]: `src-report-a1b2`，第 12 页，快照于 2026-07-14。
```

在一段共享同一证据时可做 paragraph-level citation；同段包含多个独立主张时分别引用。让 frontmatter `sources` 收齐正文实际使用的 source IDs。

不得只引用另一篇 agent-generated wiki 页或 output。Wiki link 用于导航，raw citation 用于证明。引用 derived OCR/转写时仍指向 raw source，并补充 derived locator。

短引原文只用于保留准确措辞或个人声音。明确标注说话者和上下文，不把 agent 改写冒充用户原话。

## 综合而不是追加

- 编辑前立即重读整页，把新证据放入最合适的主题段落。
- 让页面先给定义或结论，再写演变、关系、冲突与开放问题。
- 用具体日期、单位、owner、范围和归因替代“最近”“很多”“大家认为”等模糊词。
- 更新相关页的 wikilinks；只建立有解释价值的关系，不堆砌“相关链接”。
- 第三个独立子主题出现时考虑拆页；页面过薄时优先丰富而非继续拆分。
- 保持人类陈述、来源陈述和 agent interpretation 可区分。

## 保留冲突与时间

新证据与旧主张不一致时：

1. 保留双方文本、source ID、locator、published/captured/as-of 时间；
2. 检查是否只是定义、时间窗口、范围或粒度不同；
3. 将页面标为 `conflicted` 或加入显眼的冲突段落；
4. 仅依据 policy 中的 authority、明确的生效时间或用户裁决选择当前结论；
5. 把被替代内容标为 superseded，而不是删除历史证据。

指标必须写明定义、单位、窗口、时区、filters、system of record 与 `as_of`。决定必须区分背景、选项、证据、选择、owner、日期、理由与后续结果。

## 维护索引与可选前端视图

- 把 `_index.md` 当作人工可编辑的内容导航；增量编辑，不由 `rebuild` 覆盖。
- 把 `_catalog.md`、`_sources.md`、`_backlinks.json` 当作可删除重建的 state。
- 检测到 Obsidian workspace 时，让可选 `Wiki.base` 和 Properties 使用标准 YAML 字段。Bases/Dataview 只是视图，不作为知识正确性的依赖。
- 用 heading 或 block anchor 为重要 claim 提供稳定内部链接。

## 提交前检查

- 每个新页是否有来源且不是 stub；
- 每个 material claim 是否能到 raw；
- `sources`、aliases、状态、日期与敏感度是否一致；
- 冲突与不确定性是否可见；
- 人工 `_index.md` 是否保留；
- generated files 是否只由 rebuild 生成；
- 旧 `also`、`last_updated`、source IDs 是否仍可读；
- lint 是否无本次新增错误。
