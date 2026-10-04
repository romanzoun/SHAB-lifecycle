#!/usr/bin/env bash
# Runs ON THE SERVER as /opt/shab-harvester/daily_catchup.sh
# Catch-up from last done day (min overlap 1 day) to today (Europe/Zurich).
#
# Guarantee for the catch-up window [FROM, TO]:
#   no shortfall days (result_count > discovered_count) before scrape finishes.
# Historical shortfalls outside the window are left alone (separate rediscover).
set -uo pipefail
cd /opt/shab-harvester
mkdir -p logs

SLOT_HOUR=$(TZ=Europe/Zurich date +%H)
if [ "$SLOT_HOUR" -lt 12 ]; then
  SLOT=morning
else
  SLOT=evening
fi

exec > >(tee -a logs/daily_catchup.log) 2>&1
STARTED_EPOCH=$(date +%s)
echo "=== daily_catchup STARTED $(date -u +%FT%TZ) slot=$SLOT pid=$$ ==="
trap 'echo "=== daily_catchup EXITING code=$? at $(date -u +%FT%TZ) slot=$SLOT ==="' EXIT

exec 9>/var/lock/shab-harvest.lock
if ! flock -n 9; then
  echo "already running (flock busy) — skip"
  exit 0
fi
echo "Acquired shab-harvest.lock"

source .venv/bin/activate

TO=$(TZ=Europe/Zurich date +%F)
FROM=$(python3 - <<PY
from datetime import date, timedelta
from shab_harvester import db
today = date.fromisoformat("$TO")
yesterday = (today - timedelta(days=1)).isoformat()
with db.connect() as conn:
    last = db.scalar(
        conn,
        "SELECT MAX(publication_date) FROM import_day "
        "WHERE status IN ('discovered','empty','completed')"
    )
if not last:
    print(yesterday)
else:
    # Overlap the last done day when caught up. If that day is behind
    # yesterday, start there so missed days are not skipped.
    print(min(last, yesterday))
PY
)
echo "Range: $FROM .. $TO"

t0=$(date +%s)
python3 - <<PY
from shab_harvester import db
from shab_harvester.utils import now_iso
from_date, to_date = "$FROM", "$TO"
with db.connect() as conn:
    ts = now_iso()
    cur = conn.execute(
        "UPDATE import_day SET status='pending', last_error=NULL, updated_at=? "
        "WHERE status IN ('running','failed') "
        "AND publication_date BETWEEN ? AND ?",
        (ts, from_date, to_date),
    )
    print(f"reset_stuck_days_in_range={cur.rowcount}")
    # Re-open incomplete discovery inside the catch-up window only
    cur2 = conn.execute(
        """
        UPDATE import_day
        SET status='pending', last_error=NULL, updated_at=?
        WHERE publication_date BETWEEN ? AND ?
          AND result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (ts, from_date, to_date),
    )
    print(f"reset_shortfall_days_in_range={cur2.rowcount}")
    n = db.archive_exhausted_failures(conn)
    print(f"archived_non_public={n}")
    conn.commit()
PY

echo "=== seed-days $FROM .. $TO ==="
python -m shab_harvester.app seed-days --from "$FROM" --to "$TO"
SEED_S=$(( $(date +%s) - t0 ))

t1=$(date +%s)
echo "=== discover until no shortfall in range ==="
MAX_DISC_ATTEMPTS=10
for attempt in $(seq 1 "$MAX_DISC_ATTEMPTS"); do
  echo "--- discover attempt $attempt ---"
  python -m shab_harvester.app discover-pending-days --headless || echo "discover exited non-zero"

  stats=$(python3 - <<PY
from shab_harvester import db
from shab_harvester.utils import now_iso
from_date, to_date = "$FROM", "$TO"
with db.connect() as conn:
    ts = now_iso()
    conn.execute(
        "UPDATE import_day SET status='pending', last_error=NULL, updated_at=? "
        "WHERE status IN ('running','failed') AND publication_date BETWEEN ? AND ?",
        (ts, from_date, to_date),
    )
    cur = conn.execute(
        """
        UPDATE import_day
        SET status='pending', last_error=NULL, updated_at=?
        WHERE publication_date BETWEEN ? AND ?
          AND result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (ts, from_date, to_date),
    )
    requeued = cur.rowcount
    pending = db.scalar(
        conn,
        "SELECT COUNT(*) FROM import_day WHERE status='pending' "
        "AND publication_date BETWEEN ? AND ?",
        (from_date, to_date),
    )
    shortfall = db.scalar(
        conn,
        """
        SELECT COUNT(*) FROM import_day
        WHERE publication_date BETWEEN ? AND ?
          AND result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (from_date, to_date),
    )
    conn.commit()
    print(f"{requeued} {pending} {shortfall}")
PY
)
  set -- $stats
  requeued=$1; pending=$2; shortfall=$3
  echo "requeued_shortfall=$requeued pending_in_range=$pending shortfall_in_range=$shortfall"
  if [ "$pending" = "0" ] && [ "$shortfall" = "0" ]; then
    echo "Discover window clean (no pending, no shortfall)."
    break
  fi
  if [ "$attempt" -eq "$MAX_DISC_ATTEMPTS" ]; then
    echo "ERROR: shortfall/pending remain in $FROM..$TO after $MAX_DISC_ATTEMPTS attempts — refusing to treat catch-up as complete"
    echo "pending=$pending shortfall=$shortfall"
    exit 1
  fi
  sleep 3
done
DISC_S=$(( $(date +%s) - t1 ))

t2=$(date +%s)
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
SCRAPE_S=$(( $(date +%s) - t2 ))

python3 - <<PY
from shab_harvester import db
from_date, to_date = "$FROM", "$TO"
with db.connect() as conn:
    n = db.archive_exhausted_failures(conn)
    conn.commit()
    shortfall = db.scalar(
        conn,
        """
        SELECT COUNT(*) FROM import_day
        WHERE publication_date BETWEEN ? AND ?
          AND result_count IS NOT NULL
          AND result_count > COALESCE(discovered_count, 0)
        """,
        (from_date, to_date),
    )
    print(f"archived_non_public_final={n}")
    print(f"shortfall_in_range_after_scrape={shortfall}")
    q = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue")
    s = db.scalar(conn, "SELECT COUNT(*) FROM publication_queue WHERE status='scraped'")
    np = db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_non_public")
    print(f"queue={q} scraped={s} non_public={np}")
    if shortfall:
        raise SystemExit(f"REFUSING DONE: {shortfall} shortfall day(s) still in {from_date}..{to_date}")
PY

TOTAL_S=$(( $(date +%s) - STARTED_EPOCH ))
echo "=== FINISHED slot=$SLOT seed_s=$SEED_S discover_s=$DISC_S scrape_s=$SCRAPE_S total_s=$TOTAL_S ==="
echo "=== DAILY_CATCHUP_DONE (window clean, no shortfall) ==="
