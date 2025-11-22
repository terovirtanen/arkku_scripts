#!/bin/bash
# Test MQTT publishing script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/mqtt_test.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Testing MQTT price publishing..."
echo "Time: $(date)"
echo ""

# Activate venv and run the script
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 porssisahko_mqtt_publish.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "MQTT test completed at $(date)"
echo "Check the log file for details: $LOG_FILE"