#!/bin/bash
# Manual test run of the porssisahko script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/porssisahko_test.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Running porssisahko price fetching script..."
echo "Time: $(date)"
echo ""

# Activate venv and run the script
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 porssisahko_read.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "Test run completed at $(date)"
echo "Check the log file for details: $LOG_FILE"