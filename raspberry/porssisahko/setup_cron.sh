#!/bin/bash
# Setup cron job for porssisahko price fetching

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add cron jobs - runs at 11 PM and 6 AM daily
(crontab -l 2>/dev/null; echo "0 23,6 * * * cd $SCRIPT_DIR && source venv/bin/activate && python3 porssisahko_read.py") | crontab -

echo "Cron job added: runs daily at 23:00 and 06:00"
echo "Current crontab:"
crontab -l | grep porssisahko_read.py