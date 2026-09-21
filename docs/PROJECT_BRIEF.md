# SkillShift Lab Project Brief

## What This Project Is

SkillShift Lab is a vocational digital skill transition platform for the Agent era.

It connects two worlds:

- School-based foundation skill education.
- Realistic work in which students use agents to complete more complex professional tasks.

The first target field is higher vocational Big Data Technology.

## Current Product Definition

SkillShift Lab is not trying to replace formal classes immediately.

The first stage focuses on:

- second classroom activities,
- after-class practice,
- AI interest groups,
- competition training,
- professional extension training,
- employment-oriented skill practice.

## Core Tracks

Foundation Track confirms what the student can do with limited or no agent help.

Agent Track allows the student to use agents, but raises task complexity and checks whether the student can delegate, judge, verify, correct, and take over agent work.

The research layer compares both tracks to understand skill transfer.

## Current Stage

The project is in the Dev OS and P0 research/planning stage.

Do not start full business platform development yet.

Current priority:

1. Establish agent-friendly development governance.
2. Collect real traditional training tasks.
3. Audit how current agents affect those tasks.
4. Rebuild a small number of tasks into Foundation / Agent paired tasks.
5. Run a small voluntary pilot before deciding whether to build the broader MVP.

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

## Current P0 Route

P0-A: Collect 10 to 20 real traditional higher vocational Big Data Technology training tasks and run an Agent impact audit.

P0-B: Validate teacher and student needs.

P0-C: Rebuild 3 tasks into Foundation Track + Agent Track paired tasks.

P0-D: Create a single vertical slice.

P0-E: Run a small voluntary after-class pilot with 5 to 20 students.

Only after Gate 0 passes should the project enter formal MVP development.

## MVP Direction After Gate 0

M1 should be one SQL/MySQL vertical slice.

The full path should include:

teacher creates task -> student enters in browser -> chooses execution environment -> completes Foundation / Agent task -> collaborates with agent -> real execution -> evidence -> Hidden Verifier -> submission -> teacher report.

Do not expand to Hadoop, Kafka, or Flink before the M1 slice works.

## Current Historical Assets

The project plan documents in `wenben/` are historical and strategic assets.

They should be preserved and not overwritten by agents:

- `SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`: current main planning document.
- `SkillShift_Lab_项目立项书暨研究开发文档_V2.0.docx`: older historical version.

Agents should not read the full project plan for every task. Use this brief first, then open the plan only when the task requires deeper context.
