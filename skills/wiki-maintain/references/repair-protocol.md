# 安全修复协议

## 先确认授权范围

| 目标 | 默认 audit | 明确 repair 后 | 额外要求 |
| --- | --- | --- | --- |
| generated `_catalog/_sources/_backlinks` | 只读 | 可 `rebuild` | 不得覆盖 `_index.md` |
| agent-owned `wiki/` | 只读 | 可做最小修复 | 立即重读、保留 citations |
| `outputs/` | 只读 | 可修复 agent 产物 | 保持 classification |
| human-owned `data/inbox/notes` | 只读 | 仍不得默认改 | 需要对具体内容的明确授权 |
| `raw/sources` | hash 检查 | 不得修改/删除 | 异常时隔离并报告 |
| `raw/derived`、`.wiki/state` | 只读 | 可重建 | 必须仍能追到 raw |
| schema/policy/adapters/bridges | 只读 | 转 `wiki-configure` | 分离 migration |
| `.obsidian/` | 只读 | 不在 maintain 中修改 | 需要明确配置请求 |

“cleanup” 不等于允许删除人的内容或 raw。“fix all” 也只覆盖本次报告中可安全修复的 agent-owned 问题。

## 建立 transaction

1. 固定 repair scope 与发现列表。
2. 记录每个目标文件的路径、当前 hash 和预期修改。
3. 生成最小 diff；让 subagent 只提出候选 diff，不直接写盘。
4. 由单一主 agent 在写前立即重读目标文件。
5. hash 不同或 Obsidian/另一 agent 已改动时停止覆盖，重新合并。
6. 应用后运行 lint/doctor，并记录一个 maintain event。

不要把无关格式化、目录重排或文风重写塞入修复 transaction。

## 修复链接与索引

- 先确认 target 的 title/aliases/旧 also，再修复 wikilink；不要仅凭相似字符串猜实体。
- 重命名页面时同时更新所有入链、aliases、人工 `_index.md` 条目和 anchors；高风险时保留旧 alias。
- 只用 `rebuild` 生成 `_catalog.md`、`_sources.md`、`_backlinks.json`。若生成器试图改 `_index.md`，立即停止。
- 对孤儿页先判断它是否应被链接、合并、归档或本来就是入口页；不要为了“零孤儿”添加无意义链接。

## 合并重复页面

1. 核实二者确为同一实体/概念，而非同名或不同时间版本。
2. 选取拥有稳定链接和较完整证据的 canonical page。
3. 逐 claim 合并，保留各自 source IDs、locator、时间、冲突与人类措辞。
4. 将被合并标题加入 canonical `aliases`；更新入链。
5. 默认把旧页标为 superseded 或保留短 redirect，不直接删除。
6. 重建索引并检查 backlinks。

## 修复陈旧与冲突

- 缺少新证据时只标 `needs-review`、设置 `review_after` 或陈述 gap；不得联网补写事实。
- 来源冲突时保留双方并标 `conflicted`。只有 authority、effective time 或用户裁决明确时才选 current。
- 更新 `as_of` 时必须有支持该时间的来源；页面编辑日期不能冒充数据时间。
- 指标口径不完整时补 gap，不从数字本身反推定义。

## 处理 raw 异常

发现 raw hash 变化时：

1. 停止所有会写 wiki 的操作；
2. 保存只读诊断：source ID、metadata hash、actual hash、mtime 和引用它的页面；
3. 不把当前字节覆盖回“正确版本”，也不修改 metadata 迁就变化；
4. 让用户从可信备份恢复，或把变化后的内容作为新 source 捕获并标记关系；
5. 恢复后重新 lint 受影响 citations。

## 保持旧契约

- 不批量删除 `also` 或 `last_updated`；现代 `aliases`/`updated` 可增量共存。
- 不把 `raw/entries` 移入新布局作为普通 repair。
- 不覆盖或重新生成人工 `_index.md`。
- 将需要统一字段、移动目录或升级 bridge 的工作作为独立 configure migration。

## 验收

修复完成前确认：授权范围内的发现已关闭；raw hash 未变化；human-owned 文件未变化；人工 index 保留；generated state 可重建；citation 可解析；classification 未下降；旧兼容 fixture 仍通过；event 准确列出修改和验证结果。
