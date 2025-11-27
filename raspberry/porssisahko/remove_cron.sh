#!/bin/bash
# Remove all porssisahko cron jobs

echo "Current porssisahko cron jobs:"
crontab -l 2>/dev/null | grep -E "(porssisahko|car_charger)" || echo "No porssisahko cron jobs found"

echo ""
read -p "Do you want to remove all porssisahko cron jobs? (y/N): " confirm

if [[ $confirm =~ ^[Yy]$ ]]; then
    # Remove all porssisahko related cron jobs
    crontab -l 2>/dev/null | grep -v -E "(porssisahko_read|porssisahko_optimize|car_charger_manager)" | crontab -
    
    if [ $? -eq 0 ]; then
        echo "✓ All porssisahko cron jobs removed successfully"
        echo ""
        echo "Remaining cron jobs:"
        crontab -l 2>/dev/null || echo "No cron jobs remaining"
    else
        echo "✗ Failed to remove porssisahko cron jobs"
        exit 1
    fi
else
    echo "Operation cancelled"
fi