#!/usr/bin/env bash
# Long-running analyzer walk. Safe to restart; state lives in SQLite.
set -euo pipefail
export SHAB_ANALYZER_DB="${SHAB_ANALYZER_DB:-/mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite}"
export SHAB_HARVESTER_XML="${SHAB_HARVESTER_XML:-/opt/shab-raw/raw_xml}"
ANALYZER_SRC="${ANALYZER_SRC:-/mnt/HC_Volume_106976683/src/SHAB-ANALYZER}"
VENV="${VENV:-/mnt/HC_Volume_106976683/analyzer/.venv}"
LOCK="${LOCK:-/var/lock/shab-analyzer-walk.lock}"
LOG_DIR="${LOG_DIR:-/mnt/HC_Volume_106976683/analyzer/logs}"
mkdir -p "$(dirname "$SHAB_ANALYZER_DB")" "$LOG_DIR"
cd "$ANALYZER_SRC"
exec flock -n "$LOCK" "$VENV/bin/python" -m shab_analyzer.app walk \
  --xml-root "$SHAB_HARVESTER_XML" \
  --db "$SHAB_ANALYZER_DB" \
  --lock "$LOCK" \
  --poll 300
