# 合成预算生命周期契约验证报告（PCP-15 / PCP-16）

- Task ID：`R0-SYNTHETIC-BUDGET-LIFECYCLE-001`
- 类型：FEATURE / Gate B 控制面本机安全契约
- Gate：Gate B，总体仍为 **PARTIAL**
- 结论：**PASS（仅限本机合成账本状态机；不代表生产账本、真实费用或部署就绪）**
- 报告日期：2026-09-24

## 结论边界

本报告只验证未来预算服务的保守行为：先预留；只有确认未派发才释放；一旦已尝试派发且结果未知，仍占用预留，等待后续对账；合成结算不能高于预留。它不读取供应商、价格、账单或账户，也不产生任何费用。

## 已修改文件及原因

| 文件 | 原因 |
| --- | --- |
| `apps/agent-first/agent_first/synthetic_budget_ledger.py` | 显式 SQLite 路径的本机合成预算状态机与事务占用计算。 |
| `tests/test_synthetic_budget_ledger.py` | 预留、释放、未知派发、结算、重开、子进程并发与拒绝路径测试（7 条）。 |
| `apps/agent-first/run_synthetic_budget_lifecycle_evidence.py` | 生成并自扫描本任务机器可复核 Artifact。 |
| `artifacts/R0-SYNTHETIC-BUDGET-LIFECYCLE/evidence.json` | 固定合成流程及规则结果。 |
| `specs/R0-SYNTHETIC-BUDGET-LIFECYCLE/README.md` | 任务边界、Proposed 状态机、验收和停止条件。 |
| `artifacts/R0-PRODUCTION-CONTROL-PLANE-READINESS/READINESS_CHECKLIST_2026-09-24.md` | PCP-15/16 标为“本机部分完成”，汇总更新为 0/28 关闭、7 项部分证据。 |
| `docs/CURRENT_STATE.md`、`docs/README.md` | 把本机证据接入当前状态与文档入口；不改变生产范围。 |

## 实际执行命令与结果

```text
python -m compileall -q apps\agent-first
  -> exit 0
python -m unittest discover -s tests -p 'test_synthetic_budget_ledger.py' -v
  -> 7 tests, OK
python -m unittest discover -s tests -p 'test_control_plane_persistence.py' -v
  -> 4 tests, OK
python -m unittest discover -s tests -p 'test_school_budget_contract.py' -v
  -> 5 tests, OK
python apps\agent-first\run_synthetic_budget_lifecycle_evidence.py
  -> artifact_self_scan=clean
git diff --check
  -> exit 0
```

定向与相关回归合计 **16/16** 通过。完整测试集合在 Windows AppContainer 旧实验处未能在本轮有限时运行中收尾；它不是本任务验收条件，且 Foundation Spike 保持 PARTIAL，不得以此报告提升其状态。

## 已验证事实

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| SBL-01 | PASS | 同 reservation ID/金额幂等；改金额复用被拒；超过 10,000 分被拒。 |
| SBL-02 | PASS | `RESERVED` 才能进入 `RELEASED_BEFORE_DISPATCH`；`RECONCILIATION_REQUIRED` 释放被拒。 |
| SBL-03 | PASS | 仅已派发记录可结算；结算值不能超过预留；重复不同结算被拒。 |
| SBL-04 | PASS | 关闭并重开 SQLite 后，待对账状态仍保守占用，新增预留仍守住上限。 |
| SBL-05 | PASS | 两个有限时本机子进程各请求 6,000 分，结果一项接受、一项因上限拒绝；重开后占用为 6,000 分。 |
| SBL-06 | PASS | 只使用显式临时路径；无网络、无环境变量读取、无默认数据库路径。 |

状态机在本任务中仍是 **Proposed**：

```text
RESERVED --未派发失败--> RELEASED_BEFORE_DISPATCH
RESERVED --尝试派发--> RECONCILIATION_REQUIRED --合成结算--> SETTLED
```

## Artifact 与 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/synthetic_budget_ledger.py` | `E664AE0DB443D800F5574B9089AB51E9771672D6D33E20736D68A10BC11E1D68` |
| `apps/agent-first/run_synthetic_budget_lifecycle_evidence.py` | `3073C5D16592BFC0CFE21E93E4001B747E21F82164114993AF376678913EC181` |
| `tests/test_synthetic_budget_ledger.py` | `353FCC15226B8C56DEFC2A00D0507322B4976E776143A8C7E6D5751BD529EF2E` |
| `specs/R0-SYNTHETIC-BUDGET-LIFECYCLE/README.md` | `EFE508EDC96C5D534830F4EEBEDD1773652453F9B3B99A21BE2AB52999F5229B` |
| `artifacts/R0-SYNTHETIC-BUDGET-LIFECYCLE/evidence.json` | `85EFBB198F703A76C640B452A403B03D38C6775400B9911425CFAA37CF32E676` |

## 已知限制与新风险

1. SQLite 是本机合成验证工具，不是已选生产数据库；PCP-08、PCP-14 仍未关闭。
2. “已派发”是本地状态机的模拟输入，并不证明供应商收到、拒绝或扣费；真实对账来源、价格版本、告警和月度重置仍属于 PCP-17 的决策。
3. 状态机保守地把未知结果占满预留，能避免超额，但可能暂时低估可用额度；生产时需要正式对账流程，不能自动释放。
4. 当前多进程测试只覆盖同一台本机、两个受限子进程；未证明多服务器、高可用或生产数据库行为。

## 下一步与是否需要用户决定

下一步可继续完成不接触真实数据的 PCP-23（服务运行身份与主机加固方案）、PCP-25（部署与回滚草案）或 PCP-26（监控清单草案）。

不需要用户为本次本机证据再作决定。真正上线前仍需要项目负责人决定：生产数据库、密钥服务、真实费用对账/告警/月度重置、数据保留、真实身份与域名/TLS。

## Git diff 摘要

- 新增 5 个本任务文件（状态机、测试、证据生成器、Artifact、规格）。
- 更新 3 个权威状态/入口文件与 1 个就绪清单，只登记已验证的“本机部分完成”，未关闭任何生产前置项。
- 工作区已有其他未提交改动保持原状；未执行删除、重置、清理、提交、推送或部署。

## Commit

`NONE`
