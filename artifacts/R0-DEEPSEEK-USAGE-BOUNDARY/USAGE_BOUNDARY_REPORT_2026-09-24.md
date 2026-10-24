# DeepSeek 请求长度与 usage 元数据边界报告

- Task ID：`R0-DEEPSEEK-USAGE-BOUNDARY-001`
- Gate：B，本机合成契约子任务
- 结果：**PARTIAL**。本机实现与假响应测试通过；PCP-17 仍未关闭，Gate B 和生产控制面均不能据此宣称就绪。

## 改动

- `apps/agent-first/agent_first/deepseek_contract.py`：所有消息内容按 UTF-8 总字节数限制在 16,384，错误不回显内容；测试验证刚好达到上限接受、超限拒绝。
- `apps/agent-first/agent_first/deepseek_usage.py`：强制解析响应 ID、模型、prompt/completion/total Token 及缓存命中数，校验合计并推导缓存未命中数；提供明确价格快照的纯本地成本估算，向上取整到分。
- `deepseek_runtime.py` 与 `scripted_guidance.py`：usage 只附着于进程内 Guidance；缺失或矛盾则失败关闭。
- `domain.manifest()` 保持字段白名单，提交 Manifest 不序列化 provider usage、请求 ID或估算费用。
- 新增 contract/usage/runtime/纵向闭环测试；更新探针规格、PCP-17 状态、项目当前状态和文档入口。

## 实际验证命令与结果

在 `F:\比赛\skillshift` 中使用 Python 3：

```powershell
$env:PYTHONUTF8='1'; python -m compileall -q apps\agent-first
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_usage_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_runtime_contract.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
```

结果（本任务原始快照）：编译 PASS；4 组针对性测试分别 6/6、3/3、5/5、8/8 PASS，共 22/22。最初回归共 94 项、93 PASS、1 项预先标记 skip，并排除了当时会发生 ACL 超时的 Windows isolation 模块。冻结 Agent-first 演示在内存重新生成后与 `demo.json` 字节一致；未覆盖写原 Artifact。Artifact 自扫描与 `git diff --check` 均 PASS。`evidence.json` 只记录合成断言，不含提示词、回答、真实身份、Key 或供应商日志。

## 价格快照与证据边界

纯函数使用快照 `deepseek-v4.1-flash-2026-09-10-r1`。合成用量 1,000,000 prompt（其中缓存命中 250,000）及 500,000 completion 得到峰时 551 分、闲时 276 分；1 Token 案例验证向上取整。此为公开价格快照下的本机估算，不是实际费用或对账结果。已复核[官方 Chat Completions usage 字段](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion/)：响应包含 `prompt_cache_hit_tokens`、`prompt_cache_miss_tokens`，且 `prompt_tokens_details.cached_tokens` 应与 cache hit 一致。代码要求三个字段一致，但未发起请求验证真实响应。

## 限制与风险

- 16,384 字节是 Spike 限制，不代表产品或课堂输入长度结论，也不是 Token 数上限。
- 本任务执行时 Windows AppContainer 隔离测试未运行；后续复核见下方更正。即使对应测试通过，也不能关闭 Foundation 的网络隔离、Provider 进程树集成、真实符号链接攻击和同步/重放缺口。
- 假响应验证不能证明供应商当前真实响应一定提供这些字段。若真实数据缺失或改变，当前运行时会安全失败，而非给出成本结论。
- 账单来源、逐请求预留/结算对账、费用责任人、告警阈值、月度重置、价格快照更新流程均未验证或决定。
- 未连接网络/DeepSeek/ECS；未用真实凭据或学生数据；未部署、未产生费用。

## Gate 与下一步

PCP-17 由“仅 Proposed 研究”变为“本机部分完成”。生产对账、账单和阈值仍属负责人/运维决策与外部证据依赖；当前部署就绪仍 **0/28 关闭**。继续执行已有不涉及真实账号的 Gate B 本机审计/回归；如果推进到真实响应或账单核验，先停止并请求授权与账号/费用边界决定。

## 后续回归状态更正（2026-09-24）

Task ID：`R0-GATE1-WINDOWS-TEST-RECHECK-001` 后续核验发现，本报告的 94 项测试结果是较早快照。其后一次全量回归为 101 项、100 PASS、1 SKIP，Windows isolation 独立复跑 7/7 PASS。再后续 `R0-TEACHER-TASK-AUTHORING-001` 加入两项测试，当前 `python -m unittest discover -s tests` 为 103 项、102 PASS、1 SKIP。唯一 skip 仍是 Foundation 真实符号链接攻击的 `WinError 1314`。详细命令和安全解释见 `artifacts/GATE-1-SECURITY-ROUTE-RESEARCH/GATE_1_SECURITY_ROUTE_RESEARCH_2026-09-24.md`。以上回归不改变 Gate B / PCP-17 的 PARTIAL 和生产就绪 0/28 状态。

## Git

- Git diff 摘要：新增 usage 模块、合成用量测试、规格和 Artifact；更新 DeepSeek 请求/运行时、纵向回归、就绪清单与当前状态文档。
- 工作区原有未提交改动很多，本任务只保留并在其上作范围内编辑；未提交。
- Commit：`NONE`

## 可复核 SHA-256

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/deepseek_contract.py` | `358A02275F6C401C01752AF975C66169F576BCB745B7B133FF2C6BDCA12CAF6D` |
| `apps/agent-first/agent_first/deepseek_usage.py` | `7ED6318F5C100843676604434876A968C336540E6FBB09C365CC76E816BC0531` |
| `apps/agent-first/agent_first/deepseek_runtime.py` | `B41E33C84D1858DF23384F591C7F001FADD64AA9515F60B3DE8B8C02A880B919` |
| `tests/test_deepseek_usage_contract.py` | `55705C4B88D2B908C54ACB6C0235509A023788E15849FC23CFF00F0D62F6375E` |
| `tests/test_agent_first_vertical_slice.py` | `94ADD5F54E6F55089D85D2BFC999712A1D9044D8C3B908D5E2BB89BB6E7DF7BB` |
| `specs/R0-DEEPSEEK-USAGE-BOUNDARY/README.md` | `77B853B9C0B599C1D7336EC939A775A081391F8EB6350E35B707C5AA6B8B70A6` |
| `artifacts/R0-DEEPSEEK-USAGE-BOUNDARY/evidence.json`（已追加当前全量回归结果） | `80EEA10B63445884291F965A55F0316A0530CD9FBDEACD0C3D8181CF3A433A3F` |
