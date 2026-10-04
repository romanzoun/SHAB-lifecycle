#!/usr/bin/env bash
# Shared GitHub HTTPS auth helpers (.env.git). Source from other scripts — do not run directly.

_git_env_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

load_github_token() {
  local root
  root="$(_git_env_root)"
  cd "${root}"

  if [[ -f "${root}/.env.git" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${root}/.env.git"
    set +a
  fi

  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "ERROR: GITHUB_TOKEN fehlt. Kopiere .env.git.example nach .env.git und trage dein Token ein." >&2
    return 1
  fi
}

github_token_remote_url() {
  local remote_url repo_path

  remote_url="$(git remote get-url origin)"
  if [[ "${remote_url}" != https://github.com/* ]]; then
    echo "ERROR: \`git remote get-url origin\` ist kein https://github.com/... (${remote_url})." >&2
    return 1
  fi

  repo_path="${remote_url#https://github.com/}"
  printf 'https://x-access-token:%s@github.com/%s' "${GITHUB_TOKEN}" "${repo_path}"
}
