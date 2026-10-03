#!/bin/bash
set -euo pipefail

DEST="/var/www/html/car_charger/"

sudo mkdir -p "$DEST"

if [ -f "composer.json" ]; then
	if command -v composer >/dev/null 2>&1; then
		echo "Running composer install..."
		composer install --no-dev --prefer-dist --optimize-autoloader --no-interaction --no-progress
	else
		echo "Warning: composer not found. Skipping dependency install." >&2
	fi
fi

sudo rsync -av --exclude 'apache_setup.sh' --exclude '.env.example' ./ "$DEST"
