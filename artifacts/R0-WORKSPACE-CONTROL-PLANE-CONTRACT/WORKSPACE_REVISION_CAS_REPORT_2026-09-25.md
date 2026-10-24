# Workspace Revision / Stale-Write Contract Report

- Task ID: `R0-WORKSPACE-REVISION-CAS-001`
- Current Gate: P3 local synthetic API contract
- Result: **PASS for tested in-memory synthetic write paths; overall contract remains PARTIAL**
- Commit: `NONE`

## Files changed and rationale

- `tests/test_workspace_api.py`: added one regression test that walks all five workspace write types and proves each accepted write advances revision and a new follow-up using the prior revision is rejected.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: made the already intended compare-and-swap behavior explicit for every successful workspace state write, including the boundary between stale new requests and valid idempotent replays.
- `docs/CURRENT_STATE.md`: refreshed the API test count, full-suite snapshot and evidence pointer.
- This report records scope and limits. The API implementation was not changed in this task.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **PASS, 22/22**.
- `python -m unittest discover -s tests -v`: **PASS, 138 total; 137 passed, 1 skipped; exit 0; 47.773 seconds**.
- `git diff --check`: **PASS** after documentation/report edits.
- The sole skip is the existing real symlink path test, skipped because Windows returned `WinError 1314` when creating a symlink. It does not establish symlink safety.

## What the regression proves

In a single fixed synthetic workspace, it covers start, scripted Agent turn, student proposal decision, submission, and teacher review. For each operation it asserts the accepted response increments the revision by one and a distinct-key request using the pre-write revision returns `stale_revision`. This tests the existing event-driven revision increment in the in-memory adapter; it does not establish database transactions, cross-process concurrency, or production compare-and-swap semantics.

## Limits and risks

- PASS applies only to these five local in-memory synthetic write paths and this deterministic test sequence.
- Same-key idempotency replay behavior remains covered separately; this new test intentionally uses distinct keys for stale writes.
- No real authentication, tenant authorization, persistent store, HTTP server, front-end integration, model, credentials, ECS, deployment, student data, or code execution was involved.
- Artifact source remains a candidate fixture and its API references still report `NOT_COMPUTED`; the full vertical product workflow is not connected.
- Foundation Spike remains PARTIAL, including the symlink test privilege gap and previously identified operating-system isolation gaps.

## Next work, decision status, and Git

Continue contract closure by mapping every route and request/response shape to tests, then test route-specific failure and replay semantics before any front-end connection. The teacher and student pages must not be presented as a connected end-to-end product until API integration and a permitted browser QA path exist. No user decision is needed for this synthetic test/spec clarification.

The worktree has extensive pre-existing modified and untracked files; none were discarded or cleaned. `git diff --stat` reports only tracked modifications and is cumulative, not a complete inventory of this task. No commit, push, deployment, deletion, reset, cleanup, service launch, or browser operation occurred. Commit: `NONE`.
