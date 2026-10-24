# Workspace P3 DTO / Conflict / Retry Guards Report

- Task ID: `R0-WORKSPACE-P3-DTO-CONFLICT-RETRY-AUDIT-2026-09-26`
- Gate: P3 local synthetic API / WSGI callable / DTO client
- Result: **PASS for the three bounded fixes; overall product remains PARTIAL**
- Date: 2026-09-26

## Scope and evidence boundary

This pass stayed within the existing local synthetic contract. It did not start an HTTP server, bind a port, open a browser, use real teacher/student data, call a model, connect to ECS, execute student code, deploy, commit, push, delete, move, reset, or clean files. Fixed demo roles remain non-authenticated; API state remains process memory.

## Changes

1. `apps/agent-first/agent_first/workspace_wsgi.py`: preflight errors no longer reuse `req-demo`; each WSGI error envelope receives a fresh opaque `req-wsgi-*` request ID.
2. `apps/agent-first/agent_first/workspace_api.py`: query parsing preserves blank values and separately rejects blank/non-integer cursors and page limits instead of treating them as omitted defaults.
3. `apps/workspace-client.mjs`: successful envelopes require a non-empty `request_id`; Workspace `artifact_refs` are checked against the existing ArtifactReference DTO guard.
4. Tests add coverage for distinct WSGI preflight IDs, blank cursor/page-limit rejection, malformed Workspace artifact references, and missing success request IDs.
5. `apps/student-web/app.js`: when no published workspace exists, the page now disables the editor, file switching, Agent input, and submission entry while retaining the explicit empty-task message.
6. Student pages no longer silently select the first published task. Zero tasks stays empty; one task follows the existing path; multiple tasks are explicitly blocked because the product has not yet defined task selection.
7. `apps/teacher-web/app.js`: remediation and review-queue reads now isolate per-assignment failures; successful history and other task results are not cleared by one failed task read. Detail-read failures remain local to the current submission area.

## Verification

- `python -B -m unittest discover -s tests -v`: **178 tests, 177 PASS, 1 SKIP**.
- `python -B -m unittest discover -s tests -p 'test_workspace*.py' -v`: **75/75 PASS**.
- `node --test tests/workspace-client.test.mjs`: **36/36 PASS**.
- Frontend static tests: **19/19 PASS**.
- `python -B -m unittest discover -s tests -v`: **179 tests, 178 PASS, 1 SKIP** after the later UI guards were integrated.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, `node --check apps/student-web/app.js`: PASS.
- `python -m py_compile` over the relevant Python source files: PASS.
- `git diff --check`: PASS.

The skipped test is the existing Windows symbolic-link creation case (`WinError 1314`); it is not evidence that symlink safety passed.

The multi-task and partial-failure claims are supported by static source assertions and controlled DTO-path checks, not browser timing or live HTTP evidence.

## Remaining read-only audit findings

The UI audit also identified multi-assignment teacher review selection, student selection among multiple published assignments, and per-assignment isolation of partial read failures. These are retained as follow-up design/implementation items because resolving them changes the page interaction model or requires an explicit single-assignment invariant. They were not silently changed in this bounded pass.

## Hashes

Hashes were captured after the final edits and are recorded in the completion report; this artifact itself is the source for the report hash.

Commit: `NONE`
