#!/usr/bin/env bash
# Print walk state machine coverage from the server.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER_LOCAL="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$ANALYZER_LOCAL/../SHAB-harvester/scripts/remote/_common.sh"
"${SSH[@]}" /mnt/HC_Volume_106976683/analyzer/.venv/bin/python -m shab_analyzer.app status \
  --db /mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite
echo "--- systemd ---"
"${SSH[@]}" systemctl --no-pager --full status shab-analyzer-walk.service | head -20
