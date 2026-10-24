# Gate 1 受限执行安全路线研究

## 状态

- 主 Task ID：`G1-SECURITY-ROUTE-001`
- Gate：Gate 1
- 日期：2026-09-24
- 结论：**PARTIAL。** 已完成只读路线研究与 QA 审计；尚无实现或运行时安全闭合证据。
- 决策状态：**Proposed，未接受。** 不进入 Gate 2，也不创建教师—学生纵向闭环规格。

## 本 Gate 的受限协作任务

| Task ID | 目标 | 结果 |
| --- | --- | --- |
| `G1-SEC-WINPROC-001` | Windows 本机进程树、停止语义与最小权限路线研究。 | PARTIAL；Job Object 可作为可验证树终止机制，但当前实现只有根进程 `kill()`。 |
| `G1-SEC-NET-001` | Windows 网络隔离路线研究。 | PARTIAL；普通共享 `sys.executable` 的防火墙规则不足；AppContainer 零网络能力为首选 Proposed 路线。 |
| `G1-QA-FS-001` | Foundation Spike 覆盖、Artifact 与符号链接测试环境审计。 | PARTIAL；复跑仍为 4 PASS / 1 SKIP；发现根目录符号链接检查的静态缺口。 |
| `G1-ECS-CONTROL-PLANE-001` | ECS 控制面边界审计。 | PASS（规划边界）；仅基于项目文件审阅，未连接 ECS、未读取连接信息或敏感文件。 |

所有子任务均为只读；没有 Agent 修改权威规格、架构、ADR、源代码、系统安全策略或 ECS。

## 当前可复核事实

1. 当前 `LocalRestrictedProcessProvider` 使用普通 `subprocess.Popen` 启动 Python，超时只调用根进程 `kill()`；没有 Job Object、AppContainer、受限令牌启动、进程树枚举或 `STOP_UNCONFIRMED` 状态。
2. 当前环境的 Foundation 测试仍是 5 项中 4 项 PASS、1 项 SKIP；符号链接夹具被 `WinError 1314` 阻断。测试未生成子进程，不能证明树终止。
3. Provider 没有操作系统级网络隔离。没有一般 Shell API 或依赖安装入口，不等于 Python 运行进程没有网络能力；FS-04 继续为 FAIL。
4. `LocalRestrictedProcessProvider.__init__` 先对传入 root 调用 `resolve()`，再检查 `is_symlink()`；传入的根符号链接会先失去“链接”身份。现有测试没有覆盖根链接、Workspace 根链接、junction/reparse point 或 TOCTOU。
5. 本地事件只保存在内存 list；无服务端同步、持久 append-only、幂等、重放、重复、乱序、缺失或版本错误处理。FS-06 继续为 PARTIAL。
6. 现有 ECS 只可作为未来 API、教师 Web、模型网关、任务与提交包元数据的候选控制面；不得执行任意学生代码。此次未进行部署或服务器变更。

## Proposed 安全路线

### 首选：受限 Windows 本机 Spike

建立一个**单独授权、独立 Worktree/隔离目录**的最小原生启动器 Spike：

```text
专用合成 Python Runner
    ├─ AppContainer：零网络 capability
    ├─ 每 Workspace 的 AppContainer SID ACL
    └─ Job Object：不允许 breakaway，负责资源与进程树终止
```

- AppContainer 是文件、凭据、网络与进程隔离的 Proposed 主边界；对合成 Python 的兼容性尚无证据。
- Job Object 是 Proposed 生命周期边界。停止须以 `TerminateJobObject` 与 Job 内进程清空的双重观测为准；任何 API 错误、观测冲突或超时均只能记录 `STOP_UNCONFIRMED`，并阻止后续工具调度。
- Restricted Token 只可作为纵深防御，不能单独充当网络或完整沙箱边界。
- Windows Firewall/WFP 仅可作为受管设备上的补充或诊断路线。不得静默新增规则；共享 `sys.executable` 的程序路径规则无法可靠约束其子进程，不能单独关闭 FS-04。

相关官方资料：

- Windows Job Objects：https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- TerminateJobObject：https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-terminatejobobject
- AppContainer isolation：https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation
- AppContainer legacy applications：https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-for-legacy-applications-
- WFP Application Layer Enforcement：https://learn.microsoft.com/en-us/windows/win32/fwp/application-layer-enforcement--ale-

## Gate 2 前必须补齐的客观证据

| Spike 验收项 | 当前状态 | Gate 2 前的最小证据 |
| --- | --- | --- |
| FS-02 路径/符号链接 | PARTIAL | 在仅含临时目录的专用测试帐户或测试机中覆盖根/Workspace/目录/文件符号链接、junction/reparse point 与跨 Workspace 越界；创建权限不足即 BLOCKED，不能将 SKIP 记为 PASS。 |
| FS-04 网络与命令策略 | FAIL | 已验证 AppContainer token/profile、零网络 capability、Workspace ACL；隔离进程对受控端点的 TCP/UDP IPv4/IPv6、bind/listen 均失败，同时基线进程成功；隔离建立或验证失败必须 fail-closed。 |
| FS-05 进程树与停止 | PARTIAL | 合成父子进程均处于 Job；终止 Job 后双重确认无关联进程；模拟 API/观测失败时记录 `STOP_UNCONFIRMED` 且拒绝后续调度。 |
| FS-06 事件同步与防重放 | PARTIAL | 独立的服务端契约/实现规格、幂等标识、单调序列、重放/重复/乱序/缺失/错误版本负测与恢复状态；不得把本地内存列表当作服务端事实。 |

若 AppContainer + Job Object 无法以合成 Python 实验给出上述证据，必须停止本机不可信执行路线。届时只有在用户就供应商、费用、数据保留、执行位置与隔离生命周期作出明确决定后，才能研究**新的独立受管执行节点**；现有 ECS 仍被排除在执行平面之外。

## ECS 控制面审计

依据当前交接、ADR-001、技术规范与质量规范，未来控制面可考虑：身份、任务、教师复核、模型网关、最小事件索引和提交包元数据。当前不得实施：任意代码执行、学生 Workspace 挂载、模型密钥下发到 Node、学生个人数据处理、Artifact 全量上传、部署或公网服务。

对现有工作区仅进行了敏感文件名只读扫描；未发现项目内 `.env*`、`*.pem`、`*key`、`*credential*` 或 `*secret*` 候选。该扫描不是对主机、Git 历史或 ECS 的凭据安全保证。

## 文件一致性待处理项

`specs/R0-FOUNDATION-SPIKE/README.md` 当前仍写作 `Planned`，而正式交接、`docs/CURRENT_STATE.md` 与 `SPIKE_REPORT.md` 表明其已实施且结果为 PARTIAL。根据来源优先级，主控未静默修改该规格；这是需要在下一次**明确文档一致性修订**中处理的冲突记录，不改变本 Gate 的安全结论。

## 实际执行命令与结果

```text
python -B -m py_compile execution/providers/local_restricted_process.py apps/student-studio/reference_node.py apps/student-studio/run_foundation_demo.py tests/test_foundation_spike.py
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B apps/student-studio/run_foundation_demo.py
```

结果：编译通过；测试为 4 PASS / 1 SKIP；合成演示成功。见 `artifacts/GATE-0-WORKSPACE-EVIDENCE-AUDIT/GATE_0_AUDIT_2026-09-24.md` 的哈希与完整复跑记录。

附加只读检查包括：`git status --short --branch`、`git diff --stat`、项目文档与实现检索、Artifact SHA-256 校验、Windows 版本/权限/防火墙服务与 cmdlet 可用性查询，以及敏感文件名扫描。没有运行无限任务、开发服务器、提权、WFP/防火墙改动、进程终止实验或 ECS 操作。

## 已知限制与新风险

- AppContainer、专用 Python Runner 和 Workspace ACL 的兼容性未验证。
- Job Object 对特定 breakaway/非标准创建路径的覆盖必须由实际实验验证。
- 网络连接失败本身可能有歧义；证明须使用受控端点、基线连通性和身份/策略观测，不能从超时推断隔离成功。
- WFP、AppContainer profile、测试帐户或符号链接权限可能涉及管理策略；没有用户明确授权不得创建或更改。
- 当前 Spike 规格状态与实施状态不一致；在其被明确校正前，不能将 `Planned` 当作“尚未执行”，也不能将现有实现误标为 Verified。

## 下一步与用户决策

当前不需要用户为只读研究作决定。

进入任何 Gate 1 实现前，需要用户明确选择：是否授权一个仅处理合成脚本、无真实数据/模型/部署的 Windows 隔离 Launcher Spike（可能需要独立 Worktree 和受管测试环境）。若选择不验证该路线，是否允许另行制定“独立受管执行节点”方案；该方案将涉及执行位置、提供商、成本、数据保留和安全责任，不能默认启动。

## Git diff 摘要与 Commit

- 本 Gate 新增本报告；Gate 0 新增一份只读审计报告。
- 工作区原有 8 个已跟踪修改文件和既有未跟踪内容均未触碰或整合。
- Commit：`NONE`

## 后续实测与产品路线校正（2026-09-24）

本节更新后续 Windows Spike 与已接受的 Agent-first 产品决策；前文保留为当时的研究快照，不再单独代表当前路线结论。

1. **AppContainer 网络路线：Proposed 前提被反例推翻。** 后续 `artifacts/R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/NETWORK_DENIAL_REPORT.md` 与 `network-denial-probe.json` 记录：普通主机 IPv4/IPv6 TCP、UDP、bind/listen 基线均成功；零 capability AppContainer 子进程中 IPv4 UDP `sendto` 成功（退出码 82）。因此“仅零 capability AppContainer 即已提供网络隔离”不成立，不能据此关闭 Foundation FS-04。受控 UDP 反例优先于本报告原先的 Proposed 假设。
2. **进程树证据仅限原语。** `R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/SPIKE_REPORT.md` 的 WIL-01 证明一组标准 CreateProcess 父子进程处于同一 Job、终止后 PID 列表为空；这没有集成进 `LocalRestrictedProcessProvider`，也没有覆盖 breakaway/非标准子进程创建路径或 stop-unconfirmed 状态，因此 Foundation FS-05 仍 PARTIAL。
3. **Runner 启动证据不构成沙箱。** `R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE/COPIED_RUNNER_REPORT.md` 报告临时复制的 Python Runner 可在 AppContainer token 与 Job 中退出 0；这是一次限定合成运行。系统 Python 直接启动仍曾失败，网络反例也表明不能把该 profile 当作完整隔离边界。
4. **测试和哈希快照存在时效差异。** 较早报告记录 Windows Spike 4/4 PASS 及源码 SHA-256 `1DC9075180057DEAEB868ED8FBB7EEF391C0D5F78D8D9BE6375A181E2F30D089`、测试 SHA-256 `50292C6434AD82F4A125D0133515FF2A963B5916455E559785D9C18F785BD7E6`；当时工作区对应源码/测试哈希分别为 `6E790B52AA0984C557B4665046D089B6C17BEA0F941DD959B564AF92D33973BF`、`6F864865C064A791F6FDCF75007494E2D1019A6B3A2E1DFCA6D195FFF27FF017`。**本报告初次写成时**因避免重跑此前曾超时的 20 秒 `icacls` 复合 ACL 探针，排除了整个 Windows isolation 测试文件；该当时结论已被本报告“回归复核更正”附录中的后续 7/7 独立复跑和 101 项全量结果取代，不再代表当前测试状态。
5. **学生正常上网不在该 Sandbox 问题范围。** Agent-first 产品路径已由 `docs/adr/ADR-004-agent-first-r0-delivery-boundary.md` 及后续规格确认；学生使用平台与教育 Agent 时不被本 Spike 禁止访问互联网。FS-04 仅讨论未来可选的学生代码/进程执行边界，不能外推为课堂断网、平台 Agent 不联网或学校网络政策。
6. **Foundation 不再是 Agent-first 教师 Web 的前置门。** 较早“关闭 Foundation 后才可做教师 Web”的建议仅适用于本机不可信代码执行路径；与当前主线冲突的部分由较高优先级 R0 产品决策覆盖。Agent-first 页面/API 已在无本机执行边界下独立验证；这不关闭 Foundation FS-02/04/05/06。
7. **根符号链接的静态检查顺序缺口已有本机修复，但攻击实测仍缺。** `specs/R0-FOUNDATION-SYMLINK-GUARD-REPAIR/README.md` 与当前代码显示 Provider 在规范化前检查传入根路径，且有 mock 测试锁定调用顺序。该测试不创建真实链接；本轮 Foundation 测试仍因 `WinError 1314` 跳过真实目录符号链接攻击，所以 FS-02 继续 PARTIAL。当前 `local_restricted_process.py` SHA-256 为 `B7EBC64DE844C023CAE1B706043726741DB5E75CE666A0C35C138BA9CDF0C721`，`test_foundation_spike.py` 为 `E93717AEAD69F0ED644E9EC6D4FF36DD9898F8A99D5A1A3228893BA4EBA981DC`，二者与更新后的 Foundation Spike 报告一致；本报告第 2 节的早期 root-link 缺口描述是历史快照。
8. **网络反例可独立复核。** `NETWORK_DENIAL_REPORT.md` SHA-256：`B838B5EB1C854491E8408E6C53D1E4792E863992CCC7C0FE2396E13B912DFC70`；`network-denial-probe.json` SHA-256：`E8B9BA7B83D7809632004BD3604BF8E3FF87C5D0423F1229CA5EA2450F0260F3`。同目录 `probe.json` 的 SHA-256 为 `98B6BE9C64006ED907C59FF443BB2D73C896DC23E3D221BD3A5A9831C65ED938`。这些是既有合成 Artifact，不是本轮重新执行；它们没有改变本轮回归对 Windows isolation test file 的排除状态。
9. **Gate 0 标记的 Planned 冲突已解决。** 活跃规格 `specs/R0-FOUNDATION-SPIKE/README.md` 已更新为 Implemented / PARTIAL，并明确区分 Agent-first 与本机代码执行路线。Gate 0 报告第 1 节和本报告第 5 节保留的是修改前快照；不能再将其读作当前文件状态。

当前结论：Gate 1 **PARTIAL**，纯 AppContainer 网络方案不得标为推荐可用路线；Foundation Spike **PARTIAL**；Agent-first Gate A 按独立产品路径验证。没有修改网络策略、提权、连接 ECS 或使用真实数据。

## 2026-09-24 回归复核更正

Task ID：`R0-GATE1-WINDOWS-TEST-RECHECK-001`。本次在当前工作区重新执行完整套件和 Windows isolation 模块，复核旧报告中的 `icacls` ACL 超时是否仍可复现：

```text
$env:PYTHONUTF8='1'; python -m unittest discover -s tests
Ran 101 tests in 46.989s
OK (skipped=1)

$env:PYTHONUTF8='1'; python -m unittest discover -s tests -p 'test_windows_isolation_spike.py' -v
Ran 7 tests in 46.913s
OK
```

当前完整套件结果为 100 PASS、1 SKIP；唯一跳过项仍是 Foundation 真实目录符号链接攻击，原因为 Windows `WinError 1314` 权限不足。Windows isolation 模块单独复跑 7/7 PASS；Runner 探针向 stderr 输出临时 Python 路径解析警告，但对应测试按既定契约区分兼容/ACL 失败并通过。此前记录的 20 秒 `icacls` 超时本轮两次均未复现，因此撤销“当前不得运行整个模块”的操作性限制；这不证明 ACL/Runner 兼容性已解决，也不关闭网络、子进程树集成或真实链接攻击的安全 Gate。AppContainer UDP 网络反例仍有效。

验证边界：这是本机合成测试结果，不修改系统网络/ACL 策略，不提权，不连接 ECS，不使用真实模型或数据。完整套件命令退出码 0，模块复跑退出码 0。Commit：`NONE`。

后续 Gate A 合成任务文字配置加入两项 Web 测试后，全量套件复跑为 103 项、102 PASS、1 SKIP（退出码 0）；Windows isolation 源码与测试未改，Foundation 中唯一权限跳过仍为 `WinError 1314`。因此旧 ACL 超时仍未复现，网络隔离、Provider 级进程树终止、真实符号链接攻击和服务端同步/重放防护依然没有关闭；Foundation 继续 PARTIAL。详见 `artifacts/R0-TEACHER-TASK-AUTHORING/TEACHER_TASK_AUTHORING_REPORT_2026-09-24.md`。
