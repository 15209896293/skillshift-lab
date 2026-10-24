"""Foundation Spike reference provider for a bound local Python Workspace.

This is deliberately not a production sandbox.  It demonstrates the contract
boundaries that must be tested before broader R0 work is authorized.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
import time
from typing import Mapping
from uuid import uuid4


class WorkspaceViolation(ValueError):
    """A caller tried to cross the Workspace boundary."""


class CommandPolicyViolation(ValueError):
    """A caller requested a command outside the Spike allowlist."""


@dataclass(frozen=True)
class ExecutionResult:
    run_id: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    stopped: bool
    stop_confirmed: bool
    started_at: float
    ended_at: float


class LocalRestrictedProcessProvider:
    """Run a frozen Python script inside an explicitly bound workspace.

    The Spike only permits the current Python executable plus a script located
    in the workspace.  It does not offer a general shell, dependency install,
    network access policy, or a claim of malicious-code isolation.
    """

    def __init__(self, root: Path, *, output_limit: int = 16_384) -> None:
        raw_root = Path(root)
        if raw_root.is_symlink():
            raise WorkspaceViolation("workspace root must not be a symbolic link")
        raw_root.mkdir(parents=True, exist_ok=True)
        if raw_root.is_symlink():
            raise WorkspaceViolation("workspace root must not be a symbolic link")
        self.root = raw_root.resolve()
        self.output_limit = output_limit
        self._active: dict[str, subprocess.Popen[str]] = {}

    def bind_workspace(self, workspace_id: str) -> Path:
        if not workspace_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in workspace_id):
            raise WorkspaceViolation("workspace id must be alphanumeric, hyphen, or underscore")
        raw_workspace = self.root / workspace_id
        raw_workspace.mkdir(parents=True, exist_ok=True)
        if raw_workspace.is_symlink():
            raise WorkspaceViolation("workspace must not be a symbolic link")
        workspace = self._inside_root(raw_workspace)
        if raw_workspace.is_symlink():
            raise WorkspaceViolation("workspace must not be a symbolic link")
        return workspace

    def resolve_path(self, workspace: Path, relative_path: str) -> Path:
        if not relative_path or Path(relative_path).is_absolute():
            raise WorkspaceViolation("only non-empty relative paths are allowed")
        raw_workspace = Path(workspace)
        if raw_workspace.is_symlink():
            raise WorkspaceViolation("workspace must not be a symbolic link")
        resolved_workspace = self._inside_root(raw_workspace)
        raw_candidate = resolved_workspace / relative_path
        self._reject_symlink_ancestor(resolved_workspace, raw_candidate)
        candidate = self._inside(resolved_workspace, raw_candidate)
        return candidate

    def start_python_script(self, workspace: Path, relative_script: str) -> str:
        script = self.resolve_path(workspace, relative_script)
        if script.suffix != ".py" or not script.is_file():
            raise CommandPolicyViolation("only an existing .py script in the workspace may run")
        run_id = str(uuid4())
        process = subprocess.Popen(
            [sys.executable, "-I", str(script)],
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._minimal_environment(),
        )
        self._active[run_id] = process
        return run_id

    def wait_for_run(self, run_id: str, *, timeout_seconds: float) -> ExecutionResult:
        process = self._active.get(run_id)
        if process is None:
            raise KeyError(f"unknown run: {run_id}")
        started_at = time.time()
        timed_out = False
        stopped = False
        stop_confirmed = True
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            stopped = True
            stop_confirmed = self.stop_run(run_id)
            stdout, stderr = process.communicate()
        finally:
            self._active.pop(run_id, None)
        ended_at = time.time()
        return ExecutionResult(
            run_id=run_id,
            exit_code=process.returncode,
            stdout=self._truncate(stdout),
            stderr=self._truncate(stderr),
            timed_out=timed_out,
            stopped=stopped,
            stop_confirmed=stop_confirmed,
            started_at=started_at,
            ended_at=ended_at,
        )

    def stop_run(self, run_id: str) -> bool:
        process = self._active.get(run_id)
        if process is None:
            return False
        if process.poll() is None:
            process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return False
        return process.poll() is not None

    def _inside_root(self, path: Path) -> Path:
        return self._inside(self.root, path)

    @staticmethod
    def _inside(parent: Path, path: Path) -> Path:
        resolved_parent = parent.resolve()
        resolved_path = path.resolve(strict=False)
        try:
            resolved_path.relative_to(resolved_parent)
        except ValueError as error:
            raise WorkspaceViolation("path escapes its allowed workspace") from error
        return resolved_path

    @staticmethod
    def _reject_symlink_ancestor(workspace: Path, candidate: Path) -> None:
        current = candidate
        while current != workspace:
            if current.is_symlink():
                raise WorkspaceViolation("symbolic links are not allowed in a workspace path")
            current = current.parent

    def _truncate(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return value[: self.output_limit] + "\n[output truncated by provider]"

    @staticmethod
    def _minimal_environment() -> Mapping[str, str]:
        environment: dict[str, str] = {"PYTHONIOENCODING": "utf-8"}
        for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATH"):
            value = os.environ.get(key)
            if value:
                environment[key] = value
        return environment
