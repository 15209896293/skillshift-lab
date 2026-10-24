# Student Latest Submission Read Race Guard Report

- Task ID: `R0-WORKSPACE-STUDENT-LATEST-READ-RACE-GUARD-001`
- Current Gate: P3 student read DTO and UI failure-state wiring
- Result: **PASS for latest-read field validation and stale-response guards; overall product integration remains PARTIAL**
- Contract status: Proposed local-synthetic extension; process-memory only; non-production
- Commit: `NONE`

> Evidence snapshot note: this report predates the following Student Agent collaboration-state task. `apps/workspace-client.mjs`, `tests/workspace-client.test.mjs`, the static frontend tests and the current summary counts have since changed; use `WORKSPACE_STUDENT_COLLABORATION_ERROR_STATES_REPORT_2026-09-25.md` for latest hashes and regression results.

## Read-only finding

An independent read-only audit traced the student latest-submission GET and submission retry paths. Read failures, missing DTOs, wrong workspace IDs, invalid snapshot hashes and invalid submission states already display an unknown/failure state; only an explicit `submission: null` displays “no record.” The read-only renderer uses `textContent` and does not mutate the editor or clear an unresolved submission attempt.

The audit found a race: initialization and post-submit reads could overlap. A global in-flight boolean silently returned from the post-submit read, allowing the earlier request to render an empty or old submission after a new submission had already succeeded. It also found the read data wrapper accepted extra fields even though the strict wire schema prohibits them.

## Changes

- `apps/student-web/app.js`: replace the latest-read single-flight boolean with an increasing request generation. Each read still runs, but only the newest request may write success or failure state into the latest-submission region. The guard covers both the success and `catch` paths. Older requests cannot overwrite the newest result.
- `apps/workspace-client.mjs`: latest read now requires the exact data-wrapper field set `{"submission"}` before validating either `null` or a complete Submission DTO.
- `tests/test_workspace_frontend_html.py`: add static assertions that the generation increments for each read, both success and catch paths discard stale results, and the silent single-flight guard is absent.
- `tests/workspace-client.test.mjs`: add `{submission: null, unexpected: true}` to malformed read receipts; the client rejects it as `invalid_response`.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, and `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: record this latest evidence, the static-test limit and the browser/HTTP boundary.

This is a UI source/static and client fault-injection fix. No browser timing test was possible under the no-preview boundary; no HTTP service was started.

## Commands and results

- `node --test tests/workspace-client.test.mjs`: **34/34 PASS**.
- `python tests/test_workspace_frontend_html.py`: **14/14 PASS**.
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **9/9 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **34/34 PASS** (unchanged API code; run in this task batch before the full suite).
- `python -m unittest discover -s tests -v`: **172 total, 171 passed, 1 skipped; exit 0; 46.883 seconds**. The skip is the Windows symlink-creation permission case (`WinError 1314`); it is not symlink-safety evidence. Temporary copied-runner path diagnostics appeared in isolation tests and the affected tests passed.
- `node --check apps/student-web/app.js`: **PASS**.
- `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `git diff --check`: **PASS for tracked changes**. A direct trailing-whitespace scan of changed source, tests and docs found no matches.

## Acceptance and limits

| Acceptance | Result |
|---|---|
| Older in-flight latest reads cannot overwrite a newer read's success | PASS by source guard plus static assertion |
| Older in-flight latest reads cannot overwrite a newer read's failure | PASS by source guard plus static assertion |
| A malformed latest wrapper with extra fields is rejected | PASS in Node client test |
| Latest read remains separate from editor contents and pending submission attempt | PASS by existing static source checks |
| Browser execution of the out-of-order timing scenario | NOT TESTED |
| HTTP service, visual QA, authentication, persistence, production authorization | NOT TESTED |

The generation guard is verified by static source assertions, not a live DOM scheduler. The client validates exact wrapper keys plus the fields and content used by the page; it is not a general-purpose full JSON Schema validator. Latest read shows the API's current record, not proof that a particular unknown prior write request succeeded. Fixed demo roles are URL labels, not identity. Data and retry state remain in process/page memory; code execution is closed.

## SHA-256 evidence

Hashes are over current file bytes; recompute after a later edit.

| File | SHA-256 |
|---|---|
| `apps/student-web/app.js` | `3F7A0F0DA8FF82479B82A1F739D81E127FAAC68EC66054F718E80009A40BA38B` |
| `apps/workspace-client.mjs` | `EA0B5AFDA49B3D62954CC65E0118B80CA95E20E0627B0F2EDF5CCF617E4DD02A` |
| `tests/test_workspace_frontend_html.py` | `261F03F0E08FD39A9EF6019EADC2AA703E9E7CFEBFD104F8DFCE63677318D824` |
| `tests/workspace-client.test.mjs` | `8AA4F07F000A5E0D741FD361B965B0241BC1BF5E908E6391C85836F60107738D` |
| `README.md` | `AD3564161851925F4F0BD1A70FCA7081C557F682FE05E38B36F0890A3303DEE2` |
| `docs/README.md` | `1C0ED5B5173D32EEF19E2BD3357DC3AABD7942C3724CCD85F96D25C627C8F251` |
| `docs/CURRENT_STATE.md` | `BDF169C3D2AB63DC99BFE9483654C44D9F73967B4F9EA55BBF746F71314536B6` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `00B1DD46D1319FDDE4645A2375358ADFD42397E1BE185B2D2D95D0DFD53F8B61` |

Earlier stage reports preserve their own historical snapshots; this report contains the current student/client/document hashes after this task.

## Git summary and next step

All pre-existing user changes and untracked files remain in place. No staging, commit, push, delete, reset or cleanup occurred. The displayed Git diff summary is incomplete because most application code and tests are untracked. Commit: `NONE`.

Continue with the next narrow source/error-state audit for student collaboration responses and teacher review/remediation reads. Keep verification in static, unit and direct callable form; browser/HTTP/P4 visual QA remains open pending a compliant preview path.
