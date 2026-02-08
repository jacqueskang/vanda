#!/usr/bin/env bash
set -euo pipefail

VENV_PYTHON=".venv/bin/python"
VENV_MYPY=".venv/bin/mypy"
VENV_FLAKE8=".venv/bin/flake8"
VENV_BLACK=".venv/bin/black"

if [[ ! -f "$VENV_PYTHON" ]]; then
  echo "Virtual environment not found at .venv" >&2
  echo "Please run: source ./install.sh" >&2
  exit 1
fi

echo "Running code quality checks..."
"$VENV_BLACK" src/ && echo "✅ Code formatted with black"
"$VENV_FLAKE8" src/ || (echo "⚠️  Linting issues found (non-blocking)" >&2)
"$VENV_MYPY" src/ || (echo "⚠️  Type checking issues found (non-blocking)" >&2)

echo "Checks completed (warnings above are non-blocking)"
"$VENV_PYTHON" scripts/run.py
