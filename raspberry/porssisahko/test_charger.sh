#!/bin/bash
# Manual test run of the car charger manager script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/car_charger_test.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Running car charger manager script..."
echo "Time: $(date)"
echo ""

# Activate venv and run the script
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 car_charger_manager.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "Test run completed at $(date)"
echo "Check the log file for details: $LOG_FILE"