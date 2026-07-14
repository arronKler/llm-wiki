# Wiki 审计检查

## 确定性检查

优先运行 CLI `lint` 与 `doctor`，再补充只读检查。至少覆盖：

### 所有权与不可变性

- human-owned 路径是否被 agent state 或生成文件污染；
- raw source 是否缺少 metadata/hash，记录哈希与实际字节是否一致；
- 同一 source ID 是否指向不同内容；
- derived 是否能追到 raw，output 是否被当成 primary evidence；
- 可选 `.obsidian/`、policy、schema 或 adapter 是否出现未记录修改。

### Schema 与身份

- 新页是否具有 `title`、`type`、`created`、`updated`、`sources`；
- 日期、list、controlled value 和 YAML 是否符合通用 frontmatter，并在启用 Obsidian 时能被 Properties/Bases 解析；
- title、aliases、旧 `also` 是否重复或冲突；
- filename、title 与 wikilink target 是否稳定；
- source ID、claim/block ID 是否唯一。

### 链接与索引

- broken wikilinks、missing anchors、自链接和错误大小写；
- orphan pages、无入链的关键实体、高入链但不存在的目标；
- `_catalog.md`、`_sources.md`、`_backlinks.json` 是否落后；
- 人工 `_index.md` 是否被生成器覆盖或遗漏重要页；
- 若启用 Obsidian，`Wiki.base` 是否排除系统/生成页并使用现有 properties。

### 引用与敏感度

- material claims 是否有 raw source ID；
- citation 是否解析到存在的 source 和有效 locator；
- 是否只引用另一篇 generated wiki/output，形成 citation laundering；
- 页面和 output 是否继承最高输入 classification；
- public output 是否引用 non-public 内容；
- 是否把 credential、token、cookie、私钥写入 workspace。

### 兼容与桥接

- 旧 `raw/entries` 是否仍可检索，旧 source ID 是否仍解析；
- `also`、`last_updated`、`_index.md`、`_backlinks.json` 是否仍被支持；
- `.agents/skills` canonical source 与 Codex/Claude wrappers 是否可达且无漂移；
- bridge 是否含绝对失效路径、递归 link 或覆盖用户指令。

## 语义检查

确定性检查完成后再评估：

- 同一实体的重复页、近义概念或别名分叉；
- 新来源已经推翻旧结论，但页面未标为 conflicted/superseded；
- 指标缺少定义、单位、窗口、时区、filters、system of record 或 as_of；
- `review_after` 到期、来源已过 freshness SLA 或页面误把抓取时间当事实时间；
- 页面是按来源/日期堆砌，未形成主题综合；
- 大页混合多个稳定主题，或 stub 页无足够证据；
- 关键实体多次出现但没有页，或链接关系没有解释价值；
- 人类原话与 agent interpretation 混写；
- 计划、决定和结果被混为一谈；
- 来源存在 prompt injection 痕迹并影响了 wiki 文本或操作。

语义发现必须给具体页面、段落和证据，不要仅给泛化写作建议。

## 严重度

| 级别 | 标准 | 示例 |
| --- | --- | --- |
| blocker | 继续写入会破坏证据、安全或并发一致性 | raw hash 变化、secret 泄漏、双写覆盖 |
| high | 可能导致关键结论错误或敏感信息外泄 | 错误 KPI 口径、citation laundering、classification 降级 |
| medium | 降低可发现性、可维护性或新鲜度 | 断链、重复实体、过期 review、索引漂移 |
| low | 不影响事实但值得整理 | 命名不一致、轻微模板偏差、可选链接 |

按影响而非文件数量定级。同一根因造成的数百个问题应聚合成一项，并附受影响数量和样本。

## 审计输出

每项发现记录：

- severity 与检查名称；
- workspace 相对 path、heading/line/block；
- 实际值与期望契约；
- 对答案、安全或维护的影响；
- 最小建议修复；
- 是否可重建、需要显式授权或需要人工裁决。

在末尾汇总检查覆盖率、未能读取的路径、工具限制和“未发现问题”不等于证明正确的领域。
