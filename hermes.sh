#!/bin/bash
# Hermes Knowledge Base Quick Runner
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PY="$SCRIPT_DIR/.venv/bin/python3"

if [ ! -f "$VENV_PY" ]; then
  echo "⚠️ Python virtual environment not found in $SCRIPT_DIR/.venv"
  exit 1
fi

exec "$VENV_PY" "$SCRIPT_DIR/main.py" "$@"
