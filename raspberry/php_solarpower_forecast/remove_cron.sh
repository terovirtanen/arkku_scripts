#!/bin/bash
# Remove solarpower_forecast cron jobs

CRON_TAG="solarpower_forecast"

echo "Current solarpower_forecast cron jobs:"
crontab -l 2>/dev/null | grep "$CRON_TAG" || echo "No solarpower_forecast cron jobs found"

echo ""
read -p "Do you want to remove all solarpower_forecast cron jobs? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -

    if [ $? -eq 0 ]; then
        echo "All solarpower_forecast cron jobs removed successfully"
        echo ""
        echo "Remaining cron jobs:"
        crontab -l 2>/dev/null || echo "No cron jobs remaining"
    else
        echo "Failed to remove solarpower_forecast cron jobs"
        exit 1
    fi
else
    echo "Cancelled"
fi
