#!/bin/bash
# Setup cron jobs for solarpower forecast
# Calls forecast_power.php every morning (06:00) and evening (18:00)

WEB_ROOT="/var/www/html/solarpower_forecast"
LOG_DIR="/var/log/solarpower_forecast"
CRON_TAG="solarpower_forecast"

# Create log directory if it doesn't exist
sudo mkdir -p "$LOG_DIR"
sudo chown www-data:www-data "$LOG_DIR"

echo "Setting up solarpower_forecast cron jobs..."

# Remove existing solarpower_forecast cron jobs to avoid duplicates
crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -

# Add new cron jobs
(
    crontab -l 2>/dev/null
    # Morning run at 06:00
    echo "0 6 * * * php $WEB_ROOT/index.php >> $LOG_DIR/cron.log 2>&1 # $CRON_TAG"
    # Evening run at 18:00
    echo "0 18 * * * php $WEB_ROOT/index.php >> $LOG_DIR/cron.log 2>&1 # $CRON_TAG"
) | crontab -

echo "Cron jobs added:"
crontab -l | grep "$CRON_TAG"
