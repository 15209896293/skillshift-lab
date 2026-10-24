# WSGI Vertical Flow and Readback Report

- Task ID: `R0-WORKSPACE-WSGI-VERTICAL-READBACK-001`
- Current Gate: P3 synthetic API / UI DTO integration by direct callable test
- Result: **PASS for the exercised WSGI callable path and HTTP-shaped responses; overall product integration remains PARTIAL**
- Contract status: local synthetic / in-memory / non-production; Proposed API extensions remain Proposed
- Commit: `NONE`

> Evidence snapshot note: this report records the earlier 8/8 WSGI and 171-test snapshot. A later task extended the same WSGI test file and tightened teacher CREATE/PUBLISH DTO receipt checks; current counts and hashes are in `WORKSPACE_TEACHER_CREATE_PUBLISH_RECEIPT_GUARDS_REPORT_2026-09-25.md`. Hashes below identify the file bytes captured for this report and are not asserted to match the current checkout after that later edit.

## Objective and read-only gap audit

The preceding WSGI round-trip covered teacher task creation/publication, student discovery/start, a synthetic fixture snapshot submission, teacher review, remediation, resubmission and ACK. Latest-submission and review-history reads were covered by lower-level API tests, but the entire ordered flow had not exercised those DTOs through the WSGI adapter. The existing test also did not include an Agent collaboration turn or cross-role/error responses for the two read routes.

Two independent read-only reviews confirmed that the correct boundary here is to call `WorkspaceWsgiApp` directly, not start a server. The adapter checks loopback `REMOTE_ADDR`, attaches `no-store` and `nosniff` to all responses, and presents URL-selected fixed demo roles; this does not establish deployment binding or identity authorization.

## Changes

- `apps/agent-first/agent_first/workspace_wsgi.py`: catch `TypeError` as well as `ValueError` when parsing an invalid `REMOTE_ADDR`; malformed WSGI peer values now receive the same explicit `403 loopback_only` response instead of escaping the boundary check.
- `tests/test_workspace_wsgi.py`: extended the existing direct-call vertical test without adding a test case. It now follows this sequence:
  1. Teacher creates and publishes a synthetic assignment.
  2. Student discovers it, starts the workspace, receives a deterministic `scripted-demo` guidance turn and rejects the proposed file patch.
  3. Student reads `submission: null`, submits the repository's synthetic fixture text, and reads back a complete Submission DTO exactly matching the write receipt.
  4. Teacher reads the queue and snapshot, requests remediation; student resubmits version 2 and latest-read returns the full version 2 DTO.
  5. Teacher acknowledges; latest-read returns that same submission ID in `ACCEPTED`, and review-history returns the remediation and ACK in two ordered pages.
  6. The test checks role-confused reads return uniform 404 envelopes, malformed history cursors return 400, GET responses use `no-store`, and review-history excludes snapshot and student explanation fields.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, and this spec's `README.md`: update the current evidence pointer and state what the direct-call test does and does not prove.

No server, business port, browser, real teacher/student data, credentials, model, ECS or student-code execution was used. The fixture read in the test is repository-owned synthetic text; this is not a real student file.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **8/8 PASS** after final edits.
- `python -m unittest discover -s tests -v`: **171 total, 170 passed, 1 skipped; exit 0; 47.209 seconds** after final edits. The skip is the Windows symlink-creation permission case (`WinError 1314`); it is not symlink safety evidence. Temporary copied-runner path diagnostics appeared in isolation tests and those tests passed.
- `node --test tests/workspace-client.test.mjs`: **33/33 PASS**.
- `python tests/test_workspace_frontend_html.py`: **14/14 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **34/34 PASS**.
- `python -m unittest discover -s tests -p test_workspace_json_schema.py -v`: **8/8 PASS**.
- `python -m py_compile apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_wsgi.py`: **PASS**.
- `git diff --check`: **PASS for tracked changes**. The new/modified WSGI source and test are untracked in the current pre-existing dirty checkout; a direct trailing-whitespace scan of the changed project docs and source/test files found no matches.

## Acceptance and limits

| Acceptance | Result |
|---|---|
| One direct callable test exercises the ordered teacher → student → teacher remediation cycle | PASS |
| Student latest read is empty before submit and exactly reflects the first submission, resubmission and accepted state | PASS |
| Review history pages remediation and ACK in event order without submission snapshot/explanation fields | PASS |
| Cross-role read failures, malformed cursor, cache headers and malformed peer input are explicit | PASS |
| WSGI network binding / HTTP request handling / browser rendering and visual QA | NOT TESTED |
| Fixed URL demo role is authentication or real assignment ownership | NOT CLAIMED |
| Latest/history reads identify a specific prior request whose write receipt was unknown | NOT CLAIMED |
| Persistence, retention, production authorization, execution isolation or deployability | NOT TESTED |

The WSGI call is an in-process function invocation with HTTP-shaped environ/response values. It does not prove that a server is bound exclusively to loopback, that an intermediary preserves `REMOTE_ADDR`, or that a browser can complete the flow. Latest/history DTOs remain Proposed local-synthetic extensions. The API stores submissions and reviews only in process memory. The demo actors are fixed path labels, not authentication. The scripted guidance is not a live model; a proposed diff is text only and is never applied or executed.

## SHA-256 evidence

Hashes are over the file bytes captured when this report was written. Recompute with `Get-FileHash -Algorithm SHA256` to compare the current checkout.

| File | SHA-256 |
|---|---|
| `apps/agent-first/agent_first/workspace_wsgi.py` | `704C2425C321CAC32627C6D81071E0B54E3E3DB4CC0F8AC66C0A4913C5757018` |
| `tests/test_workspace_wsgi.py` | `0C9DF6163BD62451B8BE68D822C9A9D36F607F05E6BE2CB7E13C560CB98D565B` |
| `README.md` | `74971CE7BAF50168B559D26E6503BF09A7D576795186373195918D2ECC153024` |
| `docs/README.md` | `DABFE9D194B24D6289E8C4962E23ADB6C6A67D369A8482E163AE4AEEDE3EC213` |
| `docs/CURRENT_STATE.md` | `443DC0F37E9DC487E05F4C68B68D4F8139808CDF87703F141BF26D0C8BCD6A02` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `9E95F8C1A3C84B184A90FE691771802860880C168479E317F1D8FE37D998AD99` |

## Git summary

The existing checkout contains extensive unrelated tracked modifications and untracked project assets. They were left in place. This task added no staging, commit, push, delete, reset, or cleanup action. `git diff --stat` only represents pre-existing tracked changes and does not include most untracked sources or this report. Commit: `NONE`.

## Next step

Continue the bounded P3 integration audit with a read-only comparison of teacher/student visible failure states against the direct WSGI responses, focusing on assignment publish/create retries and stale revision conflicts. Keep it static or direct-call only unless a compliant preview path is explicitly established. P4 browser/visual QA remains open; no user decision is required for the next synthetic-only audit.
