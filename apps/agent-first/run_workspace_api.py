"""启动本机合成 Workspace API 服务（仅用于本地开发演示）。

用法：
    python run_workspace_api.py --port 8000

注意：
- 仅绑定 127.0.0.1，禁止对外暴露
- 所有数据存在内存中，重启后清空
- 这是合成演示，不是生产服务
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

# 确保能 import agent_first 包
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agent_first.workspace_wsgi import create_app  # noqa: E402


LOOPBACK_HOST = "127.0.0.1"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the local synthetic Workspace API demo server."
    )
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    app = create_app()
    with make_server(LOOPBACK_HOST, args.port, app) as server:
        print(f"SkillShift synthetic Workspace API: http://{LOOPBACK_HOST}:{args.port}")
        print("  Health check: GET /api/v1/health")
        print("  Teacher API:   /api/v1/demo/teacher/...")
        print("  Student API:   /api/v1/demo/student/...")
        print("This service is loopback-only, uses synthetic data, and clears all data when stopped.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nSynthetic demo stopped.")


if __name__ == "__main__":
    main()
