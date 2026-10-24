"""Create reproducible local evidence for the R0 Foundation Spike.

The generated output is synthetic.  It does not connect to a model, service,
or student device outside this controlled workspace.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "execution" / "providers"))
sys.path.insert(0, str(ROOT / "apps" / "student-studio"))

from local_restricted_process import LocalRestrictedProcessProvider
from reference_node import ReferenceNode


def main() -> None:
    output = ROOT / "artifacts" / "R0-FOUNDATION-SPIKE"
    workspace_root = output / "synthetic-workspace-root"
    workspace_root.mkdir(parents=True, exist_ok=True)

    provider = LocalRestrictedProcessProvider(workspace_root)
    node = ReferenceNode(provider)
    workspace = node.bind_workspace("synthetic_python_task")
    script = workspace / "validate.py"
    script.write_text(
        "from pathlib import Path\n"
        "Path('result.txt').write_text('verified', encoding='utf-8')\n"
        "print('synthetic Python validation passed')\n",
        encoding="utf-8",
    )

    execution = node.run_python_validation(workspace, "validate.py", timeout_seconds=2)
    if execution.exit_code != 0:
        raise SystemExit(f"synthetic validation failed: {execution.stderr}")

    manifest = node.create_submission_manifest(
        artifact=workspace / "result.txt",
        task_version="synthetic-task/v1",
        validator_version="synthetic-validator/v1",
        human_validation_note="I ran the validator and confirmed the synthetic result artifact.",
        execution=execution,
        output_directory=output,
    )
    (output / "events.json").write_text(
        json.dumps(node.event_export(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "LIMITATIONS.md").write_text(
        "# Foundation Spike limitations\n\n"
        "- This is a local synthetic demonstration, not a real student workflow.\n"
        "- No model, API key, authentication, network sync, or teacher Web feature is present.\n"
        "- The provider does not claim OS-level network isolation or malicious-code sandboxing.\n"
        "- Windows symbolic-link rejection is implemented but needs a privileged-capable test environment.\n",
        encoding="utf-8",
    )
    print(manifest)


if __name__ == "__main__":
    main()
