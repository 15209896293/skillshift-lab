# SkillShift Lab Dev OS Implementation Plan

## Goal

Create a minimal Agent Native Development OS for SkillShift Lab.

The purpose is to let a non-technical product owner coordinate multiple agents without losing project state, overwriting historical assets, or accepting unverifiable completion claims.

## What To Add First

Create these files first:

- `AGENTS.md`
- `docs/PROJECT_BRIEF.md`
- `docs/DEV_OS_AUDIT.md`
- `docs/DEV_OS_IMPLEMENTATION_PLAN.md`
- `docs/DEVELOPMENT_WORKFLOW.md`
- `docs/CURRENT_STATE.md`
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- `docs/architecture/DATA_ARCHITECTURE.md`
- `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`
- `docs/adr/README.md`
- `docs/adr/ADR-TEMPLATE.md`
- `docs/research/README.md`
- `docs/research/P0_PROTOCOL.md`
- `docs/research/EVIDENCE_REGISTER.md`
- `specs/P0-A/README.md`
- `.github/ISSUE_TEMPLATE/feature.md`
- `.github/ISSUE_TEMPLATE/bug.md`
- `.github/ISSUE_TEMPLATE/research.md`
- `.github/ISSUE_TEMPLATE/refactor.md`
- `.github/pull_request_template.md`

## What Not To Change Yet

Do not change:

- files in `wenben/`,
- project plan wording,
- technical stack,
- product architecture status from Proposed to Accepted,
- Git state,
- GitHub remote,
- deployment settings.

## GitHub Spec Kit

Spec Kit should be treated as a method, not a ritual.

SkillShift should use these paths:

- Major feature: Assess -> Specify -> Clarify -> Plan -> Tasks -> Implement -> Test -> Converge -> PR -> Verify -> Release
- Small feature: Specify -> Plan -> Tasks -> Implement -> Verify
- Bug: Reproduce -> Root Cause -> Fix -> Regression Test -> Verify
- Research: Question -> Method -> Evidence -> Analysis -> Limitation -> Decision
- Documentation: Scope -> Update -> Consistency Check -> Merge

Before installing or initializing any official Spec Kit tooling, verify the latest official GitHub documentation.

## GitHub Project Recommendation

Use one lightweight project board with these statuses:

- Inbox
- Research
- Spec
- Ready
- In Progress
- Review
- Verify
- Blocked
- Done
- Released

Use these item types:

- FEATURE
- BUG
- RESEARCH
- REFACTOR
- DOC

Use at most three hierarchy levels:

EPIC -> FEATURE -> TASK / BUG

Do not build a complex project management system before the first vertical slice.

## Minimal CI Recommendation

Before a code stack exists, CI should only check structure and basic consistency.

After a stack exists, add checks in this order:

1. lint,
2. typecheck,
3. unit tests,
4. integration tests,
5. build,
6. runtime smoke verification.

Later checks may include:

- task schema validation,
- environment build tests,
- reference solution regression,
- Hidden Verifier positive and negative tests,
- Agent Adapter tests,
- Sandbox reset tests,
- telemetry integrity tests,
- operational and research permission tests.

## Worktree Workflow

After Git is initialized, use this rule for significant parallel work:

One Agent = One Issue = One Branch = One Worktree

Do not let multiple agents write to the same workspace at the same time.

Use shared read-only context through `docs/PROJECT_BRIEF.md`, architecture docs, ADRs, and specs.

## Risk Register

| Risk | Why It Matters | Control |
| --- | --- | --- |
| Too much process | A single product owner cannot maintain heavy bureaucracy | Keep only files that reduce confusion |
| Duplicate truth | Chat, Word, README, and code may diverge | Define source-of-truth hierarchy |
| Agent scope creep | Agents may modify architecture while coding | Require spec and allowed scope |
| False completion | Agent summaries may sound convincing without evidence | Require test results and acceptance criteria |
| Premature architecture | Long-term concepts may be implemented too early | Mark ADRs Proposed until accepted |
| Research overclaim | Pilot data may be overstated | Require limitations and no AI replacement rate |
| Privacy leakage | Student data and model calls are sensitive | Use minimum telemetry and explicit permissions |

## Acceptance Criteria For The Dev OS

- A new agent can understand the project without reading the full DOCX plan.
- A non-technical product owner can see the current stage and next action.
- Important work has a spec or issue.
- Completion requires evidence.
- Historical documents remain untouched.
- The system does not require large maintenance effort before product validation.
