# Workspace Loopback Static Asset Route Report

- Task ID: `R0-WORKSPACE-LOOPBACK-STATIC-ASSET-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for fixed static WSGI routing; overall UI/API integration remains PARTIAL**
- Commit: `NONE`

## Scope

The current teacher/student pages and `/api/v1/demo/{role}` API previously had no shared WSGI asset route. The bounded change adds an exact static-resource allowlist to `WorkspaceWsgiApp`, so direct WSGI calls can resolve the current HTML/CSS/JS modules through the same adapter as the synthetic API. No HTTP server, port or browser was started; no visual/runtime QA is claimed.

The assets are repository-owned app source. No student/teacher data, credentials, real files, model, ECS, external network, persistence or code execution was used.

## Routes and controls

- Teacher page aliases: `/demo/teacher`, `/demo/teacher/`, `/demo/teacher/index.html`; assets: `/demo/teacher/app.js`, `/demo/teacher/styles.css`.
- Student page aliases: `/demo/student`, `/demo/student/`, `/demo/student/index.html`; assets: `/demo/student/app.js`, `/demo/student/styles.css`.
- Shared module: `/demo/workspace-client.mjs`, matching the pages' relative `../workspace-client.mjs` import.
- Every static route is an exact allowlist key mapped to a fixed relative repository path. User URL text is never joined to a filesystem path.
- WSGI loopback peer validation runs before static path handling. Static responses use `no-store` and `nosniff`; non-GET methods are denied for known static routes.
- Unknown and traversal-shaped paths do not resolve to files and continue to the API router's not-found response.

This is a WSGI-callable code path, not a running preview service or a product deployment. No production authentication/authorization boundary is established; demo roles remain fixed synthetic presentation paths.

## Changes

- `apps/agent-first/agent_first/workspace_wsgi.py`: added fixed static route table and binary asset responses with explicit content types behind existing loopback enforcement.
- `tests/test_workspace_wsgi.py`: added an in-process WSGI route test for both page assets, shared client module, content types/security headers, non-loopback denial, POST denial and traversal miss.
- `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: updated route scope and current HTTP/browser evidence boundary.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **8/8 PASS**.
- `python -m unittest discover -s tests -v`: **153 tests, 152 passed, 1 skipped**, latest run exit 0, 49.448 seconds. The skipped Windows symlink test could not create a symlink due to `WinError 1314`; this is not symlink-safety evidence.
- `node --test tests/workspace-client.test.mjs`: **16/16 PASS**.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, `node --check apps/student-web/app.js`: passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`, `python -m py_compile apps\agent-first\agent_first\workspace_api.py apps\agent-first\agent_first\workspace_wsgi.py tests\test_workspace_api.py tests\test_workspace_wsgi.py tests\test_workspace_json_schema.py`, and `git diff --check`: passed.

## Acceptance

| Check | Result | Boundary |
| --- | --- | --- |
| Teacher/student HTML references resolve to allowlisted CSS/JS and module import | PASS | In-process WSGI test checks both pages' relative refs and shared-client import target. |
| Shared client module resolves at the relative import path | PASS | Static direct-call test verifies route and module content marker. |
| Non-loopback requests denied before asset response | PASS | WSGI environment test; no network listener started. |
| POST, unknown and traversal-shaped asset paths cannot read files | PASS | Direct WSGI negative tests. |
| Live HTTP and browser visual QA | NOT RUN | No service or business port opened; no browser used. |
| Production readiness | NOT CLAIMED | Fixed synthetic roles, process memory and non-production only. |

## Current phase and next step

P3 code-level DTO/client and WSGI route wiring continues. The direct route now has a coherent fixed page/API asset map, but it has not been launched and is not visual evidence. Continue with static/direct-call integration checks. Any later HTTP/browser verification must follow the user-authorized local preview boundary; the current change itself does not authorize opening a listener.

## Git

- Branch: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked work was preserved. No cleanup, reset, commit, push, server launch, browser launch or deployment occurred.
- Commit: `NONE`.
