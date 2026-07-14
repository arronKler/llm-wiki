---
name: wiki-configure
description: 安装、配置、迁移和演进一套跨 agent 可用、以本地 Markdown 为真源的 LLM wiki，支持普通目录、Git 仓库与 Obsidian 等可选前端，包括目录所有权、page schema、taxonomy、来源权威、敏感度、freshness、数据源 adapter 和 agent discovery bridge。Use when the user asks to 初始化、安装、设置、接入数据源、改规则、改分类、迁移旧 wiki、移动 workspace、升级 skills，或 configure, initialize, install, setup, migrate, add an adapter/domain, change policy/schema, or install agent bridges. 不用于日常 ingest、只读问答或普通 lint。
---

# Wiki Configure

## 目标

把当前本地目录或 Git 仓库变成可被不同 AI agent 稳定维护的 Markdown 知识系统。采用增量、可回滚配置；优先映射已有目录，避免强制搬迁用户内容。Obsidian 只是可选前端，不是初始化或运行前提。

## 定位 workspace 与工具

1. 优先采用用户明确给出的 workspace。否则从当前路径向上寻找 `.wiki/config.json`，并检查 `data/`、`inbox/`、`notes/`、`raw/`、`wiki/` 等候选；`.obsidian/` 只是额外的候选信号。
2. 仅在存在多个合理 workspace 时询问用户；不要在错误仓库根目录初始化。
3. 从本 `SKILL.md` 所在目录定位 `scripts/wiki.py` 和 `assets/`。不得假设当前工作目录是 skill 或 workspace。
4. 使用 `python3 <wiki.py> --workspace <workspace-root> ...`；旧版 `--vault` 仍作为等价兼容参数。让 CLI 生成基础配置和桥接文件，不要手写一套不兼容实现。
5. 若 `wiki-ingest`、`wiki-query`、`wiki-maintain` 任一 sibling skill 缺失，停止并提示用户从 workspace 根目录重新安装完整 suite：`npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`。

## 按需读取参考

- 在初始化、改变目录、page properties、taxonomy、ownership、索引或可选 Obsidian 视图前，读取 [references/workspace-contract.md](references/workspace-contract.md)。
- 在接入 URL、文件夹、飞书/Slack/邮件、会议、API、数据库、数据仓库、消息流或其他数据源前，读取 [references/adapters-and-security.md](references/adapters-and-security.md)。涉及认证、公司数据或 trust zone 时必须读取。
- 在迁移旧 `data/raw/entries/wiki`、安装 Codex/Claude/通用 agent bridge、移动 workspace 或升级 skill suite 前，读取 [references/migration-and-discovery.md](references/migration-and-discovery.md)。

## 初始化新 workspace

1. 先列出现有路径、已有 agent instructions 和可选编辑器配置。不要覆盖同名文件。
2. 运行增量初始化：

   ```text
   python3 <wiki.py> --workspace <workspace-root> init
   ```

3. 确认初始化只补齐缺失结构：`.wiki/config.json`、`.wiki/policy.md`、`.wiki/events/`、`.wiki/transactions/`、`raw/sources/`、`raw/derived/`、`wiki/_schema.md`、`outputs/` 等。仅在检测到 `.obsidian/` 时创建可选 `wiki/Wiki.base`；不得修改 `.obsidian/`，除非用户明确要求。
4. 以以下默认层级为起点，并允许配置映射到已有路径：
   - `data/`、`inbox/`、`notes/`：human-owned。
   - `raw/sources/`：capture tool 创建、append-only。
   - `raw/derived/`：agent/tool 创建、可重建。
   - `wiki/`：agent-owned synthesis。
   - `outputs/`：derived deliverables。
   - `.wiki/`：系统配置、事件、transaction 和 state。
5. 从 `assets/schema-template.md`、`page-template.md`、`policy-template.md`、`query-output-template.md`、`AGENTS-template.md` 和 `CLAUDE-template.md` 补齐缺失文件；Obsidian workspace 再增加 `Wiki.base`。只复制模板，不修改 assets 本身。
6. 运行 `doctor` 和 `lint`，修复初始化本身造成的问题，再记录 configure event。

## 配置领域与规则

1. 先读取现有 config、policy、schema 和代表性页面，再修改最小必要规则。
2. 把稳定的领域概念写进 schema：页面类型、必需 Properties、metric 口径、decision 字段、source authority、classification、freshness SLA 和命名约定。
3. 使用标准 YAML properties：`title`、`aliases`、`type`、`domains`、`status`、`classification`、`created`、`updated`、`as_of`、`review_after`、`confidence`、`sources`；这些字段同时兼容 Obsidian。
4. 使用标准 `aliases` 解析替代标题；旧 `also` 保持可读直至显式迁移。使用 `[[wikilinks]]` 和 heading/block anchors 连接知识。仅在启用 Obsidian 集成时增加 Bases 或 Dataview 视图，并且不把它们作为正确性依赖。
5. 将凭据引用配置为环境变量、系统钥匙串或 agent connector；禁止把 secret 写入 config、policy、adapter 或页面。
6. 对 personal、company internal、confidential 和 restricted 信任区优先采用不同 workspace/repository。不要把标签误当作 ACL。

## 配置数据源 adapter

1. 为每个 adapter 明确 `probe → fetch/snapshot → normalize → locate/cite → checkpoint` 生命周期。
2. 在 snapshot、incremental、query、pointer-only 中选择模式，并记录 authority、classification、freshness、cursor 或 query provenance。
3. 先用最小权限做 read-only probe，再验证一份小样本。不要在配置阶段批量 ingest，除非用户同时明确要求。
4. 确认 adapter 产物能由统一 `capture` 命令形成不可变 source ID，且 derived 内容能回溯 raw locator。
5. 对公司和敏感数据默认本地处理，禁止未经授权外发。

## 安装 agent discovery bridge

1. 保持 `.agents/skills/` 为唯一 canonical skill 源。不要维护多份可独立漂移的完整副本。
2. 若 suite 由 `npx skills` 安装，接受它创建的 canonical directory 与 agent-specific symlink；不要用自定义 wrapper 覆盖这些链接。
3. 对手工安装或缺少 bridge 的客户端，按用户需要运行：

   ```text
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target agents
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target codex
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target claude
   python3 <wiki.py> --workspace <workspace-root> install-bridges --target opencode
   ```

4. 生成薄 wrapper、symlink 或简短 `AGENTS.md`/`CLAUDE.md` 路由时，保留用户已有指令；除非用户明确要求，不使用 `--force`。
5. 明确说明 agent 发现边界：从 workspace 内启动通常可发现项目 skill；从 workspace 外启动的任意客户端不能仅靠目录文件保证自动发现。需要时安装 user-level link 或使用客户端的 add-dir/project 机制。
6. 运行 `doctor` 验证 canonical skill、bridge target 和路径解析。

## 迁移与升级

1. 先运行只读 `status`、`lint`、`doctor`，再制定迁移清单和回滚点。
2. 默认采用 in-place compatibility：映射旧 `data/`、读取旧 `raw/entries/`、保留 `wiki/_index.md`、`_backlinks.json`、`also` 和 `last_updated`。
3. 不把旧 raw 重新写成“更干净”的来源，不覆盖人工 `_index.md`，不批量重命名页面，不修改 human-owned 笔记。
4. 将新字段增量加入未来页面；只有用户明确要求 schema migration 时才批量回填。迁移 schema 与内容编辑分开提交。
5. 升级 canonical skills 后重新生成 bridges，运行 `doctor`、`lint`，并记录版本与 event。

## 写入与验收边界

- 把 configure 请求视为修改 `.wiki/`、schema、policy 和所选 bridges 的授权；仍不得推断出修改 `.obsidian/`、human-owned 内容或 raw 的授权。
- 使用单写者。允许 subagent 只读盘点和提出配置方案；由主 agent 串行应用修改。
- 每次 material 配置操作写一个 `.wiki/events/` 事件；不要并发 append 共享日志。
- 完成时报告 workspace root、启用的 paths、policy/schema 变化、adapter 状态、bridge 状态、可选前端兼容层、验证结果和仍需用户决定的安全选项。
