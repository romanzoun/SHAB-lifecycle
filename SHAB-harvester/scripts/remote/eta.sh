#!/usr/bin/env bash
# Estimates remaining scrape time based on the most recently scraped
# publications' timestamps (not a fixed assumption — recomputed fresh every
# time you run this, so it adapts as the rate speeds up/slows down).
# Read-only, safe to run anytime.
#
# Usage: ./eta.sh [SAMPLE_SIZE]   (default: last 500 scraped publications)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

SAMPLE="${1:-500}"

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate

python3 -c '
from datetime import datetime, timezone

from shab_harvester import db

with db.connect() as conn:
    total = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue")
    scraped = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = ?", ("scraped",))
    failed = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status = ?", ("failed",))
    remaining = total - scraped

    rows = conn.execute(
        "SELECT scraped_at FROM shab_publication_raw ORDER BY scraped_at DESC LIMIT ?", ($SAMPLE,)
    ).fetchall()

    print("scraped: {}/{} ({:.1f}%)  failed: {}  remaining: {}".format(
        scraped, total, (scraped / total * 100) if total else 0, failed, remaining
    ))

    if len(rows) < 2:
        print("Not enough scraped publications yet to estimate a rate.")
    else:
        newest = datetime.fromisoformat(rows[0]["scraped_at"].replace("Z", "+00:00"))
        oldest = datetime.fromisoformat(rows[-1]["scraped_at"].replace("Z", "+00:00"))
        elapsed = (newest - oldest).total_seconds()
        sample_count = len(rows) - 1

        if elapsed <= 0:
            print("Sample window too short to estimate a rate yet.")
        else:
            rate_per_sec = sample_count / elapsed
            print("Rate (last {} scraped): {:.2f}/s = {:.0f}/min = {:.0f}/hour".format(
                sample_count, rate_per_sec, rate_per_sec * 60, rate_per_sec * 3600
            ))

            if rate_per_sec > 0:
                eta_seconds = remaining / rate_per_sec
                days = int(eta_seconds // 86400)
                hours = int((eta_seconds % 86400) // 3600)
                minutes = int((eta_seconds % 3600) // 60)
                finish = datetime.now(timezone.utc).timestamp() + eta_seconds
                finish_str = datetime.fromtimestamp(finish, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                print("ETA: {}d {}h {}m remaining  (finishes around {})".format(
                    days, hours, minutes, finish_str
                ))
'
EOF
