#!/bin/bash
# Setup cron job for MySQL backup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ".env file not found at $SCRIPT_DIR/.env"
    echo "Please create .env file first"
    exit 1
fi

echo "Setting up MySQL backup cron job..."

# Remove existing MySQL backup cron jobs to avoid duplicates
crontab -l 2>/dev/null | grep -v "backup_mysql.sh" | crontab -

# Add new cron job
(
    crontab -l 2>/dev/null
    # MySQL backup: runs at 3:00 AM daily
    echo "0 3 * * * cd $SCRIPT_DIR && bash backup_mysql.sh >> $SCRIPT_DIR/logs/backup.log 2>&1"
) | crontab -

echo "✓ MySQL backup cron job added successfully:"
echo "  Daily backup: 03:00 AM"
echo ""
echo "Current MySQL backup cron jobs:"
crontab -l | grep "backup_mysql"
