#!/usr/bin/env bash
# One-time (or repeatable) setup on the server: syncs code, installs deps
# and Chromium, then runs init-db (idempotent — safe to re-run any time,
# e.g. after a code update).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

echo "==> Syncing code to $SERVER:$REMOTE_DIR ..."
rsync -av \
  --exclude '.venv' --exclude 'data/' --exclude 'data' \
  --exclude '__pycache__' --exclude '.git' --exclude '.DS_Store' \
  --exclude '.env' \
  -e "ssh -i $SSH_KEY" \
  "$LOCAL_PROJECT_ROOT/" "$SERVER:$REMOTE_DIR/"

echo "==> Installing dependencies and running init-db on the server ..."
"${SSH[@]}" bash -s <<EOF
set -euo pipefail
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip tmux

cd "$REMOTE_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
playwright install --with-deps chromium

[ -f .env ] || cp .env.example .env
python -m shab_harvester.app init-db
EOF

echo "==> Setup done. DB initialized on the server."
