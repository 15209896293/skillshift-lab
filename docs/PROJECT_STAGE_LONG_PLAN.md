# SkillShift Lab Project Stage Long Plan

> **Status: historical P0 research route, preserved and paused.** It does not define the current R0 product priority. For the active product baseline, read `product/R0_PRODUCT_REPOSITIONING_DECISION.md`, `product/R0_AGENT_FIRST_DELIVERY_DECISION.md`, relevant Active R0 specifications, and `PROJECT_STATUS_2026-10-09.md`. `../SkillShift_Studio_软件工程总纲_V3.0.md` is Draft and does not override the accepted decisions.

## Purpose

This document is the long-range execution plan for SkillShift Lab.

It is intended for another Codex window, Claude window, or future agent task to continue development without re-reading the entire planning document.

The plan is written for a non-technical product owner coordinating multiple agents.

## Current Baseline

Date:

2026-09-21

Current repository state:

- Git initialized on `main`.
- Dev OS baseline committed.
- P0-A public-source task seed committed.
- No product code yet.
- No GitHub remote yet.
- No deployment.
- No real student data.

Current strategic source:

- `wenben/SkillShift_Lab_项目立项书暨研究开发文档_V2.2.docx`

Daily working context:

- `README.md`
- `AGENTS.md`
- `docs/PROJECT_BRIEF.md`
- `docs/CURRENT_STATE.md`
- `docs/DEVELOPMENT_WORKFLOW.md`
- this file

## Executive Strategy

SkillShift should not start as a big platform build.

The correct path is:

1. Prove the problem using real or public traditional training tasks.
2. Prove dual-track task design on 3 tasks.
3. Prove one SQL/MySQL vertical slice.
4. Run a small voluntary pilot.
5. Only then expand to MVP and school/cohort use.

The project should use agents to accelerate evidence collection, specification, prototyping, verification, and review.

Agents must not be allowed to become uncontrolled product authors.

## Stage Map

| Stage | Name | Main Question | Output | Gate |
| --- | --- | --- | --- | --- |
| S0 | Dev OS Baseline | Can agents work safely and traceably? | Dev OS, Git baseline, rules, specs | Baseline committed |
| P0-A | Traditional Task Agent Impact Audit | Do traditional tasks change under agent assistance? | Task inventory, audit records, failure modes | 10+ tasks or justified smaller sample |
| P0-B | Needs Validation | Do students/teachers recognize the problem? | Interview/survey evidence | At least one credible user path |
| P0-C | Dual-Track Task Reconstruction | Can old tasks become Foundation + Agent pairs? | 3 task specs, evidence contracts | 3 viable dual-track candidates |
| P0-D | Vertical Slice Spec | What is the smallest end-to-end system? | M1 spec and architecture decision | Scope small enough to build |
| M1 | SQL/MySQL Vertical Slice | Can one task run end to end? | Working slice with verifier and report | Demo and checks pass |
| P0-E | Small Pilot | Will students voluntarily use it more than once? | Pilot report and product fixes | No major privacy/stability blocker |
| M2 | Minimal Product Shell | Can teacher/student/admin basics support repeated use? | Workspace, teacher lite, admin lite | Cohort-ready |
| M3 | Three-Task Pilot | Can three tasks support a small training flow? | 3 task package and reports | Repeatable session |
| M4 | Six-Task MVP | Can the product support a meaningful MVP? | 6 tasks, reports, CI, docs | MVP demo stable |
| M5 | After-Class Cohort Pilot | Can a real group use it outside class? | usage evidence and improvements | Decision for school expansion |
| M6 | Research Module | Can research export be governed and useful? | research data workflow | approved protocol |
| M7 | School/Course Expansion | Is formal school adoption justified? | deployment plan and adoption evidence | explicit partner need |

## Stage S0: Dev OS Baseline

### Status

Mostly complete.

### Done

- Root README created.
- Agent rules created.
- Project brief created.
- Architecture proposal docs created.
- ADR process created.
- P0-A spec created.
- Git initialized.
- First baseline commit created.
- P0-A public source seed committed.

### Remaining

- Optional: connect GitHub remote.
- Optional: create GitHub Project.
- Optional: install or initialize official Spec Kit tooling after confirming current official docs.

### Gate

S0 passes when:

- working tree is clean,
- Dev OS baseline is committed,
- owner understands where to put P0-A raw tasks,
- next agent can start from this file.

## Stage P0-A: Traditional Task Agent Impact Audit

### Objective

Collect and audit 10 to 20 traditional Big Data Technology training tasks.

If local historical tasks are not available yet, begin with public-source candidate tasks and label them clearly.

### Inputs

- `artifacts/P0-A/task_inventory_public_seed.md`
- `specs/P0-A/task_inventory_template.md`
- any future raw local tasks in `artifacts/P0-A/raw_tasks/`

### Work Packages

P0A-WP1: Create audit record files for the first five public candidates.

Recommended first five:

1. MySQL database creation, import, and query.
2. SQL aggregation and abnormal result diagnosis.
3. Python CSV data cleaning.
4. Multi-source data merge and consistency check.
5. User behavior analysis pipeline.

P0A-WP2: For each task, create:

- original task summary,
- expected output,
- likely agent workflow,
- likely failure modes,
- verification method,
- what the task still measures,
- possible Foundation Track,
- possible Agent Track.

P0A-WP3: Create a P0-A interim report.

P0A-WP4: When local materials arrive, add local task records and compare them with public candidates.

### Acceptance Criteria

- At least 10 task records exist, or fewer with a documented reason.
- Each record distinguishes public-source candidate vs local historical task.
- Each record has a verification idea.
- Each record avoids "AI replacement rate" language.
- At least 3 candidates are recommended for dual-track reconstruction.

### Suggested Agent Setup

Use one planning/research agent first.

Subagents are useful only after the audit template is stable.

Possible subagents:

- SQL task auditor.
- Python/data cleaning task auditor.
- Linux/Hadoop task auditor.
- evidence/verifier reviewer.

Do not let subagents edit the same audit file in parallel.

## Stage P0-B: Needs Validation

### Objective

Determine whether the problem is real for students and teachers.

### Work Packages

P0B-WP1: Create interview guide for students.

P0B-WP2: Create interview guide for teachers or mentors.

P0B-WP3: Create consent/privacy note for informal discovery.

P0B-WP4: Summarize interviews into needs, objections, and product implications.

### Acceptance Criteria

- At least 3 student voices or documented reason for fewer.
- At least 1 teacher/mentor voice or documented reason for none.
- Evidence includes objections, not only supportive comments.
- Conclusions distinguish fact, interpretation, and decision.

## Stage P0-C: Dual-Track Task Reconstruction

### Objective

Turn 3 promising traditional tasks into SkillShift dual-track tasks.

### Work Packages

For each selected task:

- Foundation Track spec.
- Agent Track spec.
- transfer/reflection question.
- evidence contract.
- hidden verifier concept.
- telemetry events to record.
- failure cases.

### Acceptance Criteria

- Foundation Track tests foundation skill.
- Agent Track is not one-prompt trivial.
- Hidden verifier does not rely on LLM self-judgment.
- Task works for students without assuming personal computer ownership.
- Privacy boundary is explicit.

## Stage P0-D: M1 Vertical Slice Spec

### Objective

Define the smallest buildable end-to-end system.

### Recommended Slice

SQL/MySQL task.

End-to-end path:

student browser -> task page -> execution environment -> SQL action -> evidence collection -> hidden verifier -> submission -> simple report.

### Work Packages

- M1 product spec.
- M1 architecture ADRs.
- data model sketch.
- task schema v0.
- verifier interface v0.
- minimal UI flow.
- CI plan for chosen stack.

### Gate

Do not build M1 until P0-A and at least part of P0-C provide enough evidence.

## Stage M1: SQL/MySQL Vertical Slice

### Objective

Build one real working slice.

### Proposed Architecture

Keep it simple:

- one web app,
- one API service if needed,
- one local or containerized MySQL environment,
- one task definition,
- one verifier,
- one report page.

### Do Not Build Yet

- multiple schools,
- full course management,
- complex research module,
- Hadoop/Kafka/Flink tasks,
- multiple execution modes,
- production-grade sandbox platform.

### Acceptance Criteria

- Student can enter task in browser.
- Task can be executed in a real or near-real environment.
- Verifier checks actual system state.
- Submission produces a readable report.
- Tests/build pass.
- Demo evidence exists.

## Stage P0-E: Small Pilot

### Objective

Test whether students voluntarily use the system and whether event/evidence data is interpretable.

### Scope

5 to 20 students.

After-class or voluntary setting.

### Acceptance Criteria

- Students understand task instructions.
- At least some students are willing to attempt a second task.
- Agent collaboration behavior can be interpreted.
- No major privacy or stability blocker.
- Product issues are recorded honestly.

## MVP Expansion Stages

### M2 Minimal Product Shell

Add:

- student workspace,
- teacher lite view,
- admin lite view,
- task registry,
- resource/account basics.

### M3 Three-Task Pilot

Package 3 tasks into one training sequence.

### M4 Six-Task MVP

Build 6 tasks only after M1/M3 evidence supports expansion.

### M5 After-Class Cohort Pilot

Run a real cohort or club-style training.

### M6 Research Module

Only after data governance is clear.

### M7 School/Course Expansion

Only if a school/teacher explicitly needs it.

## Worktree And Multi-Agent Policy

### Should Another Window Use Worktree?

Yes, for implementation or multi-file development.

No, for simple read-only review or a single small doc edit.

For the next development window, use this rule:

- If it only writes P0-A audit records: same repository is acceptable if no other agent is editing.
- If it builds code, creates CI, changes architecture, or runs parallel work: use a worktree.

### Recommended Worktree Pattern

One Issue = One Branch = One Worktree = One Agent.

Example branch names:

- `research/p0a-audit-records`
- `research/p0b-interviews`
- `spec/p0c-dual-track-tasks`
- `feature/m1-sql-slice`

### Subagent Policy

Use subagents for bounded review or parallel analysis, not for uncontrolled editing.

Good subagent tasks:

- audit one task family,
- review verifier design,
- check privacy risks,
- check over-engineering,
- review acceptance criteria.

Bad subagent tasks:

- "build the platform",
- "rewrite architecture",
- "continue development",
- editing the same files as another agent.

### Suggested Subagent Setup For P0-A

Lead agent:

- owns file changes,
- integrates output,
- checks consistency.

Subagent A:

- SQL/MySQL task analysis.

Subagent B:

- Python/data cleaning task analysis.

Subagent C:

- verifier/evidence design review.

Subagents should return notes. The lead agent should write final files.

## Handoff Prompt For Another Window

Use this prompt when starting another Codex window:

```text
You are working on SkillShift Lab at F:\比赛\skillshift.

Role:
Act as project manager, research engineer, and agent-development workflow engineer.

Read first:
- AGENTS.md
- README.md
- docs/PROJECT_BRIEF.md
- docs/CURRENT_STATE.md
- docs/PROJECT_STAGE_LONG_PLAN.md
- specs/P0-A/README.md
- specs/P0-A/task_inventory_template.md
- artifacts/P0-A/task_inventory_public_seed.md

Task:
Continue P0-A. Create formal audit records for the first five public-source candidate tasks listed in docs/PROJECT_STAGE_LONG_PLAN.md.

Allowed scope:
- artifacts/P0-A/audit_records/
- artifacts/P0-A/ interim report files if needed
- docs/CURRENT_STATE.md only if status changes

Forbidden scope:
- Do not edit files in wenben/.
- Do not build product code.
- Do not change architecture status from Proposed to Accepted.
- Do not output AI replacement rate.
- Do not claim public-source candidates are local historical school tasks.

Worktree:
If you will edit more than audit records, create a worktree first. If only writing audit records and no other agent is active, current workspace is acceptable.

Subagents:
You may use subagents for bounded analysis of SQL, Python/data cleaning, and verifier design. Subagents should return notes; the lead agent must integrate final files.

Verification:
Run structure checks and git status. Report all files changed, why, checks, limitations, risks, and commit status.
```

## Immediate Next Actions

1. Commit this long plan if approved.
2. Start P0-A audit records for the first five public-source candidates.
3. Create a P0-A interim report after those five records.
4. Ask product owner for real local training materials.
5. Decide whether to connect GitHub before M1 development.

## Main Risks

| Risk | Control |
| --- | --- |
| Building too early | Do not start M1 until P0 evidence is reviewed |
| Public materials mistaken for local evidence | Label every source clearly |
| Agent overclaims | Require evidence and limitations |
| Too many processes | Keep only useful files |
| Parallel file conflicts | Use worktree for implementation or multi-agent writing |
| Privacy drift | No real student data before protocol |
| Hidden verifier becomes LLM scoring | Verifier must check real state where possible |
