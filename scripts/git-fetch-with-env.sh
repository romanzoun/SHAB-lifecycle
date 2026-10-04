#!/usr/bin/env bash
# Fetch von origin per HTTPS unter Nutzung von GITHUB_TOKEN aus .env.git (nicht in Git speichern).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

# shellcheck disable=SC1091
source "${ROOT}/scripts/git-token-common.sh"
load_github_token

FETCH_URL="$(github_token_remote_url)"

REF_ARGS=( "$@" )
if (( ${#REF_ARGS[@]} > 0 )) && [[ "${REF_ARGS[0]}" == "origin" ]]; then
  REF_ARGS=( "${REF_ARGS[@]:1}" )
fi

if (( ${#REF_ARGS[@]} == 0 )); then
  exec git fetch "${FETCH_URL}" "+refs/heads/*:refs/remotes/origin/*" --prune
fi

if [[ "${REF_ARGS[0]}" == "--all" ]]; then
  exec git fetch "${FETCH_URL}" "+refs/heads/*:refs/remotes/origin/*" --prune
fi

exec git fetch "${FETCH_URL}" "+refs/heads/${REF_ARGS[0]}:refs/remotes/origin/${REF_ARGS[0]}"
