"""Local-only synthetic budget lifecycle contract; never a billing system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
from threading import Lock


SYNTHETIC_SCOPE = "synthetic-r0"
MONTHLY_LIMIT_FEN = 10_000
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_STATES = frozenset({"RESERVED", "RELEASED_BEFORE_DISPATCH", "RECONCILIATION_REQUIRED", "SETTLED"})


class SyntheticBudgetLedgerError(ValueError):
    """A visible local-contract failure, not a supplier or payment result."""


class BudgetHardLimitReached(SyntheticBudgetLedgerError):
    pass


class BudgetIdempotencyConflict(SyntheticBudgetLedgerError):
    pass


class BudgetLifecycleConflict(SyntheticBudgetLedgerError):
    pass


@dataclass(frozen=True)
class BudgetLifecycleReceipt:
    month: str
    reservation_id: str
    reserved_fen: int
    state: str
    settled_fen: int | None
    occupied_total_fen: int


class SqliteSyntheticBudgetLedger:
    """Explicit-path SQLite state machine for synthetic tests only.

    Unknown dispatched requests deliberately retain their reservation until a
    future reconciliation process records a bounded synthetic settlement.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        if not self.database_path.parent.is_dir():
            raise SyntheticBudgetLedgerError("database parent directory must already exist")
        self._lock = Lock()
        self._connection = sqlite3.connect(str(self.database_path), check_same_thread=False, isolation_level=None)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def reserve(self, *, scope: str, month: str, reservation_id: str, amount_fen: int) -> BudgetLifecycleReceipt:
        self._require_scope(scope)
        self._require_month(month)
        self._require_identifier(reservation_id, "reservation_id")
        self._require_amount(amount_fen, "reservation amount")
        with self._transaction():
            existing = self._fetch(scope=scope, month=month, reservation_id=reservation_id)
            if existing:
                if int(existing["reserved_fen"]) != amount_fen:
                    raise BudgetIdempotencyConflict("reservation ID cannot be reused with a different amount")
                return self._receipt(existing)
            if self._occupied_total(scope=scope, month=month) + amount_fen > MONTHLY_LIMIT_FEN:
                raise BudgetHardLimitReached("synthetic monthly hard limit would be exceeded")
            self._connection.execute(
                "INSERT INTO synthetic_budget_entries(scope, month, reservation_id, reserved_fen, state, settled_fen) VALUES (?, ?, ?, ?, 'RESERVED', NULL)",
                (scope, month, reservation_id, amount_fen),
            )
            return self._receipt(self._fetch(scope=scope, month=month, reservation_id=reservation_id))

    def mark_dispatch_attempted(self, *, scope: str, month: str, reservation_id: str) -> BudgetLifecycleReceipt:
        """Marks an attempted provider dispatch; it never assumes the request was free."""
        entry = self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
        with self._transaction():
            entry = self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
            if entry["state"] == "RECONCILIATION_REQUIRED":
                return self._receipt(entry)
            if entry["state"] != "RESERVED":
                raise BudgetLifecycleConflict("only an undispatched reservation can be marked dispatched")
            self._connection.execute(
                "UPDATE synthetic_budget_entries SET state = 'RECONCILIATION_REQUIRED' WHERE scope = ? AND month = ? AND reservation_id = ?",
                (scope, month, reservation_id),
            )
            return self._receipt(self._fetch(scope=scope, month=month, reservation_id=reservation_id))

    def release_before_dispatch(self, *, scope: str, month: str, reservation_id: str) -> BudgetLifecycleReceipt:
        """Only a proven-not-dispatched synthetic reservation may be released."""
        self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
        with self._transaction():
            entry = self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
            if entry["state"] == "RELEASED_BEFORE_DISPATCH":
                return self._receipt(entry)
            if entry["state"] != "RESERVED":
                raise BudgetLifecycleConflict("only an undispatched reservation can be released")
            self._connection.execute(
                "UPDATE synthetic_budget_entries SET state = 'RELEASED_BEFORE_DISPATCH' WHERE scope = ? AND month = ? AND reservation_id = ?",
                (scope, month, reservation_id),
            )
            return self._receipt(self._fetch(scope=scope, month=month, reservation_id=reservation_id))

    def settle_after_reconciliation(
        self, *, scope: str, month: str, reservation_id: str, settled_fen: int
    ) -> BudgetLifecycleReceipt:
        """Records a bounded synthetic settlement; no supplier bill is read or inferred."""
        self._require_amount(settled_fen, "settlement amount", allow_zero=True)
        self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
        with self._transaction():
            entry = self._require_entry(scope=scope, month=month, reservation_id=reservation_id)
            if entry["state"] == "SETTLED":
                if int(entry["settled_fen"]) != settled_fen:
                    raise BudgetIdempotencyConflict("settlement cannot be changed after it is recorded")
                return self._receipt(entry)
            if entry["state"] != "RECONCILIATION_REQUIRED":
                raise BudgetLifecycleConflict("only a dispatched reservation can be settled")
            if settled_fen > int(entry["reserved_fen"]):
                raise SyntheticBudgetLedgerError("synthetic settlement cannot exceed the conservative reservation")
            self._connection.execute(
                "UPDATE synthetic_budget_entries SET state = 'SETTLED', settled_fen = ? WHERE scope = ? AND month = ? AND reservation_id = ?",
                (settled_fen, scope, month, reservation_id),
            )
            return self._receipt(self._fetch(scope=scope, month=month, reservation_id=reservation_id))

    def get(self, *, scope: str, month: str, reservation_id: str) -> BudgetLifecycleReceipt:
        return self._receipt(self._require_entry(scope=scope, month=month, reservation_id=reservation_id))

    def _create_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_budget_entries (
                scope TEXT NOT NULL,
                month TEXT NOT NULL,
                reservation_id TEXT NOT NULL,
                reserved_fen INTEGER NOT NULL CHECK(reserved_fen > 0),
                state TEXT NOT NULL CHECK(state IN ('RESERVED', 'RELEASED_BEFORE_DISPATCH', 'RECONCILIATION_REQUIRED', 'SETTLED')),
                settled_fen INTEGER NULL CHECK(settled_fen IS NULL OR settled_fen >= 0),
                PRIMARY KEY (scope, month, reservation_id)
            )
            """
        )

    def _require_entry(self, *, scope: str, month: str, reservation_id: str) -> sqlite3.Row:
        self._require_scope(scope)
        self._require_month(month)
        self._require_identifier(reservation_id, "reservation_id")
        entry = self._fetch(scope=scope, month=month, reservation_id=reservation_id)
        if not entry:
            raise SyntheticBudgetLedgerError("synthetic reservation was not found")
        return entry

    def _fetch(self, *, scope: str, month: str, reservation_id: str) -> sqlite3.Row | None:
        self._connection.row_factory = sqlite3.Row
        return self._connection.execute(
            "SELECT scope, month, reservation_id, reserved_fen, state, settled_fen FROM synthetic_budget_entries WHERE scope = ? AND month = ? AND reservation_id = ?",
            (scope, month, reservation_id),
        ).fetchone()

    def _receipt(self, entry: sqlite3.Row | None) -> BudgetLifecycleReceipt:
        if not entry:
            raise SyntheticBudgetLedgerError("synthetic reservation was not found")
        return BudgetLifecycleReceipt(
            month=str(entry["month"]),
            reservation_id=str(entry["reservation_id"]),
            reserved_fen=int(entry["reserved_fen"]),
            state=str(entry["state"]),
            settled_fen=None if entry["settled_fen"] is None else int(entry["settled_fen"]),
            occupied_total_fen=self._occupied_total(scope=str(entry["scope"]), month=str(entry["month"])),
        )

    def _occupied_total(self, *, scope: str, month: str) -> int:
        return int(
            self._connection.execute(
                """
                SELECT COALESCE(SUM(
                    CASE state
                        WHEN 'RELEASED_BEFORE_DISPATCH' THEN 0
                        WHEN 'SETTLED' THEN settled_fen
                        ELSE reserved_fen
                    END
                ), 0)
                FROM synthetic_budget_entries
                WHERE scope = ? AND month = ?
                """,
                (scope, month),
            ).fetchone()[0]
        )

    def _transaction(self):
        class Transaction:
            def __init__(self, owner: SqliteSyntheticBudgetLedger) -> None:
                self.owner = owner

            def __enter__(self):
                self.owner._lock.acquire()
                self.owner._connection.execute("BEGIN IMMEDIATE")
                return self

            def __exit__(self, exception_type, exception, traceback) -> None:
                self.owner._connection.execute("ROLLBACK" if exception_type else "COMMIT")
                self.owner._lock.release()

        return Transaction(self)

    @staticmethod
    def _require_scope(scope: str) -> None:
        if scope != SYNTHETIC_SCOPE:
            raise SyntheticBudgetLedgerError("only the fixed synthetic scope is accepted")

    @staticmethod
    def _require_month(month: str) -> None:
        if not isinstance(month, str) or not _MONTH.fullmatch(month):
            raise SyntheticBudgetLedgerError("month must use YYYY-MM")

    @staticmethod
    def _require_identifier(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise SyntheticBudgetLedgerError(f"{label} must be a bounded non-empty opaque identifier")

    @staticmethod
    def _require_amount(value: int, label: str, *, allow_zero: bool = False) -> None:
        lower_bound = 0 if allow_zero else 1
        if not isinstance(value, int) or not lower_bound <= value <= MONTHLY_LIMIT_FEN:
            raise SyntheticBudgetLedgerError(f"{label} is outside the approved synthetic limit")
