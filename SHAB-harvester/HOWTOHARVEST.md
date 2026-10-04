# HOWTOHARVEST

Runbook for harvesting SHAB publications end-to-end on a server (e.g. a VPS),
from a fresh checkout to a full export. Written for `root@<your-server>` over
SSH, but every command works locally too — just drop the SSH wrapper.

## 0. Prerequisites on a fresh server

```bash
ssh -i ~/.ssh/hetzner_prod root@<server-ip>

apt-get update
apt-get install -y python3-venv python3-pip git

# Put the project somewhere isolated, away from other services on the box.
mkdir -p /opt/shab-harvester
cd /opt/shab-harvester
# transfer the code, e.g. from your machine:
#   rsync -av -e "ssh -i ~/.ssh/hetzner_prod" /local/path/SHAB-harvester/ root@<server-ip>:/opt/shab-harvester/

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Installs Chromium *and* the system libraries it needs (apt packages) —
# required on a headless server, this is the slow step.
playwright install --with-deps chromium
```

Copy `.env.example` to `.env` and adjust if needed (see [README.md](README.md#configuration)
for the full parameter list). On a long unattended multi-day run, prefer
**not** lowering `SHAB_SCRAPE_PAUSE_MIN/MAX` much below the defaults — nobody
is there to react if shab.ch starts rate-limiting you.

```bash
cp .env.example .env
```

**Always use `--headless`** on a server — there's no display to show a real
browser window.

## 1. Keep long jobs alive across SSH disconnects

Discovering/scraping years of data takes hours to days. Run it inside
`tmux` (or `screen`), not directly in your SSH session, so it survives a
dropped connection:

```bash
tmux new -s harvest
# ... run commands below inside this session ...
# detach without killing it: Ctrl-b then d
# reattach later:
tmux attach -t harvest
```

## 2. Init DB

Once, idempotent — safe to re-run any time (e.g. after pulling an update
that added new tables):

```bash
cd /opt/shab-harvester
source .venv/bin/activate
python -m shab_harvester.app init-db
```

## 3. Discover Segment — quarterly, 2018-09-03 to 2021-12-31

Discovery only finds which shab-ids exist for each day and queues them — it
does **not** download content yet. Doing it in quarter-sized chunks means
you always know exactly how far you've gotten, and a crash only costs you
the current chunk, not the whole range.

Each chunk is `seed-days` (cheap, just creates `import_day` placeholders)
followed by `discover-pending-days` (the actual browser-driven search):

```bash
# 2018 remainder
python -m shab_harvester.app seed-days --from 2018-09-03 --to 2018-12-31
python -m shab_harvester.app discover-pending-days --headless

# 2019
python -m shab_harvester.app seed-days --from 2019-01-01 --to 2019-03-31
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2019-04-01 --to 2019-06-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2019-07-01 --to 2019-09-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2019-10-01 --to 2019-12-31
python -m shab_harvester.app discover-pending-days --headless

# 2020
python -m shab_harvester.app seed-days --from 2020-01-01 --to 2020-03-31
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2020-04-01 --to 2020-06-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2020-07-01 --to 2020-09-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2020-10-01 --to 2020-12-31
python -m shab_harvester.app discover-pending-days --headless

# 2021
python -m shab_harvester.app seed-days --from 2021-01-01 --to 2021-03-31
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2021-04-01 --to 2021-06-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2021-07-01 --to 2021-09-30
python -m shab_harvester.app discover-pending-days --headless

python -m shab_harvester.app seed-days --from 2021-10-01 --to 2021-12-31
python -m shab_harvester.app discover-pending-days --headless
```

`discover-pending-days` only processes days with `status` `pending` or
`failed`, so re-running any of these lines after an interruption is always
safe — already-discovered days are skipped automatically.

**Check progress after each chunk:**

```bash
python -m shab_harvester.app status
```

`import_day by status` should show the chunk's days moving from `pending` to
`discovered`/`empty`. If you ever see a `result_count` of exactly
`2703514`, that's a known SHAB-search edge case (the date-filtered API
response didn't land before the count was read) — just re-run
`discover-day --date <that day>` for it; see `read_filtered_total` in
`shab_harvester/discovery.py` for the full explanation.

If a run got killed mid-day (status stuck on `running`), recover it first:

```bash
python -m shab_harvester.app reset-failed
```

## 4. Scrape everything

This is the slow, polite part — one detail page at a time, with a pause
between each (see `.env`). It only ever touches `publication_queue` rows
that are `pending` or `failed` (with attempts left), so you can run it
repeatedly in batches until nothing is left:

```bash
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
```

If a run aborts after repeated rate-limiting (`Aborting run after repeated
rate limiting.` in the output), stop and wait a while before resuming — the
loop above will just pick up where it left off once you restart it.

Check progress any time:

```bash
python -m shab_harvester.app status
python -m shab_harvester.app verify-day --date 2019-03-15   # spot-check a specific day
```

## 5. Analyze (optional — builds the organization/case/person aggregation)

```bash
python -m shab_harvester.app analyze
```

Re-running this is idempotent (only newly-scraped publications are
processed). Use `--force` to fully rebuild after a heuristic change in
`shab_harvester/analysis.py`.

## 6. Export the result

```bash
python -m shab_harvester.app export-data
```

Writes a timestamped zip to `data/exports/shab_export_<timestamp>.zip`
(DB + raw_html + raw_xml). Pull it down to your own machine:

```bash
# from your local machine, not the server:
scp -i ~/.ssh/hetzner_prod \
  root@<server-ip>:/opt/shab-harvester/data/exports/shab_export_*.zip \
  ./
```

`export-data` never deletes anything — safe to run at any point, including
mid-harvest, to checkpoint progress.

## 7. Watching it live via the dashboard (optional)

The webui binds to `127.0.0.1` by default, so it's not reachable directly
over the internet (good — don't expose it publicly). Tunnel it through SSH
instead:

```bash
# on your local machine:
ssh -i ~/.ssh/hetzner_prod -L 8765:127.0.0.1:8765 root@<server-ip>

# on the server, in another tmux pane:
cd /opt/shab-harvester && source .venv/bin/activate
python -m shab_harvester.app webui
```

Then open `http://127.0.0.1:8765/harvest` locally — it talks to the
server's dashboard through the tunnel. Note: the **Harvest** screen's
buttons start real Playwright jobs *on the server*, sharing CPU/network with
whatever you're running in tmux; the **Analyse** screen is read-only and
safe to use anytime.

If you change `.env` or pull code updates while the dashboard is running,
restart the `webui` process (Ctrl-C, run again) — it doesn't hot-reload.

## 8. Starting over / undoing a bad run

```bash
scripts/export.sh                              # back up first if in doubt
scripts/delete.sh --yes                        # wipes DB + raw_html + raw_xml
scripts/import.sh data/exports/<file>.zip --yes  # restore from a backup
```

See [README.md](README.md#data-lifecycle-export--delete--import) for details.
