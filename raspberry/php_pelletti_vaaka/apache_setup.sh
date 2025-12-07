#!/bin/bash
set -euo pipefail

DEST="/var/www/html/pellettivaaka/"

# Ensure destination exists
sudo mkdir -p "$DEST"

# Copy everything except this script and .env.example
sudo rsync -av --exclude 'apache_setup.sh' --exclude '.env.example' ./ "$DEST"
