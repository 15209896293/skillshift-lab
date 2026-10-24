# 生产控制面就绪报告

- Task ID：`R0-PRODUCTION-CONTROL-PLANE-READINESS-001`
- Gate：B（部署前置）
- 日期：2026-09-24
- 结论：**PARTIAL** —— 就绪清单与门禁文档已产出；28 项前置全部未关闭，控制面不可部署。

## 1. 本任务实际执行的命令

全部为本地只读或新增文件操作，无网络、无远程调用、无凭据、无费用。

| # | 命令 | 结果 |
| --- | --- | --- |
| 1 | `git status --short` | 确认工作区 dirty，分支 `main`，基线 `c5d6081`，与手册第 10 节一致 |
| 2 | `git branch --show-current` / `git log --oneline -3` | `main`；HEAD = `c5d6081` |
| 3 | 目录与文件枚举（`Get-ChildItem`） | 确认 `docs/`、`docs/adr/`、`docs/product/`、`docs/architecture/`、`docs/quality/`、`specs/` 现有内容 |
| 4 | 读取 14 份权威文档 | 手册第 1 节强制读取顺序全部完成 |
| 5 | `git diff --check` | PASS（exit=0，无输出） |
| 6 | `git diff --name-only` | 9 个已跟踪文件为**交接前既有**修改，本次未改动任何已跟踪文件 |
| 7 | `Get-FileHash -Algorithm SHA256` | 4 个新增文件哈希已记录（第 5 节） |
| 8 | 冲突标记与尾随空白扫描 | 4 个新文件 conflict=ok，trailing_ws_lines=0 |
| 9 | 权威文档一致性断言检查（`Select-String`） | 见第 4 节 |

未执行：ECS 连接、端口探测、凭据操作、部署、模型调用、出网请求。

## 2. 新增文件与原因

| 文件 | 原因 |
| --- | --- |
| `docs/adr/ADR-013-production-control-plane-readiness-gate.md` | 手册第 6 节要求新增 Proposed ADR，定义部署门禁 |
| `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md` | 手册第 6 节要求新增规格，写明目标、允许/禁止范围、验收与停止条件 |
| `docs/architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md` | 手册第 6 节要求新增威胁模型 |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | 手册第 6 节要求新增验收清单，每项含 Owner/证据/停止条件 |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_REPORT_2026-09-24.md` | 本报告，作为可复核验证证据 |

未修改、未删除任何现有文件；未创建重复事实来源（新清单明确把 `specs/R0-ECS-CONTROL-PLANE-READINESS/README.md` 的 ECP-01..04 纳入更大范围而不重复定义）。

## 3. 验收标准结果

| ID | 条件 | 结果 | 依据 |
| --- | --- | --- | --- |
| PCR-01 | 七域均有前置项，每项含 Owner、证据、停止条件 | PASS | 清单 28 行，字段无空缺；域 A–G 全覆盖 |
| PCR-02 | 新增 ADR 为 Proposed，未把前置描述为已完成 | PASS | ADR-013 状态行 `Proposed`；全文无“已完成/已验证/可部署”表述 |
| PCR-03 | 威胁模型为 Proposed，含资产/角色/边界/威胁/缓解/残余风险 | PASS | 8 类资产、7 类角色、7 条信任边界、13 条威胁 |
| PCR-04 | 与既有权威文档一致 | PASS | 见第 4 节，7 项断言逐条命中出处 |
| PCR-05 | 未连接 ECS、未开端口、未配置凭据、未部署、未产生费用 | PASS | 第 1 节命令清单只含本地只读命令 |
| PCR-06 | `git diff --check` 通过；哈希可复核 | PASS | exit=0；哈希见第 5 节 |

**总体：PARTIAL。** 文档交付 PASS；就绪本身 0/28 关闭，因此“控制面可部署”为 FAIL，且按 ADR-013 门禁明确禁止部署。

## 4. 权威文档一致性审计

| 断言 | 出处 | 命中 |
| --- | --- | --- |
| 预算硬上限 100 元/月（10,000 分） | `docs/adr/ADR-009-school-synthetic-probe-budget-permit.md` | 3 |
| 探针模型固定 `deepseek-flash`、关闭思考、≤600 Token、无工具 | `docs/adr/ADR-007-deepseek-first-synthetic-provider-contract.md` | 3 |
| ECS 不执行任意学生代码 | `docs/adr/ADR-010-ecs-control-plane-and-managed-secret-boundary.md` | 1 |
| 不使用 Docker | `docs/adr/ADR-010-...md`、`docs/adr/ADR-002-local-restricted-workspace-boundary.md` | 1 / 2 |
| OpenAI 路线已否决 | `docs/adr/ADR-005-openai-responses-server-gateway.md` 状态 = `Superseded`；`docs/architecture/TECHNICAL_SPEC.md` 第 46 行；`docs/README.md` 第 18 行 | 确认 |
| 模型不可用须显式降级，不静默切换供应商 | `docs/adr/ADR-008-deepseek-hosted-synthetic-runtime-authorization.md` | 2 |
| Key 只经托管密钥服务解析，禁入 Git/env/DB/客户端/日志/Artifact | `docs/adr/ADR-010-...md` | 3 |

一致性检查中未发现相互冲突的权威表述。

## 5. 可复核哈希（SHA-256）

| 文件 | SHA-256 |
| --- | --- |
| `docs/adr/ADR-013-production-control-plane-readiness-gate.md` | `80768259DCD66AB3B70592A065B9B882D2099C59CF6D1E92B13092218F6F2DF5` |
| `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md` | `32739796D48AA0E6C0F13DEF5A2482E9540F94DDE350ED3DFFF2BD345FE28DE7` |
| `docs/architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md` | `6AE1A720B0A8763D801AAF9ED8DF1C43E788E6789891B1F298BC935CEB04CDD4` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | `69107C1AF71979CAB2EA7A9F0C61A889A6B315F06AD2827C3EE710D9FFEEC7EB` |

本报告自身的哈希无法自引用，需在提交后由外部命令计算。

## 6. ECS 现状（只读审计，非本次连接）

来源：2026-09-24 上一次已授权的服务器安全初始化会话记录。本任务**未再次连接 ECS**。

| 项目 | 状态 |
| --- | --- |
| 系统 | Ubuntu 24.04.5 LTS，kernel 6.8.0-139-generic x86_64 |
| 规格 | 2 vCPU / 3.5 GiB RAM / 40 G 磁盘（2.3 G 已用，7%）/ **无 swap** |
| 监听端口 | 仅 22（SSH）+ 回环 53（systemd-resolved）；**无业务端口** |
| SSH | `PermitRootLogin no`、`PasswordAuthentication no`、`PubkeyAuthentication yes`、端口 22 |
| 管理用户 | `skillshift`（sudo NOPASSWD），仅公钥登录 |
| UFW | active，deny incoming / allow outgoing / 仅 22/tcp |
| fail2ban | active，sshd jail，maxretry=5，bantime=3600 |
| 目录 | `/srv/skillshift`、`/srv/skillshift/artifacts`、`/var/log/skillshift` 已创建，属 `skillshift` |
| Python | 3.12.3（含 venv） |
| 未部署 | 无业务服务、无 systemd 服务、无数据库、无 Docker、无 API Key、无项目文件 |

结论：主机安全基线对应 PCP-24 已具备基础，但 PCP-21 的业务入口未定义，且 A–F 域全部未开始。**ECS 安全初始化不等于控制面就绪。**

## 7. 已知限制

1. 28 项前置全部未关闭；其中 17 项（含部分依赖项）阻塞于项目负责人或校内决策。
2. 威胁模型与 ADR-013 均为 Proposed，不构成已验证的安全承诺。
3. 本任务未做任何真实环境验证；清单中的“证据”是**待产出**的证据要求，不是已有证据。
4. 新文件尚未登记到 `docs/README.md` 与 `docs/PROJECT_FILE_GOVERNANCE.md` 的文档地图中，存在入口不一致；登记属于修改现有权威文件，需另行批准。
5. ECS 现状引用的是上一次会话记录，未在本任务重新核验；如主机状态已变化，第 6 节需重新审计。

## 8. 新风险

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| 清单被误读为“已就绪” | 存在一份完整清单容易被当成完成证明 | 清单与报告均声明 0/28 关闭；ADR-013 明写“必要但不充分” |
| 停止点被绕过 | 决策未定但工程先行 | ADR-013 第 6 条固定停止条件；禁止范围列明不得代替决策 |
| 入口不一致 | 新文档未登记进文档地图 | 列为待批准后续项，不自行修改权威文件 |

## 9. 未完成项

- 28 项前置的关闭（PCP-01 … PCP-28）。
- 新文件在 `docs/README.md`、`docs/PROJECT_FILE_GOVERNANCE.md` 的登记。
- ADR-013 从 Proposed 转为 Accepted（需项目负责人确认）。
- 威胁模型的复审与确认。

## 10. 下一步

1. 请项目负责人确认 ADR-013 是否接受为 Accepted。
2. 请对第 9 节列出的 17 项决策阻塞项给出方向（身份来源、费用所有者、数据保留、域名/入口、数据库与密钥服务选型）。
3. 在决策前，可先行完成清单第 10 节列出的本地项（PCP-13、15、16、18、20、23、25、26 的方案设计）。
4. 是否批准把新文件登记进文档地图。

## 11. 声明

本任务**未连接 ECS**、**未开放任何端口**、**未创建或存储任何 API Key / AccessKey / 凭据**、**未使用真实学生或教师数据**、**未部署**、**未修改现有工作流**、**未进行真实模型调用**、**未产生费用**、**未提交或推送本地仓库**。

## 12. Git diff 摘要

- 新增（untracked）：5 个文件（ADR-013、规格 README、威胁模型、就绪清单、本报告）。
- 修改：`NONE`（9 个已跟踪文件的改动为交接前既有状态）。
- `git diff --check`：PASS。

## 13. Commit

`NONE`

## 15. 后续本机证据与运维计划状态快照（2026-09-24）

本节补充并覆盖第 6、7、9、10 节中“全部 A–F 未开始”“所有计划项未开始”及旧 PCP 统计的当前状态；第 1–14 节仍保留原始审计与 ADR 接受记录。

- ADR-013 已被项目负责人接受；部署门禁有效，仍不授权部署。
- 当前清单统计：**0/28 关闭，18 未开始，7 本机基础/部分证据，3 Proposed 计划**。PCP-13/15/16/18/20 有本机合成证据；PCP-21/24 有已记录的主机基线事实；PCP-23/25/26 只有本次运维计划，未作系统变更或演练。
- PCP-23/25/26 计划路径：`../R0-ECS-OPERATIONS-READINESS-PLAN/OPERATIONS_READINESS_PLAN_2026-09-24.md`。详细证据边界、停止条件与哈希见该报告。
- 本轮没有连接 ECS，旧 ECS 状态仍只依据 2026-09-24 先前只读核验，不是本轮重验。
- 另修正了 `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md` 里 ADR-013 仍标 Proposed 的陈旧描述；现与 Accepted ADR 状态一致。

## 16. PCP-17 费用对账研究状态快照（2026-09-24）

- 当前就绪清单统计更新为：**0/28 关闭，17 未开始，7 本机基础/部分证据，4 Proposed 计划/研究**。
- PCP-17 的官方公开价格和本地接缝研究见 `../R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH/BUDGET_RECONCILIATION_RESEARCH_2026-09-24.md`。研究发现请求输入长度没有代码级上限，运行时未持久化返回 usage/模型元数据，且真实账号账单来源未核验；因此 100 元/月只能说是已确认硬上限，不能说实际对账或控制已就绪。
- DeepSeek 官方资料显示：当前 `deepseek-flash` 服务模型为 V4.1-Flash；价格会按缓存命中、输出 Token 和北京峰/闲时变化。上述均为公开网页快照，不代表供应商账单，也不改变 ADR-007 的模型档案决策。
- PCP-17 仍未关闭；本任务未调用供应商 API、未访问私有账单、未使用 Key、未产生费用。

## 17. PCP-17 本机用量边界实现状态快照（2026-09-24）

- Task ID：`R0-DEEPSEEK-USAGE-BOUNDARY-001`。
- PCP-17 新增本机部分证据：16,384 UTF-8 字节请求上限、响应 ID/模型/Token 一致性校验、缓存命中/未命中拆分、本地显式价格快照成本估算向上取整、Manifest 不序列化 provider usage。
- 现状统计调整为 **0/28 关闭，17 未开始，8 本机基础/部分证据，3 Proposed 计划**。PCP-17 状态由 Proposed 研究推进为本机部分完成，不意味着对账或生产结算已就绪。
- 验证结果与合成用例见 `../R0-DEEPSEEK-USAGE-BOUNDARY/USAGE_BOUNDARY_REPORT_2026-09-24.md` 和 `../R0-DEEPSEEK-USAGE-BOUNDARY/evidence.json`。
- 限制：无真实供应商请求、无真实账户账单、无凭据、无部署；价格仅为本地版本化快照；供应商实际缓存 usage 字段、账单对账、预留/结算闭环、告警阈值和月度重置仍未证实。

## 14. 项目负责人接受后的文档整合（2026-09-24）

原始审计完成时，ADR-013 为 Proposed。本报告之后，项目负责人明确接受 ADR-013；主控 Agent 已将其状态改为 Accepted，并将 ADR、Proposed 威胁模型及就绪规格登记进 `docs/README.md`、`docs/PROJECT_FILE_GOVERNANCE.md`、`docs/CURRENT_STATE.md` 和当前交接手册。

此决定只接受“部署前必须关闭 28 项门禁”的规则，不关闭任何前置项，也不授权连接 ECS、开放端口、配置凭据、真实模型调用、真实身份/学生数据或部署。威胁模型仍是 Proposed。

接受整合后，下列文件哈希为：

| 文件 | SHA-256 |
| --- | --- |
| `docs/adr/ADR-013-production-control-plane-readiness-gate.md` | `80768259DCD66AB3B70592A065B9B882D2099C59CF6D1E92B13092218F6F2DF5` |
| `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md` | `32739796D48AA0E6C0F13DEF5A2482E9540F94DDE350ED3DFFF2BD345FE28DE7` |
| `docs/architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md` | `6AE1A720B0A8763D801AAF9ED8DF1C43E788E6789891B1F298BC935CEB04CDD4` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | `69107C1AF71979CAB2EA7A9F0C61A889A6B315F06AD2827C3EE710D9FFEEC7EB` |
