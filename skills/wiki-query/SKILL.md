---
name: wiki-query
description: 从受管本地 Markdown wiki 中检索、比较、追踪关系并综合回答，提供逐主张来源、时间新鲜度、敏感度、冲突与证据缺口。Use when the user asks wiki 里有什么、某人或项目发生了什么、为何做某决定、指标如何定义、比较方案、准备 briefing/research/analysis，或 asks what the wiki knows, query, search, explain, compare, synthesize, investigate, or show evidence. 默认严格只读；不静默抓取外部资料，也不自动保存问答。
---

# Wiki Query

## 目标

从已经编译的 wiki 快速给出可追溯答案。优先复用累积的综合知识，只在需要核验时回到 raw 证据。

## 定位 workspace 与工具

1. 从用户提供的路径向上寻找 `.wiki/config.json`；未提供路径时从当前目录向上寻找。
2. 若只发现旧版 `wiki/_index.md`、`wiki/_backlinks.json` 或 `raw/entries/`，按 legacy 模式只读查询，不要求用户先迁移。
3. 从本 `SKILL.md` 所在目录定位 `../wiki-configure/scripts/wiki.py`，并使用 `python3 <wiki.py> --workspace <workspace-root> ...`；旧版 `--vault` 仍作为等价兼容参数。不得依赖当前工作目录。
   若 CLI 不存在，停止并提示用户重新安装完整 suite：`npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`。不要用无来源的临时检索替代受管查询。
4. 读取 `.wiki/config.json`、`.wiki/policy.md` 与 `wiki/_schema.md`；缺失时遵循最保守的只读和敏感度策略。

## 按需读取参考

- 在选择页面、扩大搜索、跟随图关系或读取 raw 前，读取 [references/retrieval.md](references/retrieval.md)。遇到大型 workspace、模糊实体、别名、旧索引或时序问题时必须读取。
- 在形成最终答案、比较表、briefing、引用或文件产物前，读取 [references/answer-contract.md](references/answer-contract.md)。遇到冲突、陈旧指标、推断、敏感信息或用户要求证据时必须读取。

## 执行工作流

### 1. 锁定问题

1. 提取主题、时间范围、业务口径、期望输出和“当前/历史”含义。仅在不同解释会实质改变答案时追问。
2. 把 query 保持为只读操作：不得修改页面、重建索引、写事件或保存问答。
3. 不把查询词、私人片段、公司数据或 wiki 摘要发往公共搜索或未批准外部服务。

### 2. 先导航再读正文

1. 先读 `wiki/_index.md`；再读 `_catalog.md`、`_sources.md` 和 `_backlinks.json` 中存在的文件。
2. 运行：

   ```text
   python3 <wiki.py> --workspace <workspace-root> search <query> --limit 15
   ```

3. 同时检索 title、`aliases`、旧 `also`、Properties、标题和 wikilinks。需要查来源卡片时增加 `--sources`。
4. 选取约 5–15 个高相关页面，优先覆盖不同证据链；跟随 1–2 跳 wikilink 与 backlinks。避免无目的读取整个 workspace。
5. 需要精确引文、核验争议、确认数字或回答“证据是什么”时，沿 source ID 和 locator 读取最小必要 raw 片段。不要把 raw 当作默认检索语料重新综合一切。

### 3. 评估证据

1. 检查每个关键主张是否可追到 raw source ID，而非只引用另一篇 agent 总结。
2. 比较 `as_of`、`review_after`、来源发布时间、抓取时间、authority、confidence 和 classification。
3. 保留口径差异、互相冲突的来源和未决问题。不要用“较新”自动替代“更权威”，也不要把相关性写成因果关系。
4. 对指标核对定义、单位、窗口、时区、过滤条件和 system of record。缺一项时显式降低结论强度。
5. 若用户要求最新信息而 wiki 已过 freshness SLA，先说明截至时间。仅在用户请求或上层 agent 规则要求外部刷新时使用允许的外部工具；不要把临时结果静默写回 workspace。

### 4. 形成答案

1. 先回答结论，再列支撑证据、冲突、推断和缺口。
2. 让 material claim 就近引用 `[[页面#标题]]` 以及 raw source ID/locator。对数字、决定、个人陈述和时间敏感结论采用 claim-level citation。
3. 标明 `as_of` 或“截至何时”，并把 agent 推断明确写为推断。
4. 保持输出敏感度不低于任何输入。不要在公共可分享输出中泄漏 personal、internal、confidential 或 restricted 证据。
5. 找不到答案时说明查过的范围、缺少的证据和下一步最小动作；不要猜测。

## 持久化边界

- 用户只问问题时仅在对话中回答。
- 用户明确要求报告、表格、Marp、Canvas 或其他文件时，把它写入 `outputs/`，注明 derived、classification、as_of 和来源；不要把 output 当作原始证据。
- 用户明确要求“把这次结论写回 wiki”时，把答案作为待整合材料交给 `wiki-ingest`，重新绑定到 raw source IDs，而不是让 query 直接修改 wiki。
- 需要导入新的网页、文件、会议或数据库结果时转交 `wiki-ingest`；需要修复索引或页面时转交 `wiki-maintain`。
