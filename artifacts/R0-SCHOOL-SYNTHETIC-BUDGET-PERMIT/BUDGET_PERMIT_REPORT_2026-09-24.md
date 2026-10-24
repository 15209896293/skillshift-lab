# 学校合成探针预算许可报告

- Task ID：`R0-SCHOOL-SYNTHETIC-BUDGET-PERMIT-001`
- Gate：B（预算许可子阶段）
- 状态：**PARTIAL**

## 已验证范围

1. 默认学校策略拒绝请求且不预留预算。
2. 启用后，每次在请求前预留服务器配置金额；预留累计达到 10,000 分（100 元）后拒绝。
3. 非 DeepSeek、非学校统一、非合成数据或非 `deepseek-flash` 的档案不能获取许可。
4. 30 个并发请求最多允许 10 个 1,000 分预留，累计不超过 10,000 分。
5. 本地策略不能把批准的 100 元上限提高。

## 实际命令与结果

```text
python -m compileall -q apps/agent-first/agent_first
python -m unittest discover -s tests -p 'test_school_budget_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_runtime_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
```

结果：静态编译 PASS；预算许可 5/5 PASS；运行时 4/4 PASS；DeepSeek 契约 4/4 PASS；国产网关 6/6 PASS；Gate A 回归 7/7 PASS。

## 可复核哈希

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/school_budget.py` | `1EADA749BD8C28E485F4D9AE02CCAAC8C20CC323B4558DB8B82EACF49B9F5E9A` |
| `tests/test_school_budget_contract.py` | `905FD9A9C87B82EE01B4C763C92F8D73F6D6A04EF9859F26886B0911BEAB6796` |
| `docs/adr/ADR-009-school-synthetic-probe-budget-permit.md` | `692C3B2FB55F614E7DAA54D018E60D3E356C9F1D2285CC440FEF2E5C5FA3A623` |
| `specs/R0-SCHOOL-SYNTHETIC-BUDGET-PERMIT/README.md` | `5B8890FAC8EE0F2AFDE5DC6D99F34BEB4761E94B699214C99AB82B968E4A8CA2` |

## 限制

这是内存、单进程、保守预留的测试实现，不是实际费用账本。它没有价格计算、供应商用量回调、预留释放/结算、月度重置、持久化、身份/租户、管理员 UI 或真实调用。默认状态仍拒绝，因此实际消费仍为 0 元。

## Commit

`NONE`

