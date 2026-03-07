#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
	echo ".env file not found: $ENV_FILE"
	exit 1
fi

set -a
source "$ENV_FILE"
set +a

BACKUP_DIR="/mnt/usb/backup/mysql"
HOST="${MYSQL_HOST:-localhost}"
PORT="${MYSQL_PORT:-3306}"
USER="${MYSQL_USER:-root}"
if [[ -n "${MYSQL_PASSWORD:-}" ]]; then
	export MYSQL_PWD="$MYSQL_PASSWORD"
fi

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/mysql_backup.sql.gz"
RCLONE_REMOTE=jottaremote
RCLONE_TARGET_DIR="${RCLONE_TARGET_DIR:-mysql_backup}"

mkdir -p "$BACKUP_DIR"

sudo mysqldump --single-transaction --quick --lock-tables=false --all-databases | gzip > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"

if [[ -z "$RCLONE_REMOTE" ]]; then
	echo "Cloud upload skipped: set RCLONE_REMOTE to enable upload"
	exit 0
fi

if ! command -v rclone >/dev/null 2>&1; then
	echo "rclone not found. Install rclone first."
	exit 1
fi

DESTINATION="${RCLONE_REMOTE}:${RCLONE_TARGET_DIR}"
rclone copy "$BACKUP_DIR" "$DESTINATION" --create-empty-src-dirs --transfers 4 --checkers 8

echo "Cloud backup completed: $BACKUP_DIR -> $DESTINATION"
