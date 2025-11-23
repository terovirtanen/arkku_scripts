#!/bin/bash
# Test charging optimization script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/optimize_test.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Testing charging optimization..."
echo "Time: $(date)"
echo ""

# Activate venv and run the script
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 porssisahko_optimize_charging.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "Optimization test completed at $(date)"
echo "Check the log file for details: $LOG_FILE"