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

echo "Running Python code quality checks..."
"$VENV_BLACK" src/ && echo "✅ Code formatted with black"
"$VENV_FLAKE8" src/ || (echo "⚠️  Linting issues found (non-blocking)" >&2)
"$VENV_MYPY" src/ || (echo "⚠️  Type checking issues found (non-blocking)" >&2)

echo ""
echo "Building Vue.js frontend..."
cd src/ui
npm install
npm run build
cd ..

echo "✅ Frontend built to dist/ui/"
echo "Checks completed (warnings above are non-blocking)"