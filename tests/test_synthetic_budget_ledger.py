from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "agent-first"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from agent_first.synthetic_budget_ledger import (  # noqa: E402
    BudgetHardLimitReached,
    BudgetIdempotencyConflict,
    BudgetLifecycleConflict,
    MONTHLY_LIMIT_FEN,
    SYNTHETIC_SCOPE,
    SqliteSyntheticBudgetLedger,
    SyntheticBudgetLedgerError,
)


MONTH = "2026-09"


class SyntheticBudgetLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "synthetic-budget-ledger.sqlite3"
        self.ledger = SqliteSyntheticBudgetLedger(self.path)

    def tearDown(self) -> None:
        self.ledger.close()
        self.temp.cleanup()

    def reserve(self, reservation_id: str = "reserve-1", amount_fen: int = 1_000):
        return self.ledger.reserve(
            scope=SYNTHETIC_SCOPE,
            month=MONTH,
            reservation_id=reservation_id,
            amount_fen=amount_fen,
        )

    def test_reservation_is_idempotent_but_conflicting_amount_is_rejected(self) -> None:
        first = self.reserve()
        duplicate = self.reserve()
        self.assertEqual(first, duplicate)
        self.assertEqual("RESERVED", first.state)
        self.assertEqual(1_000, first.occupied_total_fen)
        with self.assertRaises(BudgetIdempotencyConflict):
            self.reserve(amount_fen=999)

    def test_pre_dispatch_release_frees_only_that_reservation(self) -> None:
        self.reserve(amount_fen=1_000)
        released = self.ledger.release_before_dispatch(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.assertEqual("RELEASED_BEFORE_DISPATCH", released.state)
        self.assertEqual(0, released.occupied_total_fen)
        repeat = self.ledger.release_before_dispatch(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.assertEqual(released, repeat)
        accepted = self.reserve("reserve-2", MONTHLY_LIMIT_FEN)
        self.assertEqual(MONTHLY_LIMIT_FEN, accepted.occupied_total_fen)

    def test_dispatch_unknown_must_hold_reservation_and_cannot_release(self) -> None:
        self.reserve(amount_fen=1_000)
        pending = self.ledger.mark_dispatch_attempted(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.assertEqual("RECONCILIATION_REQUIRED", pending.state)
        self.assertEqual(1_000, pending.occupied_total_fen)
        with self.assertRaises(BudgetLifecycleConflict):
            self.ledger.release_before_dispatch(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.assertEqual(1_000, self.ledger.get(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1").occupied_total_fen)

    def test_settlement_requires_dispatch_and_never_exceeds_reservation(self) -> None:
        self.reserve(amount_fen=1_000)
        with self.assertRaises(BudgetLifecycleConflict):
            self.ledger.settle_after_reconciliation(
                scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1", settled_fen=400
            )
        self.ledger.mark_dispatch_attempted(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        with self.assertRaises(SyntheticBudgetLedgerError):
            self.ledger.settle_after_reconciliation(
                scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1", settled_fen=1_001
            )
        settled = self.ledger.settle_after_reconciliation(
            scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1", settled_fen=400
        )
        self.assertEqual("SETTLED", settled.state)
        self.assertEqual(400, settled.occupied_total_fen)
        self.assertEqual(settled, self.ledger.settle_after_reconciliation(
            scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1", settled_fen=400
        ))
        with self.assertRaises(BudgetIdempotencyConflict):
            self.ledger.settle_after_reconciliation(
                scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1", settled_fen=399
            )

    def test_reopen_preserves_pending_reservation_and_hard_limit(self) -> None:
        self.reserve(amount_fen=6_000)
        self.ledger.mark_dispatch_attempted(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.ledger.close()
        self.ledger = SqliteSyntheticBudgetLedger(self.path)
        restored = self.ledger.get(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="reserve-1")
        self.assertEqual("RECONCILIATION_REQUIRED", restored.state)
        self.assertEqual(6_000, restored.occupied_total_fen)
        with self.assertRaises(BudgetHardLimitReached):
            self.reserve("reserve-2", 4_001)
        self.assertEqual(10_000, self.reserve("reserve-2", 4_000).occupied_total_fen)

    def test_fixed_synthetic_scope_and_explicit_parent_are_required(self) -> None:
        with self.assertRaises(SyntheticBudgetLedgerError):
            self.ledger.reserve(scope="school-real", month=MONTH, reservation_id="reserve-1", amount_fen=1)
        with self.assertRaises(SyntheticBudgetLedgerError):
            SqliteSyntheticBudgetLedger(Path(self.temp.name) / "missing" / "no-default.sqlite3")

    def test_two_bounded_child_processes_do_not_exceed_hard_limit(self) -> None:
        self.ledger.close()
        bootstrap = SqliteSyntheticBudgetLedger(self.path)
        bootstrap.close()
        child = (
            "import sys; from pathlib import Path; "
            f"sys.path.insert(0, {str(APP_ROOT)!r}); "
            "from agent_first.synthetic_budget_ledger import SqliteSyntheticBudgetLedger, SYNTHETIC_SCOPE, BudgetHardLimitReached; "
            "ledger=SqliteSyntheticBudgetLedger(Path(sys.argv[1])); "
            "\ntry:\n ledger.reserve(scope=SYNTHETIC_SCOPE, month='2026-09', reservation_id=sys.argv[2], amount_fen=6000); print('ACCEPT')\n"
            "except BudgetHardLimitReached:\n print('LIMIT')\n"
            "finally:\n ledger.close()\n"
        )

        def run_child(index: int) -> str:
            completed = subprocess.run(
                [sys.executable, "-c", child, str(self.path), f"child-{index}"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            return completed.stdout.strip()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(run_child, range(2)))
        self.assertEqual(["ACCEPT", "LIMIT"], sorted(outcomes))
        self.ledger = SqliteSyntheticBudgetLedger(self.path)
        self.assertEqual(6_000, self.ledger.get(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="child-0").occupied_total_fen
                         if outcomes[0] == "ACCEPT"
                         else self.ledger.get(scope=SYNTHETIC_SCOPE, month=MONTH, reservation_id="child-1").occupied_total_fen)


if __name__ == "__main__":
    unittest.main()
