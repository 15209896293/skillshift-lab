from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import EducationWorkflow, ScriptedGuidanceAdapter, build_synthetic_template
from agent_first.control_plane_persistence import (
    BudgetLimitReached,
    IdempotencyConflict,
    PersistenceContractError,
    SYNTHETIC_SCOPE,
    SqliteSyntheticControlPlane,
)


def manifest() -> dict:
    workflow = EducationWorkflow(
        teacher_id="teacher-demo",
        student_id="student-demo",
        template=build_synthetic_template(),
        adapter=ScriptedGuidanceAdapter(),
    )
    workflow.create_and_assign(actor_id="teacher-demo")
    workflow.start(actor_id="student-demo")
    workflow.submit(
        actor_id="student-demo",
        responsibility_kind="verification",
        response_text="我比较了任务中的字段与规则，验证这条合成记录的不一致，并写明需要再次确认的材料位置。",
    )
    return workflow.manifest()


class ControlPlanePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name) / "synthetic-control-plane.sqlite3"
        self.ledger = SqliteSyntheticControlPlane(self.path)

    def tearDown(self) -> None:
        self.ledger.close()
        self.temp.cleanup()

    def test_snapshot_is_idempotent_and_replays_after_reopen(self) -> None:
        first = self.ledger.save_manifest(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1", command_id="save-1", manifest=manifest())
        repeated = self.ledger.save_manifest(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1", command_id="save-1", manifest=manifest())
        self.assertEqual(first, repeated)
        self.ledger.close()
        self.ledger = SqliteSyntheticControlPlane(self.path)
        history = self.ledger.history(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1")
        self.assertEqual(1, len(history))
        self.assertEqual("REVIEW_REQUIRED", history[0]["status"])

    def test_command_reuse_with_different_content_is_rejected_without_overwrite(self) -> None:
        first = manifest()
        self.ledger.save_manifest(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1", command_id="save-1", manifest=first)
        changed = json.loads(json.dumps(first))
        changed["status"] = "CLOSED"
        with self.assertRaises(IdempotencyConflict):
            self.ledger.save_manifest(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1", command_id="save-1", manifest=changed)
        self.assertEqual([first], self.ledger.history(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1"))

    def test_non_synthetic_or_credential_like_manifest_is_rejected(self) -> None:
        with self.assertRaises(PersistenceContractError):
            self.ledger.save_manifest(scope="school-1", assignment_id="assignment-1", command_id="save-1", manifest=manifest())
        unsafe = manifest()
        unsafe["api_key"] = "not-a-real-key"
        with self.assertRaises(PersistenceContractError):
            self.ledger.save_manifest(scope=SYNTHETIC_SCOPE, assignment_id="assignment-1", command_id="save-1", manifest=unsafe)

    def test_concurrent_budget_reservations_stop_at_hard_limit_and_are_idempotent(self) -> None:
        def reserve(index: int):
            try:
                return self.ledger.reserve_budget(scope=SYNTHETIC_SCOPE, month="2026-09", command_id=f"reserve-{index}", amount_fen=1000)
            except BudgetLimitReached:
                return None

        with ThreadPoolExecutor(max_workers=12) as pool:
            receipts = list(pool.map(reserve, range(30)))
        accepted = [receipt for receipt in receipts if receipt]
        self.assertEqual(10, len(accepted))
        self.assertEqual(10_000, max(receipt.reserved_total_fen for receipt in accepted))
        duplicate = self.ledger.reserve_budget(scope=SYNTHETIC_SCOPE, month="2026-09", command_id="reserve-0", amount_fen=1000)
        self.assertEqual(1000, duplicate.amount_fen)
        self.assertEqual(1000, duplicate.reserved_total_fen)


if __name__ == "__main__":
    unittest.main()
