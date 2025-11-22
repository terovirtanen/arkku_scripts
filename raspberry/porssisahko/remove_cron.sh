#!/bin/bash
# Remove cron jobs for porssisahko price fetching

# Remove cron jobs containing porssisahko_read.py
crontab -l 2>/dev/null | grep -v "porssisahko_read.py" | crontab -

echo "Removed porssisahko cron jobs"