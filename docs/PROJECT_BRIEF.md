# SkillShift Lab Project Brief

## What This Project Is

SkillShift Lab is a vocational digital skill transition project for the Agent era. Its core is research into how Agent changes vocational knowledge, foundational capability, task structure and human-Agent collaboration. SkillShift Studio is the productized research infrastructure: it provides real tasks, controlled AI collaboration, minimal process evidence and teacher intervention.

The first feedback group is higher-vocational Big Data, Computing, and Software students. This is a launch focus, not a permanent product boundary. Python + CSV is the first Golden Path used to validate the foundation.

## Current Product Definition

R0 does not replace formal classes, build a full education platform, deliver student ability scores or compete with mainstream Agent capability. The current product slice is a vocational project workbench: a teacher defines an AI-enabled task, student workspace, student responsibility and deliverable; a student uses an in-product Agent around project context, inspects/validates the work and submits it; the teacher reviews task-related evidence and gives feedback or requests remediation. The teacher Web and student workspace are separate product surfaces. Python + CSV is the first synthetic Golden Path, not a permanent task boundary.

Actual code execution remains a separate security Gate. Before evidence closes the relevant path, no student or external project is executed; the current ECS remains a control-plane candidate only. The previously verified deterministic text workflow is a flow harness, not the coding Agent product. User value, a real LLM, real users, production identity/data and deployment remain unverified or gated. See `product/R0_PROJECT_AGENT_WORKSPACE_DECISION.md` and `../specs/R0-PROJECT-AGENT-WORKSPACE/README.md`.

## Long-Term Research Tracks

Foundation Track confirms what the student can do with limited or no agent help.

Agent Track allows the student to use agents, but raises task complexity and checks whether the student can delegate, judge, verify, correct, and take over agent work.

The research layer compares both tracks to understand skill transfer. These tracks are preserved as long-term research assets, not current R0 implementation scope.

## Current Stage

The project is in R0/R0.5 synthetic product-prototype and evidence-boundary work. Existing assets include the local teacher/student control-plane prototype and a separate React Web frontend source tree. The last recorded control-plane regression is from 2026-09-26; the 2026-10-09 React handoff did not run build, lint, services, or browser acceptance. See `PROJECT_STATUS_2026-10-09.md` for the dated status and evidence limits.

Current priority:

1. Establish a repeatable local demo and current build/lint/browser evidence for `apps/studio-web/` before claiming it is runnable or accepted.
2. Select one small, specified front-end follow-up after comparing the React implementation with Active product and API contracts.
3. Preserve the Foundation Spike as a separate, incomplete safety research track; do not run student or external code.
4. Keep real models, identities, student data, production persistence, deployment, research collection, and task-level custom Agent permissions behind their existing decisions and gates.

## Key Concepts

- Task Engine
- Task Graph
- Evidence Contract
- Hidden Verifier
- Sandbox
- Managed Sandbox
- Personal Node
- School Node
- Agent Gateway
- Human-Agent decision events
- Task-scoped telemetry
- Operational Data Plane
- Research Data Plane
- EDA-V
- Foundation / Agent dual-track task design
- Standardized Agent
- Live Agent

These are long-term concepts. They do not all need to be implemented in the first version.

## Preserved P0 Route

P0-A through P0-E documents and evidence remain preserved. Their expansion is paused while R0 product direction is organized. They are not a precondition for defining or validating the first Workspace foundation.

## R0 Direction

The active first path is:

teacher creates template task -> student collaborates with an in-platform education Agent -> student validates and explains/corrects -> submission package -> teacher review -> feedback or correction.

The Foundation Spike only verifies part of a future local Node route with a frozen synthetic Python project. It uses a non-Docker `LocalRestrictedProcessProvider`, no real student data, no real model key, no teacher Web and no external deployment. Its PARTIAL result must not be called a security sandbox and does not block the active no-local-execution path.

## Current Historical Assets

The project plan documents in `wenben/` are historical and strategic assets.

They should be preserved and not overwritten by agents:

- `wenben/项目计划书_源文件归档/SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`: previous research main planning document; preserve it, but it does not override the approved R0 product direction.
- `wenben/项目计划书_源文件归档/SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`: older historical version.

Agents should read `README.md`, `docs/README.md`, `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`, the current R0 specifications and relevant ADR/Spike spec before implementation work. V3.0 and prior plans are retained as Draft/historical context and do not override active R0 decisions.
