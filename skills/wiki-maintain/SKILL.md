---
name: wiki-maintain
description: 审计并安全维护 Obsidian wiki 的完整性、链接、孤儿页、重复实体、引用、raw 哈希、索引漂移、陈旧或冲突主张、schema、敏感度和 agent bridge。Use when the user asks to 检查、体检、lint、doctor、cleanup、清理、去重、修复、重建索引、刷新反链、审查新鲜度，或 audit, maintain, repair, rebuild, reindex, dedupe, check integrity. 审计默认只读；只有明确 repair/fix 请求才写入。
---

# Wiki Maintain

## 目标

先用可复现检查找出 wiki 漂移，再以最小、可审核的修改修复。保护 raw、人类笔记和人工索引不被“清理”破坏。

## 定位 vault 与工具

1. 从用户给出的路径向上寻找 `.wiki/config.json`；未给路径时从当前目录向上寻找。
2. 将含旧 `raw/entries/`、`wiki/_index.md`、`wiki/_backlinks.json` 的 vault 纳入审计，不要求先迁移。
3. 从本 `SKILL.md` 所在目录定位 `../wiki-configure/scripts/wiki.py`。统一使用 `python3 <wiki.py> --vault <vault-root> ...`，不得依赖当前工作目录。
   若 CLI 不存在，保持只读并提示用户重新安装完整 suite：`npx skills add arronKler/llm-wiki --skill '*' -a universal -a claude-code -y`。不要自行实现另一套修复工具。
4. 读取 `.wiki/config.json`、`.wiki/policy.md`、`wiki/_schema.md` 和最近相关事件。缺失的系统文件应报告为发现，不得在 audit 中自动创建。

## 按需读取参考

- 在任何 audit、lint、doctor、cleanup、breakdown、freshness 或完整性检查前，读取 [references/audit-checks.md](references/audit-checks.md)。需要决定严重度或覆盖范围时也读取。
- 在执行任何 rebuild、fix、repair、dedupe、重命名、归档或语义重写前，读取 [references/repair-protocol.md](references/repair-protocol.md)。涉及 schema、policy、adapter、bridge 或旧目录迁移时必须读取其升级边界。

## 审计工作流（默认）

1. 明确范围：全 vault、某领域、某次 ingest、某类问题或某时间窗口。默认覆盖系统契约与 wiki，不扫描无关大文件。
2. 保持严格只读：不要运行 `rebuild`、不要写 event、不要自动格式化、不要修正文案。
3. 运行：

   ```text
   python3 <wiki.py> --vault <vault-root> status
   python3 <wiki.py> --vault <vault-root> lint
   python3 <wiki.py> --vault <vault-root> doctor
   ```

4. 核对 raw 内容哈希、ownership 越界、schema、source ID、citation locator、wikilinks、aliases、重复标题、孤儿页、generated index 漂移和敏感度继承。
5. 再做语义审计：重复概念、被新证据推翻但未标记的主张、陈旧指标、缺少页面的高价值实体、错误归因、证据洗白和未显式标注的冲突。
6. 若使用 subagent 并行检查，让其只读一批页面并返回发现与候选 patch。由一个主 agent 去重、裁决和写入；禁止 subagent 修改共享文件。
7. 按 blocker、high、medium、low 排序报告。每项提供路径、定位、证据、影响、建议动作和是否需要用户确认。

## 修复工作流（仅明确授权）

1. 把用户说的 “fix/repair/修复/清理/重建” 视为对指定范围的写授权；不要把一次修复扩展为全库重构。
2. 在修改前记录目标文件哈希并生成最小 transaction/diff。立即重读每个目标页，发现并发变化时停止覆盖并重新合并。
3. 遵守层级权限：
   - 允许重建 `_catalog.md`、`_sources.md`、`_backlinks.json` 等生成文件。
   - 允许在授权范围内修复 agent-owned `wiki/`。
   - 不得修改 human-owned `data/`、`inbox/`、`notes/`。
   - 不得修改或删除既有 `raw/sources/`；哈希异常只隔离和报告。
   - 不得用生成内容覆盖人工维护的 `wiki/_index.md`。
4. 优先补链接、补引用、合并重复别名、标记 `conflicted`/`superseded`/`archived`；默认不硬删除页面。
5. 仅在用户明确要求时运行 `rebuild`。完成后运行 `lint` 与 `doctor`，确认没有引入新断链、schema 或 classification 问题。
   若 CLI 拒绝覆盖 unmanaged 或被修改的生成文件，先展示冲突；只有用户明确同意接管时才运行 `rebuild --force`。该命令会先把冲突文件备份到 `.wiki/transactions/`，完成时报告备份路径。
6. 用 `event maintain --message <summary> --data <json>` 记录一操作一事件文件。
7. 返回实际修改、保留未动内容、验证结果、剩余风险和需要进一步裁决的冲突。

## 升级边界

- 将 schema、policy、adapter、ownership、freshness 规则或 agent discovery bridge 的变化交给 `wiki-configure`。
- 将新增外部证据交给 `wiki-ingest`；维护流程不得为“补全资料”而静默联网或抓取。
- 将只读知识问题交给 `wiki-query`。
- raw 哈希异常、并发写冲突、敏感信息疑似外泄或无法确定所有权时立即停止修复，保留证据并报告。
