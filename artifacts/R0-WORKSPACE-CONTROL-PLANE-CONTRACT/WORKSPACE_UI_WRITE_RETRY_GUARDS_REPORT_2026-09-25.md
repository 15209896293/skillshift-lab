# Workspace UI Write and Retry Guards Report

- Task ID: `R0-WORKSPACE-UI-WRITE-RETRY-GUARDS-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for bounded write-lock and uncertain-submission behavior; overall UI/API product integration remains PARTIAL**
- Commit: `NONE`

## Audit finding and change

Static review found that teacher save/publish and student submission controls could be activated repeatedly while their writes were pending. On the student path, an unknown submission result also left the editor and explanation open; edited content could then be presented as a retry even though the client retained the original idempotency key.

The teacher task form now guards against re-entry and disables both save and publish controls until the operation settles. The student submission path now guards against duplicate in-flight writes, captures the click-time workspace ID, revision and DTO, and disables the confirmation button while waiting. If the write result is unavailable, malformed or otherwise uncertain, the exact captured DTO remains available under the same client idempotency key; the editor, file switching and explanation field are frozen, and the button states that it retries the same submission. A definite rejection or revision conflict clears the pending snapshot and restores edit controls using the latest readable workspace state. The UI does not claim success on an unknown receipt.

No API contract or product scope changed. No HTTP service or browser was run.

## Changed files

- `apps/teacher-web/app.js`: added a task-write re-entry guard and disabled save/publish buttons during pending writes.
- `apps/student-web/app.js`: added a submission re-entry guard, immutable retry DTO/revision capture, unknown-result freeze and explicit same-submission retry state.
- `tests/test_workspace_frontend_html.py`: added source-level assertions for the guard, frozen content and exact captured DTO retry path; updated the expected submit call after introducing the captured attempt object.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: refreshed current test counts and linked this P3 evidence.

## Commands and results

- `node --check apps/teacher-web/app.js`: PASS.
- `node --check apps/student-web/app.js`: PASS.
- `python -m unittest discover -s tests -p test_workspace_frontend_html.py -v`: **4/4 PASS**.
- `node --test tests/workspace-client.test.mjs`: **16/16 PASS**.
- `python -m unittest discover -s tests -v`: **154 tests, 153 passed, 1 skipped**, exit code 0, 47.063 seconds.
- Skip: Windows symlink creation was denied by the environment (`WinError 1314`); this is not evidence that symlink attacks are prevented.

## Acceptance and boundary

| Check | Result | Boundary |
| --- | --- | --- |
| Repeated teacher save/publish activation while pending is blocked | PASS | Static source assertion; no browser interaction. |
| Repeated student submit activation while pending is blocked | PASS | Static source assertion; no browser interaction. |
| Unknown student submission retains original DTO, workspace and revision | PASS | Source path assertion plus existing client idempotency retry test. |
| Unknown submission locks the content and presents a same-submission retry label | PASS | Static source assertion; actual visual and DOM state unverified. |
| Definite rejection clears retry state and restores controls | PASS | Static source assertion; runtime browser behavior unverified. |
| Teacher create/publish unknown-outcome retry preserves the same DTO across the multi-step flow | PARTIAL | Current guard blocks only concurrent in-flight clicks; unknown create/publish recovery is not yet frozen to an immutable task attempt. |
| HTTP, browser rendering, service restart, multi-client concurrency | NOT VERIFIED | No service, port or browser was started. |

Task-level P3 result is **PASS** for these bounded controls. The overall UI/API integration remains **PARTIAL**, and P4 visual QA is still outstanding. This is local synthetic, process-memory-only, non-production behavior. Teacher/student demo routes are fixed presentation roles, not authentication. Submitted text is not executed. The prior Windows symlink test remains skipped, and Foundation Spike remains PARTIAL.

## Git and follow-up

- Branch observed: `codex/r0-teacher-task-authoring`.
- Existing modified and untracked files were preserved. No staging, cleanup, reset, deletion, commit, push, service launch, port opening, browser launch or deployment occurred.
- Commit: `NONE`.
- Next: close the teacher create/publish uncertain-outcome path by preserving the exact task DTO and step (create versus publish) for safe same-request retry. Do not claim browser or full-product integration until a compliant preview path is available.
