# scripts/remote

Local scripts you run **on this Mac** that drive the harvester **on the
server** over SSH (`root@46.225.119.148`). Each one is a single command —
no manual SSH/tmux typing needed. They all share connection settings from
`_common.sh` (server IP, SSH key, remote path, tmux session name).

```bash
cd scripts/remote
./setup.sh           # one-time (or repeatable) install + init-db
./discover-all.sh    # start the 2018-09-03..today discover run, detached
./status.sh          # check progress, anytime
./status-detail.sh   # last N days, with notifications/scraped/failed per day
./eta.sh              # estimated time remaining for the current scrape run
./still-running.sh   # is a job still active?
./scrape-all.sh      # start scraping everything found, detached
./install-cron.sh    # install daily catch-up cron (06:00 + 18:00 Zurich)
./catchup-report.sh  # show recent daily_catchup durations
./rediscover-shortfall.sh  # backfill incomplete discovery days
./export.sh          # back up DB + raw files, download the zip to this Mac
```

All scripts must be run from inside `scripts/remote/` (they `cd` to their
own directory first, so running them via a full path also works:
`./scripts/remote/status.sh` from the project root).

## Prerequisite

`~/.ssh/hetzner_prod` must exist and have access to `root@46.225.119.148`.
Test it once with:

```bash
ssh -i ~/.ssh/hetzner_prod root@46.225.119.148 "echo OK"
```

## `setup.sh`

**What it does:** `rsync`s the project to `/opt/shab-harvester` on the
server (excluding your local `.venv`, DB, and raw files — the server gets
its own), then over SSH: installs `python3-venv`/`tmux`, creates a venv,
`pip install`s requirements, runs `playwright install --with-deps chromium`
(slow — pulls in system libraries), copies `.env.example` → `.env` if no
`.env` exists yet, and runs `init-db`.

**Run it:** once for a fresh server, or again any time you want to push a
code update (`init-db` is idempotent, safe to re-run; existing `.env` is
left alone).

**Expect:** a few minutes (Chromium download is the slow part). Ends with
`Setup done. DB initialized on the server.` Safe to re-run — never touches
`data/shab_harvester.sqlite` if it already exists on the server.

## `discover-all.sh`

**What it does:** writes a script to the server that seeds + discovers all
31 quarters from 2018-09-03 to today, then starts it inside a detached
`tmux` session named `harvest`, and returns immediately — your Mac doesn't
need to stay connected.

**Run it:** once, after `setup.sh`.

**Expect:**
- `Started discover-all in tmux session 'harvest' on the server.` — it's
  now running unattended on the server. Takes hours.
- If a `harvest` tmux session is **already** running (from this script,
  `scrape-all.sh`, or you manually), it refuses to start a second one and
  prints how to attach instead — it will **not** double-run anything.
- Check progress later with `status.sh` / `still-running.sh`.

## `scrape-all.sh`

**What it does:** same pattern as `discover-all.sh`, but for downloading
detail pages: loops `scrape-pending --limit 500` in a detached `tmux`
session called `harvest` until `publication_queue` has nothing left
`pending`/retriable-`failed`.

**Run it:** after discovery has found something to scrape (you don't have
to wait for *all* discovery to finish — anything already `discovered` can
be scraped while later quarters are still being found, if you run this in
parallel under a different approach; the scripts as shipped use the same
`harvest` session name, so run them one after another, not at the same
time).

**Expect:** same "already running" guard as `discover-all.sh`. Takes hours
to days depending on how much was discovered. Runs unattended.

## `status.sh`

**What it does:** read-only. Runs the standard `status` command on the
server, plus two extra lines:

```
Days discovered (2018-09-03..2026-06-24): 120/120 (100.0%)
Publications scraped: 23747/96186 (24.7%)  failed=0  running=0
```

**Run it:** any time, as often as you like — including while
`discover-all.sh`/`scrape-all.sh` is actively running. It only reads the
SQLite file, never interferes.

**Expect:** instant output, no side effects.

## `status-detail.sh [N]`

**What it does:** read-only. Lists the `N` most recently touched
`import_day` rows (default 20 — i.e. wherever discovery/scraping currently
is), one line per day: status, number of SHAB notifications found that day
(`result_count`), how many of that day's publications are already
`scraped`, and how many are stuck `failed` in `publication_queue`.

**Run it:** any time you want to see *which specific days* are progressing
(or stuck), not just the aggregate totals from `status.sh`.

**Expect:**
```
date         status      notifications   scraped   failed  last touched
2019-05-21   discovered           1088         0        0  2026-06-24T22:41:41Z
2019-05-22   running                 -         0        0  2026-06-24T22:41:41Z
2019-05-19   empty                   0         0        0  2026-06-24T22:41:06Z
```
A nonzero `failed` column on a day means some of its publications hit
errors while scraping and are being retried (up to 3 attempts) — if they
stay nonzero across repeated checks, run `reset-failed` on the server.

## `eta.sh [SAMPLE_SIZE]`

**What it does:** read-only. Estimates remaining scrape time. Computes the
actual rate from the timestamps of the most recently scraped publications
(default: last 500 — pass a number to use a bigger/smaller window), not a
fixed assumption, so the estimate adapts as the real rate speeds up or
slows down (e.g. after Chromium warms up, or if shab.ch starts throttling).

**Run it:** any time — the bigger `SAMPLE_SIZE`, the smoother/more
historical the rate estimate; the smaller, the more it reflects only very
recent speed.

**Expect:**
```
scraped: 562/2613340 (0.0%)  failed: 0  remaining: 2612778
Rate (last 499 scraped): 1.08/s = 65/min = 3872/hour
ETA: 28d 2h 51m remaining  (finishes around 2026-07-23 22:50 UTC)
```
With fewer than 2 scraped publications yet, it just reports the counts
without a rate/ETA (nothing to compute a rate from).

## `still-running.sh`

**What it does:** read-only. Checks whether the `harvest` tmux session
exists on the server and, if so, prints its last ~15 output lines (via
`tmux capture-pane`) without attaching — so it can't accidentally type into
or disturb the live session.

**Run it:** any time you want a quick "is it still going, and what's the
latest line" check without a full `status.sh`.

**Expect:** either
```
RUNNING: tmux session 'harvest' is active.
--- last output ---
[discover] 2019-04-12: discovered
...
```
or
```
NOT RUNNING: no tmux session 'harvest' on the server.
```
(the latter is also what you'll see once a job finishes normally, since the
session prints "Press enter to close." and waits — until you press enter
in `tmux attach`, it's technically still "RUNNING"; after you close it, or
if it crashed, this reports not running).

## `install-cron.sh` / daily catch-up

Installs `/opt/shab-harvester/daily_catchup.sh` and a crontab (Europe/Zurich
**06:00** + **18:00**). Uses `flock -n` so overlapping runs skip. Logs:
`logs/daily_catchup.log` and `logs/daily_catchup.cron.log`.

After max scrape retries, unreachable detail pages are archived into
`shab_publication_non_public` (list title, URL, rubric, …) and the queue
status becomes `non_public`. CLI: `archive-non-public`.

`./catchup-report.sh` prints recent STARTED/FINISHED lines.

## `export.sh`

**What it does:** runs `export-data` on the server (zips DB + raw_html +
raw_xml into `data/exports/shab_export_<timestamp>.zip`), then `scp`s that
exact file down into this Mac's `data/exports/`.

**Run it:** any time you want a checkpoint, including mid-harvest — it's
read-only with respect to the harvest itself.

**Expect:** prints the downloaded file's local path on success, e.g.
`Done: /Users/romanzoun/.../data/exports/shab_export_20260624-190000.zip`.
Import it locally with:
```bash
python -m shab_harvester.app import-data --zip data/exports/<file>.zip --yes
```

## Troubleshooting

- **"tmux session 'harvest' is already running"** when you didn't expect
  it: someone (maybe you, manually) already started one. Attach and look:
  `ssh -i ~/.ssh/hetzner_prod root@46.225.119.148 -t tmux attach -t harvest`.
  Detach again with `Ctrl-b d` without typing `exit`.
- **A script hangs on the SSH connection itself:** check the server is
  reachable at all (`ssh -i ~/.ssh/hetzner_prod root@46.225.119.148 echo OK`)
  before assuming the harvester is the problem.
- **Re-running `discover-all.sh`/`scrape-all.sh` after a crash:** safe —
  `discover-pending-days`/`scrape-pending` only touch `pending`/`failed`
  rows, so nothing already done gets redone. If something got stuck on
  `running` (process died mid-item), run `reset-failed` on the server first
  (it resets both `failed` and `running` back to `pending`).
