# Workspace Proposal Decision Retry Report

- Task ID: `R0-WORKSPACE-PROPOSAL-DECISION-RETRY-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for same-action retry and UI decision locking; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Scope

This follow-up covers student accept/reject/takeover writes when a response may be lost. The client already retains an idempotency key after an uncertain write. The UI now prevents a different proposal action from racing on the same operation key and makes same-action retry explicit in the enabled controls.

Only fixed synthetic state and mock-fetch/direct tests are used. No real student data, credentials, model, ECS, external network, persistence, port, browser or code execution was used.

## Behavior

- Accept/reject/takeover buttons are disabled while a decision request is pending.
- The handler captures the proposal, workspace and revision IDs at click time and sends those captured values.
- On a successful decision, the proposal ID is cleared and the three controls stay disabled until the next API response carries a new proposal; then the controls are restored only if that response contains a proposal.
- On an unavailable/invalid receipt, only the action that was just attempted is re-enabled. Repeating it uses the still-pending identical route/body idempotency key; other decisions stay disabled until resolution.
- On known rejection/conflict, the existing API error state is shown and no success is fabricated.

The API and its current in-memory idempotency ledger remain the source of replay behavior. This does not establish persistence across service restart or browser reload.

## Changes

- `apps/student-web/app.js`: added proposal decision control state, action-context capture and safe re-enabling for a newly returned proposal or an uncertain same-action retry.
- `tests/workspace-client.test.mjs`: added an uncertain proposal decision response test that verifies same idempotency key and matching replay receipt.
- `tests/test_workspace_frontend_html.py`: locks the pending/restore/retry-control wiring for the student page.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`: record the behavior and current evidence boundary.

## Commands and results

- `node --test tests/workspace-client.test.mjs`: **16/16 PASS**.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`: **3/3 PASS**.
- `python -m unittest discover -s tests -v`: **152 tests, 151 passed, 1 skipped**, latest run exit 0, 50.602 seconds. The Windows symlink test skipped due to `WinError 1314`; it is not symlink-safety evidence.
- `node --check apps/student-web/app.js`, `node --check apps/workspace-client.mjs`: passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`, `python -m py_compile ...` for the existing Workspace API/WSGI/schema test files, and `git diff --check`: passed.

## Acceptance

| Check | Result | Boundary |
| --- | --- | --- |
| Lost proposal decision receipt can be retried with the same key/body | PASS | Mock-fetch test verifies key replay and matching DTO receipt. |
| Conflicting decision buttons are locked in flight | PASS | Static student-page test plus app code inspection. |
| Uncertain result only offers same action for retry | PASS | Static page check; client keeps pending key for the identical operation. |
| New proposal unlocks decision controls again | PASS | State update is tied to a returned proposal ID. |
| Browser interaction and visual QA | NOT RUN | No integrated compliant preview route; no port or browser opened. |
| Production readiness | NOT CLAIMED | Fixed demo role, in-memory state, non-production; no execution. |

## Current phase

P3 DTO wiring and error/retry handling continue. API/read DTO tests cover the synthetic teacher-publish → student-discover/start/collaborate/submit → teacher-review/remediation → student-resubmit loop. UI client tests now also cover read DTO validation, teacher review readback and student same-action proposal retry. The overall integration remains **PARTIAL** while HTTP/browser runtime verification is unavailable.

## Git

- Branch: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked work was preserved. No cleanup, reset, commit, push, server launch, browser launch or deployment occurred.
- Commit: `NONE`.
