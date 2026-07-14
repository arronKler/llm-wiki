# Workspace 契约与可选 Obsidian 集成

CLI 的旧版 `--vault` 参数仍作为 `--workspace` 的等价别名，不要求存在 `.obsidian/`。Markdown 与本地文件是权威层；Obsidian 只是可选前端。

## 默认层级

| 路径 | owner | 规则 |
| --- | --- | --- |
| `data/`, `inbox/`, `notes/` | human | 可读；仅在用户明确指定内容时写入 |
| `raw/sources/` | capture tool | exclusive-create、append-only，旧版本永不修改 |
| `raw/derived/` | agent/tool | OCR、转写、规范化；可重建且必须回溯 raw |
| `wiki/` | agent | 可维护的长期综合知识 |
| `outputs/` | agent | 报告、表格、slides 等 derived deliverables |
| `.wiki/` | system | config、policy、events、transactions、state |
| `.obsidian/` | human/app | 默认不修改 |

在 `.wiki/config.json` 中映射实际路径。已有 workspace 可以把其他 glob 声明为 human-owned 或 agent-owned；不要为追求默认目录而移动内容。

把 Markdown wiki 视为权威综合层。把 FTS、vector、qmd、Dataview、Bases 结果和 generated catalogs 视为可重建索引或视图，而非事实来源。

## 系统文件

采用以下职责：

- `.wiki/config.json`：版本、路径映射、搜索 backend 和有限的运行选项；
- `.wiki/policy.md`：authority、classification、external tool 与写入边界；
- `wiki/_schema.md`：页面类型、Properties、citation 和写作规则；
- `.wiki/events/`：一操作一事件文件；
- `.wiki/transactions/`：写前 hash、候选 patch 和提交状态；
- `.wiki/state/`：锁、缓存与其他可重建状态；
- `wiki/_index.md`：人工维护的内容导航；
- `wiki/_catalog.md`、`_sources.md`、`_backlinks.json`：生成导航；
- `wiki/Wiki.base`：仅在检测到 Obsidian workspace 时创建的可选 Bases 视图。

不要让 CLI 覆盖 `_index.md`。不要要求 log 由多个 agent append；需要时间线时从 event files 生成。

## 页面 Properties

新知识页至少包含 `title`、`type`、`created`、`updated`、`sources`。稳定公共字段为：

```yaml
title: Page title
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
```

推荐 status：`draft`、`current`、`needs-review`、`conflicted`、`superseded`、`archived`。

推荐 classification：`public`、`personal`、`internal`、`confidential`、`restricted`。

推荐 confidence：`high`、`medium`、`low`、`unknown`。

只有在 `_schema.md` 定义语义后才增加领域字段。保持标准 YAML 可被通用 Markdown 工具读取，并兼容 Obsidian Properties 和 Bases。

## 页面类型

优先复用：

- `entity`：人、团队、组织、客户、产品、系统、dataset、地点；
- `concept`：方法、政策、心智模型和可复用思想；
- `project`：目标、范围、owner、状态、里程碑与结果；
- `process`：业务流程、责任边界或 runbook；
- `decision`：背景、选项、证据、选择、理由与后果；
- `metric`：定义、lineage、时间语义、限制与观测值；
- `comparison`：沿明确维度比较；
- `synthesis`：跨来源答案或持续演化的 thesis；
- `timeline`：顺序本身重要的事件。

让文件夹从数据中逐渐形成，不预建复杂 taxonomy。页面可通过 `domains` 跨文件夹分类。

## 可选 Obsidian 集成

- 使用 `[[wikilinks]]` 表达 durable relationships；使用标准 `aliases` 解析替代标题。
- 为重要 claim 使用 heading 或 block anchor，例如 `^claim-...`。
- 文件名尽量使用 lowercase kebab-case；title/aliases 可使用中文和多语言。
- 检测到 Obsidian workspace 时可以把 Bases 作为默认可视化层；把 Dataview 作为可选增强，不作为必需插件。
- 把附件原件放 raw，由 derived Markdown 引用；不要让远程易失 URL 成为唯一证据。
- 不自动修改 `.obsidian/` 的 attachment、plugin、hotkey 或 workspace 设置。可给用户建议，只有明确要求时才改。

## 内容质量与证据

让 material factual、numeric、personal 和 decision claims 追到 raw source ID 与 locator。让 wiki links 负责导航，让 citations 负责证明。保留冲突双方和时间；只按 authority、effective time 或用户裁决解决。

让人类原话与 agent synthesis 清晰可辨。围绕主题综合，不把页面写成 ingestion log。优先标记 superseded/archived，不硬删除历史知识。

## 并发与安全

保持一个写者。让 subagent 只读分析和提出 patch。写前检查 hash，冲突时停止覆盖。labels 不是 ACL；需要真正隔离的个人与公司 trust zones 应使用不同 workspace/repository。
