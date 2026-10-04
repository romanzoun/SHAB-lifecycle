#!/usr/bin/env bash
# Start the parser watchdog (`codex exec` or `claude -p` je nach --engine).
# Voraussetzung: `codex login` bzw. `claude auth login`, SSH-Key ~/.ssh/hetzner_prod
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 "$ROOT/scripts/rule_watch.py" "$@"
