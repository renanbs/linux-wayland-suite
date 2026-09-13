#!/usr/bin/env bash
# manage-cpu-turbo.sh — Forwarder to canonical Python CPU Turbo Boost tool
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/manage-cpu-turbo.py" "$@"
