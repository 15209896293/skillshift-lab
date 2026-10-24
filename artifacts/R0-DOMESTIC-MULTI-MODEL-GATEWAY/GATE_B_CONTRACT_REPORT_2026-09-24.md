# Gate B 国产多模型网关契约报告

- Task ID：`R0-DOMESTIC-MULTI-MODEL-GATEWAY-001`
- 日期：2026-09-24
- Gate：B（本地契约子阶段）
- 总体状态：**PARTIAL**

## 已验证范围

已在本地、无网络、无真实密钥、合成任务范围内验证：

1. 国产 provider 仅能从固定允许列表选择；不接受任意 provider 或 endpoint。
2. 学校托管与教师 BYOK 档案只允许服务端凭据引用；档案序列化不含明文 Key 或 secret。
3. 学生问题不能修改 server-owned provider、模型、工具或联网搜索策略。
4. 未授权运行时明确返回 `MODEL_UNAVAILABLE`；不会伪造真实模型回答。
5. 确定性引导降级在 Guidance、事件与 Manifest 中可见；Manifest 不含凭据引用、作弊或能力结论。

## 实际命令与结果

```text
python -m compileall -q apps/agent-first/agent_first
python -m unittest discover -s tests -p 'test_agent_first_vertical_slice.py' -v
python -m unittest discover -s tests -p 'test_domestic_model_gateway_contract.py' -v
python -m unittest discover -s tests -p 'test_openai_gateway_contract.py' -v
git diff --check
```

结果：静态编译 PASS；Gate A 回归 7/7 PASS；国内网关契约 6/6 PASS；历史 OpenAI 无网络契约 4/4 PASS；`git diff --check` PASS。历史 OpenAI 测试只证明保留记录仍可运行，不是当前模型路线证据。

## 可复核文件哈希

| 文件 | SHA-256 |
| --- | --- |
| `apps/agent-first/agent_first/model_gateway.py` | `442411207D4E7ED6EA3F8AFF23CF6AAB4629983D67DA1022087D435D954B8F6F` |
| `apps/agent-first/agent_first/scripted_guidance.py` | `4CBABBF2AC67BB096F464B1DD804C51988B59A1ABF325A91DC2A60801F789277` |
| `apps/agent-first/agent_first/domain.py` | `550417541552C066212EBF572A9CB7907F0D78EDD88363B36C12276D6B2E37E5` |
| `tests/test_domestic_model_gateway_contract.py` | `083F69807660E3A59134603E1B6F18A330B0ADA569103398F5C608819CFC0FCE` |
| `docs/adr/ADR-006-domestic-multi-model-gateway-and-credential-boundary.md` | `30CE40DA6CA69681F96C3A76A37A4785699BAF8F6F82D175C06EA396DC533EEF` |
| `specs/R0-DOMESTIC-MULTI-MODEL-GATEWAY/README.md` | `A9D8E1530B76FED7E6701B9D54AC273DD75A033DA4ED5575FD1B7A9E44FBCABD` |

## 未关闭项与禁止跨越

尚未实现或验证：身份/租户、学校管理员与教师授权、真实凭据库、密钥轮换/撤销、预算原子扣减、供应商数据保留条款、真实模型质量/时延/费用、真实网络调用、RAG、部署、真实学生数据或试用。

因此这不是可用的真实 BYOK 功能，也不是永久免费 LLM；当前唯一可验证的基础降级是确定性引导。真实调用前，必须按 ADR-006 完成供应商、成本、数据路径与服务端运行时的独立决定和合成探针。

## Commit

`NONE`

