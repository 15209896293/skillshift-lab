# P0-A First Five Public-Source Candidates: Interim Report

## Status and Scope

- **Research task:** P0A-WP1 / P0A-WP2; this report is a P0-A intermediate artifact.
- **Date:** 2026-09-21
- **Coverage:** `P0A-PUB-001`, `P0A-PUB-002`, `P0A-PUB-008`, `P0A-PUB-009`, and `P0A-PUB-010`.
- **Completed in this pass:** five formal design-stage audit records, each with a task summary, traditional expected output, possible agent path, human intervention points, failure modes, machine-verifiable evidence plan, assessment-value analysis, dual-track direction, limitations, and P0-C recommendation.
- **Not completed in this pass:** collection of a local historical task; an agent-assisted run; human observation; timing; a final verifier implementation; any student evaluation; or a P0-A Gate decision.

## Evidence Classification

All five entries are **public-source candidates**. They are not asserted to be local historical school tasks. The registered source basis is either public teaching material or a search-derived theme. In particular, `P0A-PUB-009` still lacks an exact verified public assignment sheet and is intentionally marked with a source-gap limitation.

The records use the following public materials only as task-pattern support:

- Xiamen University Database Lab user-behavior teaching case: <https://dblab.xmu.edu.cn/post/useranalysis/>
- Xiamen University Database Lab aggregation example: <https://dblab.xmu.edu.cn/blog/1005/>
- Xiamen University Database Lab data-cleaning example: <https://dblab.xmu.edu.cn/blog/5419/>

These sources do not prove local curriculum history, a specific local rubric, or any observed agent outcome.

## Conditional P0-C Candidate View

| Task ID | Candidate status | Why | Required evidence before selection |
| --- | --- | --- | --- |
| P0A-PUB-001 | Strong, conditional | Supports a bounded SQL/MySQL slice; database state can be verified. | Exact task/fixture, data dictionary, MySQL verifier, at least one recorded run. |
| P0A-PUB-002 | Strong, conditional | Tests semantic verification and diagnosis beyond query generation. | Teacher-confirmed metric definitions and hidden abnormal fixtures. |
| P0A-PUB-008 | Strong, conditional | Well-suited to fixture-based output and lineage checks. | Cleaning policy, licensed fixture, output schema, recorded run. |
| P0A-PUB-009 | Possible, conditional | Strong reconciliation potential but public assignment provenance is incomplete. | Attributable task, privacy-safe multi-source fixture, mapping and reconciliation contract. |
| P0A-PUB-010 | Possible, conditional | Rich collaboration/verification signals but scope must remain narrow. | De-identified fixture, deterministic metric contract, managed execution plan. |

No candidate is selected for P0-C by this report. The labels are design recommendations to be tested, not evidence of viability.

## Cross-Task Design Findings to Test

1. Generated code or SQL is insufficient evidence; each candidate needs a deterministic check of real state, output rows, aggregate results, or reconciled invariants.
2. The likely human role is requirement clarification, assumption control, verification, error diagnosis, and responsibility for final interpretation. This is a hypothesis to evaluate through run records, not a measured conclusion.
3. Foundation tasks should retain explicit data contracts and small managed fixtures. Agent tasks should add ambiguity, verification responsibility, correction, and takeover rather than merely permit a one-prompt answer.
4. No task should require personal-computer ownership, real student data, uncontrolled access to external models, or an LLM acting as the hidden verifier.

## P0-A Progress Against Acceptance Criteria

| Criterion | Current result | Evidence / limitation |
| --- | --- | --- |
| AC1: 10 real traditional tasks recorded, or documented reason for fewer | **FAIL / in progress** | Five public-source candidate records exist; no local historical tasks are yet available and the 10-task threshold is not met. |
| AC2: Original goal, environment, expected output, audit notes | **PARTIAL** | Present for five reconstructed public candidates; original local task artifacts are absent. |
| AC3: Clear agent impact classification | **PARTIAL** | Records distinguish planned paths/failure hypotheses from `Not tested`; no measured impact classification is claimed. |
| AC4: Failure modes and human intervention points | **PASS for design documentation** | Included in all five records; not yet empirically observed. |
| AC5: Avoid prohibited replacement-rate language | **PASS** | No such metric or claim is used. |
| AC6: At least three recommendations if evidence supports them | **PARTIAL** | Three conditional strong candidates are identified, but no P0-C selection is made until real task/run evidence exists. |

## Next Evidence-First Steps

1. Ask the product owner or teachers for licensable local task sheets, scoring rules, data dictionaries, and sanitized fixtures; record them as local only after provenance is confirmed.
2. Find or archive attributable public assignment sheets for `P0A-PUB-009` before treating it as more than a pattern candidate.
3. Define versioned fixtures and deterministic verifiers for one SQL task and one Python task.
4. Run a bounded, recorded agent-assisted audit with human intervention notes; preserve prompts, tool/environment versions, outputs, verifier results, and failures.
5. Add at least five further task records or document why the P0-A sample remains smaller.
