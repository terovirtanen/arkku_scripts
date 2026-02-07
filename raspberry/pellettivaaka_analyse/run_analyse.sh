#!/usr/bin/env bash
set -euo pipefail

# Configuration: set parameters here
START="2026-02-01 00:00:00"
END="2026-02-02 00:00:00"
PASSWORD="CHANGEME"
HOST="192.168.100.50"
DB="pellet_measurements"
USER="admin"
# Optional outputs (leave empty to skip)
CSV_OUT=""
PLOT_OUT=""  # e.g. "weight.png"
SHOW_PLOT="false"  # true/false
# Consumption calc (leave false to skip)
CONSUMPTION="false"  # true/false
THRESHOLD="0.1"

# Resolve script directory and Python
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON_BIN:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PY="python"
  else
    echo "Python interpreter not found (looked for python3/python)." >&2
    exit 1
  fi
fi

# Build args
ARGS=(
  "--start" "$START"
  "--end" "$END"
  "--host" "$HOST"
  "--db" "$DB"
  "--user" "$USER"
)

if [[ -n "$CSV_OUT" ]]; then
  ARGS+=("--csv" "$CSV_OUT")
fi
if [[ -n "$PLOT_OUT" ]]; then
  ARGS+=("--plot" "$PLOT_OUT")
fi
if [[ "${SHOW_PLOT}" == "true" ]]; then
  ARGS+=("--show-plot")
fi
if [[ "${CONSUMPTION}" == "true" ]]; then
  ARGS+=("--consumption" "--threshold" "$THRESHOLD")
fi

# Export password for the script
export PELLET_DB_PASSWORD="$PASSWORD"

# Run
exec "$PY" "$SCRIPT_DIR/analyse.py" "${ARGS[@]}"
