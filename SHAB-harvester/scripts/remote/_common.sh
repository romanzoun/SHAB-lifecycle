#!/usr/bin/env bash
# Shared config for the scripts/remote/*.sh scripts. Sourced, not run directly.
SSH_KEY="$HOME/.ssh/hetzner_prod"
SERVER="root@46.225.119.148"
REMOTE_DIR="/opt/shab-harvester"
TMUX_SESSION="harvest"

SSH=(ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$SERVER")

LOCAL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
