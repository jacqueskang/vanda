#!/usr/bin/env bash
set -euo pipefail

VENV_PYTHON=".venv/bin/python"

if [[ ! -f "$VENV_PYTHON" ]]; then
  echo "Virtual environment not found at .venv" >&2
  echo "Please run: source ./install.sh" >&2
  exit 1
fi

exec "$VENV_PYTHON" -c "import sys; sys.path.insert(0, 'src'); import asyncio; from server import main; asyncio.run(main())"
