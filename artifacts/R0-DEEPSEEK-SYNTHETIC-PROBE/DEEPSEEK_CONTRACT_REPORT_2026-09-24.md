# DeepSeek 首个合成探针契约报告

- Task ID：`R0-DEEPSEEK-SYNTHETIC-PROBE-001`
- Gate：B（供应商契约子阶段）
- 状态：**PARTIAL**

## 已验证范围

项目负责人选择 DeepSeek 后，已在本地、无网络、无真实 Key 范围内验证：

1. 首个档案固定为学校管理的 DeepSeek `deepseek-flash`，不含明文 Key、endpoint 或 SDK。
2. 请求只构造任务范围的 system/user 消息；关闭思考，最大输出为 600 Token，且非流式。
3. 请求不含 tools、tool choice、user ID 或学生可覆写的模型配置。
4. 其他 provider、其他模型或超过上限的输出均被拒绝；运行时未授权时明确返回 `MODEL_UNAVAILABLE`。

## 实际命令与结果

```text
python -m compileall -q apps/agent-first/agent_first
python -m unittest discover -s tests -p 'test_deepseek_contract.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
```

结果：静态编译 PASS；DeepSeek 契约 4/4 PASS；通用国产网关契约 6/6 PASS；Gate A 回归 7/7 PASS。

## 可复核哈希

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/deepseek_contract.py` | `EB9760738972BACB1189800BE3893BDF374C16A57020F36ABB0D75441E96325E` |
| `tests/test_deepseek_contract.py` | `D676BD56F1907649ADC6D2F7C52DD1679E5BE18F6D37FDD687F0667909013B2E` |
| `docs/adr/ADR-007-deepseek-first-synthetic-provider-contract.md` | `B1CB404120996CD4914749C8945A168D48464CADD8FF7B483435B26B04903F48` |
| `specs/R0-DEEPSEEK-SYNTHETIC-PROBE/README.md` | `78E09E84E299700B70FD9F9B75A8FAFF59C099B795FDF253E7CC27BF7F307924` |

## 未关闭项

未发生真实 DeepSeek 请求，未配置 Key 或费用，未选择托管/学校本地部署，未定义供应商数据保留条款，未实现身份/租户、凭据库、预算、撤销、配额、真实质量测试、RAG、部署或真实学生使用。

因此 DeepSeek 仅是首个已选供应商和可测试请求契约，不是已可用的真实教育模型能力。

## Commit

`NONE`

