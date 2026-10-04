#!/usr/bin/env bash
# Re-discover the recent window with ID accumulation, then scrape new pubs.
set -uo pipefail
cd /opt/shab-harvester
mkdir -p logs
exec > >(tee -a logs/rediscover_recent.log) 2>&1
echo "=== rediscover_recent started $(date -u +%FT%TZ) ==="
exec 9>/var/lock/shab-harvest.lock
if ! flock -n 9; then
  echo "lock busy"
  exit 1
fi
source .venv/bin/activate
export SHAB_SCROLL_WAIT_MS="${SHAB_SCROLL_WAIT_MS:-700}"
python -m shab_harvester.app discover-pending-days --headless
python3 - <<'PY'
from shab_harvester import db
with db.connect() as conn:
    rows = conn.execute("""
        SELECT publication_date, status, discovered_count, result_count, last_error
        FROM import_day WHERE publication_date >= '2026-09-14'
        ORDER BY publication_date
    """).fetchall()
    for r in rows:
        print(f"{r['publication_date']} {r['status']} {r['discovered_count']}/{r['result_count']} {r['last_error']}")
PY
echo "=== scrape ==="
while true; do
  python -m shab_harvester.app scrape-pending --limit 500 --headless || echo "scrape failed"
  remaining=$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='pending' OR (status='failed' AND attempt_count<3)\"))
")
  echo "remaining: $remaining"
  [ "$remaining" -eq 0 ] && break
done
echo "=== REDISCOVER_RECENT_DONE ==="
