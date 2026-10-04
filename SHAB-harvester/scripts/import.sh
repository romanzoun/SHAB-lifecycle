#!/usr/bin/env bash
# Restores the database and raw_html/raw_xml from a zip created by
# scripts/export.sh. Wipes whatever is currently there first. Irreversible.
# Usage: scripts/import.sh data/exports/shab_export_20260622-120000.zip --yes
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 1 ]; then
    echo "Usage: scripts/import.sh <path-to-export.zip> --yes"
    exit 1
fi

ZIP_PATH="$1"
shift

if [ "${1:-}" != "--yes" ]; then
    echo "This deletes whatever is currently in the database/raw files and replaces it with $ZIP_PATH."
    echo "Re-run as: scripts/import.sh $ZIP_PATH --yes"
    exit 1
fi

python -m shab_harvester.app import-data --zip "$ZIP_PATH" --yes
