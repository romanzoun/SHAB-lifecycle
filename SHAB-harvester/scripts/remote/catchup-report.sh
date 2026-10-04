#!/usr/bin/env bash
# Parse daily_catchup.log for morning/evening step durations.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

"${SSH[@]}" bash -s <<'EOF'
LOG=/opt/shab-harvester/logs/daily_catchup.log
if [ ! -f "$LOG" ]; then
  echo "No $LOG yet (cron has not run)."
  exit 0
fi
echo "=== recent FINISHED lines ==="
grep -E 'FINISHED slot=|DAILY_CATCHUP_DONE|already running|STARTED' "$LOG" | tail -n 40
EOF
