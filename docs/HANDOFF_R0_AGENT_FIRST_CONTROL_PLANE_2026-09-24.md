# SkillShift R0 后续主控 Agent 交接手册

## 0. 手册状态

- 日期：2026-09-24。
- 目的：交接当前 Agent-first 产品原型、国产模型路线与合成控制面基础。
- 取代关系：不覆盖 `HANDOFF_R0_CONTINUATION_2026-09-24.md`；本手册补充其后已完成的 Gate A 网页交互和 Gate B 合成持久化证据。
- 当前总判断：**Gate A = PASS（合成、确定性范围）；Gate B = PARTIAL；Foundation Spike = PARTIAL；生产部署门禁仍 0/28 关闭。** PCP-17 已补成本估算所需的本机请求长度与用量契约证据，但真实账单/结算未验证。

本项目是研究主线下的教育 Agent 产品化基础设施。目标不是与 Codex/Cursor 比通用 Agent 能力，也不是检测外部 AI 或替学生完成电脑操作。R0 首先验证：教师能否低负担完成创建、复核和补正（A）；学生在允许 Agent 时能否完成验证、解释、纠错、接管或补正（B）。

## 1. 新 Agent 的强制读取顺序

1. `AGENTS.md`
2. `README.md`
3. `docs/README.md`
4. `docs/PROJECT_FILE_GOVERNANCE.md`
5. `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
6. `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`
7. `docs/product/R0_RESEARCH_TASK_EVIDENCE_CONTRACT.md`
8. `docs/product/REQUIREMENTS_SPEC.md`
9. `docs/architecture/TECHNICAL_SPEC.md`
10. `docs/quality/QUALITY_SPEC.md`
11. `docs/adr/ADR-004-agent-first-r0-delivery-boundary.md`
12. `docs/adr/ADR-006-domestic-multi-model-gateway-and-credential-boundary.md` 至 `ADR-013-production-control-plane-readiness-gate.md`，以及 `docs/architecture/PRODUCTION_CONTROL_PLANE_THREAT_MODEL.md`（Proposed）
13. `docs/CURRENT_STATE.md`
14. 与本次任务直接对应的 `specs/<TASK-ID>/README.md` 和 `artifacts/<TASK-ID>/`。

如文件冲突，按 `AGENTS.md` 的来源优先级处理；不得按方便程度选择旧文件。ADR-005 是已否决的 OpenAI 历史记录，绝不可重新作为当前方案。

## 2. 已确认的产品与模型决策

### 产品边界

首条闭环固定为：

```text
教师创建冻结合成任务
→ 学生在平台内向教育 Agent 提问
→ 学生提交任务关联的验证/解释/纠错/补正
→ 教师认可或请求说明、补正、环境处理
→ 学生回应并重提
```

首条闭环不读取/写入/运行学生电脑文件，不调用 Shell、浏览器控制、子进程或本机 Workspace。Foundation Spike 仍是未来可选 Code Workspace 的安全研究，不能被首条闭环的通过掩盖。

### 模型与费用边界

- 不使用 OpenAI API。
- 未来首个供应商：DeepSeek；合成探针模型固定为 `deepseek-flash`，关闭思考、输出最多 600 Token、无 tools、无联网搜索。
- 学校统一托管 API 是已授权的未来路线；学生永不配置或持有模型 Key。教师 BYOK 仅是未来服务端凭据引用能力，当前没有实现。
- 月度硬上限：100 元（10,000 分）；当前只验证本地预留，不是实际费用账本。
- 当前无真实 Key、无真实模型调用、无费用、无真实学生或教师内容出网。

### ECS 边界

现有 ECS 只可作为未来控制面候选：API、模型网关、预算许可、任务/提交元数据和教师 Web 后端。它绝不运行本地模型、任意学生代码、学生 Workspace、Shell 或浏览器自动化。当前未部署、未开放业务端口、未配置密钥或数据库。

## 3. 已实现内容与可信证据

| 事项 | 状态 | 关键文件 | 证据 |
| --- | --- | --- | --- |
| Gate A 确定性工作流 | PASS | `apps/agent-first/agent_first/domain.py`、`scripted_guidance.py` | `tests/test_agent_first_vertical_slice.py`，8/8；四个冻结案例 Artifact。 |
| 本机教师/学生网页与 JSON API | PASS，仅合成 | `agent_first/local_web.py`、`web/`、`run_local_web.py` | `tests/test_local_web_prototype.py`，8/8；教师可编辑固定字段结构内的四项合成任务文字；教师/学生视图和刷新恢复一致。短时页面仍非生产服务。 |
| 国产多模型网关契约 | PASS，仅无网络契约 | `model_gateway.py` | `tests/test_domestic_model_gateway_contract.py`，6/6。 |
| DeepSeek 请求与运行时接缝 | PASS，仅假传输层 | `deepseek_contract.py`、`deepseek_runtime.py` | 请求 6/6、运行时 5/5；无 HTTP/Key。 |
| DeepSeek 输入与用量边界 | PASS，仅合成契约；PCP-17 仍部分 | `deepseek_usage.py` | 请求契约 6/6、用量估算 3/3、运行时 5/5；真实请求和账单未验证。官方余额接口仅返回余额状态/分项，不是消费流水；对账证据见 `artifacts/R0-DEEPSEEK-BUDGET-RECONCILIATION-RESEARCH/BUDGET_RECONCILIATION_RESEARCH_2026-09-24.md` §7。 |
| 100 元预算许可 | PASS，仅内存契约 | `school_budget.py` | 5/5；不是实际账本。 |
| 合成控制面持久化 | PASS，仅本机 SQLite | `control_plane_persistence.py` | `tests/test_control_plane_persistence.py`，4/4；可重开回放、幂等/冲突、并发上限。 |
| 控制面本机安全契约 | PASS，仅本机合成 | `secret_scan.py`、`log_redaction.py`、`audit_log.py` | `tests/test_local_safety_contract.py`，34/34；对应 PCP-13/18/20 仅部分完成。 |
| Foundation Spike | PARTIAL（仅可选本机代码执行路径） | `execution/providers/`、`apps/student-studio/` | AppContainer 零 capability 实测仍允许 IPv4 UDP；Job Object 仅有标准父子进程原语证据、未集成 Provider；根链接静态检查顺序已修复但真实链接攻击仍受 `WinError 1314` 阻断；服务端同步/重放未实现。Foundation 不阻止无本机代码执行的 Agent-first 教师 Web，亦不限制学生自行上网。 |

完整报告：

- `artifacts/R0-AGENT-FIRST-VERTICAL-SLICE/demo.json`
- `artifacts/R0-LOCAL-WEB-PROTOTYPE/WEB_PROTOTYPE_REPORT_2026-09-24.md`，报告 SHA-256：`9CCB26DF93A9A9FAAB2DC71F5483585DD8A89ACF2C1EE1310F61B350132E5CA6`
- `artifacts/R0-TEACHER-TASK-AUTHORING/TEACHER_TASK_AUTHORING_REPORT_2026-09-24.md`，任务规格与实现证据；`evidence.json` SHA-256：`939A77C4C69DDFB5C0FBEE2A9E621CFAB1BAA16EA5E90D359FF97780B1C8E259`
- `artifacts/R0-SYNTHETIC-CONTROL-PLANE-PERSISTENCE/PERSISTENCE_CONTRACT_REPORT_2026-09-24.md`，报告 SHA-256：`2D106B71611AFFE11C021B6533A11451F6EFC1E1CE002B75401227B56DF165E9`
- `artifacts/R0-LOCAL-CONTROL-PLANE-SAFETY-CONTRACT/SAFETY_CONTRACT_REPORT_2026-09-24.md`
- `artifacts/R0-DEEPSEEK-HOSTED-SYNTHETIC-RUNTIME/HOSTED_RUNTIME_CONTRACT_REPORT_2026-09-24.md`
- `artifacts/R0-SCHOOL-SYNTHETIC-BUDGET-PERMIT/BUDGET_PERMIT_REPORT_2026-09-24.md`
- `artifacts/R0-FOUNDATION-SPIKE/SPIKE_REPORT.md`
- `artifacts/R0-DEEPSEEK-USAGE-BOUNDARY/USAGE_BOUNDARY_REPORT_2026-09-24.md` 与 `evidence.json`（当前 evidence.json SHA-256：`80EEA10B63445884291F965A55F0316A0530CD9FBDEACD0C3D8181CF3A433A3F`）

## 4. 可安全复跑的命令

在仓库根目录 PowerShell 中执行；均不需要网络、Key、服务器或长期服务：

```powershell
$env:PYTHONUTF8='1'
python -m compileall -q apps\agent-first
python -m unittest discover -s tests -p 'test_control_plane_persistence.py' -v
python -m unittest discover -s tests -p 'test_local_web_prototype.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_runtime_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_usage_contract.py' -v
python -m unittest discover -s tests -p 'test_school_budget_contract.py' -v
git diff --check
```

初始定向组曾为 **35/35 PASS**。2026-09-24 usage 边界后，四组相关定向测试为 **22/22 PASS**。Windows 重查时全量为 101 项，教师任务文字配置新增 2 项后最新全量 `python -m unittest discover -s tests` 为 **103 项、102 PASS、1 SKIP**；Windows isolation 模块此前独立复跑 **7/7 PASS**，此前记录的 `icacls` 超时两次均未复现。唯一 skip 是 Foundation 真实目录符号链接攻击因 `WinError 1314` 权限不足；测试通过不等于 Foundation 安全门关闭，AppContainer IPv4 UDP 反例、Provider 未集成 Job Object、真实链接攻击和服务端重放同步缺口仍在。

网页演示仅在人工查看时短时启动：

```powershell
Set-Location apps\agent-first
python run_local_web.py --port 8765
```

它仅绑定 `127.0.0.1`。查看完必须停止；不得改为公网、局域网或 ECS 监听。

## 5. 当前缺失项（不可伪称已完成）

1. 真实用户登录、学校身份、角色授权与租户隔离；
2. 生产关系数据库、迁移、备份、加密、数据保留/退出与操作审计；
3. 托管密钥服务、服务身份、持久且可对账的预算账本；
4. 真实 DeepSeek 合成探针、费用核对、监控与故障处理；
5. ECS 部署、域名、HTTPS、网络入口、CI/CD；
6. 真实教师流程验证、真实学生非计分试用、研究授权或研究数据导出；
7. 安全的本机代码执行、Windows 网络隔离、进程树终止与符号链接攻击验证。

任何上述项都不能由“当前测试通过”推导出来。

## 6. 下一位 Agent 的建议首个任务

已完成 **RESEARCH / DOC** 任务：`R0-PRODUCTION-CONTROL-PLANE-READINESS-001`。ADR-013 已被项目负责人接受；就绪清单仍为 0/28，控制面不可部署。

- 证据：`artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_REPORT_2026-09-24.md`；详单在 `READINESS_CHECKLIST_2026-09-24.md`。
- PCP-13、PCP-15、PCP-16、PCP-17、PCP-18、PCP-20、PCP-23、PCP-25、PCP-26 仍有生产侧未关闭项。继续只做无需外部决策的本地工作；不得连接 ECS、开放端口、创建/索要/粘贴 Key、使用真实数据、部署或真实调用模型。

在该任务通过并获得相关决定前，不得把当前网页/API/SQLite 原型部署到 ECS。

## 7. 主控与多人协作规则

1. 主控 Agent 是唯一架构、规格和权威文档整合者。
2. 每个子任务必须含 Task ID、目标、允许范围、禁止范围、验收证据和停止条件。
3. 多个 Agent 不得同时改同一权威文档；主控最终统一整合。
4. 大型多文件工作优先独立 Worktree；但当前 `main` 有大量未提交及未跟踪的项目状态，创建 Worktree 前必须先确认不会遗漏这些文件。
5. 命令必须有界、可停止、可验证；禁止无限循环、无期限服务器、无期限等待或用 sleep 代替推进。
6. 每完成一个 Gate，把状态、证据、限制和下一步写入文件；聊天不是项目事实。
7. 不自动 commit、push、deploy、delete、reset 或 clean。

## 8. 绝对禁止与研究伦理边界

- 不处理真实学生数据、密码、私钥、AccessKey、模型 API Key；不要求用户在聊天发送它们。
- 不把日志、粘贴、过程缺失、相似度或 Agent 输出当作作弊、学生能力、努力程度或外部 AI 使用证明。
- 不自动评分、不生成能力画像、不输出“AI 替代率”。
- 不让现有 ECS 或未通过 Foundation Spike 的 Provider 执行任意学生代码。
- 不把确定性引导、假传输层、SQLite 合成测试或局部网页演示称为真实模型能力、生产可用、真实课堂效果或部署完成。

## 9. 汇报模板

每次汇报必须包含：

```text
Task ID：
当前 Gate：
已修改文件及原因：
实际执行命令与结果：
PASS / PARTIAL / FAIL：
Artifact、哈希或可复核证据：
已知限制和新风险：
下一步：
是否需要用户决策：
Git diff 摘要：
Commit：NONE（除非用户明确要求提交）
```

## 10. Git 工作区事实

- 当前分支：`main`；基线提交：`c5d6081`。
- 工作区为 dirty，既有修改和大量未跟踪的 R0 文档、Artifact、代码均是当前项目状态的一部分；不要用 `git reset --hard`、`git clean`、批量删除或覆盖来“整理”。
- 本次交接没有创建 commit、push 或部署。
