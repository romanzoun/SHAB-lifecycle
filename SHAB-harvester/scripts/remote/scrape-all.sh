#!/usr/bin/env bash
# Starts scraping everything currently pending in publication_queue on the
# server inside tmux, detached, looping in batches until the queue is
# empty. Returns immediately; keeps running after this script exits.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "tmux session '$TMUX_SESSION' is already running on the server."
    echo "Attach with: ssh -i $SSH_KEY $SERVER -t tmux attach -t $TMUX_SESSION"
    exit 1
fi

cat > "$REMOTE_DIR/scrape_all.sh" <<'INNER'
#!/usr/bin/env bash
set -euo pipefail
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

echo "=== SCRAPE_ALL_DONE ==="
INNER

chmod +x "$REMOTE_DIR/scrape_all.sh"

tmux new-session -d -s "$TMUX_SESSION" "$REMOTE_DIR/scrape_all.sh; echo; echo 'Press enter to close.'; read"
echo "Started scrape-all in tmux session '$TMUX_SESSION' on the server."
EOF
