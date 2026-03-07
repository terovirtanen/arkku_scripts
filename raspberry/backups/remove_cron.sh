#!/bin/bash
# Remove MySQL backup cron jobs

echo "Removing MySQL backup cron jobs..."

# Remove backup_mysql.sh cron jobs
crontab -l 2>/dev/null | grep -v "backup_mysql.sh" | crontab -

echo "✓ MySQL backup cron jobs removed"
echo ""
echo "Remaining cron jobs:"
crontab -l 2>/dev/null || echo "No cron jobs found"
