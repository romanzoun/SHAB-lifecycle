#!/usr/bin/env bash
# Checks whether discover-all.sh / scrape-all.sh is still active in tmux on
# the server, and shows the last few lines of its output without attaching
# (so it doesn't interfere with the session).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
    echo "RUNNING: tmux session '$TMUX_SESSION' is active."
    echo "--- last output ---"
    tmux capture-pane -t "$TMUX_SESSION" -p | tail -n 15
else
    echo "NOT RUNNING: no tmux session '$TMUX_SESSION' on the server."
fi
EOF
