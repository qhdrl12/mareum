#!/usr/bin/env python3
"""
Script to run the ReAct Agent API server.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import run_server


def main():
    parser = argparse.ArgumentParser(description="Run ReAct Agent API Server")
    parser.add_argument(
        "--config",
        type=str,
        default="examples/configs/openai_comaptible.yaml",
        help="Path to agent configuration file",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the server to"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server to"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Set environment variable for agent config
    os.environ["AGENT_CONFIG_PATH"] = args.config

    print(f"🚀 Starting ReAct Agent API Server...")
    print(f"📄 Agent Config: {args.config}")
    print(f"🌍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print("-" * 50)

    # Run the server
    run_server(host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
