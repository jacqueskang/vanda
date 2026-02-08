#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
PYTHON_BIN=""

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Python not found. Install Python 3 and re-run this script." >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Install dependencies using the venv python
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r requirements.txt

echo "✅ Venv setup complete!"
echo ""
echo "To activate the virtual environment in future terminal sessions, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Tip: Run this script with 'source' to activate in your current shell:"
echo "  source ./install.sh"
echo ""

# Activate the virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated!"
