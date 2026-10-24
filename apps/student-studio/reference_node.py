"""Local-only reference Node for the R0 Foundation Spike.

It creates append-only events and a local submission manifest.  Network sync,
authentication, model calls, and a desktop UI are intentionally absent.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from typing import Any

from local_restricted_process import ExecutionResult, LocalRestrictedProcessProvider


EVENT_SCHEMA_VERSION = "r0-foundation-spike/v1"


@dataclass(frozen=True)
class Event:
    sequence: int
    event_type: str
    occurred_at: float
    payload: dict[str, Any]


class ReferenceNode:
    """A deterministic, local-only Node implementation used by tests."""

    def __init__(self, provider: LocalRestrictedProcessProvider, *, node_version: str = "0.1.0-spike") -> None:
        self.provider = provider
        self.node_version = node_version
        self.events: list[Event] = []

    def bind_workspace(self, workspace_id: str) -> Path:
        workspace = self.provider.bind_workspace(workspace_id)
        self._append("workspace.bound", {"workspace_id": workspace_id})
        return workspace

    def run_python_validation(self, workspace: Path, script: str, *, timeout_seconds: float) -> ExecutionResult:
        self._append("agent.run_created", {"workspace": workspace.name, "script": script})
        self._append("agent.tool_called", {"tool": "run_command", "script": script})
        run_id = self.provider.start_python_script(workspace, script)
        result = self.provider.wait_for_run(run_id, timeout_seconds=timeout_seconds)
        self._append(
            "runtime.command_finished",
            {
                "run_id": run_id,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "stopped": result.stopped,
                "stop_confirmed": result.stop_confirmed,
            },
        )
        return result

    def create_submission_manifest(
        self,
        *,
        artifact: Path,
        task_version: str,
        validator_version: str,
        human_validation_note: str,
        execution: ExecutionResult,
        output_directory: Path,
    ) -> Path:
        digest = sha256(artifact.read_bytes()).hexdigest()
        manifest = {
            "schema_version": EVENT_SCHEMA_VERSION,
            "task_version": task_version,
            "validator_version": validator_version,
            "node_version": self.node_version,
            "python_version": sys.version,
            "artifact": {"relative_path": artifact.name, "sha256": digest, "size": artifact.stat().st_size},
            "execution": asdict(execution),
            "event_references": [event.sequence for event in self.events],
            "human_validation_note": human_validation_note,
            "sync_status": "NOT_IMPLEMENTED",
        }
        output_directory.mkdir(parents=True, exist_ok=True)
        path = output_directory / "submission-manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self._append("submission.package_created", {"manifest": path.name, "artifact_sha256": digest})
        return path

    def event_export(self) -> list[dict[str, Any]]:
        return [asdict(event) | {"schema_version": EVENT_SCHEMA_VERSION} for event in self.events]

    def _append(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append(
            Event(
                sequence=len(self.events) + 1,
                event_type=event_type,
                occurred_at=time.time(),
                payload=payload,
            )
        )
