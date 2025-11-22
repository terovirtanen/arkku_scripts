#!/bin/bash
# Setup cron job for porssisahko price fetching

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add cron jobs - runs at 3 AM and 3 PM daily
(crontab -l 2>/dev/null; echo "0 3,15 * * * cd $SCRIPT_DIR && python3 porssisahko_read.py") | crontab -

echo "Cron job added: runs daily at 03:00 and 15:00"
echo "Current crontab:"
crontab -l | grep porssisahko_read.py