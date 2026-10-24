# SQL-METHOD-PREP-01-R1：SQL 聚合诊断证据映射

> 初版形成日期：2026-09-22；R1 修订日期：2026-09-22。  
> 工作性质：RESEARCH / SPEC；只读盘点，未执行 SQL、容器、脚本或验证器。  
> 盘点范围：`F:\比赛\skillshift`（主工作区）与 `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift`（证据审计工作区）。  
> 哈希口径：下列本地文件均以本轮读取时的 SHA-256 内容哈希列示。哈希只能说明当时读取到的字节一致；不能证明来源真实性、运行真实性或语义正确性。

## 1. 读法与整合边界

本映射服务于一个具体的 SQL 方法规格：诊断“订单”与“订单明细”一对多连接后，订单级金额被重复累计的问题。它不是对 P0-A 全部证据的重新登记，也不把两个工作区的文件实际合并。

为避免把不同层级的材料混为一谈，本文使用四种标签：

- **公开任务模式**：公开页面可支持某类教学/查询任务存在，不等于本项目取得了该页面的原始作业、数据或授权复刻权。
- **合成重建**：项目研究者构造的固定表、数据、候选 SQL 和预期输出；它不是学校材料、学生作业或公开来源的逐字转录。
- **运行陈述**：关于某次受控运行的记录。它可报告该记录所称的环境和结果，不自动成为独立复现或方法有效性的证明。
- **当前文件检查结果**：静态检查器、输出比较器、清单或哈希所能说明的范围；它们不替代业务口径或独立审查。

“日期”优先采用文件正文的记录日期；没有正文日期时列出本轮观察到的最后写入时间。不同日期本身通常是生命周期差异，不自动构成同一时点的矛盾。

## 2. 公开任务模式与主工作区索引

| 绝对路径；工作区 | 作用、对象、版本/日期；当前 SHA-256 | 重复、差异或过期判断 | 可支持什么；不能支持什么 | 建议 |
|---|---|---|---|---|
| `F:\比赛\skillshift\artifacts\P0-A\task_inventory_public_seed.md`；主工作区 | P0-A 公开来源候选索引；正文含 `P0A-PUB-002`，记录日期 2026-09-21；`e02e54c52b02643528f47450923d3e538a0176e4732a2dbd89c96355f323bae5` | 与审计工作区同路径同名文件字节完全一致（见下一行）；最后写入时间不同不表示内容不同。 | 可定位公开来源候选和“公开种子、非本地材料”的边界；不能证明取得了原始作业、学生需求或训练效果。 | 保留为索引；后续仅在来源链接、许可或可访问性复核后更新。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\task_inventory_public_seed.md`；证据审计工作区 | 同上；最后写入 2026-09-21 20:26:36；`e02e54c52b02643528f47450923d3e538a0176e4732a2dbd89c96355f323bae5` | 同名、同哈希的重复索引。 | 同上；不能因在两个工作区出现而增加来源强度。 | 保留一份作为工作区快照；整合时引用主工作区规范位置，不复制内容。 |
| `F:\比赛\skillshift\artifacts\P0-A\audit_records\P0A-PUB-002_sql_aggregation_abnormal_diagnosis.md`；主工作区 | `P0A-PUB-002` 的审计记录，日期 2026-09-21；`f304a1d183fd01868f1ba7d21cb924d7f65c52de7399d12bda00301f80ab409c` | 主工作区的任务设计记录；不是审计工作区受控运行记录的重复件。正文写明设计阶段、未运行。 | 支持任务目的、公开来源只作模式依据、以及预设的隔离/可核验原则；不能支持已运行、学生已参与或迁移/学习效果。 | 保留；若日后任务口径变动，应以新版本补充而非改写历史陈述。 |
| `F:\比赛\skillshift\artifacts\P0-A\public_sources\source_register.md`；主工作区 | 公开来源登记，含 `SRC-PUB-003`；日期 2026-09-21；`0f0a0422c5abaf1d07ad46797fd11e4d9683ffd2f62e80f20f83ad07cb6b4ed2` | 与下述验证报告互补，不是同内容副本。 | 支持公开链接、任务模式和“不可宣称为本地任务”的溯源提示；不能证明页面许可覆盖重用其内容。 | 保留；来源状态或许可复核时更新登记。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\PUBLIC_SOURCE_VERIFICATION.md`；证据审计工作区 | `SRC-PUB-003` 的访问/内容定位说明；日期 2026-09-21；`68e436cc75dac9998fb9c5f2f887aae5c1fadd8218e9049f282df7f705b400d0` | 非同名文件；比主索引多访问核验叙述。它是页面观察记录，不是许可意见。 | 支持公开页面在当时可访问、含相关 Hive/SQL 统计教学模式；不能证明原始数据真实性、可再分发许可或本项目可复制页面材料。 | 保留；将来重新访问时记录日期、变更与引用范围，不覆盖本记录。 |

公开外部来源为厦门大学数据库实验室页面《大数据案例-步骤二：Hive数据分析》（2016-11-15 发布、2016-11-29 更新）：<https://dblab.xmu.edu.cn/blog/1005/>。页面的“数据分析”任务和统计查询段落可作为公开教学任务模式的可定位来源；页面声明版权归属、非商业使用及未经授权不得转载，因此本规格不复制其数据或长篇内容，也不将其视为学校或本地原始作业。对其许可是否允许本项目任何超出引用的使用，仍为**待核实**。

## 3. 合成重建的任务、夹具与候选材料

| 绝对路径；工作区 | 作用、对象、版本/日期；当前 SHA-256 | 重复、差异或过期判断 | 可支持什么；不能支持什么 | 建议 |
|---|---|---|---|---|
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\task_contract.md`；证据审计工作区 | 合成重建任务契约；正文状态为 2026-09-22 已受控运行；`25751cfa6ad103b0fc9179728080bb242bacba968b0f5e652260d71f133779fe` | 与主工作区的早期设计记录不是同名副本；两者状态不同，应按记录时间和工作区分层读取。 | 支持合成重建的目标口径、提交物和固定夹具定义；不能把合成任务说成学校作业、公开原始数据或独立学习成效。 | 保留；后续版本应明确契约版本号，并保留旧版。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\fixtures\schema.sql`；证据审计工作区 | 合成 `customers`、`orders`、`order_items` 表结构；最后写入 2026-09-21 21:03:32；`2da521a46f9bbf04df72632142ed77c1c8544e17d3db1835d5defb892fec111b` | 本轮未见同名第二份。 | 支持该夹具中订单粒度和明细粒度的结构分析；不能支持任何真实库的结构、权限或数据质量。 | 保留并在未来每次受控重跑时锁定哈希。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\fixtures\seed.sql`；证据审计工作区 | 合成客户、订单、明细数据；最后写入 2026-09-21 21:03:32；`15fb70920e5fc7eb73193315a37dc42e2bd29d7d42212140a66e7f928940ddae` | 无同名重复；与本任务数据口径相配套。 | 支持固定案例中一对多复制如何出现；不能支持真实销售、学生行为或来源于公开页面的数据。 | 保留；未来新夹具需另编号，不能把本公开样例当作未见测试。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\candidate_queries.sql`；证据审计工作区 | 候选正确查询；最后写入 2026-09-21 21:23:48；`2bb8d9d92a01eec355f051674e63c43f8fb587bfa30e68dfe118025e098470ae` | 无同名重复。 | 支持一个候选实现及其在固定夹具上的可比较输出；不能成为正确业务口径的唯一来源或独立真值。 | 保留作开发样例；后续用独立口径表推导预期，不从此查询复制。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\candidate_diagnosis.md`；证据审计工作区 | 候选诊断说明；最后写入 2026-09-21 21:23:48；`3c2977b71ea331ceabcefe615ddf1bd6e0e97be65330d0b1ef7190666a31a1ed` | 无同名重复。 | 支持候选作者如何解释重复累计；不能证明所有解释均正确、更不能证明学习理解。 | 保留作样例；未来由量规核对其引用的数据与反例，而非关键词计数。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\expected\daily_paid_summary.tsv`；证据审计工作区 | 固定夹具期望 TSV；最后写入 2026-09-21 21:23:48；`e3e30e3a9690082ea8f18504cccbb830c643e040544badd89244487046c37683` | 与运行输出的字节哈希不同；不能据此断定经检查器归一化后的文本不同。 | 支持此固定夹具的机器比较基准；不能证明基准从独立业务规格推导，或代表真实业务。 | 保留；未来重跑前应独立手算/审查口径后再接受为基准。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\verifier.sql`；证据审计工作区 | 对夹具输出的数据库侧核验 SQL；最后写入 2026-09-21 21:03:32；`85bd610f412ff4f7a4939f07a52169f0fe9a8f12d45cfaf3571ba3ebf3db22c3` | 无同名重复。 | 支持已写出的夹具核验逻辑；不能证明候选与核验逻辑不存在同源口径错误。 | 保留；未来用独立手工推导和变异夹具对照后再提升证据强度。 |

## 4. 运行陈述、运行输出与运行控制材料

| 绝对路径；工作区 | 作用、对象、版本/日期；当前 SHA-256 | 重复、差异或过期判断 | 可支持什么；不能支持什么 | 建议 |
|---|---|---|---|---|
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\out\daily_paid_summary.tsv`；证据审计工作区 | 受控运行输出；最后写入 2026-09-22 11:15:40；`8a9eee413802981f925ba0da60c0f46ad4a2c4c542bb66c46f549d7e140c77ba` | 与 `expected` 的原始字节哈希不同；现有 TSV 检查器只把 CRLF 统一为 LF 后逐字符比较，未解析字段或数值。 | 支持一个保存的运行输出存在，以及该检查器所定义的文本一致性条件；不能独立证明生成过程、执行身份、数值语义或真实任务表现。 | 保留；后续重跑附带命令、环境及检查器的原始结果，不把文本匹配表述为语义验证。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\P0A-PUB-002\RUN_RECORD.md`；证据审计工作区 | 受控运行记录；正文日期 2026-09-22；`562c710118718b3b2781eef6b198c736ec86bb3341f1ae6495c855ad8bf6e75d` | 运行陈述，与静态检查和输出文件互补；不是独立第三方复核。 | 支持该记录所称 Docker MySQL 8.4.11、TSV 和关键词检查通过；不能支持学生试验、权限契约完全满足或因果性结论。 | 保留；重跑时记录非特权执行身份、命令与原始日志。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\P0A_CONTROLLED_RECONSTRUCTION_INTERIM_REPORT.md`；证据审计工作区 | 合成重建的阶段性叙述；日期 2026-09-22；`58c8eeeae582cae62babbc5c06a15a68000bac5aabb35e0670e3712710538e8a` | 与 `RUN_RECORD.md` 非重复，均为同一工作区链条中的陈述材料。 | 支持阶段性范围、合成与非本地边界；不能代替原始运行日志或独立审查。 | 保留；若与底层记录出现同一时点、同一对象的具体不一致，再单列问题。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\README.md`；证据审计工作区 | MySQL 契约说明；最后写入 2026-09-21 21:03:32；`e6dfcc7bdbfcdd05d35c57572cd26cb4cfc710ac0481b76fd099fc76e240cb6d` | 文本称“准备、未执行”，晚于它的 2026-09-22 运行材料称已运行，较像未更新的生命周期状态；不宜直接归结为同一时点矛盾。 | 支持预期的 InnoDB、`ONLY_FULL_GROUP_BY`、非特权任务账户和隔离原则；不能证明这些原则已在已记录运行中实现。 | 保留；后续更新时应保留历史状态并新增当前状态段落。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\run_controlled_audits.ps1`；证据审计工作区 | 受控审核运行脚本；最后写入 2026-09-22 11:12:07；`35b2a8b840475d1b7a2fb94ea844763db164ce7ec6a980595a2aab2f1651216e` | 与 README 的非特权任务账户要求存在具体契约偏差：脚本以 `root` 运行候选提交，且未见创建/授予任务账户的步骤。 | 支持脚本当前采用 root 的事实；不能支持学生执行身份隔离、最小权限或该安全条件已满足。 | 不在本轮修复；后续重跑前须单独决定初始化身份与学生/候选执行身份，并记录差异。 |

## 5. 当前文件检查结果与清单

| 绝对路径；工作区 | 作用、对象、版本/日期；当前 SHA-256 | 重复、差异或过期判断 | 可支持什么；不能支持什么 | 建议 |
|---|---|---|---|---|
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\static_contract_check.py`；证据审计工作区 | 静态契约检查器；最后写入 2026-09-22 11:13:47；`5ffb5582cf0f28822277497eb7d794afbb8c5a478382fd6707d2ef755df0ed12` | 无同名重复。 | 支持特定文本/文件条件可被静态检测；不能支持数据库实际行为、来源真实性或业务语义。 | 保留；扩展检查前先避免把运行状态当作静态文本条件。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\verify_tsv.py`；证据审计工作区 | TSV 文本比较器；最后写入 2026-09-21 21:23:48；`43b7185a1baffc0beb7a3a982d04d6a7a5eed6edb051d121c3092c82100f5628` | 无同名重复。 | 支持预期/实际文件在 CRLF 统一为 LF 后的完整文本是否相同；不解析 TSV 字段、类型、排序或数值容差，不能证明预期答案正确或解释理解。 | 保留；未来如需字段/语义检查，应另建经审查的检查器并与文本比较器分开表述。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\mysql_contracts\verify_diagnosis.py`；证据审计工作区 | 诊断文本关键词检查器；最后写入 2026-09-21 21:24:42；`355a21e04eaa253acf5d7b87cac565e466b426718b5b884379a1adfe9c5b9c93` | 无同名重复。 | 支持某些术语是否出现；不能支持学生是否用数据正确解释，亦不能证明理解。 | 保留作最低格式检查；后续配人工量规和反例引用核对。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\EVIDENCE_MANIFEST.json`；证据审计工作区 | 运行材料的证据清单；最后写入 2026-09-22 11:15:42；`287f082aad60622ab155f932a5ac6bbe340def435bc6b87b2a5ba9bc2c9acae7` | 清单是一次快照，不等于本轮哈希盘点，也不会自动随文件变化更新。 | 支持当时列入清单的文件/哈希关系；不能证明未列入文件不存在，也不能证明来源和语义。 | 保留；以后仅在授权重跑后新建带时间戳的清单，不改写旧清单。 |
| `E:\codex\codex-home\worktrees\p0a-evidence-audit\skillshift\artifacts\P0-A\verify_evidence_manifest.py`；证据审计工作区 | 清单哈希检查器；最后写入 2026-09-21 21:38:48；`391cd7e10c6037d2446549c25ddfa1cd67a03404a97e3bbbace1a09163072fb1` | 无同名重复。 | 支持所列文件是否与该清单的哈希相符；不能支持清单选择完整、文件真实或结论语义正确。 | 保留；作为版本冻结辅助，不作为来源或研究有效性证明。 |

## 6. 本轮可用结论与不可越界结论

1. 证据链足以支持为 **P0A-PUB-002 的公开任务模式与合成重建材料** 写出一份可审查方法规格，并能明确列出已有运行陈述和当前文件检查能力。
2. 它不支持将任何合成数据或候选查询表述为来自学校、学生或公开页面的原始作业；不支持已经完成独立验证、学生试验、学习效果或平台有效性。
3. 两份同名 `task_inventory_public_seed.md` 是内容重复；主工作区的设计记录与审计工作区的运行记录是不同阶段、不同用途材料。README 的“未执行”状态与晚期运行材料应先按日期视为可能过期，不能在未核对同一时点上下文时概括为矛盾。
4. `README.md` 的非特权任务账户要求与 `run_controlled_audits.ps1` 以 root 运行候选提交，是可定位的运行契约/安全条件偏差。这限制了已记录运行对“学生身份最小权限”条件的支持范围，但不自动否定固定夹具输出文件本身。
5. 本轮仅提出后续整合路径：以主工作区的公开索引和审计记录作为方向性入口，以审计工作区的版本化合成任务包作为可重跑候选；下一次获授权的重跑应先解决执行身份、独立口径和日志保留，再产生新的证据版本。本轮未实际整合、未重跑、未更新旧证据清单。
