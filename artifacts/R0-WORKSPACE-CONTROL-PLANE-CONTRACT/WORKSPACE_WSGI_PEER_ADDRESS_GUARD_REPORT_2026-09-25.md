# WSGI Peer Address Guard Report

- Task ID: `R0-WORKSPACE-WSGI-PEER-ADDRESS-GUARDS-001`
- Current Gate: P3 local synthetic WSGI adapter boundary
- Result: **PASS for direct-call peer-address behavior; deployment and reverse-proxy safety remain unverified**
- Commit: `NONE`

## Read-only audit

The WSGI adapter checks `REMOTE_ADDR` with `ipaddress.ip_address(...).is_loopback` and does not read `HTTP_X_FORWARDED_FOR`. The active contract states that the adapter's code does not guarantee deployment or reverse-proxy configuration. A narrow test was added to preserve that boundary without launching a listener.

## Change

- `tests/test_workspace_wsgi.py`: add a direct callable test that accepts IPv6 loopback `::1`, rejects documentation-range IPv6 `2001:db8::1`, and rejects non-loopback IPv4 `192.0.2.5` even when a forged `X-Forwarded-For: ::1` header is present. The test comment says this is not evidence for proxy configuration, network binding or deployment security.
- Updated `README.md`, `docs/README.md`, `docs/CURRENT_STATE.md` and the active contract spec with the current test counts and boundary.
- Added this Artifact.

## Commands and results

- `python -m unittest discover -s tests -p test_workspace_wsgi.py -v`: **10/10 PASS**.
- `python -m unittest discover -s tests -v`: **176 total, 175 passed, 1 skipped; exit 0; 48.298 seconds**. The skipped test is the Windows symlink-creation permission case; it is not symlink-safety evidence. Existing copied-runner diagnostics appeared during passing Windows isolation probes and do not establish OS isolation.
- Final `git diff --check`: **PASS**.
- Touched-file trailing-whitespace scan: **PASS**.

## Acceptance and limits

| Criterion | Result |
|---|---|
| IPv6 loopback is accepted by the direct WSGI callable | PASS |
| IPv6 non-loopback is rejected | PASS |
| A forwarded loopback value cannot override a non-loopback `REMOTE_ADDR` | PASS |
| Actual network binding, browser, HTTP listener, reverse-proxy chain or deploy configuration | NOT TESTED |

This is a direct WSGI callable check for the local synthetic adapter only. `/demo/teacher` and `/demo/student` remain fixed demonstration routes, not authentication. The API remains process-memory-only and non-production; code execution stays disabled. P4 browser/visual QA and production security gates remain open.

## SHA-256 evidence

Hashes cover current file bytes; recompute with `Get-FileHash -Algorithm SHA256` after edits.

| File | SHA-256 |
|---|---|
| `tests/test_workspace_wsgi.py` | `6BFFF5222B034D00D764C6D83134D0050187A3EC0182ADEFEE0B53CA3170BA99` |
| `README.md` | `8E64B52D1DF8282670020F69050BA2B27A1A3C891E7524A265BA591CD61E224C` |
| `docs/README.md` | `E14269FFD72F51731D7A2D029320654D50B159E038E51B7F7BBE5974B20CDFD8` |
| `docs/CURRENT_STATE.md` | `20DDAF1D8CEF9981417ECF1A2F5AE237383F8296018FAB76646E44CB19AA52C6` |
| `specs/R0-WORKSPACE-CONTROL-PLANE-CONTRACT/README.md` | `B9DC9714432B516D80A3FF282D84C0331CCA0E316EF2393112FF59B3DEC6B172` |

## Git summary and follow-up

- Existing tracked edits and untracked files were preserved; no staging, commit, push, deployment, deletion, reset or cleanup.
- Tracked `git diff --stat` is cumulative and omits untracked implementation and artifacts; inspect `git status --short` for the full state.
- Continue within synthetic P3 with bounded DTO/error-state review. HTTP/browser visual QA remains open because this task did not establish an authorized preview path.
- Commit: `NONE`.
