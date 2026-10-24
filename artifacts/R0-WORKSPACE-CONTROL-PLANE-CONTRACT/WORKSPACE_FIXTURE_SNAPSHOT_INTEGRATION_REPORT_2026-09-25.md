# Workspace Fixture-to-Snapshot Integration Report

- Task ID: `R0-WORKSPACE-FIXTURE-SNAPSHOT-INTEGRATION-001`
- Current Gate: P3 local synthetic API / frontend DTO wiring
- Result: **PASS for fixture-to-snapshot WSGI evidence; overall UI/API product integration remains PARTIAL**
- Commit: `NONE`

## Scope and audit finding

A read-only gap audit found that student page embedded content was tested byte-for-byte against the candidate fixture, but the WSGI teacher/student round-trip test submitted a separately hand-written single-file string. That left the fixture-to-`artifact_contents`-to-submission-snapshot-to-teacher-queue evidence split across tests.

The bounded change makes the direct WSGI synthetic round trip read the three repository-owned fixture text files (`main.py`, `orders.csv`, `README.md`) and submit those contents with the same allowlisted names. It compares each returned snapshot's content, UTF-8 byte count and SHA-256 against the fixture manifest, then verifies that the teacher review queue returns the same snapshots. The remediation version keeps the file set and changes only the synthetic `main.py` text.

This does not promote `CANDIDATE_CANONICAL_SOURCE` to an accepted unique source. The student page still embeds a copy, and its existing byte-equality test remains the evidence that the current copy matches the candidate fixture. No production source-of-truth decision was made.

## Changed files

- `tests/test_workspace_wsgi.py`: replaced the unrelated hand-written initial submission sample with manifest-backed fixture contents and per-file content/size/hash assertions through the WSGI API and review queue.
- `docs/CURRENT_STATE.md`: records the verified task outcome and corrects the stale branch name to the branch observed during this run.
- `artifacts/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/WORKSPACE_LOOPBACK_STATIC_ASSET_REPORT_2026-09-25.md`: refreshes the latest full-suite duration and points to this subsequent evidence.
- `README.md`, `docs/README.md`, `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md`: make the newest artifact discoverable and state its candidate-source boundary.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **8/8 PASS**.
- `python -m unittest discover -s tests -v`: **153 tests, 152 passed, 1 skipped**, exit code 0, 49.448 seconds.
- Skip: Windows symlink creation denied with `WinError 1314`; this is not symlink-attack safety evidence.
- `node --test tests/workspace-client.test.mjs`: **16/16 PASS**.
- `node --check apps/workspace-client.mjs`, `node --check apps/teacher-web/app.js`, and `node --check apps/student-web/app.js`: passed.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: passed.
- `python -m py_compile apps/agent-first/agent_first/workspace_api.py apps/agent-first/agent_first/workspace_wsgi.py tests/test_workspace_api.py tests/test_workspace_wsgi.py tests/test_workspace_json_schema.py`: passed.
- `git diff --check`: passed.

## Gate and limitations

| Acceptance | Result | Evidence boundary |
| --- | --- | --- |
| Candidate fixture contents form the actual bounded `artifact_contents` payload | PASS | In-process WSGI call; repository synthetic fixture only. |
| API snapshots preserve fixture text, UTF-8 byte count and manifest SHA-256 | PASS | Three per-file assertions against the manifest. |
| Teacher queue reads back the submitted snapshots unchanged | PASS | Same WSGI application instance and in-memory API. |
| Remediation can submit a next version with a bounded file correction | PASS | Only the synthetic `main.py` fixture text is extended. |
| Fixture is the formally accepted unique source | NOT CLAIMED | Manifest still explicitly says `CANDIDATE_CANONICAL_SOURCE`; student page embeds matching bytes. |
| Browser/UI behavior, HTTP runtime, persistence, production use | NOT VERIFIED | No server, port or browser was started. |

This task is P3 evidence PASS within its bounded scope. Overall UI/API product integration and P4 visual QA remain **PARTIAL**. The flow is local synthetic, process-memory only and non-production. Demo routes are fixed presentation roles, not authentication. Submitted code-like text is stored as text and never executed. Foundation Spike remains PARTIAL; the symlink skip does not close its gap.

## Git and next route

- Current branch observed: `codex/r0-teacher-task-authoring`.
- Existing dirty and untracked work was preserved. Nothing was staged, reset, cleaned, committed, pushed, deployed or deleted.
- Commit: `NONE`.
- Continue with static DTO/error-path review and evidence hygiene. Browser visual QA remains pending until an explicitly compliant preview path is established; do not route around that constraint.
