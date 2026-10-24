# Workspace Idempotency, Revision and Event Guards Report

- Task ID: `R0-WORKSPACE-IDEMPOTENCY-REVISION-EVENT-GUARDS-001`
- Current Gate: P3 synthetic UI/API DTO and error-state wiring
- Result: **PASS for the covered idempotency, DTO revision and direct WSGI event-chain assertions; overall product integration remains PARTIAL**
- Scope: local synthetic, in-process memory, non-production
- Commit: `NONE`

## Read-only audit findings

Independent review identified two code gaps and one vertical-coverage gap:

1. `WorkspaceApi._mutate` fingerprinted operation and body, but not the `If-Match` precondition. A cached write receipt could therefore replay after the caller changed or omitted the revision header.
2. Student submit success advanced local state from optional envelope `revision` only. A valid DTO with the required `data.workspace_revision` but no envelope revision left the page on a stale CAS revision.
3. The WSGI vertical workflow exercised the complete teacher/student flow, but did not read and correlate the emitted event chain with write receipts.

## Changes

- `apps/agent-first/agent_first/workspace_api.py`: include normalized `If-Match` in state-write idempotency fingerprints. Exact retries with the same key, body and precondition replay the original response; a missing or changed precondition for a cached key returns `409 idempotency_conflict` before any second side effect. Create-assignment writes retain a `null` precondition.
- `apps/student-web/app.js`: after submit, advance local revision from required `data.workspace_revision`, falling back to the optional envelope revision only if needed.
- `tests/test_workspace_api.py`: extend replay coverage to changed and missing `If-Match`; assert conflict and no duplicate submission/event.
- `tests/test_workspace_wsgi.py`: through direct WSGI calls, verify exact submission replay, changed-precondition conflict, and the full eight-event sequence with receipt sequence, event type and resource reference correspondence.
- `tests/test_workspace_frontend_html.py`: assert submit UI consumes the required DTO revision.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, active contract spec: refresh current evidence pointer and regression counts, retaining the non-production boundary.
- Added this report under `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/`.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **34/34 PASS**.
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **9/9 PASS**.
- `python tests/test_workspace_frontend_html.py`: **17/17 PASS**.
- `node --test tests/workspace-client.test.mjs`: **35/35 PASS**.
- `python -m unittest discover -s tests -v`: **175 total, 174 passed, 1 skipped; exit 0; 48.925 seconds**. The skip is the Windows symlink-creation permission case; it is not symlink-safety evidence. Existing Windows isolation probes print temporary copied-runner diagnostics while passing; those diagnostics do not establish OS isolation.
- `node --check apps/student-web/app.js`: **PASS**.
- `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_api.py tests/test_workspace_wsgi.py tests/test_workspace_frontend_html.py`: **PASS**.
- `git diff --check`: **PASS**.

## Acceptance

| Criterion | Result |
|---|---|
| Same idempotency key, DTO and If-Match replays the exact receipt without a new submission/event | PASS |
| Same key/body with changed or missing If-Match returns `idempotency_conflict` without a second submission/event | PASS |
| Student submission updates the next local CAS revision from required DTO field when envelope revision is absent | PASS by static source assertion; no browser runtime used |
| WSGI event list is strictly increasing and unique, with expected event type/resource for publish, start, Agent Turn, proposal decision, submit, review, resubmit and ACK | PASS |
| Real HTTP/browser timing, rendering, authentication, persistence or production integration | NOT TESTED |

## Independent post-fix review

Two bounded read-only reviews confirmed all six state-changing route families (publish, start, Agent Turn, proposal decision, submission and teacher review) pass `If-Match` into the shared fingerprint path; create-assignment is the only write without a resource revision precondition. They also confirmed that fingerprint normalization and `_match_revision` use the same quote-stripping behavior, and that the student submit handler now follows the required DTO revision with a static test. No additional missed call site was identified. The frontend review notes that the static test does not execute a DOM handler or inspect a subsequent runtime request header; that remains outside this run's evidence.

## SHA-256 evidence

Recompute with `Get-FileHash -Algorithm SHA256` after any edit.

| File | SHA-256 |
|---|---|
| `apps/agent-first/agent_first/workspace_api.py` | `7717F3808C7E0D68EFF4BD63DF2C19A25A298BB64283DFE982D3D3C8C8CB2ACA` |
| `apps/student-web/app.js` | `6B140914E89426420609A8EB0D119C245ABB1114C25C03131B21F7127E0FE893` |
| `tests/test_workspace_api.py` | `86E5F7D78F58C6AABB3FB79528139346A819432D9CF4DB39E8F344B15037EC24` |
| `tests/test_workspace_wsgi.py` | `D97AED7D170E2B539F100B3C59C0585637E685AAD924E9F0E067F8F794202D8C` |
| `tests/test_workspace_frontend_html.py` | `CAB9331B7A83668A75C129C684C6F097FA6C5A88AA377CB2DB18AD85112CB067` |
| `README.md` | `60C232935ED78A4325D06472ADB51072B13A0C2D5439FFC9DFBC88E21BFC9544` |
| `docs/README.md` | `BAD2BD7E48BB3E78C13FE2A14716C2EB355FAE035DC6FA0F194FA6C501EBB379` |
| `docs/CURRENT_STATE.md` | `70879398AC9B4BACA8F6239FE55D2BB57DBD1EA4995954A0BDB5BCDBB3D93788` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `7EFB215BFAE74F587AD7FFE2BD264FEBAE7187FA6699D8922D3B1ACD00F13DB0` |

The previously handed-off value `9C4DAAE105B3DCD490BD18F3B9D6C64AF43ADF4D7EC8402D54193C38A1A6263B` was recomputed and matches the bytes of `WORKSPACE_ARTIFACT_SNAPSHOT_REPORT_2026-09-25.md`; it is the report hash, not a persisted individual submission snapshot. The three candidate fixture file hashes were also recomputed and match `fixtures/orders-audit-v1/manifest.json`: `main.py` `8559DE9BEFF659D172DAAFD806813F11C51B756D1B114ABE548DC65E035187A1`, `orders.csv` `FA25D89EDFA82B28B19D1AD0913AA44759D4C4C39516DC44040C5AD999888E79`, `README.md` `827CC97EB5594A9F693D8CA560C8A1E83A47ED84DF9D236B6EA305628B18C141`. These are repository fixture bytes, not a snapshot persisted by the API.

## Limitations, risks and next step

- The UI/API flow remains a fixed-role local synthetic prototype; demo role paths are not authentication, API state is process memory, and the wire/API extension remains Proposed.
- No HTTP service, browser, business port, real user, real model, host file path access or code execution was used. Browser visual QA and dynamic UI race testing remain open.
- A wrong or absent If-Match on a reused key is now a key-content conflict by design; callers must retain and retry the original exact request identity.
- Foundation Spike remains PARTIAL; the symlink permission skip is not evidence of symlink safety. The workspace continues to be non-production.
- No user decision is needed for the next bounded synthetic step: continue auditing UI recovery and client DTO edges, then verify any concrete finding with direct/static tests. Keep P4 HTTP/browser QA explicitly open unless separately authorized.

## Git summary

- Branch: `codex/r0-teacher-task-authoring`.
- Preserved pre-existing dirty tracked edits and untracked project files; no staging or cleanup.
- `git diff --stat` shows only tracked edits and omits much of the existing untracked implementation; the new report and source/test files are also untracked in this working tree. Review `git status --short` for the complete state.
- Commit: `NONE`.
