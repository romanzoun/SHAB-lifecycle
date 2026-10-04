#!/usr/bin/env bash
# Deploy daily_catchup.sh to the server and install crontab (06:00 + 18:00 Europe/Zurich).
# Idempotent. Does not start a catch-up immediately (next cron slot will).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

echo "==> Syncing code (excluding data/ and .env) ..."
rsync -av \
  --exclude '.venv' --exclude 'data/' --exclude 'data' \
  --exclude '__pycache__' --exclude '.git' --exclude '.DS_Store' \
  --exclude '.env' \
  -e "ssh -i $SSH_KEY" \
  "$LOCAL_PROJECT_ROOT/" "$SERVER:$REMOTE_DIR/"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate
mkdir -p logs

cp -f scripts/remote/daily_catchup.server.sh "$REMOTE_DIR/daily_catchup.sh"
chmod +x "$REMOTE_DIR/daily_catchup.sh"

# Ensure schema has non_public table
python -m shab_harvester.app init-db
python -m shab_harvester.app archive-non-public

# Close idle finished harvest session if present (does not hold flock after exit)
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  if pgrep -f 'shab_harvester.app (scrape-pending|discover-pending|discover-day)' >/dev/null 2>&1; then
    echo "WARNING: harvest work still running — cron installed, flock will skip overlaps."
  else
    echo "Killing idle tmux session '$TMUX_SESSION'"
    tmux kill-session -t "$TMUX_SESSION" || true
  fi
fi

# Install/replace only our marked crontab block
EXISTING=\$(crontab -l 2>/dev/null || true)
FILTERED=\$(printf '%s\n' "\$EXISTING" | grep -v 'shab-daily-catchup' || true)
{
  printf '%s\n' "\$FILTERED"
  echo "# shab-daily-catchup BEGIN"
  echo "CRON_TZ=Europe/Zurich"
  echo "0 6 * * * /opt/shab-harvester/daily_catchup.sh >> /opt/shab-harvester/logs/daily_catchup.cron.log 2>&1  # shab-daily-catchup"
  echo "0 18 * * * /opt/shab-harvester/daily_catchup.sh >> /opt/shab-harvester/logs/daily_catchup.cron.log 2>&1  # shab-daily-catchup"
  echo "# shab-daily-catchup END"
} | crontab -

echo "==> crontab installed:"
crontab -l | grep -A5 'shab-daily-catchup' || crontab -l

echo "==> Smoke: flock skip when free (dry run start+quick exit check via flock -n)"
flock -n /var/lock/shab-harvest.lock echo "flock OK (lock free)"

echo "Done. Next runs: 06:00 and 18:00 Europe/Zurich."
echo "Manual run: /opt/shab-harvester/daily_catchup.sh"
EOF
