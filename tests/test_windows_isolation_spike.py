from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "execution" / "providers"))

from windows_isolation_spike import (
    WindowsIsolationSpikeError,
    WindowsJob,
    probe_appcontainer_python_launch,
    probe_copied_runner,
    probe_zero_capability_network_denial,
    probe_as_json,
    probe_job_tree,
    probe_zero_capability_profile,
)


@unittest.skipUnless(os.name == "nt", "Windows-only Spike")
class WindowsIsolationSpikeTests(unittest.TestCase):
    def test_synthetic_standard_child_is_terminated_with_its_job(self) -> None:
        result = probe_job_tree()
        self.assertEqual(result.state, "PASS", result.detail)
        self.assertTrue(result.parent_in_job)
        self.assertTrue(result.child_in_job)
        self.assertTrue(result.parent_exited)
        self.assertTrue(result.child_exited)
        self.assertEqual(result.active_pids_after_terminate, ())

    def test_profile_probe_is_explicit_about_permission_or_cleanup_failure(self) -> None:
        result = probe_zero_capability_profile()
        self.assertIn(result.state, {"PASS", "BLOCKED", "FAIL"})
        self.assertRegex(result.create_hresult, r"^0x[0-9A-F]{8}$")
        if result.state == "PASS":
            self.assertEqual(result.delete_hresult, "0x00000000")
        else:
            self.assertTrue(result.detail)

    def test_invalid_process_handle_is_not_reported_as_job_assignment_success(self) -> None:
        with WindowsJob() as job:
            with self.assertRaises(WindowsIsolationSpikeError):
                job.assign_process_handle(0)

    def test_appcontainer_python_probe_is_explicit_about_runtime_or_cleanup_failure(self) -> None:
        result = probe_appcontainer_python_launch()
        self.assertIn(result.state, {"PASS", "BLOCKED", "FAIL"})
        self.assertRegex(result.create_hresult, r"^0x[0-9A-F]{8}$")
        if result.state == "PASS":
            self.assertTrue(result.token_is_appcontainer)
            self.assertTrue(result.process_in_job)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.active_pids_after_exit, ())
            self.assertEqual(result.delete_hresult, "0x00000000")
        else:
            self.assertTrue(result.detail)

    def test_copied_runner_probe_is_explicit_about_compatibility_or_acl_failure(self) -> None:
        result = probe_copied_runner()
        self.assertIn(result.state, {"PASS", "BLOCKED", "FAIL"})
        self.assertIn("temporary runner directory removed", result.detail)
        self.assertNotIn("\\Users\\", result.detail)

    def test_zero_capability_network_denial_is_explicit(self) -> None:
        result = probe_zero_capability_network_denial()
        self.assertIn(result["state"], {"PASS", "BLOCKED", "FAIL"})
        if result["state"] == "PASS":
            self.assertEqual(result["baseline_ipv4_ipv6"], "PASS")
            self.assertEqual(result["appcontainer"]["exit_code"], 0)

    def test_evidence_payload_has_no_workspace_or_user_path(self) -> None:
        payload = probe_as_json()
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(str(Path.home()), rendered)
        self.assertNotIn("\\Users\\", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertEqual(payload["schema_version"], "r0-windows-isolation-launcher-spike/v1")


if __name__ == "__main__":
    unittest.main()
