"""Business team entry point and public exports."""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from vanda_team.agents import get_or_create_workflow
from vanda_team.server import main

__all__ = ["get_or_create_workflow", "main"]


if __name__ == "__main__":
    asyncio.run(main())
