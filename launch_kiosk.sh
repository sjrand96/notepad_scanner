#!/usr/bin/env bash
# Launch notepad_scanner: Flask backend + default browser
# Usage: ./launch_kiosk.sh
# Press Ctrl+C when done to stop the server.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv and start Flask in background
source .venv/bin/activate
python backend/app.py &
FLASK_PID=$!

# Ensure Flask is killed when this script exits (e.g. Ctrl+C)
cleanup() {
  kill "$FLASK_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for Flask to listen before opening browser
sleep 3

# Open in default browser (xdg-open)
xdg-open 'http://127.0.0.1:5000'

# Keep script running so Flask stays alive; Ctrl+C exits and runs cleanup
wait
