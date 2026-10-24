# 产品方向修订与 Gate A 合成闭环报告

## Task ID

- `PRODUCT-DIRECTION-CLARIFICATION-001`：产品方向整合。
- `R0-AGENT-FIRST-VERTICAL-SLICE-001`：Gate A 合成教育 Agent 闭环。

## 当前 Gate 与结论

**Gate A：PASS（仅限确定性、合成、无本机自动执行的闭环）。**

项目负责人已确认首条路径为“教师创建任务 → 学生平台内教育 Agent 协作 → 学生验证/解释/补正 → 教师复核 → 学生重新提交”。本机 Code Workspace Foundation Spike 被保留为后续可选能力；其既有 PARTIAL/FAIL 不变，不能被称为安全沙箱。

Gate A 的 PASS 不代表真实模型能力、真实学生价值、学习效果、生产安全、部署或完整产品完成。

## 文件变化与原因

| 类别 | 文件 | 原因 |
| --- | --- | --- |
| 已确认决策 | `docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md` | 将项目负责人的产品方向确认写成权威文件。 |
| ADR | `docs/adr/ADR-004-agent-first-r0-delivery-boundary.md` | 将首条闭环与后续本机执行路线分离。 |
| 规格 | `specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md` | 定义 Gate A 范围、禁止项、验收和停止条件。 |
| 活跃规范与入口 | `README.md`、`docs/README.md`、产品/技术/质量规范、交接、状态、ADR-001 至 ADR-003、Foundation Spike spec | 消除“Foundation 必须先 PASS 才可做首条闭环”的冲突，同时保留安全事实。 |
| Gate A 实现 | `apps/agent-first/`、`tests/test_agent_first_vertical_slice.py` | 提供确定性适配器、版本化状态机、最小提交和 7 项测试。 |
| 演示 Artifact | `artifacts/R0-AGENT-FIRST-VERTICAL-SLICE/demo.json` | 保存四个冻结合成案例的可复核结果。 |

## 已执行验证

| 命令 | 结果 |
| --- | --- |
| `python -B -m py_compile apps/agent-first/agent_first/__init__.py apps/agent-first/agent_first/domain.py apps/agent-first/agent_first/scripted_guidance.py apps/agent-first/run_demo.py tests/test_agent_first_vertical_slice.py` | PASS。 |
| `python -B -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v` | PASS，7 tests。 |
| `python -B apps/agent-first/run_demo.py` | PASS，生成 4 个合成案例。 |
| `python -B -m unittest discover -s tests -p 'test_foundation_spike.py' -v` | PASS，5 tests；SKIP 1 个真实符号链接测试（`WinError 1314`）。 |
| `rg -n -i "^\\s*(import|from)\\s+(socket|urllib|http|requests|subprocess|os|pathlib)\\b" apps/agent-first/agent_first` | PASS，无匹配；Gate A 引导包无网络/宿主机工具导入。 |
| `git diff --check` | PASS。 |

一次早期命令 `python -B -m unittest tests/test_agent_first_vertical_slice.py -v` 因 `tests/` 不是 Python package 而失败；随后使用项目测试发现命令重跑并通过。一次测试发现教师复核理由过短，被正确拒绝；测试案例已改为满足最小理由要求后通过。

## 可复核哈希

```text
445603EE6324BBC101B7E27251B7BD6828A803A73E3CEB9A3DD2AB3E5957BCA1  docs/product/R0_AGENT_FIRST_DELIVERY_DECISION.md
FDBADFF8D42D7C0EF9122F95FE2146B828DD8562B44520303665DA00CF4FA799  docs/adr/ADR-004-agent-first-r0-delivery-boundary.md
D60A0F895EA8F5695DA1C7F6AED1AAAD4E6C23C8D148693C4B05405C66B87C72  specs/R0-AGENT-FIRST-VERTICAL-SLICE/README.md
73FC31D0257A39E1869031B63D158394CD1971E07A759955D0FC53AEA1B68CF5  docs/product/REQUIREMENTS_SPEC.md
550417541552C066212EBF572A9CB7907F0D78EDD88363B36C12276D6B2E37E5  apps/agent-first/agent_first/domain.py
4CBABBF2AC67BB096F464B1DD804C51988B59A1ABF325A91DC2A60801F789277  apps/agent-first/agent_first/scripted_guidance.py
937CE41C7EC9C4ED18B53BB5298F30896C3AFD7CB53331F866E9B54827D511B6  tests/test_agent_first_vertical_slice.py
C5FDCC25544A42C9C7F3143669B042A95383D007E60B0A658FE431529E4F5687  artifacts/R0-AGENT-FIRST-VERTICAL-SLICE/demo.json
```

修改前的 14 份权威文件快照位于 `prechange-docs/`，用于恢复和审计；没有覆盖 `wenben/` 内历史计划书。

## 已知限制与新风险

- `ScriptedGuidanceAdapter` 是确定性模拟，不是 LLM，也不证明教育 Agent 的实际质量。
- 当前是可复现的本地领域闭环与 JSON 演示，不是教师可用的图形界面、真实身份服务或部署。
- 未接触任何真实学生数据、模型 Key、密码、私钥、ECS 或外部网络。
- Foundation Spike 仍为 PARTIAL；未来引入本机代码、文件、命令、依赖或 Agent 网络工具时必须重新进入独立安全 Gate。

## 下一步与用户决策

下一步是 Gate B：决定真实教育 Agent 的模型供应商、服务端数据路径、成本上限、密钥保管和失败策略。该决定会改变隐私、费用与部署边界，不能由本报告或模拟适配器代替。

## Git

- 分支：`main`。
- 当前存在用户先前的跟踪修改和大量未跟踪 R0 材料；本任务未移动、删除或覆盖无关内容。
- Commit：`NONE`。
