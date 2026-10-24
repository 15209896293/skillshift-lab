# ADR-005 OpenAI Responses 服务端网关

## Status

**Superseded（2026-09-24）**。项目负责人已明确“不使用 OpenAI API”；本 ADR 与对应代码/报告只保留为一次未发生真实调用的历史设计记录。它不再是 Gate B 路线，也不得配置、请求或部署。

当前 Gate B 的国内教育模型路线研究见 `../product/DOMESTIC_EDUCATION_AGENT_MODEL_ROUTE_RESEARCH.md`；在新的供应商决定前，保持确定性 Gate A 适配器。

## Context

Gate A proves only a deterministic, local teaching-workflow simulation. The project owner has authorized OpenAI as the candidate provider for a real education Agent. The product must not place provider keys in student clients, send real student data by default, or turn a model response into a hidden verifier, grade, cheating conclusion, or unrestricted computer-control tool.

OpenAI's official documentation states that API keys must not be exposed in code or public repositories and should be supplied through environment variables or a secret-management service. It also documents setting spend alerts and hard limits, and notes that Responses are stored by default unless `store: false` is used. See [Production best practices](https://developers.openai.com/api/docs/guides/production-best-practices) and [Responses migration guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses).

## Decision

1. The first real-model route will use the OpenAI **Responses API** through a server-side gateway only.
2. The student client never receives an OpenAI API key. A dedicated project/service key, when later created by the project owner, is injected only into the server runtime's secret store or environment.
3. Gate B uses frozen synthetic tasks only. Requests set `store: false`; no built-in web search, file search, MCP, function calling, browser control, shell, local file or code-execution tools are enabled.
4. The model ID is a server-side, versioned allowlist setting, not a student-controlled input. Its first production choice is **Proposed** until quality, latency and cost evaluation establishes a suitable model for the task.
5. The gateway fails closed when configuration is absent, malformed or unauthorized. It exposes a recoverable `MODEL_UNAVAILABLE` condition, not a fabricated Agent answer.
6. Model output is task guidance only. Student validation/interpretation and teacher review remain required; output cannot automatically grade, score, label cheating or establish ability.

## Consequences

- Gate B can implement and test contracts without an API key or network call.
- A live request needs a separate, owner-configured project key, spend guardrail and one bounded synthetic test; neither key nor request payload may be pasted into chat, source, Git or Artifact.
- Before real students or non-synthetic content, data purpose, notice, retention, access and appropriate institutional process remain separate decisions.
- The existing ECS remains a future control-plane candidate and may not run arbitrary student code.

## Evidence

- `../product/R0_AGENT_FIRST_DELIVERY_DECISION.md`
- `../product/REQUIREMENTS_SPEC.md`
- `../../specs/R0-OPENAI-RESPONSES-GATEWAY/README.md`
- [OpenAI Production best practices](https://developers.openai.com/api/docs/guides/production-best-practices)
- [OpenAI Responses migration guidance](https://developers.openai.com/api/docs/guides/migrate-to-responses)

## Related ADRs

- ADR-004 (Agent-first delivery boundary)
- ADR-003 (submission and data boundary)
