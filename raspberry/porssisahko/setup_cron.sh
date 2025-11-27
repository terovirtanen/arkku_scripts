#!/bin/bash
# Setup cron job for porssisahko price fetching

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Add cron jobs - runs at 3 AM and 3 PM daily with logging
(crontab -l 2>/dev/null; echo "0 15,3 * * * cd $SCRIPT_DIR && source venv/bin/activate && python3 porssisahko_read.py >> $SCRIPT_DIR/logs/cron.log 2>&1") | crontab -

echo "Cron job added: runs daily at 15:00 and 03:00"
echo "Current crontab:"
crontab -l | grep porssisahko_read.py