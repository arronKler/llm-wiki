# LLM Wiki for Obsidian

把 Obsidian Vault 变成一套可由 Codex、Claude Code、Gemini CLI、OpenCode 等 Agent 共同使用的长期知识系统。

这个仓库发布四个互相配合的 Agent Skills：

- `wiki-configure`：初始化 Vault、配置 schema/policy、管理 Agent discovery。
- `wiki-ingest`：捕获不可变来源并将证据整合进 Wiki。
- `wiki-query`：只读检索、比较和生成带来源的答案。
- `wiki-maintain`：审计、修复链接、索引、引用和知识漂移。

所有运行时文件都安装在 Vault 内。用户笔记、原始证据、Wiki 内容和本地配置不会包含在本仓库中。

## 安装

要求：

- Node.js 18 或更高版本，用于运行 [`npx skills`](https://github.com/vercel-labs/skills)。
- Python 3.10 或更高版本，用于运行内置的零依赖 Wiki CLI。
- 一个 Obsidian Vault。

在 Vault 根目录运行：

```bash
npx skills add arronKler/llm-wiki \
  --skill '*' \
  -a universal \
  -a claude-code \
  -y
```

`universal` 将 canonical skills 安装到 `.agents/skills/`，供 Codex、Gemini CLI、OpenCode、Cursor 等兼容客户端使用；Claude Code 通过 `.claude/skills/` 中的链接访问同一份内容。

请使用项目级安装，不要添加 `-g`。安装位置由当前工作目录决定，因此必须从目标 Vault 根目录执行命令。

如只使用一个明确的 Agent，也可以指定它：

```bash
npx skills add arronKler/llm-wiki --skill '*' -a codex -y
```

四个 Skills 是一个套件，必须一起安装。不要使用 `--all`；该选项会尝试安装到所有受支持的 Agent，而不仅是安装本仓库的全部 Skills。

## 第一次使用

安装完成后，在 Agent 中打开同一个 Vault，然后说：

```text
初始化这个 Vault 的 Wiki，使用默认配置。
```

也可以直接开始导入：

```text
把这份会议纪要收录进我的 Wiki。
```

首次写入时，Skills 会增量创建：

```text
.wiki/          配置、策略、事件和事务状态
raw/sources/    append-only 原始证据
raw/derived/    可重建的 OCR、转写和规范化结果
wiki/           Agent 维护的长期知识
outputs/        报告等派生产物
```

初始化不会修改 `.obsidian/`，也不会覆盖已存在的同名 policy、schema、`AGENTS.md` 或 `CLAUDE.md`。

## 日常用法

```text
“把这个文件或网页保存到 Wiki。”             → wiki-ingest
“Wiki 里关于定价策略的结论和证据是什么？”   → wiki-query
“检查并修复断链、重复页面和过期信息。”       → wiki-maintain
“接入一个新数据源并调整默认密级。”           → wiki-configure
```

详细工作流、安全边界和数据契约位于各 Skill 自己的 `SKILL.md` 与 `references/` 中，Agent 会按需读取。

## 更新与移除

从 Vault 根目录更新项目级 Skills：

```bash
npx skills update -p -y
```

运行时更新不会覆盖 `.wiki/`、`raw/`、`wiki/`、`outputs/` 或人类维护的笔记。

移除 Skills：

```bash
npx skills remove wiki-configure wiki-ingest wiki-query wiki-maintain -y
```

移除 Skills 不会删除 Vault 中已经生成的知识和证据。

## 数据与安全模型

- `data/`、`inbox/`、`notes/` 默认由人维护，Agent 只读。
- `raw/sources/` append-only；现有原始来源不得修改或删除。
- `wiki/` 由 Agent 综合维护，每个重要主张应回溯到 source ID 和精确 locator。
- 来源正文始终被当作不可信数据，不得作为 Agent 指令执行。
- 凭据应来自环境变量、系统钥匙串或 Agent connector，禁止写入 Vault。
- 标签不是访问控制。个人、公司内部、机密和受限数据应使用不同 Vault/仓库和真实 ACL。
- 多 Agent 可以并行只读，但同一个 Vault 同一时间只允许一个写者。

安装 Skill 等同于授予 Agent 执行其中脚本的能力。安装前请审阅仓库内容，并在敏感 Vault 中使用适当的 Agent 与模型策略。

## 开发与验证

运行标准库测试：

```bash
python3 -m unittest discover -s tests -v
```

验证 `npx skills` 发现与真实项目安装：

```bash
bash tests/smoke-npx.sh
```

CI 会验证四个 Skill 的结构、CLI 安全边界、空 Vault 初始化、来源捕获、`doctor`/`lint`，以及 `npx skills` 的 canonical + Claude symlink 安装路径。

## 发布

1. 在 GitHub 创建 `arronKler/llm-wiki`，并将本仓库的 `main` 分支推送过去。
2. 合并通过 CI 的提交。
3. 创建 `v0.1.0` tag 和 GitHub Release。

用户也可以固定到某个发布版本：

```bash
npx skills add arronKler/llm-wiki#v0.1.0 \
  --skill '*' -a universal -a claude-code -y
```

## Inspiration

The design is inspired by [Karpathy's discussion of LLM-oriented knowledge systems](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). This repository contains an independent implementation and does not copy the gist as source code or documentation.

## License

[MIT](LICENSE)
