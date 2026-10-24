# 本机合成安全契约验证报告（PCP-13 / PCP-18 / PCP-20）

- Task ID：`R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT-001`
- 类型：FEATURE / 本机安全基础
- Gate：Gate B，总体仍为 **PARTIAL**
- 结论：**PASS（仅限本机合成安全契约；不代表生产控制面就绪）**
- 报告日期：2026-09-24

## 结论边界

本报告只证明三件事：敏感内容在四类 sink 会被拒绝；日志字段分类与错误净化有正负向测试；审计事件只追加且读取默认拒绝。它**不**证明 ECS 已加固、生产控制面已就绪、真实密钥已托管、真实数据已可处理。所有结论限定为**本机合成安全契约**。

## 已修改文件及原因

| 文件 | 类型 | 原因 |
| --- | --- | --- |
| `apps/agent-first/agent_first/secret_scan.py` | 新增 | PCP-13：凭据形字段名与值的静态扫描与拒绝，findings 不携带被匹配的值。 |
| `apps/agent-first/agent_first/log_redaction.py` | 新增 | PCP-18：日志字段显式分类、个人信息最小化、错误信息净化、禁止推断守卫。 |
| `apps/agent-first/agent_first/audit_log.py` | 新增 | PCP-20：append-only 审计事件、哈希链校验、默认拒绝的读取策略。 |
| `tests/test_local_safety_contract.py` | 新增 | 上述三模块的正向 + 负向单元测试（34 条）。 |
| `apps/agent-first/run_safety_contract_evidence.py` | 新增 | 生成 `evidence.json`，并对生成的 Artifact 做自扫描。 |
| `artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/evidence.json` | 新增 | 机器可复核证据。 |
| `specs/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/README.md` | 新增 | 规格：目标、允许/禁止范围、验收表 SC-01…SC-10、停止条件。 |

未修改任何既有权威文档、既有 ADR 条款、既有工作流或 Foundation Spike。

## 实际执行命令与结果

```text
python -m compileall -q apps\agent-first                      -> exit 0
python -m unittest discover -s tests -p 'test_local_safety_contract.py'   -> 34 tests, OK
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -> 7 tests, OK
python -m unittest discover -s tests -p 'test_school_budget_contract.py'     -> 5 tests, OK
python -m unittest discover -s tests -p 'test_control_plane_persistence.py'  -> 4 tests, OK
python -m unittest discover -s tests -p 'test_local_web_prototype.py'        -> 5 tests, OK
python apps\agent-first\run_safety_contract_evidence.py        -> artifact_self_scan=clean
git diff --check                                              -> exit 0（无空白错误）
```

合计 **55/55** 测试通过（34 新增 + 21 既有回归）。无网络请求、无模型调用、无真实凭据、无费用。

## 已验证事实

1. **PCP-13**：`sk-…` 供应商 Key、`AKIA…`/`LTAI…` 云 AccessKey、`Bearer …`、`password: …` 赋值、`-----BEGIN … PRIVATE KEY-----` 假私钥块，以及 `api_key` / `access_key` / `credential_reference` 等凭据形字段名，在 **manifest / log / error / artifact** 四类 sink 全部被拒绝；拒绝信息与 findings 只含 rule ID 与已擦除位置，**不含被匹配的值**。
2. 干净合成 Manifest 在四类 sink 全部通过，说明拒绝不是"一律拒绝"的假安全。
3. **PCP-18**：44 个日志字段显式分类（operational 21 / personal 11 / secret 8 / forbidden_inference 4）；未分类字段被拒；personal 字段被最小化为 `[redacted]`；secret 与 forbidden-inference 字段整体拒绝而非"脱敏后保留"。错误信息中的绝对路径与邮箱被擦除、长度有界。
4. **PCP-20**：审计事件带稳定 ID（`audit-000001-<hash12>`）、角色、UTC 时间、有界动作（14 个）与有界理由码（11 个）；无 update/delete 接口；哈希链 `verify_chain()` 为真。读取默认拒绝：`system` 角色无读取权限；平台运维读不到学生内容类事件；学生只读到自己的事件。
5. 禁止推断在字段级与文本级均被拒绝：`判定…作弊`、`AI 替代率`、`auto-grading`、能力评分/画像等不产出。

## Artifact 与 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/secret_scan.py` | `C4367117EDC4975CBCB63E8E81DE5B855BDD513AFFAE5551255AB03795024142` |
| `apps/agent-first/agent_first/log_redaction.py` | `AF52161C24A6DC1687992387447459374FB0B662C95C85AC433A8D35C263BFA3` |
| `apps/agent-first/agent_first/audit_log.py` | `C746D45199F68D0F4599C4B4EACCC57CAE49DC203F60E6A65ACFFB4B2AA80DCC` |
| `apps/agent-first/run_safety_contract_evidence.py` | `7D01A77BA602C0634E2B0D21B8B125CF6BDA6A30FE1AC3ED6335466D1F0E203D` |
| `tests/test_local_safety_contract.py` | `EAA8F596198B078C11E9DB27CBF99D901557B986B5872200370C67E368389229` |
| `specs/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/README.md` | `641C596A86031D1F6665C95F22D62E49238AA026E96A63A88D73074A2B7C6F2A` |
| `artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/evidence.json` | `52151E1543EBF652D50C48EBD87E9FBD2160E30D12A337C49DC6D027E6623EB8` |

## 已知限制与新风险

**限制**

1. 字段名规则按**子串**匹配风险词，属保守取向：仅含 "secret" 字样的分节名也会被拒绝。该行为在自身 Artifact 上实际发生（分节键 `pcp_13_secret_scan`），处理方式是把键改名为 `pcp_13_sensitive_content_scan`，并把该次拒绝记录在 `self_scan.observed_field_name_false_positive`，而不是放宽规则。
2. 日志字段分类是显式白名单：新增字段必须先登记，否则写入被拒。这是有意的摩擦。
3. 审计日志是**内存实现**，只验证 append-only 与哈希链语义；不含持久化、保留期限、外部防篡改存储、运维身份。
4. 扫描是启发式，不是密钥管理器，不构成"已扫描即安全"的声明；不做熵检测，不做编码/混淆后检测。
5. `git diff --check` 不覆盖未跟踪文件，因此对 6 个新文件另做了空白与行尾检查（0 处问题，并已按项目惯例补齐文件末尾换行）。

**新风险**

1. 保守的字段名规则可能在后续 Artifact 中产生更多假阳性，需要命名纪律或后续引入更精确的词元匹配（属独立决策，不在本任务范围）。
2. `agent_first/__init__.py` 未导出新模块，调用方需从子模块导入；若后续要统一门面，需单独决策。

## 是否需要用户决策

- 需要决策（后续，不阻塞本任务）：PCP-20 的**访问者清单与访问范围**（哪些角色可读哪些事件）、PCP-19 的**保留期限与删除路径**、PCP-11/12 的**密钥服务选型与轮换周期**。这三项超出本机可做范围，需真实决定。

## 下一步

1. 将 `READINESS_CHECKLIST_2026-09-24.md` 中 PCP-13 / PCP-18 / PCP-20 从"未开始"更新为"本机部分完成（PARTIAL）"，并注明生产部分仍待决策——该更新涉及现有权威 Artifact，**需用户确认后执行**。
2. 其余 PCP 项依赖真实云账户、真实身份、密钥服务、数据库或保留期限决定，继续停在停止条件内。

## Git diff 摘要

- 新增未跟踪文件 7 个（3 个模块、1 个测试、1 个证据生成器、1 个 Artifact、1 个规格）。
- 修改既有文件：**0**（工作区中 `AGENTS.md`、`README.md` 等 `M` 状态为本任务之前既已存在，非本次改动）。
- `git diff --check`：通过（exit 0）。
- 空白/行尾检查（新文件）：0 处问题。

## Commit

`NONE` —— 未执行 commit 或 push，按任务边界要求保留给用户决定。

## 边界声明

- 未连接 ECS、未开端口、未部署、未创建 systemd 服务；
- 未创建/索要/保存/粘贴任何真实 Key、密码、私钥、AccessKey；
- 未读取环境变量或真实凭据文件；
- 未出网、未调用真实模型、未产生费用；
- 未接触真实账号、教师、学生或学校数据；
- 未运行学生代码或任意外来代码。
