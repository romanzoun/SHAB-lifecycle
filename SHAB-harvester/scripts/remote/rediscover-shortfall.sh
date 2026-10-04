#!/usr/bin/env bash
# Reset shortfall days, deploy scroll fix, start rediscover+scrape on server.
# Does NOT install cron.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

echo "==> Syncing code to server ..."
# Never sync local data/ — on the server it is a symlink to the volume.
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

cp -f scripts/remote/rediscover_shortfall.server.sh "$REMOTE_DIR/rediscover_shortfall.sh"
cp -f scripts/remote/daily_catchup.server.sh "$REMOTE_DIR/daily_catchup.sh"
chmod +x "$REMOTE_DIR/rediscover_shortfall.sh" "$REMOTE_DIR/daily_catchup.sh"

if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
  if pgrep -f 'shab_harvester.app (scrape-pending|discover-pending|discover-day)' >/dev/null 2>&1; then
    echo "ERROR: harvest work already running. Aborting."
    exit 1
  fi
  echo "Killing idle tmux session '$TMUX_SESSION'"
  tmux kill-session -t "$TMUX_SESSION"
fi

python3 - <<'PY'
from shab_harvester import db
from shab_harvester.utils import now_iso
with db.connect() as conn:
    cur = conn.execute(
        """
        UPDATE import_day
        SET status = 'pending', last_error = NULL, updated_at = ?
        WHERE result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (now_iso(),),
    )
    print(f"reset_shortfall_days={cur.rowcount}")
    pending = db.scalar(conn, "SELECT COUNT(*) FROM import_day WHERE status='pending'")
    print(f"pending_days_now={pending}")
    conn.commit()
PY

tmux new-session -d -s "$TMUX_SESSION" "$REMOTE_DIR/rediscover_shortfall.sh; echo; echo 'Press enter to close.'; read"
echo "Started rediscover-shortfall in tmux '$TMUX_SESSION' (cron NOT installed)."
sleep 4
tail -n 30 logs/rediscover_shortfall.log 2>/dev/null || true
EOF
