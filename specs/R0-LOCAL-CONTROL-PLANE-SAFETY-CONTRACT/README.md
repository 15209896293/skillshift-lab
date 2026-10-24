# R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT：本机合成安全契约

## 状态

- Task ID：`R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT-001`
- 类型：FEATURE / 本机安全基础
- 状态：**Implemented / Verified（2026-09-24；仅限本机合成数据与假凭据文本）**。
- 覆盖部署前清单：PCP-13、PCP-18、PCP-20（仅"本地可做"部分）。
- 上游：ADR-010、ADR-013、`docs/architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md`、`docs/quality/QUALITY_SPEC.md`。

## 目标

在**不接真实云账户、不接真实模型、不出网、不使用真实凭据**的前提下，用本机代码与测试固定三条安全契约的最小形状：

1. PCP-13：敏感内容的静态扫描与拒绝（Manifest / 日志 / 错误 / Artifact 四类 sink）；
2. PCP-18：日志字段分类、个人信息最小化与错误信息净化；
3. PCP-20：最小 append-only 审计事件结构与默认拒绝的读取边界。

本规格只证明"契约存在且可被测试拒绝"，**不证明生产部署就绪**。

## 允许范围

- 在 `apps/agent-first/agent_first/` 新增 `secret_scan.py`、`log_redaction.py`、`audit_log.py`；
- 在 `tests/` 新增 `test_local_safety_contract.py`（正向 + 负向）；
- 在 `artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/` 生成 `evidence.json`；
- 只使用合成数据与**明显为假**的凭据文本（`sk-synthetic-...`、`AKIASYNTHETIC...`、`Bearer synthetic-...`、`-----BEGIN PRIVATE KEY-----` 假体）；
- 运行有界的本机检查：`compileall`、定向单元测试、`git diff --check`、Artifact 自扫描与 SHA-256。

## 禁止范围

- 不连接 ECS、不开端口、不部署、不创建 systemd 服务；
- 不创建、索要、保存或粘贴真实 Key、密码、私钥、AccessKey；
- 不读取环境变量中的凭据，不读取真实 `.env` / `settings.json`；
- 不接真实 DeepSeek 或其他供应商，不出网，不产生费用；
- 不接真实账号、教师、学生或学校数据；
- 不修改现有权威文档、既有 ADR 条款、既有工作流或 Foundation Spike；
- 不自动 commit、push、删除、reset、clean。

## 验收

| ID | 条件 | 证据 |
| --- | --- | --- |
| SC-01 | 假凭据与凭据形字段名在 Manifest / 日志 / 错误 / Artifact 四类 sink 均被拒绝。 | `test_local_safety_contract.py::SecretScanTests`；`evidence.json.pcp_13_sensitive_content_scan.refusals`。 |
| SC-02 | 扫描结论与拒绝信息**不含被匹配的值**，规则命中只暴露 rule ID 与已擦除的位置。 | `SecretScanTests::test_findings_never_carry_the_matched_value`、`test_refusal_message_never_carries_the_matched_value`。 |
| SC-03 | 干净合成 Manifest 在四类 sink 全部通过（避免"一律拒绝"的假安全）。 | `SecretScanTests::test_clean_synthetic_manifest_passes_every_sink`；`clean_synthetic_manifest_accepted=true`。 |
| SC-04 | 日志字段必须显式分类：未分类字段被拒；personal 字段被最小化为占位符；secret 与 forbidden-inference 字段整体拒绝而非"脱敏后保留"。 | `LogRedactionTests`；`evidence.json.pcp_18_log_redaction.positive_case / negative_cases`。 |
| SC-05 | 错误信息净化：绝对路径与邮箱被擦除、长度有界；含凭据形文本或禁止结论的错误被拒绝。 | `LogRedactionTests::test_error_message_*`；`error_sanitization`。 |
| SC-06 | 审计事件只追加：无 update/delete 接口，事件带稳定 ID、角色、UTC 时间、有界动作与有界理由码，哈希链可验证。 | `AuditLogTests`；`evidence.json.pcp_20_audit_log.event_ids / chain_verified`。 |
| SC-07 | 审计读取默认拒绝：角色不在策略内即拒绝，平台运维不得读取学生内容类事件，学生只读自己的事件。 | `AuditLogTests::test_student_reads_only_own_events`、`test_platform_operator_cannot_read_student_content_events`、`test_system_role_has_no_read_access`。 |
| SC-08 | 不产出作弊、能力、外部 AI 使用或自动评分结论：字段级与文本级均有拒绝规则。 | `LogRedactionTests::test_log_text_asserting_a_cheating_verdict_is_refused`、`test_error_message_refuses_prohibited_conclusions`；`forbidden_inference_rules`。 |
| SC-09 | 规格、测试、Artifact 可互相定位：本文件 → 模块路径 → 测试用例名 → Artifact 字段。 | 上表各行的 `module` / `module` 路径与 `evidence.json` 字段名。 |
| SC-10 | 生成的 Artifact 自身通过同一契约扫描。 | `evidence.json.self_scan.result = "clean"`。 |

## 已知限制

- 字段名规则按**子串**匹配风险词，属保守取向：一个仅含 "secret" 字样的分节名也会被拒绝。实测该行为发生在自身 Artifact 的分节键上（`pcp_13_secret_scan`），处理方式是把分节键改名为 `pcp_13_sensitive_content_scan`，并把该次拒绝记录在 `self_scan.observed_field_name_false_positive`，而不是放宽规则。
- 字段分类词表是**显式白名单**：新增日志字段必须先登记，否则写入被拒。这是有意的摩擦，不是遗漏。
- 审计日志是**内存实现**，仅验证 append-only 与哈希链语义；不含持久化、保留期限、外部防篡改存储与运维身份。
- 扫描规则是启发式，不是密钥管理器，也不构成"已扫描即安全"的声明。
- 全部结论限定为**本机合成安全契约**，不代表生产控制面、ECS 加固或部署就绪。

## 停止条件

需要真实云账户、真实身份、密钥托管服务、数据库服务、数据保留期限、ECS 操作、域名、TLS、真实模型调用或任何费用决定时，停止在本规格范围内推进并另行决策。

## 关联文件

- 代码：`apps/agent-first/agent_first/secret_scan.py`、`log_redaction.py`、`audit_log.py`
- 证据生成器：`apps/agent-first/run_safety_contract_evidence.py`
- 测试：`tests/test_local_safety_contract.py`
- Artifact：`artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/evidence.json`
- 报告：`artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/SAFETY_CONTRACT_REPORT_2026-09-24.md`
