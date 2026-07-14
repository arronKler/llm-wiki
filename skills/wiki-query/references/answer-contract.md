# 回答与引用契约

## 采用答案优先结构

根据问题复杂度使用最小充分结构：

```markdown
结论：直接回答用户的问题。

证据：列出最关键的 2–5 条，并就近引用 wiki 页与 raw source locator。

冲突与限制：说明口径、时间、新鲜度、反例和缺失证据。

截至：YYYY-MM-DD 或“当前 wiki 未记录可靠 as_of”。
```

简单事实不必机械套模板。复杂比较、决策 briefing 或分析必须把事实、推断和建议分开。

## 就近提供双层引用

同时提供：

1. 用 `[[页面标题#相关标题]]` 或明确 workspace 相对路径帮助用户在任意 Markdown 前端导航；启用 Obsidian 时这些 wikilinks 可直接跳转；
2. 用 raw `source_id` + locator 证明 material claim。

示例：

```markdown
Q2 支付转化率记录为 18.4%，口径排除退款订单。
（[[支付转化率#2026 Q2]]；`src-report-a1b2` p.12；as_of 2026-06-30）
```

若只有 wiki 综合而找不到 raw citation，明确写“二手综合，原始证据未解析”，并降低 confidence。不要让多个 agent-generated 页面互相引用形成虚假证据链。

## 标记证据状态

使用准确措辞：

- “来源明确记录……”：直接证据；
- “多个来源一致支持……”：独立来源相互印证；
- “这表明/可以推断……”：agent interpretation；
- “wiki 中存在冲突……”：保留双方；
- “未找到……”：证据缺口；
- “截至 YYYY-MM-DD……”：时间边界。

不要把 absence of evidence 写成 evidence of absence，不要把相关性写成因果，不要把计划写成已完成。

## 比较与业务数据

比较时先固定相同维度：定义、时间、范围、数据源、单位、成本、风险和未知项。没有同口径证据时不要给虚假的精确排序。

对 KPI/经营数据同时给出：

- metric definition 与 system of record；
- 值、单位、窗口、filters、timezone、as_of；
- query/source ID 与 locator；
- freshness、confidence、异常或冲突。

对建议明确区分“wiki 中的事实”“基于事实的推断”“建议动作”。

## 控制引用与原文

只引用支撑结论的最少原文。对个人、会议或消息中的原话保留说话者和上下文；避免因截断改变含义。若用户无权查看某个敏感细节，不通过引用绕过 classification。

## 处理外部刷新

用户要求“最新/现在”而 wiki 过期时：

1. 先说明 wiki 的 as_of；
2. 使用当前 agent 允许的外部工具获取 public 或获批资料；
3. 不在外部查询中泄露 non-public 内容；
4. 把临时外部结果与 workspace 证据分开引用；
5. 除非用户明确要求 ingest，不把临时结果写回 wiki。

## 生成持久化 output

仅在用户明确要求文件时写入 `outputs/`。为输出记录 title、type、classification、created/updated、as_of、sources，并标注 derived。让输出引用 raw source IDs，不把它作为后续事实的唯一来源。

用户要求把新综合变成长期知识时，交给 ingest 流程重新检查页面匹配、冲突和 raw citations。
