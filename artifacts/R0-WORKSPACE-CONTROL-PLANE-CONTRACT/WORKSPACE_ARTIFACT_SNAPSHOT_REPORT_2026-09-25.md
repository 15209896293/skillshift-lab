# Synthetic Submission Artifact Snapshot Report

- Task ID: `R0-WORKSPACE-ARTIFACT-SNAPSHOT-001`
- Current Gate: P3 local synthetic API contract; submission artifact handoff
- Result: **PASS for bounded synthetic in-memory snapshot behavior; overall integration remains PARTIAL**
- Commit: `NONE`

## Files changed and rationale

- `apps/agent-first/agent_first/workspace_api.py`: accepts only a selected allowlist of UTF-8 text snapshots, validates exact name correspondence and byte limits, computes SHA-256 server-side, and includes snapshots in submission/teacher review queue responses. It never reads or writes a host file path and never executes content.
- `tests/test_workspace_api.py`: tests content/hash fidelity, exact selected-name matching, teacher queue visibility, type/NUL rejection, 8 KiB per-file cap, 12 KiB combined cap, and existing lifecycle/replay behavior with the expanded DTO.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json`: adds strict `ArtifactSnapshot` response shape and submission field.
- `tests/test_workspace_json_schema.py`: validates produced snapshot DTOs and rejects unknown path fields, path-like names and over-limit content.
- `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: updates the proposed synthetic-only boundary and limits; makes clear production file handling/retention is not decided.
- `docs/CURRENT_STATE.md`, `apps/README.md`, `docs/README.md`: update current counts, product/API boundary and integration state.
- No browser UI was wired in this task. The pages remain local demonstrations.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **PASS, 26/26**.
- `python -m unittest discover -s tests -p test_workspace_json_schema.py -v`: **PASS, 4/4**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `python -m py_compile apps\agent-first\agent_first\workspace_api.py tests\test_workspace_api.py tests\test_workspace_json_schema.py`: **PASS, exit 0**.
- `python -m unittest discover -s tests -v`: **PASS, 142 total; 141 passed, 1 skipped; exit 0; 48.033 seconds**.
- The one skipped test is the existing symlink creation test; Windows returned `WinError 1314`. It does not prove symlink safety.
- `git diff --check`: **PASS** after this report and documentation were complete.

## Evidence and acceptance

- Selected names must match content-map keys exactly; arbitrary path names remain refused by the existing allowlist test.
- Each response snapshot contains the exact submitted text, UTF-8 byte count and server-computed SHA-256; teacher review queue returns the same snapshot.
- Missing content, NUL, non-text content, >8 KiB individual content and >12 KiB combined content fail closed.
- Snapshot responses are bounded further by the existing 16 KiB JSON request body limit. Data is held only in the current synthetic process memory and disappears when it stops.
- No real student data, credentials, model/API, network, ECS, deployment or code execution was used. No server was launched.

## Limits and risks

- This is a local synthetic adapter contract, not authorization to upload real student files. Production retention, encryption, deletion, identity, audit access and file policy remain undecided.
- The teacher/student frontends still do not call this API. No end-to-end or visual result is claimed.
- The starter fixture remains a candidate source; this change hashes submitted snapshots but does not resolve the initial-file duplication among fixture and pages.
- Foundation Spike remains PARTIAL. The symlink privilege skip and operating-system isolation gaps remain open.

## Next work and Git

Next continue with pure code tests for the frontend-to-DTO mapping, then connect the independent teacher and student screens only within this synthetic adapter boundary. Browser visual QA still needs a compliant preview path; no alternate navigation was attempted. No user decision is required for this synthetic-only test contract. Extensive pre-existing worktree changes were preserved; tracked `git diff --stat` is cumulative and omits untracked files. No staging, commit, push, deployment, deletion, reset or cleanup occurred. Commit: `NONE`.
