#!/usr/bin/env bash
# Deletes the entire database and all downloaded raw_html/raw_xml files,
# then re-initializes an empty schema. Irreversible (run scripts/export.sh
# first if you want a backup — exports live outside data/raw_html|raw_xml
# and the DB file, so they survive this).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" != "--yes" ]; then
    echo "This deletes the entire database and all downloaded raw_html/raw_xml files."
    echo "Re-run as: scripts/delete.sh --yes"
    exit 1
fi

python -m shab_harvester.app reset-all --yes
