#!/usr/bin/env bash
# Runs ON THE SERVER at /opt/shab-harvester/rediscover_shortfall.sh
set -uo pipefail
cd /opt/shab-harvester
mkdir -p logs
exec > >(tee -a logs/rediscover_shortfall.log) 2>&1
echo "=== rediscover_shortfall started: $(date -u +%FT%TZ) pid=$$ ==="
trap 'echo "=== rediscover_shortfall EXITING code=$? at $(date -u +%FT%TZ) ==="' EXIT

exec 9>/var/lock/shab-harvest.lock
if ! flock -n 9; then
  echo "ERROR: shab-harvest.lock busy — another harvest holds it"
  exit 1
fi
echo "Acquired shab-harvest.lock"

source .venv/bin/activate
export SHAB_SCROLL_MAX_ROUNDS="${SHAB_SCROLL_MAX_ROUNDS:-400}"
export SHAB_SCROLL_WAIT_MS="${SHAB_SCROLL_WAIT_MS:-1000}"
export SHAB_SCROLL_STABLE_ROUNDS="${SHAB_SCROLL_STABLE_ROUNDS:-5}"

for attempt in 1 2 3 4 5; do
  echo "=== discover attempt $attempt at $(date -u +%FT%TZ) ==="
  python -m shab_harvester.app discover-pending-days --headless || echo "discover exited non-zero"

  python3 - <<'PY'
from shab_harvester import db
from shab_harvester.utils import now_iso
with db.connect() as conn:
    cur = conn.execute(
        """
        UPDATE import_day
        SET status = 'pending', last_error = NULL, updated_at = ?
        WHERE result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (now_iso(),),
    )
    still = db.scalar(conn, "SELECT COUNT(*) FROM import_day WHERE status='pending'")
    short = db.scalar(conn, """
        SELECT COUNT(*) FROM import_day
        WHERE result_count IS NOT NULL AND result_count > COALESCE(discovered_count, 0)
    """)
    print(f"requeued_shortfall={cur.rowcount} pending={still} shortfall_days={short}")
    conn.commit()
PY

  remaining_pending=$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE status='pending'\"))
")
  echo "pending days left: $remaining_pending"
  [ "$remaining_pending" = "0" ] && break
  sleep 5
done

echo "=== scrape-pending until empty ==="
while true; do
  python -m shab_harvester.app scrape-pending --limit 500 --headless || echo "scrape batch failed, retrying..."
  remaining=$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='pending' OR (status='failed' AND attempt_count<3)\"))
")
  echo "remaining: $remaining"
  [ "$remaining" -eq 0 ] && break
  sleep 2
done

python3 - <<'PY'
from shab_harvester import db
with db.connect() as conn:
    q = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue")
    s = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status='scraped'")
    short = db.scalar(conn, """
        SELECT COUNT(*) FROM import_day
        WHERE result_count IS NOT NULL AND result_count > COALESCE(discovered_count, 0)
    """)
    miss = db.scalar(conn, """
        SELECT COALESCE(SUM(result_count - COALESCE(discovered_count,0)),0) FROM import_day
        WHERE result_count IS NOT NULL AND result_count > COALESCE(discovered_count, 0)
    """)
    print(f"FINAL queue={q} scraped={s} shortfall_days={short} est_missing={miss}")
PY
echo "=== REDISCOVER_SHORTFALL_DONE ==="
