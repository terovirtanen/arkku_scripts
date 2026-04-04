#!/usr/bin/env bash
set -euo pipefail

# Configuration: set parameters here
# kulutus 2021-01-21 - 2026-01-31: säkillinen eli 500kg
START="2026-01-21 00:00:00"
END="2026-04-4 00:00:00"
PASSWORD="${1:-}"
HOST="192.168.100.50"
DB="pellet_scale"
USER="admin"
# Optional outputs (leave empty to skip)
CSV_OUT=""
PLOT_OUT=""  # e.g. "weight.png"
SHOW_PLOT="false"  # true/false
# Consumption calc (leave false to skip)
CONSUMPTION="true"  # true/false
THRESHOLD="0.1"
DEBUG="false"  # true/false to print rows and consumption events

# Resolve script directory and ensure project virtual environment exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating virtual environment: $VENV_DIR"

  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$VENV_DIR"
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$VENV_DIR"
  else
    echo "Python interpreter not found for creating virtual environment." >&2
    exit 1
  fi
fi

# Ensure required packages are installed or repaired in the virtual environment
"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

PY="${PYTHON_BIN:-$VENV_DIR/bin/python}"
if [[ ! -x "$PY" ]]; then
  echo "Python interpreter not found in virtual environment: $PY" >&2
  exit 1
fi

if [[ -z "$PASSWORD" ]]; then
  echo "Usage: $0 <db_password>" >&2
  exit 1
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
if [[ "${DEBUG}" == "true" ]]; then
  ARGS+=("--print-rows" "--print-consumption-events")
fi
# Export password for the script
export PELLET_DB_PASSWORD="$PASSWORD"

# Run
exec "$PY" "$SCRIPT_DIR/analyse.py" "${ARGS[@]}"
