from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first import (
    AccessMode,
    ModelGatewayPolicyError,
    ModelProfile,
    ProviderId,
    SchoolMonthlySyntheticBudgetPermit,
    SchoolSyntheticProbePolicy,
    build_deepseek_school_synthetic_profile,
)


def request() -> dict[str, object]:
    return {"model": "deepseek-flash"}


class SchoolBudgetContractTests(unittest.TestCase):
    def test_default_policy_denies_without_reserving_budget(self) -> None:
        permit = SchoolMonthlySyntheticBudgetPermit(SchoolSyntheticProbePolicy(school_scope_id="synthetic-school"))
        allowed = permit.authorize(profile=build_deepseek_school_synthetic_profile(credential_reference="ref/v1"), request=request())
        self.assertFalse(allowed)
        self.assertEqual(0, permit.reserved_fen)

    def test_enabled_policy_reserves_before_call_and_stops_at_hard_limit(self) -> None:
        policy = SchoolSyntheticProbePolicy(
            school_scope_id="synthetic-school",
            reservation_per_request_fen=2_500,
            enabled=True,
        )
        permit = SchoolMonthlySyntheticBudgetPermit(policy)
        profile = build_deepseek_school_synthetic_profile(credential_reference="ref/v1")
        self.assertEqual([True, True, True, True, False], [permit.authorize(profile=profile, request=request()) for _ in range(5)])
        self.assertEqual(10_000, permit.reserved_fen)

    def test_non_deepseek_non_school_or_non_synthetic_profiles_are_denied(self) -> None:
        permit = SchoolMonthlySyntheticBudgetPermit(
            SchoolSyntheticProbePolicy(school_scope_id="synthetic-school", enabled=True)
        )
        base = build_deepseek_school_synthetic_profile(credential_reference="ref/v1")
        wrong_provider = ModelProfile(
            **{**base.__dict__, "provider": ProviderId.QWEN, "model_id": "qwen-test"}
        )
        wrong_access = ModelProfile(
            **{**base.__dict__, "access_mode": AccessMode.TEACHER_BYOK}
        )
        wrong_data = ModelProfile(
            **{**base.__dict__, "data_classification": "real-student-data"}
        )
        self.assertFalse(permit.authorize(profile=wrong_provider, request=request()))
        self.assertFalse(permit.authorize(profile=wrong_access, request=request()))
        self.assertFalse(permit.authorize(profile=wrong_data, request=request()))
        self.assertEqual(0, permit.reserved_fen)

    def test_concurrent_requests_never_reserve_more_than_hard_limit(self) -> None:
        policy = SchoolSyntheticProbePolicy(
            school_scope_id="synthetic-school",
            reservation_per_request_fen=1_000,
            enabled=True,
        )
        permit = SchoolMonthlySyntheticBudgetPermit(policy)
        profile = build_deepseek_school_synthetic_profile(credential_reference="ref/v1")
        results: list[bool] = []
        result_lock = threading.Lock()

        def attempt() -> None:
            allowed = permit.authorize(profile=profile, request=request())
            with result_lock:
                results.append(allowed)

        threads = [threading.Thread(target=attempt) for _ in range(30)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)
        self.assertEqual(10, sum(results))
        self.assertEqual(10_000, permit.reserved_fen)

    def test_policy_cannot_raise_approved_limit(self) -> None:
        with self.assertRaises(ModelGatewayPolicyError):
            SchoolSyntheticProbePolicy(school_scope_id="synthetic-school", monthly_limit_fen=10_001)


if __name__ == "__main__":
    unittest.main()
