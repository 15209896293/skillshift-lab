"""Local-only budget permit contract for the first school-managed synthetic probe.

The counter reserves a conservative configured amount before a provider call.
It is an in-memory test seam, not an accounting, identity, or billing system.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Mapping

from .model_gateway import AccessMode, ModelGatewayPolicyError, ModelProfile, ProviderId


MONTHLY_SYNTHETIC_LIMIT_FEN = 10_000  # 100 CNY; one CNY equals 100 fen.


@dataclass(frozen=True)
class SchoolSyntheticProbePolicy:
    """Future school-admin configuration without any credential or personal identity."""

    school_scope_id: str
    monthly_limit_fen: int = MONTHLY_SYNTHETIC_LIMIT_FEN
    reservation_per_request_fen: int = 100
    enabled: bool = False

    def __post_init__(self) -> None:
        if not self.school_scope_id.strip():
            raise ModelGatewayPolicyError("school_scope_id must be a non-empty server-owned scope")
        if self.monthly_limit_fen != MONTHLY_SYNTHETIC_LIMIT_FEN:
            raise ModelGatewayPolicyError("the first probe is fixed to the approved 100 CNY monthly limit")
        if not 1 <= self.reservation_per_request_fen <= self.monthly_limit_fen:
            raise ModelGatewayPolicyError("reservation_per_request_fen must fit within the approved monthly limit")


class SchoolMonthlySyntheticBudgetPermit:
    """Thread-safe, fail-closed in-memory permit for a single synthetic school scope."""

    def __init__(self, policy: SchoolSyntheticProbePolicy) -> None:
        self.policy = policy
        self._reserved_fen = 0
        self._lock = Lock()

    @property
    def reserved_fen(self) -> int:
        with self._lock:
            return self._reserved_fen

    def authorize(self, *, profile: ModelProfile, request: Mapping[str, object]) -> bool:
        if not self.policy.enabled:
            return False
        if profile.provider is not ProviderId.DEEPSEEK:
            return False
        if profile.access_mode is not AccessMode.SCHOOL_MANAGED:
            return False
        if profile.data_classification != "synthetic-task-only":
            return False
        if request.get("model") != "deepseek-flash":
            return False
        with self._lock:
            next_reservation = self._reserved_fen + self.policy.reservation_per_request_fen
            if next_reservation > self.policy.monthly_limit_fen:
                return False
            self._reserved_fen = next_reservation
            return True
