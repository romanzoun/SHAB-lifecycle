#!/usr/bin/env bash
# Starts a watcher on the server (detached tmux session "harvest-watcher")
# that waits for discovery to finish, then automatically:
#   1. moves data/ onto the mounted volume (if VOLUME_PATH is mounted and
#      data/ isn't already a symlink to it)
#   2. runs scrape-all inline, in this same "harvest-watcher" session — NOT
#      in a separate "harvest" session. So once this is running, check
#      progress with status.sh/status-detail.sh (DB-based) rather than
#      still-running.sh, which only ever looks for "harvest".
#
# Completion is checked against the database (any import_day rows still
# pending/running/failed?), not against the discover-all.sh tmux session —
# that session may finish, get closed, or even have its tmux server die
# entirely (has happened) without affecting this check. If discovery is
# already 100% done when this script starts, it proceeds immediately.
#
# Deliberately does NOT call any `tmux send-keys`/`kill-session` on a
# leftover "harvest" session — doing so killed the entire tmux server twice
# in testing (taking this watcher down mid-script). Not worth the risk.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

VOLUME_PATH="/mnt/HC_Volume_106139937"
WATCHER_SESSION="harvest-watcher"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
if tmux has-session -t "$WATCHER_SESSION" 2>/dev/null; then
    echo "Watcher already running ('$WATCHER_SESSION'). Not starting a second one."
    exit 1
fi

cat > "$REMOTE_DIR/auto_continue.sh" <<'INNER'
#!/usr/bin/env bash
set -uo pipefail
cd "$REMOTE_DIR"
VOLUME_PATH="$VOLUME_PATH"
TMUX_SESSION="$TMUX_SESSION"

# Survive even if the tmux session itself dies for some reason — everything
# also goes to a plain file we can read over SSH regardless of tmux state.
exec > >(tee -a "$REMOTE_DIR/auto_continue.log") 2>&1
echo "=== auto_continue.sh started: \$(date -u +%FT%TZ) (pid \$\$) ==="
trap 'echo "=== auto_continue.sh EXITING with code \$? at \$(date -u +%FT%TZ), last command: \${BASH_COMMAND} ==="' EXIT

echo "Watching import_day for completion (checking the DB, not tmux)..."
source .venv/bin/activate
while true; do
    remaining_days=\$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE status IN ('pending','running','failed')\"))
")
    echo "days still pending/running/failed: \$remaining_days"
    if [ "\$remaining_days" -eq 0 ]; then
        echo "Discovery finished (confirmed via DB). Proceeding."
        break
    fi
    sleep 30
done

# Deliberately not touching any leftover discover-all.sh tmux session here:
# calling tmux send-keys / kill-session from inside this script killed the
# *entire* tmux server twice in a row (taking this watcher session down with
# it, mid-script). Not worth the risk -- if a stale "harvest" session is
# still sitting at "Press enter to close.", it's harmless and can be closed
# manually later.

if [ -d "\$VOLUME_PATH" ] && [ ! -L "$REMOTE_DIR/data" ]; then
    echo "Moving data/ onto \$VOLUME_PATH ..."
    mkdir -p "\$VOLUME_PATH/shab-data"
    rsync -av "$REMOTE_DIR/data/" "\$VOLUME_PATH/shab-data/"
    rm -rf "$REMOTE_DIR/data"
    ln -s "\$VOLUME_PATH/shab-data" "$REMOTE_DIR/data"
    echo "Moved. $REMOTE_DIR/data is now a symlink to \$VOLUME_PATH/shab-data."
else
    echo "Volume not present or data/ already a symlink — skipping move."
fi

echo "Starting scrape-all ..."
cd "$REMOTE_DIR"
source .venv/bin/activate
while true; do
  python -m shab_harvester.app scrape-pending --limit 500 --headless
  remaining=\$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='pending' OR (status='failed' AND attempt_count<3)\"))
")
  echo "remaining: \$remaining"
  [ "\$remaining" -eq 0 ] && break
done

echo "=== AUTO_CONTINUE_DONE (discover -> move -> scrape all finished) ==="
INNER

chmod +x "$REMOTE_DIR/auto_continue.sh"
tmux new-session -d -s "$WATCHER_SESSION" "$REMOTE_DIR/auto_continue.sh; echo; echo 'Press enter to close.'; read"
echo "Started watcher in tmux session '$WATCHER_SESSION'. It will move data + start scraping automatically once discovery finishes."
EOF
