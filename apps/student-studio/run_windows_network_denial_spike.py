"""Write one bounded local-loopback network-denial probe result."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "execution" / "providers"))

from windows_isolation_spike import probe_zero_capability_network_denial


def main() -> None:
    output = ROOT / "artifacts" / "R0-WINDOWS-ISOLATION-LAUNCHER-SPIKE"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "network-denial-probe.json"
    path.write_text(json.dumps(probe_zero_capability_network_denial(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
