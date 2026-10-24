"""Explicit launcher for the loopback-only synthetic web demonstration."""

from __future__ import annotations

import argparse
from wsgiref.simple_server import make_server

from agent_first.local_web import LocalWebApplication


LOOPBACK_HOST = "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run only the local SkillShift synthetic web demonstration.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    app = LocalWebApplication()
    with make_server(LOOPBACK_HOST, args.port, app.wsgi) as server:
        print(f"SkillShift synthetic demo: http://{LOOPBACK_HOST}:{args.port}")
        print("This service is loopback-only, uses synthetic data, and clears all data when stopped.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Synthetic demo stopped.")


if __name__ == "__main__":
    main()
