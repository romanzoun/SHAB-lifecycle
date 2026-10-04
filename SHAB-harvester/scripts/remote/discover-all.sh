#!/usr/bin/env bash
# Starts the full discover run (2018-09-03 -> today, quarter by quarter) on
# the server inside tmux, detached, and returns immediately. Check progress
# with status.sh or still-running.sh; it keeps running after this script
# (and your SSH connection) exits.
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

cat > "$REMOTE_DIR/discover_all.sh" <<'INNER'
#!/usr/bin/env bash
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate

QUARTERS=(
  "2018-09-03:2018-12-31"
  "2019-01-01:2019-03-31" "2019-04-01:2019-06-30" "2019-07-01:2019-09-30" "2019-10-01:2019-12-31"
  "2020-01-01:2020-03-31" "2020-04-01:2020-06-30" "2020-07-01:2020-09-30" "2020-10-01:2020-12-31"
  "2021-01-01:2021-03-31" "2021-04-01:2021-06-30" "2021-07-01:2021-09-30" "2021-10-01:2021-12-31"
  "2022-01-01:2022-03-31" "2022-04-01:2022-06-30" "2022-07-01:2022-09-30" "2022-10-01:2022-12-31"
  "2023-01-01:2023-03-31" "2023-04-01:2023-06-30" "2023-07-01:2023-09-30" "2023-10-01:2023-12-31"
  "2024-01-01:2024-03-31" "2024-04-01:2024-06-30" "2024-07-01:2024-09-30" "2024-10-01:2024-12-31"
  "2025-01-01:2025-03-31" "2025-04-01:2025-06-30" "2025-07-01:2025-09-30" "2025-10-01:2025-12-31"
  "2026-01-01:2026-03-31" "2026-04-01:2026-06-24"
)

for q in "\${QUARTERS[@]}"; do
  from="\${q%%:*}"
  to="\${q##*:}"
  echo "=== discovering \$from .. \$to ==="
  python -m shab_harvester.app seed-days --from "\$from" --to "\$to"
  python -m shab_harvester.app discover-pending-days --headless
done

echo "=== DISCOVER_ALL_DONE ==="
INNER

chmod +x "$REMOTE_DIR/discover_all.sh"

tmux new-session -d -s "$TMUX_SESSION" "$REMOTE_DIR/discover_all.sh; echo; echo 'Press enter to close.'; read"
echo "Started discover-all in tmux session '$TMUX_SESSION' on the server."
EOF
