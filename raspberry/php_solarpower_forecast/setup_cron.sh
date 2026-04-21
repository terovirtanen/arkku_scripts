#!/bin/bash
# Setup cron jobs for solarpower forecast
# Calls forecast_power.php every morning (06:00) and evening (18:00)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_ROOT="/var/www/html/solarpower_forecast"
CRON_TAG="solarpower_forecast"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "Setting up solarpower_forecast cron jobs..."

# Remove existing solarpower_forecast cron jobs to avoid duplicates
crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -

# Add new cron jobs
(
    crontab -l 2>/dev/null
    # Morning run at 06:00
    echo "0 6 * * * php $WEB_ROOT/index.php >> $SCRIPT_DIR/logs/cron.log 2>&1 # $CRON_TAG"
    # Evening run at 18:00
    echo "0 18 * * * php $WEB_ROOT/index.php >> $SCRIPT_DIR/logs/cron.log 2>&1 # $CRON_TAG"
) | crontab -

echo "✓ Solarpower forecast cron jobs added successfully:"
echo "  Morning run: daily at 06:00"
echo "  Evening run: daily at 18:00"
echo ""
echo "Current solarpower_forecast cron jobs:"
crontab -l | grep "$CRON_TAG"
