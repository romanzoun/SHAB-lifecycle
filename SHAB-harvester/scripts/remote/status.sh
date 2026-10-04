#!/usr/bin/env bash
# Shows current harvest status on the server: the standard `status` output,
# plus "days discovered" and "publications scraped" as clean X/Y (Z%).
# Read-only — safe to run anytime, including while discover-all.sh /
# scrape-all.sh are running in tmux.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./_common.sh

"${SSH[@]}" bash -s <<EOF
set -euo pipefail
cd "$REMOTE_DIR"
source .venv/bin/activate

python -m shab_harvester.app status
echo

python3 -c "
from shab_harvester import db
with db.connect() as conn:
    total_days = db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE publication_date BETWEEN '2018-09-03' AND '2026-06-24'\")
    done_days = db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE publication_date BETWEEN '2018-09-03' AND '2026-06-24' AND status IN ('discovered','empty','completed')\")
    days_pct = round(done_days / total_days * 100, 1) if total_days else 0

    total_pub = db.scalar(conn, 'SELECT COUNT(*) FROM publication_queue')
    scraped_pub = db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='scraped'\")
    failed_pub = db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='failed'\")
    running_pub = db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='running'\")
    pub_pct = round(scraped_pub / total_pub * 100, 1) if total_pub else 0

    print(f'Days discovered (2018-09-03..2026-06-24): {done_days}/{total_days} ({days_pct}%)')
    print(f'Publications scraped: {scraped_pub}/{total_pub} ({pub_pct}%)  failed={failed_pub}  running={running_pub}')
"
EOF
