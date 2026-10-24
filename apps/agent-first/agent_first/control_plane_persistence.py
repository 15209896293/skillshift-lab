"""Synthetic-only SQLite persistence contracts for the future R0 control plane."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from threading import Lock
from typing import Any


SYNTHETIC_SCOPE = "synthetic-r0"
MONTHLY_LIMIT_FEN = 10_000
MAX_MANIFEST_BYTES = 65_536
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_FORBIDDEN_FIELD_PARTS = ("secret", "password", "accesskey", "credential", "api_key")


class PersistenceContractError(ValueError):
    """A safe, visible contract failure; never an authorization claim."""


class IdempotencyConflict(PersistenceContractError):
    pass


class BudgetLimitReached(PersistenceContractError):
    pass


@dataclass(frozen=True)
class SnapshotReceipt:
    assignment_id: str
    command_id: str
    revision: int
    content_hash: str


@dataclass(frozen=True)
class BudgetReceipt:
    month: str
    command_id: str
    amount_fen: int
    reserved_total_fen: int


class SqliteSyntheticControlPlane:
    """Explicit-path, local-only storage for synthetic tests; not a production DB."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self._lock = Lock()
        self._connection = sqlite3.connect(str(self.database_path), check_same_thread=False, isolation_level=None)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA busy_timeout = 1000")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def save_manifest(self, *, scope: str, assignment_id: str, command_id: str, manifest: dict[str, Any]) -> SnapshotReceipt:
        self._require_scope(scope)
        self._require_id(assignment_id, "assignment_id")
        self._require_id(command_id, "command_id")
        encoded = self._manifest_bytes(manifest)
        content_hash = sha256(encoded).hexdigest()
        with self._transaction():
            existing = self._connection.execute(
                "SELECT content_hash, revision FROM commands WHERE scope = ? AND assignment_id = ? AND command_id = ?",
                (scope, assignment_id, command_id),
            ).fetchone()
            if existing:
                if existing[0] != content_hash:
                    raise IdempotencyConflict("a command ID cannot be reused with different manifest content")
                return SnapshotReceipt(assignment_id, command_id, int(existing[1]), content_hash)
            revision = int(
                self._connection.execute(
                    "SELECT COALESCE(MAX(revision), 0) + 1 FROM snapshots WHERE scope = ? AND assignment_id = ?",
                    (scope, assignment_id),
                ).fetchone()[0]
            )
            self._connection.execute(
                "INSERT INTO snapshots(scope, assignment_id, revision, manifest_json, content_hash) VALUES (?, ?, ?, ?, ?)",
                (scope, assignment_id, revision, encoded.decode("utf-8"), content_hash),
            )
            self._connection.execute(
                "INSERT INTO commands(scope, assignment_id, command_id, content_hash, revision) VALUES (?, ?, ?, ?, ?)",
                (scope, assignment_id, command_id, content_hash, revision),
            )
            return SnapshotReceipt(assignment_id, command_id, revision, content_hash)

    def history(self, *, scope: str, assignment_id: str) -> list[dict[str, Any]]:
        self._require_scope(scope)
        self._require_id(assignment_id, "assignment_id")
        rows = self._connection.execute(
            "SELECT manifest_json FROM snapshots WHERE scope = ? AND assignment_id = ? ORDER BY revision",
            (scope, assignment_id),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def reserve_budget(self, *, scope: str, month: str, command_id: str, amount_fen: int) -> BudgetReceipt:
        self._require_scope(scope)
        self._require_id(command_id, "command_id")
        if not _MONTH.fullmatch(month):
            raise PersistenceContractError("month must use YYYY-MM")
        if not isinstance(amount_fen, int) or not 0 < amount_fen <= MONTHLY_LIMIT_FEN:
            raise PersistenceContractError("reservation amount is outside the approved synthetic limit")
        with self._transaction():
            existing = self._connection.execute(
                "SELECT amount_fen, reserved_total_fen FROM budget_reservations WHERE scope = ? AND month = ? AND command_id = ?",
                (scope, month, command_id),
            ).fetchone()
            if existing:
                if int(existing[0]) != amount_fen:
                    raise IdempotencyConflict("a budget command ID cannot be reused with a different amount")
                return BudgetReceipt(month, command_id, amount_fen, int(existing[1]))
            current = int(
                self._connection.execute(
                    "SELECT COALESCE(SUM(amount_fen), 0) FROM budget_reservations WHERE scope = ? AND month = ?",
                    (scope, month),
                ).fetchone()[0]
            )
            total = current + amount_fen
            if total > MONTHLY_LIMIT_FEN:
                raise BudgetLimitReached("synthetic monthly budget hard limit would be exceeded")
            self._connection.execute(
                "INSERT INTO budget_reservations(scope, month, command_id, amount_fen, reserved_total_fen) VALUES (?, ?, ?, ?, ?)",
                (scope, month, command_id, amount_fen, total),
            )
            return BudgetReceipt(month, command_id, amount_fen, total)

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS snapshots (
                scope TEXT NOT NULL, assignment_id TEXT NOT NULL, revision INTEGER NOT NULL,
                manifest_json TEXT NOT NULL, content_hash TEXT NOT NULL,
                PRIMARY KEY (scope, assignment_id, revision)
            );
            CREATE TABLE IF NOT EXISTS commands (
                scope TEXT NOT NULL, assignment_id TEXT NOT NULL, command_id TEXT NOT NULL,
                content_hash TEXT NOT NULL, revision INTEGER NOT NULL,
                PRIMARY KEY (scope, assignment_id, command_id)
            );
            CREATE TABLE IF NOT EXISTS budget_reservations (
                scope TEXT NOT NULL, month TEXT NOT NULL, command_id TEXT NOT NULL,
                amount_fen INTEGER NOT NULL, reserved_total_fen INTEGER NOT NULL,
                PRIMARY KEY (scope, month, command_id)
            );
            """
        )

    def _transaction(self):
        class Transaction:
            def __init__(self, owner: SqliteSyntheticControlPlane) -> None:
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
            raise PersistenceContractError("only the fixed synthetic scope is accepted")

    @staticmethod
    def _require_id(value: str, label: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise PersistenceContractError(f"{label} must be a bounded non-empty opaque identifier")

    @staticmethod
    def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
        if not isinstance(manifest, dict) or manifest.get("schema_version") != "agent-first-submission/v1":
            raise PersistenceContractError("only a versioned synthetic submission manifest is accepted")
        task = manifest.get("task")
        if not isinstance(task, dict) or not str(task.get("id", "")).startswith("synthetic-"):
            raise PersistenceContractError("manifest task must be the frozen synthetic task")
        SqliteSyntheticControlPlane._reject_sensitive_fields(manifest)
        encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_MANIFEST_BYTES:
            raise PersistenceContractError("manifest exceeds the synthetic contract size limit")
        return encoded

    @staticmethod
    def _reject_sensitive_fields(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(part in normalized for part in _FORBIDDEN_FIELD_PARTS):
                    raise PersistenceContractError("manifest cannot contain credential-like fields")
                SqliteSyntheticControlPlane._reject_sensitive_fields(nested)
        elif isinstance(value, list):
            for nested in value:
                SqliteSyntheticControlPlane._reject_sensitive_fields(nested)
