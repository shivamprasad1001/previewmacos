#!/usr/bin/env bash
# Runner script for Preview (macOS Linux edition)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export QT_LOGGING_RULES="${QT_LOGGING_RULES:-qt.qpa.services=false}"

# Launch Preview
python3 "$SCRIPT_DIR/main.py" "$@"
