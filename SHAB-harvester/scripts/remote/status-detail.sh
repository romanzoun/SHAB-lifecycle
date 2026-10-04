#!/usr/bin/env bash
# Lists the most recently processed days with their SHAB notification count
# (result_count), scrape progress, and failed queue items. Read-only, safe
# to run anytime.
#
# Usage: ./status-detail.sh [N]   (default: last 20 days, by most recently
# touched first — i.e. wherever discovery/scraping currently is)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

N="${1:-20}"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate

python3 -c '
from shab_harvester import db

with db.connect() as conn:
    rows = conn.execute(
        "SELECT d.publication_date, d.status, d.result_count, d.discovered_count, d.scraped_count, "
        "d.updated_at, "
        "(SELECT COUNT(*) FROM publication_queue q "
        " WHERE q.publication_date = d.publication_date AND q.status = ?) AS failed_count "
        "FROM import_day d ORDER BY d.updated_at DESC LIMIT ?",
        ("failed", $N),
    ).fetchall()

    if not rows:
        print("No import_day rows yet.")
    else:
        print("{:<12} {:<11} {:>13} {:>9} {:>8}  last touched".format(
            "date", "status", "notifications", "scraped", "failed"
        ))
        for r in rows:
            notifications = r["result_count"] if r["result_count"] is not None else "-"
            print("{:<12} {:<11} {!s:>13} {:>9} {:>8}  {}".format(
                r["publication_date"], r["status"], notifications,
                r["scraped_count"], r["failed_count"], r["updated_at"]
            ))
'
EOF
