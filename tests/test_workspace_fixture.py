from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "agent-first"))

from agent_first.workspace_api import ALLOWED_ARTIFACTS


FIXTURE_DIR = ROOT / "fixtures" / "orders-audit-v1"
EXPECTED_MEDIA_TYPES = {
    "main.py": "text/x-python",
    "orders.csv": "text/csv",
    "README.md": "text/markdown",
}


class WorkspaceFixtureTests(unittest.TestCase):
    def test_api_catalog_matches_candidate_fixture_manifest(self) -> None:
        manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
        fixture_catalog = {entry["logical_name"]: entry["media_type"] for entry in manifest["files"]}
        self.assertEqual(ALLOWED_ARTIFACTS, fixture_catalog)

    def test_manifest_and_fixed_fixture_bytes_match(self) -> None:
        self.assertFalse(FIXTURE_DIR.is_symlink())
        manifest_path = FIXTURE_DIR / "manifest.json"
        self.assertFalse(manifest_path.is_symlink())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual("synthetic-project-fixture/v1", manifest["schema_version"])
        self.assertEqual("orders-audit-v1", manifest["project_id"])
        self.assertEqual("CANDIDATE_CANONICAL_SOURCE", manifest["fixture_status"])
        self.assertFalse(manifest["execution_enabled"])
        self.assertEqual(set(EXPECTED_MEDIA_TYPES), {entry["logical_name"] for entry in manifest["files"]})

        for entry in manifest["files"]:
            name = entry["logical_name"]
            self.assertIn(name, EXPECTED_MEDIA_TYPES)
            self.assertEqual(EXPECTED_MEDIA_TYPES[name], entry["media_type"])
            self.assertEqual(name, Path(name).name)
            path = FIXTURE_DIR / name
            self.assertFalse(path.is_symlink())
            data = path.read_bytes()
            self.assertEqual(entry["size_bytes"], len(data), name)
            self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest(), name)

    def test_fixture_is_synthetic_non_executable_and_keeps_uncertainty_visible(self) -> None:
        source = (FIXTURE_DIR / "main.py").read_text(encoding="utf-8")
        data = (FIXTURE_DIR / "orders.csv").read_text(encoding="utf-8")
        readme = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("这里只展示代码，不会执行", source)
        self.assertIn("O-105,2,89.00,160.00", data)
        self.assertIn("哪些业务规则仍需确认", readme)

    def test_student_prototype_embedded_content_matches_candidate_fixture_bytes(self) -> None:
        source = (ROOT / "apps" / "student-web" / "app.js").read_text(encoding="utf-8")
        for name in EXPECTED_MEDIA_TYPES:
            start = source.index(f'  "{name}": {{')
            end = source.index("\n  },", start)
            section = source[start:end]
            match = re.search(r'content:\s*("(?:\\.|[^"\\])*")', section)
            self.assertIsNotNone(match, name)
            embedded_content = json.loads(match.group(1))
            self.assertEqual((FIXTURE_DIR / name).read_bytes(), embedded_content.encode("utf-8"), name)


if __name__ == "__main__":
    unittest.main()
