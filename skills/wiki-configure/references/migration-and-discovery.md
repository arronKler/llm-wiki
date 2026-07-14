# 旧 Vault 迁移与跨 Agent 发现

## 采用兼容优先迁移

先盘点，不先移动：

- Obsidian vault root 与 `.obsidian/`；
- `data/`、`inbox/`、`notes/` 等 human-authored 路径；
- 旧 `raw/entries/*.md` 的 frontmatter 与 ID；
- `wiki/_index.md`、`_backlinks.json` 和页面类型；
- `also`、`last_updated`、旧 `sources` 与 wikilinks；
- `.claude/skills`、`.codex/skills`、`.opencode/skills`、`.agents/skills`、`AGENTS.md`、`CLAUDE.md`；
- git、sync、symlink 和大小写敏感性。

把现有路径映射进 `.wiki/config.json`。默认保留原位，不强制改成新目录大小写或 taxonomy。

## 兼容旧 personal wiki 契约

- 把 `data/` 当 human-owned source drop，不改写。
- 把 `raw/entries/` 当合法 immutable legacy source cards；继续解析其 `id`、`date`、`source_type`、`source_path` 等字段。
- 把旧 source ID 保持为引用目标；不批量换成 `src-*`。
- 继续用 `also` 做检索与 link resolution；新页使用 `aliases`。显式迁移时可以双写一段过渡期。
- 继续读取 `last_updated`；新页使用 `updated`。不要删除旧字段直到所有消费者升级。
- 保留人工 `wiki/_index.md` 的标题、分类、summary 和注释。CLI 只生成 `_catalog.md`、`_sources.md`、`_backlinks.json`。
- 读取旧 `_backlinks.json`，但允许由新 CLI 以兼容格式重建；先备份并验证消费者。

只有用户明确要求统一 schema 时才批量回填。把 schema migration 与内容修订分成不同 transaction 和 event。

## Canonical skill 布局

保持：

```text
<vault>/.agents/skills/
  wiki-ingest/
  wiki-query/
  wiki-maintain/
  wiki-configure/
```

让 `.agents/skills` 成为唯一可编辑真源。其他客户端使用薄 wrapper 或 symlink 指向 canonical `SKILL.md`，不要复制四套完整内容。

首选从 vault 根目录使用 `npx skills` 安装完整套件：

```text
npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y
```

保持项目级安装，不使用 `-g`。接受安装器写入的 `skills-lock.json`、`.agents/skills` canonical copy 和 `.claude/skills` directory symlink。四个 skill 通过 sibling 相对路径共享 `wiki-configure/scripts/wiki.py`，因此不得只安装其中一部分。

生成 wrapper 时：

- 让 frontmatter 的 name/description 足以触发；
- 让正文只指向 canonical skill 并要求完整读取；
- 使用相对路径或可重建 link，避免硬编码旧机器绝对路径；
- 保留用户已有 `.claude/skills`、`.codex/skills`、AGENTS/CLAUDE 指令；
- 未显式要求时不使用 `--force`。

## 理解 agent discovery 边界

不同 agent 客户端的发现位置和 symlink 支持不同。不能承诺“文件放入 vault 后，从任意目录启动的所有 agent 都自动发现”。采用以下保证层级：

1. 从 vault 内以 project/repo 方式启动：使用项目级 `.agents/skills`。
2. Claude 或只扫描专属目录的客户端：生成 `.claude/skills` 薄 wrapper，或使用其 add-dir/project 机制。
3. Gemini CLI、OpenCode 与新版 Codex 可直接发现 `.agents/skills`；仅在客户端策略禁用 agent-compatible 路径时，才为 OpenCode 生成可选 `.opencode/skills` 薄 wrapper。
4. 旧 Codex 配置：在需要时生成 `.codex/skills` bridge；优先迁移到 `.agents/skills`。
5. 从 vault 外任意位置启动：显式安装 user-level link/skill，或让客户端把 vault 加入 workspace；这属于每个客户端的一次性配置。
6. 完全不支持 Agent Skills 的 agent：用极短 `AGENTS.md`/`CLAUDE.md` 说明 vault root、权限边界和四个 canonical skill 路径。

不要让 bridge 自己包含完整知识契约，否则升级时会漂移。

## 移动 vault

移动后重新运行 `locate`、`install-bridges` 和 `doctor`。检查：

- symlink target 与 wrapper relative path；
- `.wiki/config.json` 是否使用 vault-relative paths；
- adapter 是否残留绝对路径；
- Obsidian attachments 和 wikilinks；
- git submodule/sync 忽略规则；
- user-level link 是否仍指向旧位置。

不要通过全局搜索替换 raw source 内的原始路径；raw 是证据。只更新配置、derived mappings 和 bridges。

## 升级与回滚

1. 记录当前 skill/version、config、schema、policy 和 bridge hash。
2. 只升级 canonical skills 与兼容的 CLI/assets。
3. 不在同一 transaction 中批量改写 wiki 内容。
4. 重新生成 wrappers，运行 `doctor`、`lint` 和 legacy fixture。
5. 失败时恢复 canonical/config/bridge，不回滚或重写新捕获的 raw sources。

验收至少覆盖：从 vault 内分别触发 ingest/query/maintain/configure；旧 source 与 aliases 可查；bridge 不覆盖已有指令；从 vault 外启动时能给出明确安装提示而非静默失败。
