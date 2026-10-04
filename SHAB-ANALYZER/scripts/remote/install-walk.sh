#!/usr/bin/env bash
# Deploy analyzer code to the structured volume and enable the walk systemd unit.
# Does not touch harvest raw. Idempotent. Restarts the walk so it resumes from SQLite state.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER_LOCAL="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$ANALYZER_LOCAL/../SHAB-harvester/scripts/remote/_common.sh"

# Paths live on the structured volume. Do not retarget /opt/shab-structured.
VOLUME="/mnt/HC_Volume_106976683"
REMOTE_SRC="$VOLUME/src/SHAB-ANALYZER"
REMOTE_RUN="$VOLUME/analyzer"

echo "==> Syncing SHAB-ANALYZER to structured volume ..."
"${SSH[@]}" mkdir -p "$REMOTE_SRC" "$REMOTE_RUN/logs"
rsync -av \
  --exclude '.venv' --exclude 'data/' --exclude '__pycache__' \
  --exclude '.pytest_cache' --exclude '.git' --exclude '.DS_Store' \
  --exclude '*.egg-info' --exclude 'examples/' \
  -e "ssh -i $SSH_KEY" \
  "$ANALYZER_LOCAL/" "$SERVER:$REMOTE_SRC/"

scp -i "$SSH_KEY" "$ANALYZER_LOCAL/scripts/remote/walk.server.sh" \
  "$SERVER:$REMOTE_RUN/walk.sh"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
VOLUME="/mnt/HC_Volume_106976683"
SRC="\$VOLUME/src/SHAB-ANALYZER"
RUN="\$VOLUME/analyzer"
chmod +x "\$RUN/walk.sh"
test -f "\$SRC/pyproject.toml"
ls -ld /opt/shab-raw/raw_xml /opt/shab-raw

PY=""
for cand in python3.12 python3.11 python3; do
  if command -v "\$cand" >/dev/null 2>&1; then
    PY="\$cand"
    break
  fi
done
if [ -z "\$PY" ]; then
  echo "No python3 found" >&2
  exit 1
fi
echo "Using \$PY (\$(\$PY --version))"

if [ ! -x "\$RUN/.venv/bin/python" ]; then
  "\$PY" -m venv "\$RUN/.venv"
fi
"\$RUN/.venv/bin/pip" install -q -U pip setuptools wheel
"\$RUN/.venv/bin/pip" install -q -e "\$SRC"

cat >/etc/systemd/system/shab-analyzer-walk.service <<'UNIT'
[Unit]
Description=SHAB analyzer XML walk (resumable state machine)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=20
Environment=SHAB_ANALYZER_DB=/mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite
Environment=SHAB_HARVESTER_XML=/opt/shab-raw/raw_xml
Environment=PYTHONUNBUFFERED=1
WorkingDirectory=/mnt/HC_Volume_106976683/src/SHAB-ANALYZER
ExecStart=/mnt/HC_Volume_106976683/analyzer/.venv/bin/python -m shab_analyzer.app walk --xml-root /opt/shab-raw/raw_xml --db /mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite --lock /var/lock/shab-analyzer-walk.lock --poll 300
StandardOutput=append:/mnt/HC_Volume_106976683/analyzer/logs/walk.log
StandardError=append:/mnt/HC_Volume_106976683/analyzer/logs/walk.log

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable shab-analyzer-walk.service
systemctl restart shab-analyzer-walk.service
sleep 3
systemctl --no-pager --full status shab-analyzer-walk.service | head -25
echo "==> walk_job:"
"\$RUN/.venv/bin/python" - <<'PY'
import sqlite3
conn = sqlite3.connect("file:/mnt/HC_Volume_106976683/analyzer/shab_analyzer.sqlite?mode=ro", uri=True, timeout=3)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT state, parser_version, processed, ok_count, partial_count, heartbeat_at FROM walk_job WHERE id=1").fetchone()
print(dict(row) if row else "no job yet")
PY
EOF

echo "Done. Resume is automatic. Check: ssh ... python -m shab_analyzer.app status"
