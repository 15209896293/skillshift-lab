# Student Collaboration Error-State Report

- Task ID: `R0-WORKSPACE-STUDENT-COLLABORATION-ERROR-STATES-001`
- Current Gate: P3 student Agent/Proposed Action DTO and failure-state wiring
- Result: **PASS for the covered UI source guards and client response/error contracts; overall UI/API product integration remains PARTIAL**
- Contract status: local synthetic, process/page memory, non-production
- Commit: `NONE`

## Independent read-only audit

An independent review checked Student Agent Turn and Proposed Action handling, plus teacher remediation reads. It found three student-side gaps:

1. On unknown REJECT or STUDENT_TAKEOVER receipt, the handlers kept the proposal ID only in a mutable global. The student could send a new Agent Turn, replace that ID, and lose the ability to retry the exact old decision.
2. The API DTO validator allowed `availability=UNAVAILABLE`; the UI success path still cleared the attempt, inserted a reply, and showed a success toast.
3. Proposal decision responses require `data.workspace_revision`, but the UI used only the optional top-level `revision`. A valid receipt without the envelope revision could be reported as a successful decision while leaving the next write's local If-Match stale.

The review did not find a definite false-empty/false-success path in teacher remediation reads: read failures are presented as unknown, DTO state is validated, and generation checks guard stale asynchronous completions. Dynamic DOM concurrency verification remains absent.

## Changes

- `apps/student-web/app.js`
  - Adds `proposalDecisionAttempt` with the original proposal ID, workspace ID, revision and decision for REJECT/STUDENT_TAKEOVER.
  - While that attempt is in flight or unknown, disables new Agent questions and submission entry, rejects a different proposal decision, and permits only retry of the same action. The client continues to reuse the original idempotency key for the same route/body.
  - Clears the attempt only after a success receipt or a definite refusal; an unknown result remains pending.
  - Handles a valid `UNAVAILABLE` Agent Turn as an explicit no-guidance state: it retains the question in the input, adds no assistant response, and shows no success toast.
  - Uses `data.workspace_revision` before the optional envelope revision for ACCEPT, REJECT and TAKEOVER.
- `tests/test_workspace_frontend_html.py`: add source checks for fixed decision context, blocking new questions during unknown outcomes, non-success handling of `UNAVAILABLE`, and DTO revision usage.
- `tests/workspace-client.test.mjs`: add a response-contract case proving `UNAVAILABLE` is represented as such and an Agent/decision DTO revision is usable when envelope revision is omitted.
- Updated `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md`, and the active contract spec. Earlier stage reports retain snapshot notes pointing to this latest evidence.

## Commands and results

- `node --test tests/workspace-client.test.mjs`: **35/35 PASS**.
- `python tests/test_workspace_frontend_html.py`: **16/16 PASS**.
- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **9/9 PASS**.
- `python -m unittest discover -s tests -p test_workspace_api.py -v`: **34/34 PASS** (API source unchanged by this task).
- `python -m unittest discover -s tests -v`: **174 total, 173 passed, 1 skipped; exit 0; 48.696 seconds**. The skip is the Windows symlink-creation permission case (`WinError 1314`); it is not symlink-safety evidence. Temporary copied-runner path diagnostics appeared in isolation tests and affected tests passed.
- `node --check apps/student-web/app.js`: **PASS**.
- `node --check apps/workspace-client.mjs`: **PASS**.
- `python -m json.tool specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/workspace-api-v1.schema.json > $null`: **PASS**.
- `git diff --check`: **PASS for tracked changes**. Direct trailing-whitespace scan of touched source, test and documentation files found no matches.

## Acceptance and limits

| Acceptance | Result |
|---|---|
| Unknown REJECT/TAKEOVER keeps exact decision, proposal, workspace and revision available for same-action retry | PASS by source assertions; Node client separately verifies idempotency replay |
| New Agent questions and submission entry cannot replace an unknown proposal decision | PASS by source assertions |
| `UNAVAILABLE` does not render a guidance reply or success toast and leaves input intact | PASS by source assertions; DTO allowance checked by Node client test |
| All three proposal decisions advance local revision from the required DTO revision, even if envelope revision is absent | PASS by source assertions and Node response-contract test |
| Teacher remediation error handling and DTO shape | PASS by prior source/API/client checks; dynamic stale response timing not exercised |
| Browser-run interaction, layout, visual QA, real HTTP or production authorization | NOT TESTED |

These are static source assertions and mock-fetch response-contract tests, not a browser-run UI state machine. REJECT/TAKEOVER controls retain pending state only in the current page; reload loses the attempt and no persistence guarantee is claimed. The `scripted-demo` API is not a live model; no student code is run. Fixed demo roles are not authentication. The API remains in process memory, and the overall product stays non-production.

## SHA-256 evidence

Hashes are over current file bytes. Recompute with `Get-FileHash -Algorithm SHA256` after any edit.

| File | SHA-256 |
|---|---|
| `apps/student-web/app.js` | `82135C4024A29D4CDEB67D684567F5CF39E27A3150B03B40CCB810313CA96018` |
| `apps/workspace-client.mjs` | `EA0B5AFDA49B3D62954CC65E0118B80CA95E20E0627B0F2EDF5CCF617E4DD02A` |
| `tests/test_workspace_frontend_html.py` | `43EE80F99704D9F9EA885A60EE825F41B87D71281C77628DD054844455022F9F` |
| `tests/workspace-client.test.mjs` | `923DF249F1F6B0B1D22CEA9D65DDBDAAE7F9266332F8280E52F49260EAC8B6BF` |
| `README.md` | `AE5EF21474D5D90C50F879708F5BAD47D51BC63ACDE08C0E253F03D1255FEFD5` |
| `docs/README.md` | `CC5013F1BE3A9B1823E2E2188C39699D70491C803C4F2CD3ACC812712F1409C1` |
| `docs/CURRENT_STATE.md` | `4986D8E85ED54FADE76CBA8EA1051CA9E01CC7ACDEE7240E9AE02B1566E2EC2E` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `073FA59BECA79EA01F02A4E4EF63FF1743E6F2295784224D3681A7A45D64FAE8` |

## Git summary and next step

Extensive pre-existing tracked edits and untracked files were preserved. This task did not stage, commit, push, delete, reset or clean anything. The tracked `git diff --stat` omits most untracked code and tests. Commit: `NONE`.

Continue with a bounded audit of the WSGI vertical flow's revision/idempotency behavior across Agent Turn, proposal decision, submission and teacher review, and check whether the current direct-call test has an observable event/revision gap. Keep it direct-call/static only. Browser/HTTP/P4 remains open; no user decision is needed for that audit.
