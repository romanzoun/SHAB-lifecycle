#!/usr/bin/env bash
# Runs export-data on the server, then downloads the resulting zip to this
# Mac's data/exports/. Safe, non-destructive, can be run anytime (even
# while discover-all.sh/scrape-all.sh are running in tmux).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

echo "==> Running export-data on the server ..."
zip_name=$("${SSH[@]}" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate
python -m shab_harvester.app export-data 1>&2
ls -t data/exports/shab_export_*.zip | head -n 1
EOF
)
zip_name=$(basename "$zip_name")

echo "==> Downloading $zip_name ..."
mkdir -p "$LOCAL_PROJECT_ROOT/data/exports"
scp -i "$SSH_KEY" "$SERVER:$REMOTE_DIR/data/exports/$zip_name" "$LOCAL_PROJECT_ROOT/data/exports/"

echo "==> Done: $LOCAL_PROJECT_ROOT/data/exports/$zip_name"
