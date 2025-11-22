#!/bin/bash
# Manual test run of the porssisahko script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/porssisahko_read.py"
LOG_FILE="$SCRIPT_DIR/logs/porssisahko_test.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Running porssisahko price fetching script..."
echo "Script: $PYTHON_SCRIPT"
echo "Log: $LOG_FILE"
echo "Time: $(date)"
echo ""

# Run the script and capture output
cd "$SCRIPT_DIR"
python3 "$PYTHON_SCRIPT" 2>&1 | tee "$LOG_FILE"

echo ""
echo "Test run completed at $(date)"
echo "Check the log file for details: $LOG_FILE"