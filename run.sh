#!/usr/bin/env bash
set -euo pipefail

VENV_PYTHON=".venv/bin/python"

if [[ ! -f "$VENV_PYTHON" ]]; then
  echo "Virtual environment not found at .venv" >&2
  echo "Please run: source ./install.sh" >&2
  exit 1
fi

"$VENV_PYTHON" scripts/run.py
