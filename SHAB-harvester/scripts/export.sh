#!/usr/bin/env bash
# Zips the database and all downloaded raw_html/raw_xml files into
# data/exports/shab_export_<timestamp>.zip. Safe, non-destructive.
set -euo pipefail
cd "$(dirname "$0")/.."

python -m shab_harvester.app export-data
