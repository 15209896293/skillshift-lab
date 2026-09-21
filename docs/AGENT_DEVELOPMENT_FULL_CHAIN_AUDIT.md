# SkillShift Agent Development Full Chain Audit

## Purpose

This document explains how SkillShift should use AI agents for software development, research, documentation, and project management.

It is written for a non-technical product owner who will coordinate Codex, Claude, and other agents over a long project.

The core idea is simple:

Do not manage agents by trusting their confidence. Manage agents by giving them clear scope and requiring evidence.

## 1. The Human Role

The human product owner is the final decision maker.

The human does not need to know every technical detail, but must control:

- product direction,
- task priority,
- acceptance criteria,
- scope boundaries,
- privacy boundaries,
- whether evidence is good enough,
- when to move to the next stage.

The human should not ask agents to "just continue developing" without a task boundary.

Good human command:

```text
Work only on P0-A. Create a research spec and task inventory template. Do not write product code. Do not modify project plan documents. Report files changed and evidence.
```

Risky human command:

```text
Continue building SkillShift.
```

## 2. Agent Role Types

SkillShift should use different agents for different job types.

| Agent Role | Good At | Should Not Do |
| --- | --- | --- |
| Product Planning Agent | turning product direction into specs and acceptance criteria | deciding strategic direction alone |
| Software Engineering Agent | implementing scoped code tasks | changing architecture casually |
| Code Review Agent | finding bugs, missing tests, risks, regressions | rewriting code without approval |
| Research Agent | collecting evidence, summarizing limitations | making broad claims from weak evidence |
| DevOps Agent | CI, environment, deployment workflow | deploying or pushing without approval |
| Documentation Agent | keeping docs consistent and readable | creating duplicate truth |
| Data Governance Agent | privacy, telemetry, research data boundaries | treating student data as ordinary logs |

One agent may play multiple roles, but each task should name the active role.

## 3. Full Chain From Idea To Release

### Stage 1: Idea / Problem

Human states the problem in plain language.

Agent output should be:

- what problem is being solved,
- who it affects,
- why now,
- what is out of scope.

Do not code here.

### Stage 2: Research / Assessment

Use this when the project is uncertain.

For SkillShift, P0-A is the first example:

- collect traditional tasks,
- run agent impact audit,
- record failure modes,
- decide what task types are worth rebuilding.

Output must include evidence and limitations.

### Stage 3: Spec

A spec defines what will be built or studied.

It should answer:

- goal,
- users,
- workflow,
- allowed scope,
- forbidden scope,
- acceptance criteria,
- verification method.

If a task has no acceptance criteria, an agent can make it look complete while missing the point.

### Stage 4: Plan

Plan means the implementation approach.

For a technical task, it should say:

- files likely to change,
- data model impact,
- UI impact,
- tests needed,
- risks.

For a research task, it should say:

- method,
- sample,
- data collection format,
- analysis path,
- limitations.

### Stage 5: Tasks

Break work into small tasks.

Each task should be small enough that one agent can finish and verify it.

Bad task:

```text
Build the platform.
```

Good task:

```text
Create a P0-A task inventory template with fields for original goal, expected output, agent completion result, time, human intervention, failure mode, and dual-track candidate status.
```

### Stage 6: Implementation

Agent changes files only inside the approved scope.

Rules:

- no hidden architecture changes,
- no large refactor,
- no deleting historical assets,
- no private data exposure,
- no unapproved dependency or service choices.

### Stage 7: Test / Verify

Agent must run relevant checks or explain why checks do not exist.

Evidence may include:

- command output,
- rendered document check,
- test result,
- build result,
- runtime screenshot,
- verifier output,
- data sample,
- manual acceptance checklist.

For SkillShift, agent text alone is never enough.

### Stage 8: Converge

Converge means re-checking the work against the original spec.

Questions:

- Did the agent actually do the requested work?
- Did it add extra things?
- Did it break source-of-truth rules?
- Are acceptance criteria satisfied?
- Are limitations visible?
- Are next steps clear?

### Stage 9: Review

Use a second agent or human review for important work.

Reviewer should focus on:

- bugs,
- missing verification,
- privacy risks,
- scope creep,
- duplicate truth,
- over-engineering.

### Stage 10: Merge / Release

Only after GitHub and CI exist:

- PR reviewed,
- CI passed,
- evidence accepted,
- documentation updated,
- release state recorded.

Before that system exists, status should be Verify, not Done.

## 4. SkillShift-Specific Agent Rules

### Product Direction

Agents may propose, but the human decides.

Do not let agents turn every long-term concept into first-version features.

### Architecture

The following are long-term proposed concepts:

- Task Engine,
- Hidden Verifier,
- Agent Gateway,
- Managed Sandbox,
- Personal Node,
- Operational / Research Data Plane.

Agents must not implement all of them at once.

### Research

Agents must keep research humble.

Allowed:

- "In this small sample, these task types were often completed faster with agent help."

Forbidden:

- "AI will replace Big Data Technology students."
- "The AI replacement rate is X%."
- "This pilot proves the education model."

### Student Data

Agents must treat student data as sensitive by default.

Never default to sending names, student IDs, private files, or unrestricted activity logs to third-party models.

## 5. Where Agents Commonly Fail

| Failure | What It Looks Like | Control |
| --- | --- | --- |
| Overconfidence | Says "completed" without evidence | require test results and AC checklist |
| Scope creep | Adds architecture while doing a small task | define forbidden scope |
| Duplicate truth | README, docs, specs all contain conflicting status | maintain source-of-truth hierarchy |
| Fake verification | Uses LLM opinion instead of real checks | require commands, renders, tests, or data |
| Over-engineering | Builds too many systems before P0 evidence | use Gate 0 |
| Privacy drift | Logs too much student behavior | task-scoped telemetry only |
| Context overload | Reads huge plan every time and gets confused | start from PROJECT_BRIEF |
| File pollution | Multiple agents edit same workspace | one issue, one branch, one worktree |

## 6. Recommended Agent Operating Model

### For The Product Owner

Use this pattern:

```text
Role:
You are acting as [role].

Task:
Do [specific task].

Context:
Use docs/PROJECT_BRIEF.md and [specific spec].

Allowed:
[what may be changed]

Forbidden:
[what must not be changed]

Verification:
[how to prove completion]

Report:
Use the standard completion report.
```

### For Agents

Before acting, the agent should answer internally:

- What is the task type?
- What source of truth applies?
- What files may I touch?
- What must I not touch?
- What evidence will prove this?
- What would count as failure?

## 7. Suggested First Agent Tasks

Do these before product code:

1. Review Dev OS skeleton for over-engineering and missing boundaries.
2. Initialize Git only after user approval.
3. Verify official GitHub Spec Kit documentation.
4. Create P0-A task inventory template.
5. Collect first 3 to 5 candidate traditional training tasks.
6. Design the P0-A audit report format.
7. Decide the first SQL/MySQL vertical slice only after P0-A evidence begins.

## 8. Current Readiness Assessment

| Area | Current State | Readiness |
| --- | --- | --- |
| Strategic direction | V2.2 plan exists | strong |
| Daily development context | PROJECT_BRIEF created | initial |
| Agent rules | AGENTS.md created | initial |
| Architecture docs | proposed docs created | initial |
| ADR process | template created | initial |
| Research workflow | P0 protocol created | initial |
| Specs | P0-A draft created | initial |
| Git | not initialized | blocked pending user decision |
| GitHub | not configured | blocked pending user decision |
| CI | not configured | blocked pending Git and stack decision |
| Product code | not started | intentionally not started |

## 9. Recommendation

SkillShift should use agents in this order:

1. Stabilize the development operating system.
2. Run P0 research tasks.
3. Use evidence to choose the first vertical slice.
4. Build only one end-to-end slice.
5. Add CI and tests around the slice.
6. Use review agents to check scope, privacy, and verification.
7. Expand only after gates pass.

This makes agents useful as force multipliers without letting them become uncontrolled project authors.
