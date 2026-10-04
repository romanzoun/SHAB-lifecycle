# PLAN — Harvesting

Aktuellerhalten der **Rohdaten** von shab.ch. Keine Strukturierung, keine Events, kein BI.

```
SHAB-harvester          SHAB-ANALYZER                 SHAB-BI
(raw sammeln)    →      (Rule-Engine / Events)  →     (Visualisierung / BI)
```

Siehe Analyzer: [../SHAB-ANALYZER/PLAN-Ruleengine-automation.md](../SHAB-ANALYZER/PLAN-Ruleengine-automation.md).

---

## Rolle

| Macht | Macht nicht |
|-------|-------------|
| Tage seedén / discoveren | Meldungen klassifizieren |
| Detailseiten scrapen (HTML/XML) | Regelwerk / Extraktion |
| SQLite Raw + Dateien schreiben | Unternehmenszustand / Projektion |
| Export/Import, Status, ETA | Dashboards |

Rohdaten bleiben unverändert, nachdem sie geschrieben wurden. Der eingebaute `analyze`-Befehl ist nur ein **Prototyp** und gehört nicht zur Harvesting-Produktionslinie — die echte Strukturierung liegt im Analyzer.

---

## Ist-Zustand (Server)

| Item | Wert |
|------|------|
| Host | `root@46.225.119.148` |
| App | `/opt/shab-harvester` |
| Raw | `/mnt/HC_Volume_106139937/shab-data` (Symlink `data/` und `/opt/shab-raw`) |
| Raw-Volume | ~246 GB, ~129 GB belegt — nur Harvest, nie löschen |
| Structured | `/mnt/HC_Volume_106976683/shab-structured` (`/opt/shab-structured`) |
| Structured-Volume | ~246 GB, leer — Analyzer-DB, später Postgres/Neo4j |
| Historie | ab ~2018-09-03 geseedet/discovered |
| Betrieb bisher | manuell via `scripts/remote/*` + tmux (`harvest`) |
| Cron | **06:00 + 18:00** Europe/Zurich via `install-cron.sh` |

Kernfluss:

```
seed-days → discover-pending-days → scrape-pending (Loop bis Queue leer)
→ exhausted fails → shab_publication_non_public (Listen-Metadaten)
```

Remote-Hilfen unter [`scripts/remote/`](scripts/remote/): `setup.sh`, `discover-all.sh`, `scrape-all.sh`, `auto-continue.sh`, `rediscover-shortfall.sh`, `install-cron.sh`, `catchup-report.sh`, `status.sh`, `eta.sh`, `still-running.sh`, `export.sh`.

---

## Ziel dieses Plans

**Datenbasis dauerhaft aktuell halten:** zweimal täglich Catch-up vom letzten vollständigen Tag bis „heute“, ohne Doppelstarts und ohne die Raw-Historie anzufassen.

---

## Täglicher Catch-up (Cron)

### Zeiten

Zeitzone **Europe/Zurich**:

| Zeit | Zweck |
|------|--------|
| `06:00` | Morgen-Lauf (Nacht/Früh-Publikationen) |
| `18:00` | Abend-Lauf (Tagespublikationen) |

### Logik `daily_catchup.sh`

1. **`flock -n /var/lock/shab-harvest.lock`** — wenn schon ein Catch-up/manueller Harvest läuft: sauber abbrechen (nicht killen).
2. `TO = heute` (Server-Lokaldatum in Europe/Zurich).
3. `FROM = max(letzter Tag mit status discovered|empty|completed, heute − 1 Tag)` — Überlappung von 1 Tag ist ok (`seed` ist idempotent; Discover nur für pending/failed).
4. Stuck Days (`running`/`failed`) → `pending` (bzw. `reset-failed`).
5. `seed-days --from FROM --to TO`
6. `discover-pending-days --headless` (mit begrenzten Retries bei transienten Fehlern/DB-Lock)
7. Loop Discover **bis im Fenster [FROM, TO] weder `pending` noch Shortfall** (`result_count > discovered_count`) — max. 10 Versuche, sonst Exit 1 (kein „DONE“)
8. Loop `scrape-pending` bis Queue leer; erneut Shortfall-Check im Fenster
9. Exhausted fails → `shab_publication_non_public`; Queue-Status `non_public`
10. Historische Shortfalls **außerhalb** [FROM, TO] bleiben unberührt (eigenes `rediscover-shortfall`)

### Non-public / Failed

Wenn die Detailseite nach max. Retries nicht erreichbar ist (Timeout / nicht öffentlich):

- Speichern was aus der Discovery-Liste da ist: `publication_id`, Datum, Titel, `list_info`, URL, geparste Rubrik/Ref, Fehlertext
- **Kein** UID/Body (gibt es ohne Detailseite nicht)
- CLI: `python -m shab_harvester.app archive-non-public`

### Timing-Report

`scripts/remote/catchup-report.sh` — liest die geloggten Dauern und zeigt Morgen- vs. Abend-Läufe. Vor Cron-Go-Live gibt es noch keine Slot-Historie.

### Bekannte Lücke vs. SHAB-UI (~2.78 M Treffer)

Keine Kalenderlücken 2018-09-03..2026-09-14. Queue ≈ **2.69 M** (− ~89 k). Ursache: ~829 Tage mit unvollständigem Discover (`discovered_count` oft ~100 trotz höherem `result_count`). Rediscovery-Backfill = separates Follow-up, nicht Teil des Tages-Crons.

### Repo-Artefakte

| Datei | Zweck |
|-------|--------|
| [`scripts/remote/daily-catchup.sh`](scripts/remote/daily-catchup.sh) | Quelle; wird auf Server nach `/opt/shab-harvester/daily_catchup.sh` deployed |
| [`scripts/remote/install-cron.sh`](scripts/remote/install-cron.sh) | Idempotent: Script syncen + Crontab-Einträge setzen |
| Update [`scripts/remote/README.md`](scripts/remote/README.md) | Cron dokumentieren |

Beispiel-Crontab:

```cron
CRON_TZ=Europe/Zurich
0 6 * * * /opt/shab-harvester/daily_catchup.sh >> /opt/shab-harvester/logs/daily_catchup.cron.log 2>&1
0 18 * * * /opt/shab-harvester/daily_catchup.sh >> /opt/shab-harvester/logs/daily_catchup.cron.log 2>&1
```

---

## Betriebsregeln

- **Kein zweites tmux `harvest`**, solange flock greift bzw. Session aktiv ist.
- Laufenden manuellen Catch-up **nicht** per Cron killen.
- `status.sh` / schwere Full-Table-Scans sparsam — große SQLite (~20 GB+) → Lock-Risiko für Scrapes.
- Speicher vor langen Backfills prüfen: `df -h /mnt/HC_Volume_106139937`.
- Raw-HTML/XML **nie löschen** für Analyzer/BI; Export bei Bedarf über `export.sh`.

---

## Abgrenzung

| Thema | Wo |
|-------|-----|
| Deterministische Extraktion, Rulebook, Quarantäne | SHAB-ANALYZER |
| Visualisierung, Warehouse, Dashboards | SHAB-BI |
| Harvester-`analyze` (Prototyp) | bleibt, wird nicht zur Produktions-Pipeline ausgebaut |

---

## Umsetzungsschritte

1. `daily_catchup.sh` im Repo schreiben (Logik wie oben).
2. `install-cron.sh` — rsync Script + crontab installieren.
3. Einmal manuell dry/smoke auf dem Server (flock + kurzer Lauf).
4. Crontab aktivieren; ersten 06:00-/18:00-Lauf im Log verifizieren.
5. README remote um Cron ergänzen.

## Erfolgsmetrik

- Nach jedem erfolgreichen Lauf: `max(import_day done) >= heute` (bzw. letzter SHAB-Publikationstag) und `publication_queue` remaining ≈ 0 (außer frische Failed mit Retry-Limit).
- Keine parallelen Scrape-Prozesse durch Cron-Überlappung.
