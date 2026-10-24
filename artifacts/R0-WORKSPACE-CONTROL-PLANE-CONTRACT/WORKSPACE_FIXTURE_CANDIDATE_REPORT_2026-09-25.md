# Candidate Synthetic Fixture Source Report

- Task ID: `R0-WORKSPACE-FIXTURE-CANDIDATE-001`
- Current Gate: P3 workspace API contract; candidate fixture consistency only
- Result: **PARTIAL**
- Commit: `NONE`

## Changed files and rationale

- `fixtures/orders-audit-v1/main.py`, `orders.csv`, `README.md`: establish one fixed, synthetic example package for the currently demonstrated order-audit project. The Python file is instructional text and is not executed.
- `fixtures/orders-audit-v1/manifest.json`: records schema/version, candidate status, execution disabled, logical filenames, MIME types, byte lengths and SHA-256 digests.
- `tests/test_workspace_fixture.py`: verifies manifest-to-byte integrity, synthetic/non-executable framing, API allowlist alignment, and byte-for-byte equivalence with the student prototype's currently embedded content.
- `apps/README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`: expose the fixture and latest evidence while retaining its candidate status and integration limits.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_fixture.py -v`: **PASS, 4/4**.
- `python -m unittest discover -s tests -v`: **PASS, 137 total; 136 passed, 1 skipped; exit 0; 47.798 seconds**.
- The skipped test is `test_rejects_symlink_path_when_supported`; Windows returned `WinError 1314` because symbolic-link creation privilege is unavailable. This is not evidence that symlink attacks are blocked.
- The full suite includes existing Foundation Windows-isolation probes. Their output reports temporary copied-runner diagnostics; the probes completed, but do not close the Foundation security gaps.
- `git diff --check`: run after report and documentation edits (see final verification below).

## Evidence and hashes

The test checks actual bytes against the manifest at runtime. SHA-256 values for the current fixture package:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `fixtures/orders-audit-v1/main.py` | 483 | `8559de9beff659d172daafd806813f11c51b756d1b114abe548dc65e035187a1` |
| `fixtures/orders-audit-v1/orders.csv` | 97 | `fa25d89edfa82b28b19d1ad0913aa44759d4c4c39516dc44040c5ad999888e79` |
| `fixtures/orders-audit-v1/README.md` | 287 | `827cc97eb5594a9f693d8ca560c8a1e83a47ed84df9d236b6ea305628b18c141` |
| `fixtures/orders-audit-v1/manifest.json` | 759 | `3af44afc347bd717b5ff34c1d434cabf5fbb918713dc9e4d3f6ef95764ce61c1` |
| `tests/test_workspace_fixture.py` | — | `904c0c9be5ae51b2e181a2438bec5edc567a7a9509fdb696a6d3592e7c1e01ec` |

## Acceptance and limits

- PASS: manifest filenames/MIME types match the API's fixed artifact allowlist.
- PASS: manifest byte lengths and SHA-256 match the local files; the three student-page embedded strings match those bytes exactly.
- PASS: fixture content states that code is not run and keeps unresolved business rules explicit.
- PARTIAL: `fixture_status` is `CANDIDATE_CANONICAL_SOURCE`, not an accepted canonical-source decision. The API does not read fixture files or compute hashes; Artifact references remain `NOT_COMPUTED`.
- PARTIAL: the student page still embeds copies and the teacher page still has separate demonstration content. No UI now consumes this fixture, and no browser integration/visual QA was performed.
- The sample data is synthetic only. No student data, real model, credential, network, ECS, deployment, or code execution was involved.
- Foundation Spike remains PARTIAL; the symlink privilege skip and other known isolation gaps remain open.

## Next work, risks, and decision status

Next safe implementation step is a static design/contract task: define how the teacher task catalog and student workspace refer to one immutable starter-project version, without reading arbitrary paths or executing files. Then implement a fixture-backed read-only adapter only if the existing product/API contract supports it, with tests for path traversal, symlink substitution, digest mismatch, missing files, and bounded file sizes. Keep all current pages and API behavior unchanged until a permitted preview path exists for visual integration QA.

No user decision is needed for this synthetic consistency check. Acceptance of a production artifact-source design, filesystem access, real user data, model/Key, ECS, deployment, or code execution remains outside this report and requires its own approved boundary.

## Git

- Worktree contains extensive pre-existing modified and untracked project artifacts; they were preserved.
- `git diff --stat` only summarizes tracked modifications and does not include untracked files, so it is not a complete inventory of this task's artifacts.
- No commit, push, deployment, deletion, reset, cleanup, or server launch occurred.
- Commit: `NONE`.
