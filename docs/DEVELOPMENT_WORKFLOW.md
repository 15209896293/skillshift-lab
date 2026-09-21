# SkillShift Lab Development Workflow

## Plain Language Summary

Each agent should behave like a careful contractor:

1. Take one clearly bounded job.
2. Work in an isolated place when code changes are significant.
3. Change only what the job allows.
4. Prove what changed with checks.
5. Report evidence, risks, and remaining work.

## Work Types

### FEATURE

Use when adding product behavior.

Flow:

Assess -> Specify -> Clarify -> Plan -> Tasks -> Implement -> Test -> Converge -> PR -> Verify -> Release

### BUG

Use when fixing broken behavior.

Flow:

Reproduce -> Root Cause -> Scoped Fix -> Regression Test -> Verify -> PR

### RESEARCH

Use when answering an uncertain product, education, or technical question.

Flow:

Question -> Method -> Evidence -> Analysis -> Limitations -> Conclusion -> Decision

### REFACTOR

Use only when there is a clear technical reason.

Flow:

Reason -> Boundary -> Test Protection -> Small Change -> Regression Verification

### DOC

Use when updating project knowledge.

Flow:

Scope -> Update Single Source of Truth -> Consistency Check -> Merge

## Multi-Agent Rule

For significant work after Git is initialized:

One Agent = One Issue = One Branch = One Worktree

Agents should not share the same writable workspace for parallel work.

If two agents need the same file, the product owner decides the order.

## Worktree Command Template

Use only after Git is initialized.

```powershell
git status --short --branch
git switch main
git pull
git worktree add ..\skillshift-ISSUE-ID -b issue/ISSUE-ID-short-name
```

Do not run these commands until the repository and branch policy are confirmed.

## Task Intake Template

Every task should define:

- Goal
- Context
- Allowed Scope
- Forbidden Scope
- Dependencies
- Acceptance Criteria
- Verification
- Evidence Required

## Completion Report Template

Use this structure at the end of every task:

```text
TASK ID:

FILES CHANGED:

WHY:

TEST COMMANDS:

TEST RESULTS:

ACCEPTANCE CRITERIA:
- AC1: PASS/FAIL
- AC2: PASS/FAIL

KNOWN LIMITATIONS:

NEW RISKS:

FOLLOW-UP:

GIT DIFF SUMMARY:

COMMIT:
NONE
```

## Definition Of Done

A feature is Done only when all required conditions are true:

- spec requirements satisfied,
- acceptance criteria passed,
- tests passed,
- lint/typecheck/build passed when available,
- convergence review passed,
- no unresolved critical regression,
- required documentation updated,
- runtime/demo verification completed,
- PR merged once GitHub workflow exists.

Before PR merge exists, the status should be Verify, not Done.
