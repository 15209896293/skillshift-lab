"""Generate a self-scanned Artifact for the local synthetic budget lifecycle."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from agent_first.secret_scan import SinkKind, require_clean, scan
from agent_first.synthetic_budget_ledger import SYNTHETIC_SCOPE, SqliteSyntheticBudgetLedger


OUTPUT = ROOT / "artifacts" / "R0-SYNTHETIC-BUDGET-LIFECYCLE" / "evidence.json"


def main() -> None:
    with TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "evidence.sqlite3"
        ledger = SqliteSyntheticBudgetLedger(database_path)
        reserved = ledger.reserve(
            scope=SYNTHETIC_SCOPE, month="2026-09", reservation_id="evidence-reserve-1", amount_fen=1_000
        )
        pending = ledger.mark_dispatch_attempted(
            scope=SYNTHETIC_SCOPE, month="2026-09", reservation_id="evidence-reserve-1"
        )
        settled = ledger.settle_after_reconciliation(
            scope=SYNTHETIC_SCOPE, month="2026-09", reservation_id="evidence-reserve-1", settled_fen=400
        )
        released = ledger.reserve(
            scope=SYNTHETIC_SCOPE, month="2026-09", reservation_id="evidence-reserve-2", amount_fen=600
        )
        released = ledger.release_before_dispatch(
            scope=SYNTHETIC_SCOPE, month="2026-09", reservation_id="evidence-reserve-2"
        )
        ledger.close()

    evidence = {
        "schema_version": "synthetic-budget-lifecycle-evidence/v1",
        "task_id": "R0-SYNTHETIC-BUDGET-LIFECYCLE-001",
        "scope": "local-synthetic-only",
        "monthly_limit_fen": 10_000,
        "state_machine": ["RESERVED", "RELEASED_BEFORE_DISPATCH", "RECONCILIATION_REQUIRED", "SETTLED"],
        "rules": {
            "unknown_dispatch_keeps_reservation": True,
            "release_requires_undispatched_state": True,
            "settlement_is_bounded_by_reservation": True,
            "real_provider_or_billing_data_used": False,
        },
        "synthetic_flow": {
            "reserved": {"state": reserved.state, "occupied_total_fen": reserved.occupied_total_fen},
            "pending": {"state": pending.state, "occupied_total_fen": pending.occupied_total_fen},
            "settled": {"state": settled.state, "settled_fen": settled.settled_fen, "occupied_total_fen": settled.occupied_total_fen},
            "released": {"state": released.state, "occupied_total_fen": released.occupied_total_fen},
        },
    }
    findings = scan(evidence, sink=SinkKind.ARTIFACT)
    evidence["self_scan"] = {"result": "clean" if not findings else "refused", "finding_count": len(findings)}
    text = json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    require_clean(text, sink=SinkKind.ARTIFACT)
    print(f"artifact={OUTPUT}")
    print("artifact_self_scan=clean")


if __name__ == "__main__":
    main()
