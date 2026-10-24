# DeepSeek 托管合成运行时契约报告

- Task ID：`R0-DEEPSEEK-HOSTED-SYNTHETIC-RUNTIME-001`
- Gate：B（运行时授权子阶段）
- 状态：**PARTIAL**

## 已验证范围

项目负责人已授权学校统一付费的 DeepSeek 官方托管合成路线。当前只验证默认拒绝的服务端接缝：

1. 未取得预算/授权许可时，不解析凭据、不调用传输层，并返回 `MODEL_UNAVAILABLE`。
2. 凭据缺失或撤销时，不调用传输层，错误不泄露凭据引用。
3. 假许可与假传输层下，请求只访问固定官方目标，且 payload 维持 `deepseek-flash`、无工具、无用户 ID 的合成约束。
4. 畸形供应商响应不会伪造教学指导，而是返回可见不可用状态。

## 实际命令与结果

```text
python -m compileall -q apps/agent-first/agent_first
python -m unittest discover -s tests -p 'test_deepseek_runtime_contract.py' -v
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
```

结果：静态编译 PASS；DeepSeek 运行时契约 4/4 PASS；DeepSeek 请求契约 4/4 PASS；通用国产网关 6/6 PASS；Gate A 回归 7/7 PASS。

## 可复核哈希

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/deepseek_runtime.py` | `FF1F8FA74B1F435CBEFCBC74B57A9DE0890DBDCAD71C42CB1D88629A39F3CA43` |
| `tests/test_deepseek_runtime_contract.py` | `96A5BDD0F57E1CD52060B017429ED0CC7D416E551E0870781E2E39A44EE91A34` |
| `docs/adr/ADR-008-deepseek-hosted-synthetic-runtime-authorization.md` | `CD9BD6247F19E0519B2E486436685BD6854D87AE0EF6514446E55EA601147FBF` |
| `specs/R0-DEEPSEEK-HOSTED-SYNTHETIC-RUNTIME/README.md` | `163F0FEE382775D23C54E3C0AF80AF4DA8B51FD5A964EEE2E2018A3E4246618F` |

## 未关闭项

没有真实 Key、凭据库、预算服务、身份/租户、告警、费用上限、供应商数据保留确认、部署或真实 DeepSeek 请求。假传输层 PASS 不等于网络连通、费用、模型质量、供应商可用性或真实凭据安全。

在这些项被独立配置和验证前，默认许可为拒绝，系统不得出网或扣费。

## Commit

`NONE`

