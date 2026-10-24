# Assignment Catalog Visibility Report

- Task ID: `R0-WORKSPACE-ASSIGNMENT-CATALOG-001`
- Current Gate: P3 local synthetic API contract
- Result: **PASS for fixed-demo assignment visibility; overall API/product remains PARTIAL**
- Commit: `NONE`

## Files changed and rationale

- `tests/test_workspace_api.py`: added a test proving draft/published visibility in the teacher and student assignment catalogs.
- `docs/CURRENT_STATE.md`: updated the API/full-suite counts and evidence index.
- This report records the narrow route result. No runtime implementation or UI changed.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **PASS, 25/25**.
- `python -m unittest discover -s tests -v`: **PASS, 141 total; 140 passed, 1 skipped; exit 0; 49.715 seconds**.
- `git diff --check`: **PASS** after this report and state update.
- The sole full-suite skip is the real symlink path test; Windows returned `WinError 1314` due to unavailable symlink creation privilege. This is not evidence of symlink protection.

## Acceptance evidence

- A draft appears in the teacher catalog.
- The same draft is absent from the student catalog and direct student read is not found.
- After teacher publication, the task appears in the student catalog with `PUBLISHED` state.

This verifies the fixed synthetic route behavior only, not production role or assignment authorization.

## Limits, risks, next, and decision

- Teacher and student frontends still use local demo state and are not connected to this API.
- The current contract does not transfer the student's edited file contents to the teacher; only allowlisted names and a written explanation reach the submission object. This is an integration gap against the product-level expectation that submissions include project artifacts. Next step is to define and test a synthetic-only artifact snapshot handoff, with fixed filenames, strict byte limits, no filesystem paths, no execution, and ephemeral storage before connecting the pages.
- Real file upload, persistence/retention, real identities/data, models, credentials, ECS and deployment remain out of scope. Foundation Spike remains PARTIAL.
- No user decision is required for this visibility test. Whether/how to retain real student files in a future deployment remains a separate decision.
- Existing dirty files were preserved. No staging, commit, push, deployment, deletion, reset or cleanup occurred. Tracked `git diff --stat` is cumulative and omits untracked files. Commit: `NONE`.
