# Step-by-step: this Mac → 46.225.119.148

Concrete, copy-pasteable commands for *your* exact setup. Generic
explanations are in [HOWTOHARVEST.md](HOWTOHARVEST.md) — this file is just
"run this, then this".

- Local project: `/Users/romanzoun/business/SHAB-lifecycle/SHAB-harvester`
- Server: `root@46.225.119.148`, key `~/.ssh/hetzner_prod`
- Remote project path: `/opt/shab-harvester`

---

## A. On this Mac — ship the code

```bash
rsync -av --exclude '.venv' --exclude 'data/shab_harvester.sqlite' \
  --exclude 'data/raw_html' --exclude 'data/raw_xml' --exclude '__pycache__' \
  -e "ssh -i ~/.ssh/hetzner_prod" \
  /Users/romanzoun/business/SHAB-lifecycle/SHAB-harvester/ \
  root@46.225.119.148:/opt/shab-harvester/
```

(Excludes your local DB/raw files/venv — the server gets a fresh, empty
`data/` and builds its own venv. Re-run this same command any time you want
to push code changes later.)

## B. On the server — one-time setup

```bash
ssh -i ~/.ssh/hetzner_prod root@46.225.119.148
```

Then, on the server:

```bash
apt-get update
apt-get install -y python3-venv python3-pip

cd /opt/shab-harvester
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium   # slow — installs Chromium + system libs

cp .env.example .env
python -m shab_harvester.app init-db
```

## C. On the server — start the harvest in tmux

```bash
tmux new -s harvest
cd /opt/shab-harvester
source .venv/bin/activate
```

Discover, quarter by quarter, 2018-09-03 → 2026-06-24 — **one command**, runs
all 31 chunks, then scrapes everything found, then loops the scrape until
the queue is empty. Paste this whole block as-is:

```bash
QUARTERS=(
  "2018-09-03:2018-12-31"
  "2019-01-01:2019-03-31" "2019-04-01:2019-06-30" "2019-07-01:2019-09-30" "2019-10-01:2019-12-31"
  "2020-01-01:2020-03-31" "2020-04-01:2020-06-30" "2020-07-01:2020-09-30" "2020-10-01:2020-12-31"
  "2021-01-01:2021-03-31" "2021-04-01:2021-06-30" "2021-07-01:2021-09-30" "2021-10-01:2021-12-31"
  "2022-01-01:2022-03-31" "2022-04-01:2022-06-30" "2022-07-01:2022-09-30" "2022-10-01:2022-12-31"
  "2023-01-01:2023-03-31" "2023-04-01:2023-06-30" "2023-07-01:2023-09-30" "2023-10-01:2023-12-31"
  "2024-01-01:2024-03-31" "2024-04-01:2024-06-30" "2024-07-01:2024-09-30" "2024-10-01:2024-12-31"
  "2025-01-01:2025-03-31" "2025-04-01:2025-06-30" "2025-07-01:2025-09-30" "2025-10-01:2025-12-31"
  "2026-01-01:2026-03-31" "2026-04-01:2026-06-24"
)

for q in "${QUARTERS[@]}"; do
  from="${q%%:*}"
  to="${q##*:}"
  echo "=== discovering $from .. $to ==="
  python -m shab_harvester.app seed-days --from "$from" --to "$to"
  python -m shab_harvester.app discover-pending-days --headless
done

echo "=== discovery done, now scraping everything ==="
while true; do
  python -m shab_harvester.app scrape-pending --limit 500 --headless
  remaining=$(python3 -c "
from shab_harvester import db
with db.connect() as conn:
    print(db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='pending' OR (status='failed' AND attempt_count<3)\"))
")
  echo "remaining: $remaining"
  [ "$remaining" -eq 0 ] && break
done
echo "=== all done ==="
```

**Detach and walk away:** `Ctrl-b` then `d` (do **not** type `exit`). Close
your laptop, close the terminal — it keeps running on the server.

## D. Coming back later — checking progress

Reattach to watch it live:

```bash
ssh -i ~/.ssh/hetzner_prod root@46.225.119.148
tmux attach -t harvest
```

Or, without disturbing the running session, open a **second** SSH connection
and just query the state:

```bash
ssh -i ~/.ssh/hetzner_prod root@46.225.119.148
cd /opt/shab-harvester && source .venv/bin/activate
python -m shab_harvester.app status
```

What the numbers mean:

```
import_day by status:
  discovered: 320      <- days where the SHAB search ran and found hits, queued
  empty: 210            <- days searched, genuinely 0 publications (weekends etc.)
  pending: 700          <- days seeded but not yet searched
  failed: 3             <- days where discovery crashed (retry with reset-failed)
publication_queue by status:
  scraped: 4500          <- publications fully downloaded (metadata+HTML+XML)
  pending: 12000         <- publications found but not yet downloaded
  failed: 12             <- download attempts that errored (auto-retried up to 3x)
shab_publication_raw total: 4500   <- actual rows with full content (== scraped above)
```

**"How many of how many days are done" for the whole 2018-09-03→2026-06-24
range specifically:**

```bash
python3 -c "
from shab_harvester import db
with db.connect() as conn:
    total = db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE publication_date BETWEEN '2018-09-03' AND '2026-06-24'\")
    done = db.scalar(conn, \"SELECT COUNT(*) FROM import_day WHERE publication_date BETWEEN '2018-09-03' AND '2026-06-24' AND status IN ('discovered','empty','completed')\")
    print(f'{done}/{total} days discovered')
"
```

**"How many publications scraped vs found, as a percentage":**

```bash
python3 -c "
from shab_harvester import db
with db.connect() as conn:
    total = db.scalar(conn, 'SELECT COUNT(*) FROM publication_queue')
    scraped = db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='scraped'\")
    failed = db.scalar(conn, \"SELECT COUNT(*) FROM publication_queue WHERE status='failed'\")
    pct = round(scraped / total * 100, 1) if total else 0
    print(f'{scraped}/{total} scraped ({pct}%), {failed} failed')
"
```

Or, for a single specific day's detail (matches `result_count` vs what's
actually in the queue/downloaded so far):

```bash
python -m shab_harvester.app verify-day --date 2019-03-15
python -m shab_harvester.app day-overview --date 2019-03-15 --status failed
```

**Dashboard view (optional)**, from your Mac, in a separate terminal — keep
this open as long as you want, it's read-only and doesn't interfere with
the harvest:

```bash
ssh -i ~/.ssh/hetzner_prod -L 8765:127.0.0.1:8765 root@46.225.119.148
# then, on the server in a third pane/session:
cd /opt/shab-harvester && source .venv/bin/activate && python -m shab_harvester.app webui
```

Open `http://127.0.0.1:8765/analyse` locally.

## E. When it's all done — pull the data back to this Mac

On the server:

```bash
python -m shab_harvester.app export-data
```

On this Mac:

```bash
scp -i ~/.ssh/hetzner_prod \
  root@46.225.119.148:/opt/shab-harvester/data/exports/shab_export_*.zip \
  /Users/romanzoun/business/SHAB-lifecycle/SHAB-harvester/data/exports/
```

Then locally:

```bash
cd /Users/romanzoun/business/SHAB-lifecycle/SHAB-harvester
source .venv/bin/activate
python -m shab_harvester.app import-data --zip data/exports/<the-file>.zip --yes
```
