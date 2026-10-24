from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "execution" / "providers"))
sys.path.insert(0, str(ROOT / "apps" / "student-studio"))

from local_restricted_process import LocalRestrictedProcessProvider, WorkspaceViolation
from reference_node import ReferenceNode


class FoundationSpikeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "allowed-root"
        self.provider = LocalRestrictedProcessProvider(self.root, output_limit=40)
        self.node = ReferenceNode(self.provider)
        self.workspace = self.node.bind_workspace("workspace_01")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_rejects_workspace_escape(self) -> None:
        with self.assertRaises(WorkspaceViolation):
            self.provider.resolve_path(self.workspace, "../outside.py")
        with self.assertRaises(WorkspaceViolation):
            self.provider.resolve_path(self.workspace, str(Path(self.tempdir.name).resolve()))

    def test_rejects_root_symbolic_link_before_normalizing(self) -> None:
        candidate = Path(self.tempdir.name) / "linked-root"
        with (
            mock.patch("local_restricted_process.Path.is_symlink", return_value=True),
            mock.patch("local_restricted_process.Path.resolve", side_effect=AssertionError("root must not resolve first")),
        ):
            with self.assertRaises(WorkspaceViolation):
                LocalRestrictedProcessProvider(candidate)

    def test_rejects_symlink_path_when_supported(self) -> None:
        outside = Path(self.tempdir.name) / "outside"
        outside.mkdir()
        link = self.workspace / "linked-outside"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symbolic links unavailable in this environment: {error}")
        with self.assertRaises(WorkspaceViolation):
            self.provider.resolve_path(self.workspace, "linked-outside/secret.py")

    def test_runs_frozen_python_script_and_creates_manifest(self) -> None:
        script = self.workspace / "validate.py"
        artifact = self.workspace / "result.txt"
        script.write_text(
            "from pathlib import Path\n"
            "Path('result.txt').write_text('verified', encoding='utf-8')\n"
            "print('Python validation passed')\n",
            encoding="utf-8",
        )
        result = self.node.run_python_validation(self.workspace, "validate.py", timeout_seconds=2)
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(artifact.is_file())
        manifest_path = self.node.create_submission_manifest(
            artifact=artifact,
            task_version="synthetic-task/v1",
            validator_version="synthetic-validator/v1",
            human_validation_note="I ran the validator and confirmed result.txt contains verified.",
            execution=result,
            output_directory=Path(self.tempdir.name) / "artifacts",
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["sync_status"], "NOT_IMPLEMENTED")
        self.assertEqual(manifest["artifact"]["relative_path"], "result.txt")
        self.assertGreaterEqual(len(self.node.event_export()), 4)
        self.assertEqual([event["sequence"] for event in self.node.event_export()], list(range(1, len(self.node.event_export()) + 1)))

    def test_timeout_is_reported_without_success(self) -> None:
        script = self.workspace / "slow.py"
        script.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
        result = self.node.run_python_validation(self.workspace, "slow.py", timeout_seconds=0.05)
        self.assertTrue(result.timed_out)
        self.assertTrue(result.stopped)
        self.assertTrue(result.stop_confirmed)
        self.assertNotEqual(result.exit_code, 0)

    def test_output_is_truncated(self) -> None:
        script = self.workspace / "loud.py"
        script.write_text("print('x' * 100)\n", encoding="utf-8")
        result = self.node.run_python_validation(self.workspace, "loud.py", timeout_seconds=2)
        self.assertIn("output truncated by provider", result.stdout)


if __name__ == "__main__":
    unittest.main()
