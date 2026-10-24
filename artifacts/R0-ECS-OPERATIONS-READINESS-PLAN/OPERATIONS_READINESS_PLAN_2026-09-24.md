# ECS 控制面运维就绪计划（PCP-23 / PCP-25 / PCP-26）

- Task ID：`R0-ECS-OPERATIONS-READINESS-PLAN-001`
- Gate：Gate B，总体仍为 **PARTIAL**；生产就绪门禁仍 **0/28 关闭**
- 结论：**PASS（文档计划完整性）；实机和生产就绪均未验证**
- 状态：Proposed plan
- 日期：2026-09-24

## 目的与适用边界

这份计划为未来的 SkillShift 平台控制面整理运维步骤。现有 Ubuntu ECS 是控制面候选，只可承载平台 API、模型网关、预算许可、任务/提交元数据和教师 Web 后端。不得运行学生 Workspace、任意学生代码、本地大模型、浏览器自动化或通用 Shell。

当前学生在自己的网络中可以正常使用互联网。本计划不会限制学生上网，也不把普通互联网访问解释为违规。未来服务器的入站和出站策略只服务于平台运行，需按 API、DeepSeek、数据库、密钥服务、DNS 和系统更新等实际依赖列清后另行批准；目前没有选择具体开放端口或出站地址。

本文件是提案。文中的服务限制、告警阈值和回滚顺序都需要在实际部署前冻结，并在目标 Ubuntu/systemd 版本及合成环境中验证。

## 1. PCP-23：服务身份与主机加固（Proposed）

### 建议的服务边界

- 为应用创建独立、不可交互登录的普通服务账户；进程不得以 root 运行。
- 部署代码目录只读；运行状态目录单独授权写入。数据库/日志若由托管服务承担，不把它们放进代码目录。
- systemd unit 不放 API Key、密码或凭据引用；凭据未来只能经服务身份访问批准的托管密钥服务。
- 先使用 systemd 支持的文件系统、设备、权限提升、临时目录和资源限制能力形成最小权限基线。候选方向包括 `NoNewPrivileges`、`ProtectSystem`、`ProtectHome`、`PrivateTmp`、`PrivateDevices` 与显式可写路径。
- 不直接照抄未经验证的 syscall allowlist 或极端资源限制。Python 运行库、TLS、数据库驱动和日志功能可能需要系统调用或目录；每条限制先在测试服务中启用并做兼容性回归，再纳入生产模板。
- 应用不得提供执行任意命令、学生代码或任意 URL 的服务端接口。必要的出站访问只能来自明确的产品功能，并记录目的、协议、域名/服务和失败策略。

### 关闭 PCP-23 的证据

1. 冻结 unit 文件及文件/目录权限清单，证明服务账户不能修改代码、读取无关用户目录或访问凭据文件。
2. 在目标 ECS 的实际 systemd 版本做 `systemd-analyze verify` 和服务启动验证。
3. 用合成任务完成 API、数据库连接、托管密钥解析（只用测试密钥服务/假接口）、日志脱敏和优雅停止的回归。
4. 以服务账户做负向检查：不能写代码目录、不能读无关 home、不能提权、没有学生执行器/任意 shell 进程。
5. 保存 unit 文件哈希、脱敏后的权限/进程审计结果和回滚记录。

任何权限拒绝导致服务绕过限制运行、回退 root 或把密钥写入 unit/环境文件，均为停止条件。

## 2. PCP-25：发布与回滚（Proposed）

### 建议的发布顺序

1. 先在本机完成静态检查、单元/集成/负向测试与构建；失败则不打发布包。
2. 生成不可变发布包，记录版本、源码提交（将来建立 PR 后）、依赖锁定信息、构建流水线和包 SHA-256。未建立可信 CI/CD 和制品来源前，不从开发目录直接复制上线。
3. 发布前核对就绪门禁、备份和当前版本；确认业务端口仍关闭，直到网络入口及 TLS 决策和审核完成。
4. 以新版本目录或不可变制品安装；配置和密钥独立于制品。数据库变更遵循先兼容后收缩；版本切换前后执行健康检查和固定合成冒烟流程。
5. 只有健康检查通过、预算许可默认拒绝/上限测试通过、敏感内容负向测试通过、日志不含用户内容，才可判定该发布批次通过。一次人工确认和证据归档仍是必要环节。

### 回滚规则

- 应用回滚：停止新版本接收请求，切换回上一个不可变版本并检查健康状态；记录版本与制品哈希。
- 数据回滚：优先采用向前兼容的迁移。未演练备份恢复和反向兼容前，不自动回滚数据库 schema，也不删除迁移后数据。
- 密钥/供应商异常：通过托管密钥权限撤销或停用供应商档案；应用默认拒绝模型调用，显示服务不可用，不回退到未授权供应商。
- 预算/审计异常：停止新模型请求，保留待对账额度与审计记录；禁止通过删账本或重置月度计数“恢复服务”。
- 每次失败需区分应用错误、数据库错误、供应商不可用、预算拒绝、权限拒绝和回滚失败。恢复验证通过前保持维护状态。

### 关闭 PCP-25 的证据

制品来源校验、目标环境合成部署演练、健康检查输出、应用回滚演练、备份恢复演练、迁移兼容性证据、版本/制品哈希清单、人工审批记录。仅有本计划或部署命令清单不算关闭。

## 3. PCP-26：监控、告警与响应（Proposed）

### 允许记录的运维事实

- 服务活性、重启次数、CPU/内存/磁盘余量；API 请求总量、延迟分位数、状态码类别；数据库连接/错误类别；模型请求的供应商/模型档案 ID、授权结果、预留额度、待对账数量、供应商错误类别与响应时间。
- 仅使用短期请求关联 ID；禁止将提示词、学生回答、提交正文、完整响应、姓名/学号、Key、凭据引用明文、Cookie、绝对文件路径写入普通日志或告警。
- 安全和预算拒绝应计数并记录原因码，不记录被拒绝的敏感值。审计访问需另按 PCP-20 的访问者清单与 PCP-19 保留期落实。

### 候选告警（阈值均 Proposed）

| 类别 | 候选触发条件 | 运行动作 |
| --- | --- | --- |
| 服务健康 | 连续健康检查失败或短时间反复重启 | 暂停发布/流量；查看脱敏错误类别；必要时回滚应用版本。 |
| 可用性 | 5xx 比例或延迟连续超过暂定窗口 | 判断应用、数据库、供应商依赖；服务错误时关闭模型调用并提供明确降级状态。 |
| 预算 | 已结算+未结算占用接近上限、待对账积压或账本拒绝异常增加 | 预算许可失败关闭；通知费用责任人；不得自动提高上限或释放未知请求。 |
| 安全 | 凭据扫描拒绝、认证/授权拒绝异常增加、审计链校验失败 | 阻断相关功能；保留最小安全事件；升级给运维和安全责任人。 |
| 容量 | 内存、磁盘、数据库连接逼近限额 | 限流或拒绝新请求，避免丢弃数据和审计事件；结合 PCP-28 重新评估容量。 |

百分比、持续时间、告警渠道、值班责任人与供应商预算阈值必须由 PCP-17/26/28 的 Owner 确认；本任务不代替费用或可用性决策。

### 关闭 PCP-26 的证据

冻结监控字段与保留策略；在合成环境触发每类告警并演练响应；证明告警正文不包含学生内容/秘密；明确值班人、升级链路、维护窗口和事故记录位置；一次端到端事件演练记录。没有告警通道和负责人时不得声称监控就绪。

## 4. 网络与学生联网边界

- 学生的个人互联网访问属于其正常上课环境，不受本控制面计划限制。
- 学生在 SkillShift 中可提交任务允许的材料并使用平台提供的教育 Agent；当前 Agent 工具能力按既有 ADR 限制。不能把学生自行上网或其他工具使用推断成作弊。
- 服务入站端口尚未决定。未来可以评估只开放必要 HTTPS 入口、SSH 来源限制及云安全组/UFW 一致性，但 PCP-21/22 需要负责人和运维方决定及实机快照。
- 服务出站访问也需按 API 和供应商实际需求评估；无证据前不声称“服务器完全断网”或已有精确域名 allowlist。

## 5. 任务与门禁映射

| PCP | 当前可交付 | 仍缺证据/决定 | 当前结论 |
| --- | --- | --- | --- |
| PCP-23 | 服务身份、unit 限制和实机负向测试计划 | 目标系统 unit、权限快照、进程审计与合成服务验证 | 计划已形成；未关闭 |
| PCP-25 | 制品、发布、应用回滚、数据恢复与停止规则 | 数据库/CI 决策、演练、备份恢复证据 | 计划已形成；未关闭 |
| PCP-26 | 指标、隐私约束、告警候选和响应动作 | 阈值/渠道/Owner、保留期、端到端演练 | 计划已形成；未关闭 |

当前生产就绪清单仍为 **0/28 关闭**。本计划未关闭任何 PCP 项。

## 已修改文件及原因

- `specs/R0-ECS-OPERATIONS-READINESS-PLAN/README.md`：明确目标、范围、禁止项、验收和停止条件。
- `artifacts/R0-ECS-OPERATIONS-READINESS-PLAN/OPERATIONS_READINESS_PLAN_2026-09-24.md`：PCP-23/25/26 的 Proposed 操作计划与实机验收证据。
- `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md`：登记“计划已形成、未验证”，保持 0/28 关闭。
- `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_REPORT_2026-09-24.md`：追加本次清单状态快照，避免历史审计被误读为当前清单。
- `docs/CURRENT_STATE.md`、`docs/README.md`：同步阶段事实与文档入口。
- `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md`：修正上游 ADR-013 状态，消除 Accepted ADR 与旧 Proposed 描述不一致。

## 实际执行命令与结果

```text
Get-Content -LiteralPath 'docs\HANDOFF_R0_CONTINUATION_2026-09-24.md' -Raw -Encoding utf8
  -> 确认 Agent-first 与 Foundation 边界、ECS 状态及禁止事项
Get-Content -LiteralPath 'docs\adr\ADR-010-ecs-control-plane-and-managed-secret-boundary.md' -Raw -Encoding utf8
Get-Content -LiteralPath 'docs\adr\ADR-013-production-control-plane-readiness-gate.md' -Raw -Encoding utf8
Get-Content -LiteralPath 'specs\R0-PRODUCTION-CONTROL-PLANE-READINESS\README.md' -Raw -Encoding utf8
Get-Content -LiteralPath 'docs\architecture\DEPLOYMENT_ARCHITECTURE.md' -Raw -Encoding utf8
rg -n "PCP-23|PCP-25|PCP-26|ECS|systemd|监控|回滚|仅 22|UFW" docs artifacts specs
  -> 核对计划与 ADR/清单/既有主机审计，不连接 ECS
Test-Path -LiteralPath 'artifacts\R0-ECS-OPERATIONS-READINESS-PLAN\OPERATIONS_READINESS_PLAN_2026-09-24.md'
  -> True
Get-FileHash -Algorithm SHA256 -LiteralPath <各记录文件>
  -> 哈希见下表
Select-String -LiteralPath <各本任务文件> -Pattern '[ \t]+$'
  -> trailing_whitespace=0
git diff --check
  -> PASS
```

本任务未连接 ECS、未运行远程命令、未配置系统、未访问真实学生数据或凭据、未调用模型、未部署、未产生费用。systemd 指令均作为候选能力，具体可用性须在目标机版本验证。

技术参考（官方文档，只用于确认候选能力，不构成部署验证）：

- [Ubuntu 24.04 systemd.exec 手册](https://manpages.ubuntu.com/manpages/noble/man5/systemd.exec.5.html)：`ProtectSystem`、`ProtectHome`、`ReadWritePaths` 等服务文件系统隔离能力及局限。
- [Ubuntu Server UFW 文档](https://documentation.ubuntu.com/server/how-to/security/firewalls/index.html)：Ubuntu 的主机防火墙入口和 `--dry-run` 检查能力。

## 已知限制与风险

1. 服务器实况来自已有交接/审计文件，不是本次重新连接 ECS 核验；可能随时间变化，部署前必须刷新只读快照。
2. 云服务商未命名，因此安全组、托管密钥、云审计和制品服务细节保持 Proposed。
3. 关系数据库、备份恢复目标、日志保留、身份、费用阈值、告警渠道和域名未决，部署计划不能转为执行步骤。
4. systemd 的 sandbox 选项需要服务真实工作负载回归；错误配置可能造成不可用或诱发临时放宽权限，因此以实测兼容和失败关闭为准。
5. 学生上网许可与服务端出站策略是两项不同范围；本计划不改变前者，也不预设后者。

## 下一步与是否需要用户决定

本轮无需决定。接下来可在本地继续整理 PCP-17（费用对账方案）和 PCP-19（数据保留/退出决策草案）。后者涉及个人数据保留时间与删除规则，必须先给你看具体选项和影响，再进入任何真实数据实现。部署仍需等待 PCP 清单中所有必要项关闭和 ADR-013 门禁审查。

## SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `specs/R0-ECS-OPERATIONS-READINESS-PLAN/README.md` | `9258D74A00494769C1398C41D6270A3301FA6F7E929E0E7966A33A872E3F9F7A` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | `45CEA2130794BB582D88C21CF5B46BE40141AE89EADA2C45552DC66DE56DF509` |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_REPORT_2026-09-24.md` | `C818EE41BBCEA746818AD97FB7D1F6E5606F812CA451EB4901C80BCC7870D56D` |
| `docs/CURRENT_STATE.md` | `1654104E6EDE7172B1FCED739A33B6B91AF414CAD6F32BCE696800AD6685472B` |
| `docs/README.md` | `A6EA8936D027D86FB13B99E25499F80541F2764A6B3AF7381268E8D2062CE394` |
| `specs/R0-PRODUCTION-CONTROL-PLANE-READINESS/README.md` | `D43F867324D3A8EDC5E78F71A20593DD040F2856FDA21DFE6F05B2DCC9725A6A` |

本报告自身的 SHA-256 在最终回报中给出，避免自引用。

## Git diff 摘要

- 本任务新增 2 个文档；更新 3 个状态/索引/清单文件，并给原始就绪审计报告追加当前状态附录、修正就绪规格中的过期 ADR 状态。
- 工作区其他既有未提交修改保留；无删除、重置、清理、部署、推送或提交。

## Commit

`NONE`
