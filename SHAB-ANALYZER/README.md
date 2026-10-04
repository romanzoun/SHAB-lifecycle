# SHAB-Analyzer

Deterministische Strukturierung aus **SHAB-XML** (plus Personen im Fliesstext). Raw bleibt unangetastet. Dashboard-Linsen liegen später in **PostgreSQL** (`fact_event`); der Walk schreibt zuerst SQLite.

```
Harvester RAW  →  shab-parser walk  →  analyzer_event  →  (später Postgres)  →  GET /lens/{dimension}/{key}
```

## CLI

```bash
cd SHAB-ANALYZER
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/shab-parser parse tests/fixtures/fff92f73-ab6f-4772-ab5a-bd08831dddc5.xml
.venv/bin/shab-parser walk --xml-root /opt/shab-raw/raw_xml --once
.venv/bin/shab-parser status
.venv/bin/shab-parser gaps
.venv/bin/shab-parser warehouse-load
.venv/bin/shab-parser lens plz 6340 --mode pulse
.venv/bin/shab-parser serve --port 8770
```

### Walk (State Machine)

Zustände: `idle` → `discovering` → `walking` → `complete`. Bei Absturz: `failed` oder hängendes `walking` mit totem PID — der nächste Start übernimmt ab Checkpoint.

- `walk_item` merkt jede XML-Datei (`pending` / `ok` / `partial` / `deferred` / `error`).
- WAL-SQLite, Commit alle 50 Meldungen.
- Non-HR (KK, SB, …) wird `deferred` und blockiert HR nicht.
- `PARSER_VERSION` hochzählen, wenn Regeln sich ändern: PARTIAL/ERROR werden neu eingereiht.
- Default ohne `--once`: nach `complete` alle `--poll` Sekunden neue Harvest-XMLs nachziehen.

Server: `scripts/remote/install-walk.sh` installiert systemd `shab-analyzer-walk` mit `Restart=always`. DB: `/opt/shab-structured/analyzer/shab_analyzer.sqlite`. Raw nur lesen.

Linsen: `person`, `plz`, `canton`, `org`, `event_type`. Postgres-DDL: [sql/fact_event.postgres.sql](sql/fact_event.postgres.sql).

Harvester-`analyze` bleibt Prototyp und schreibt nicht ins Raw.

Siehe [PLAN-Ruleengine-automation.md](PLAN-Ruleengine-automation.md).
