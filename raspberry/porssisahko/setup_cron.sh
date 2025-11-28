#!/bin/bash
# Setup cron jobs for porssisahko system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please create virtual environment first"
    exit 1
fi

echo "Setting up porssisahko cron jobs..."

# Remove existing porssisahko cron jobs to avoid duplicates
crontab -l 2>/dev/null | grep -v -E "(porssisahko_read|porssisahko_optimize|car_charger_manager)" | crontab -

# Add new cron jobs
(
    crontab -l 2>/dev/null
    # Price fetching: runs at 3 AM and 3 PM daily
    echo "21 14,3 * * * cd $SCRIPT_DIR && venv/bin/python3 porssisahko_read.py >> $SCRIPT_DIR/logs/cron_read.log 2>&1"
    # Charging optimization: runs at 4 AM and 4 PM daily (after price fetch)
    echo "22 14,3 * * * cd $SCRIPT_DIR && venv/bin/python3 porssisahko_optimize_charging.py >> $SCRIPT_DIR/logs/cron_opt.log 2>&1"
    # Car charger management: runs every 10 minutes
    # echo "*/10 * * * * cd $SCRIPT_DIR && venv/bin/python3 car_charger_manager.py >> $SCRIPT_DIR/logs/cron_car_charger.log 2>&1"
) | crontab -

echo "✓ Porssisahko cron jobs added successfully:"
echo "  Price fetching: daily at 15:00 and 03:00"
echo "  Optimization: daily at 16:00 and 04:00"
echo "  Car charger: every 10 minutes"
echo ""
echo "Current porssisahko cron jobs:"
crontab -l | grep -E "(porssisahko|car_charger)"