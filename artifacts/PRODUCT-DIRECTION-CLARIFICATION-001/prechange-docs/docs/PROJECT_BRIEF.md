# SkillShift Lab Project Brief

## What This Project Is

SkillShift Lab is a vocational digital skill transition project for the Agent era. Its core is research into how Agent changes vocational knowledge, foundational capability, task structure and human-Agent collaboration. SkillShift Studio is the productized research infrastructure: it provides real tasks, controlled AI collaboration, minimal process evidence and teacher intervention.

The first feedback group is higher-vocational Big Data, Computing, and Software students. This is a launch focus, not a permanent product boundary. Python + CSV is the first Golden Path used to validate the foundation.

## Current Product Definition

R0 does not replace formal classes, build a full education platform, deliver student ability scores or compete with mainstream Agent capability. It validates a teaching-workflow loop: a teacher/mentor creates an AI-enabled task; a student works in a bound local Workspace through Studio / Agent Node; the platform creates minimal evidence and a submission package; the teacher can review, request explanation/evidence/correction, and the student can respond.

## Long-Term Research Tracks

Foundation Track confirms what the student can do with limited or no agent help.

Agent Track allows the student to use agents, but raises task complexity and checks whether the student can delegate, judge, verify, correct, and take over agent work.

The research layer compares both tracks to understand skill transfer. These tracks are preserved as long-term research assets, not current R0 implementation scope.

## Current Stage

The project is in R0 product-prototype specification and Foundation Spike verification. It has a synthetic local reference Node only; it does not implement the broader product, deployment, a production sandbox, real student use, or research experiments.

Current priority:

1. Maintain the unified R0 requirements, technical and quality specifications plus the A+B research-task-evidence contract.
2. Verify the non-Docker local restricted-process Workspace boundary through the single Foundation Spike.
3. Preserve the mixed ADR state: topology is confirmed; restricted execution and data boundaries remain Proposed until evidence exists.
4. Do not start a wider teacher/student platform slice without a separate specification and authorization.

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

The first path is:

teacher creates template task -> student Node binds a local Workspace -> agent/human runs controlled actions -> student validates and explains/corrects/takes over -> submission package -> teacher review -> feedback or correction.

The Foundation Spike only verifies the local Node portion with a frozen synthetic Python project. It uses a non-Docker `LocalRestrictedProcessProvider`, no real student data, no real model key, no teacher Web and no external deployment. The agent/runtime has access only inside its bound Workspace; host private directories, credentials, other Workspaces, arbitrary network and arbitrary dependencies are outside the Spike boundary.

## Current Historical Assets

The project plan documents in `wenben/` are historical and strategic assets.

They should be preserved and not overwritten by agents:

- `SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`: previous research main planning document; preserve it, but it does not override the approved R0 product direction.
- `SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`: older historical version.

Agents should read `README.md`, `docs/README.md`, `docs/product/R0_PRODUCT_REPOSITIONING_DECISION.md`, the current R0 specifications and relevant ADR/Spike spec before implementation work. V3.0 and prior plans are retained as Draft/historical context and do not override active R0 decisions.
