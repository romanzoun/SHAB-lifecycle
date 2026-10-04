# shab_harvester

Raw harvester for SHAB (shab.ch) publications. Collects metadata, detail HTML,
content text, XML/PDF links, UID/CHE numbers and ZEFIX links into SQLite.
The harvester itself does no parsing or classification.

A second, explicitly separate **aggregation layer** (`analyze`) builds an
entity model (organizations/persons/cases) on top of the raw data using
heuristics — see [Aggregation layer](#aggregation-layer) below.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Configuration

Every tunable runtime parameter — pause between detail pages, rate-limit
backoff/abort thresholds, retry limits, Playwright timeouts, scroll
behavior, webui host/port, DB path — lives in [`shab_harvester/config.py`](shab_harvester/config.py)
and can be overridden by environment variables, without touching code:

```bash
cp .env.example .env
# edit .env, e.g. to harvest a bit faster:
#   SHAB_SCRAPE_PAUSE_MIN=0.3
#   SHAB_SCRAPE_PAUSE_MAX=1.0
```

`.env` is loaded automatically (real environment variables always take
precedence over it) and is gitignored. See `.env.example` for the full list
with explanations. Lowering the scrape pause speeds things up but increases
the chance of being rate-limited by shab.ch — the existing backoff/abort
logic (`SHAB_MAX_CONSECUTIVE_RATE_LIMITS`) still protects against runaway
requests either way.

## Usage

```bash
python -m shab_harvester.app init-db
python -m shab_harvester.app seed-days --from 2018-09-02 --to 2026-06-22
python -m shab_harvester.app discover-day --date 2018-09-03 --headless
python -m shab_harvester.app discover-pending-days --headless
python -m shab_harvester.app scrape-pending --limit 100 --headless
python -m shab_harvester.app harvest-day --date 2018-09-03 --headless
python -m shab_harvester.app harvest-range --from 2018-09-02 --to 2018-09-10 --headless
python -m shab_harvester.app status
python -m shab_harvester.app reset-failed
python -m shab_harvester.app verify-day --date 2018-09-03
python -m shab_harvester.app day-overview --date 2018-09-03
python -m shab_harvester.app day-overview --date 2018-09-03 --status failed
python -m shab_harvester.app analyze --limit 100
python -m shab_harvester.app analyze --force
python -m shab_harvester.app export-data
python -m shab_harvester.app import-data --zip data/exports/shab_export_20260622-170701.zip --yes
python -m shab_harvester.app reset-all --yes
```

The harvester is fully restartable: stop it at any time (Ctrl-C) and rerun the
same command — `import_day` and `publication_queue` track progress, so only
`pending`/`failed` work is retried.

Data is stored under `data/`:
- `shab_harvester.sqlite` — SQLite database
- `raw_html/YYYY/MM/{publication_id}.html` — full detail page HTML
- `raw_xml/YYYY/MM/{publication_id}.xml` — exported XML (if available)

## State machine

Everything the harvester does is driven by two state machines persisted in
SQLite. Nothing is held in memory between runs, so any command can be
stopped and re-run safely.

**`import_day`** — one row per calendar day:

```
pending --discover-day--> running --+--> empty       (0 results)
                                     +--> discovered  (results found, queued)
                                                |
                                                v
                                          completed   (all queued items scraped)
running --(error)--> failed --reset-failed--> pending
```

**`publication_queue`** — one row per shab-id (`publication_id`), discovered
underneath a day:

```
pending --scrape-pending--> running --+--> scraped
                                       +--> failed (attempt_count++, retried while < 3)
```

`day-overview --date YYYY-MM-DD` renders this state machine for a single day:
every known shab-id, its current queue status, attempt count, and whether a
row already exists in `shab_publication_raw`:

```
Day 2018-09-03: import_day.status=discovered result_count=1021
  [x] 002ab7bc-... HR02-0004447641 status=scraped attempts=1 raw - Change Richard Fitzi AG ...
  [!] 0240cd56-... HR01-0004447090 status=failed attempts=2 no-raw | last_error=Timeout ...
  [ ] 02f5c514-... HR01-0004447099 status=pending attempts=0 no-raw - ...
  3/1021 scraped
```

Use `--status pending|running|scraped|failed` to filter to one state, e.g.
to inspect only what's still outstanding for a day.

## Data lifecycle (export / delete / import)

Three independent, single-purpose scripts for managing the whole data
directory as a unit:

```bash
scripts/export.sh                                              # safe, non-destructive
scripts/delete.sh --yes                                        # irreversible
scripts/import.sh data/exports/shab_export_<timestamp>.zip --yes   # irreversible
```

- **`export.sh`** → `jobs.export_data()` — zips `shab_harvester.sqlite` +
  `raw_html/` + `raw_xml/` into `data/exports/shab_export_<UTC timestamp>.zip`.
  Read-only; never deletes anything.
- **`delete.sh`** → `jobs.reset_all()` (same as `reset-all --yes`) — deletes
  the DB and `raw_html`/`raw_xml`, then re-initializes an empty schema.
  Does **not** touch `data/exports/`, so backups survive a wipe.
- **`import.sh <zip> --yes`** → `jobs.import_data()` — wipes current data
  (same as `delete.sh`) and restores the DB + raw files from the given zip.

Each requires an explicit `--yes` (CLI) since they're irreversible; the web
UI versions require typing a confirmation word (`RESET` / `IMPORT`) instead.
All three are also CLI subcommands (`export-data`, `reset-all`, `import-data`)
and forms on the Harvest screen's **Data Segment**.

## Aggregation layer

`analyze` is a second pass over `shab_publication_raw` that never modifies the
raw tables — it only reads them and writes into a separate entity model:

```
Organization (uid or name+canton fallback)
  └── Case / Verfahren (bankruptcy, liquidation, composition proceedings...)
        └── Publication (shab_publication_raw)
              └── Person / Role (extracted from mutation sentences)
```

- **Organization key**: `uid:<CHE-...>` if a UID was extracted (`match_confidence=HIGH`),
  otherwise a synthetic `cand:<normalized name>|<canton>` candidate key
  (`match_confidence=LOW` — a grouping guess, not a verified identity).
- **Event type / case type**: classified by keyword matching on `body_text`
  (e.g. "Konkurs eröffnet" → `BANKRUPTCY_OPENED`), falling back to
  `category`/`subcategory` metadata if no keyword matches. This is heuristic,
  not a legal classifier — `confidence` is stored per publication-org link
  (`keyword` / `metadata` / `fallback`).
- **Persons**: extracted only from the fairly regular German "Eingetragene
  Personen.../Ausgeschiedene Personen..." mutation sentences. Anything that
  doesn't match that phrasing is skipped rather than guessed at.
- Re-running `analyze` is idempotent (unchanged publications are skipped via
  a content-hash check). `analyze --force` fully rebuilds the aggregate
  tables from scratch — needed because `organizations`/`cases` merge fields
  additively across publications, so a heuristic fix only takes full effect
  on a rebuild, not a normal incremental run.

## Dashboard

A small web UI (stdlib `http.server` + `threading`, no JS framework, no extra
dependency) with two screens:

```bash
python -m shab_harvester.app webui --port 8765
# open http://127.0.0.1:8765/harvest or /analyse
```

**Harvest** (`/harvest`) — start any harvesting command as a background job
and watch its log update live. Commands are grouped into segments, each with
an explanation of what it does and what you'll have afterward:

- **Data Segment** — init-db, export, import, delete (see [Data lifecycle](#data-lifecycle-export--delete--import)).
- **Discover Segment** — seed-days (pick the date range), discover-day,
  discover-pending-days. Fills `publication_queue` with shab-ids, no content yet.
- **Scrape Segment** — scrape-pending, harvest-day, harvest-range. Fetches
  the actual detail pages into `shab_publication_raw` + `raw_html`/`raw_xml`.
- **Analyse / Maintenance Segment** — analyze (rebuild the aggregate layer),
  reset-failed.

Jobs run in background threads; the job list and log view
(`/harvest/job?id=`) auto-refresh while running.

**Analyse** (`/analyse`) — the raw state machine plus the aggregate layer:

- `/analyse` — totals across the whole DB (publications, with UID/ZEFIX/XML,
  queue pending/failed, organizations/persons/cases) plus all `import_day`
  rows with a scraped-progress bar.
- `/analyse/day?date=YYYY-MM-DD` — per-publication state for one day (same
  data as `day-overview`), filterable by status. Each shab-id links to its
  detail page.
- `/analyse/pub?id=<publication_id>` — everything collected for one shab-id:
  all raw fields, XML/PDF/ZEFIX/Detail links, raw metadata/links/content
  JSON, the stored detail-page HTML (inline iframe) and XML, plus a link to
  its organization if `analyze` has run.
- `/analyse/orgs` (searchable) and `/analyse/org?key=...` — organizations
  with their cases, publications, and extracted persons/roles.
- `/analyse/cases` and `/analyse/case?id=...` — all detected cases/Verfahren
  with their event timeline.

It only reads from `data/shab_harvester.sqlite`; the Analyse screens never
touch the browser/Playwright side, so they're safe to use alongside a
harvest in progress. The Harvest screen *does* launch real Playwright jobs
in background threads — those are the same browser/network operations as the
CLI commands.

## Tests

Tests cover the pure logic (`utils.py` regex/date helpers), the state machine
transitions in `db.py` (day/queue status changes, idempotent upserts,
attempt-count retry limits, `day_overview`), the aggregation heuristics in
`analysis.py` (event classification, person extraction, force-rebuild
semantics), `config.py` (env var overrides, `.env` loading, precedence), and
the dashboard's rendering/job-manager logic in `webui.py` — all against a
temporary SQLite file, no network/browser involved.

```bash
pip install -r requirements-dev.txt
pytest -q
```
