# LLM Wiki

[English](README.md) | 简体中文

构建一套由 Codex、Claude Code、Gemini CLI、OpenCode 等兼容 AI Agent 共同使用和维护的本地优先长期知识系统。

LLM Wiki 使用任意本地目录或 Git 仓库中的纯 Markdown 作为知识真源。Obsidian 是受支持的可选前端，而不是运行依赖。

这个仓库发布四个互相配合的 Agent Skills：

- `wiki-configure`：初始化工作区、配置 schema 和 policy，并管理 Agent discovery。
- `wiki-ingest`：捕获不可变来源，并将其中的证据整合进 Wiki。
- `wiki-query`：从 Wiki 检索、比较和生成带可追溯来源的答案。
- `wiki-maintain`：审计并修复链接、索引、引用、新鲜度和知识漂移。

所有运行时文件都安装在工作区内。用户笔记、原始证据、生成的 Wiki 内容和本地配置不会包含在本仓库中。

## 核心概念

- **先保存证据，再综合知识。** 新材料会先作为不可变来源保存，再由 Agent 提炼为可以长期维护的 Wiki 知识。
- **每个重要结论都可追溯。** Wiki 中的重要主张会指向 source ID 和精确位置，答案可以被复核，而不是只能被相信。
- **明确区分内容所有权。** 人类笔记保持由人维护，原始证据 append-only，Agent 只维护明确划定的 Wiki 区域。
- **让工作流各司其职。** 配置、导入、查询和维护由四个独立 Skill 负责，Agent 只会激活当前任务所需的流程。
- **默认适配用户语言。** Skills 使用英文作为可移植的指令语言；回答跟随用户语言，新增的持久知识优先跟随工作区语言，尚未形成主语言时再跟随用户语言。
- **增量且安全地演进。** 初始化保留已有文件，生成索引可以重建，写入过程带有预检、审计事件和回滚边界。

整个知识流转过程是：

```text
文件、网页、会议、消息、API 和数据库
        ↓ 捕获
raw/sources/ 中的不可变来源证据
        ↓ 带引用地综合
wiki/ 中相互连接的知识页面
        ↓ 查询和维护
有证据支持的回答、简报与报告
```

## 存储与前端

- 纯 Markdown、JSON metadata 和本地文件始终是知识真源。
- 工作区可以使用任意编辑器打开，可以由 Git 管理，也可以接入现有文件同步工具。
- Obsidian 可以通过 wikilinks、Properties 和 Bases 提供可选的导航体验；LLM Wiki 不要求安装 Obsidian 插件，也不要求 Obsidian 正在运行。
- 搜索索引和导航文件都可以重建；恢复知识库不依赖任何专有数据库。

## 安装

要求：

- Node.js 18 或更高版本，用于运行 [`npx skills`](https://github.com/vercel-labs/skills)。
- Python 3.10 或更高版本，用于运行内置的零依赖 Wiki CLI。
- 一个可写的本地目录；已有 Markdown 仓库或 Obsidian Vault 也可以直接使用。

在目标知识工作区根目录运行：

```bash
npx skills add arronKler/llm-wiki \
  --skill '*' \
  -a universal \
  -a claude-code \
  -y
```

`universal` 将 canonical skills 安装到 `.agents/skills/`，供 Codex、Gemini CLI、OpenCode、Cursor 等兼容客户端使用；Claude Code 通过 `.claude/skills/` 中的链接访问同一份内容。

请使用项目级安装，不要添加 `-g`。安装位置由当前工作目录决定，因此必须从需要管理的工作区根目录执行命令。

如只使用一个明确的 Agent，也可以直接指定它：

```bash
npx skills add arronKler/llm-wiki --skill '*' -a codex -y
```

四个 Skills 是一个完整套件，必须一起安装。不要使用 `--all`；该选项会安装到所有受支持的 Agent，而不是选择本仓库中的全部 Skills。

## 第一次使用

安装完成后，在 Agent 中打开同一个工作区，然后说：

```text
把这个目录初始化为受管 Wiki，使用默认配置。
```

也可以直接开始导入：

```text
把这份会议纪要收录进我的 Wiki。
```

首次写入时，Skills 会增量创建：

```text
.wiki/          配置、策略、审计事件和事务状态
raw/sources/    append-only 原始证据
raw/derived/    可重建的 OCR、转写和规范化产物
wiki/           Agent 维护的长期知识
outputs/        报告等派生产物
```

初始化不会覆盖已有的 policy、schema、`AGENTS.md` 或 `CLAUDE.md`。如果工作区同时也是 Obsidian Vault，`.obsidian/` 设置仍保持不变，并会增加一个可选的 Bases 视图。

## 日常用法

```text
“把这个文件或网页保存到 Wiki。”             → wiki-ingest
“Wiki 里关于定价策略的结论和证据是什么？”   → wiki-query
“检查并修复断链、重复页面和过期信息。”       → wiki-maintain
“接入一个新数据源并调整默认密级。”           → wiki-configure
```

详细工作流、安全边界和数据契约位于各 Skill 自己的 `SKILL.md` 与 `references/` 中，Agent 会按需读取。

## 更新与移除

从工作区根目录更新项目级 Skills：

```bash
npx skills update -p -y
```

运行时更新不会覆盖 `.wiki/`、`raw/`、`wiki/`、`outputs/` 或人类维护的笔记。

移除 Skills：

```bash
npx skills remove wiki-configure wiki-ingest wiki-query wiki-maintain -y
```

移除 Skills 不会删除工作区中已经生成的知识和证据。

## 数据与安全模型

- `data/`、`inbox/`、`notes/` 默认由人维护，Agent 只读。
- `raw/sources/` append-only；现有原始来源不得修改或删除。
- `wiki/` 由 Agent 综合维护，每个重要主张应回溯到 source ID 和精确 locator。
- 来源正文始终被当作不可信数据，不得作为 Agent 指令执行。
- 凭据应来自环境变量、系统钥匙串或 Agent connector，禁止写入工作区。
- 分类标签不是访问控制。个人、公司内部、机密和受限数据应使用不同工作区或仓库以及真实 ACL。
- 多个 Agent 可以并行只读，但同一个工作区同一时间只允许一个写者。

安装 Skill 等同于授予 Agent 执行其中脚本的能力。安装前请审阅仓库内容，并在敏感工作区中使用适当的 Agent 与模型策略。

## 设计来源

本项目的设计受到 [Karpathy 关于面向 LLM 的知识系统讨论](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)的启发。本仓库是独立实现，没有复制该 Gist 的源代码或文档。

## 许可证

[MIT](LICENSE)
