# PLAN — Rule-Engine Automation (SHAB-ANALYZER)

Deterministische, versionierte **Strukturierung** von SHAB-Rohmeldungen zu Unternehmensereignissen. Kein Harvesting, kein BI-Frontend.

```
SHAB-harvester          SHAB-ANALYZER                      SHAB-BI
(raw sammeln)    →      (Normalize → Rules → Events)  →    (Visualisierung / BI)
```

Harvester-Ops: [../SHAB-harvester/PLAN-Harvesting.md](../SHAB-harvester/PLAN-Harvesting.md).  
Ältere Entwürfe ([PLAN.md](PLAN.md), [IMPLEMENTATION.md](IMPLEMENTATION.md)) mit „LLM in der Produktivpipeline“ sind durch **dieses Dokument** ersetzt, soweit sie kollidieren.

---

## Rolle in der Pipeline

| Schicht | Verantwortung |
|---------|----------------|
| **Harvester** | HTML/XML/DB Raw unverändert |
| **Analyzer (dieses Plan)** | Normalisieren, profilieren, Regeln anwenden, validieren, Event Store, Quarantäne, Projektion |
| **BI** | Strukturierte Events konsumieren, Warehouse, Dashboards, Produkte |

**Kernregel:** KI darf Regelwerk **entwickeln/reparieren** (Proposal-Workflow), aber **nicht** zur normalen produktiven Extraktion. Zur Laufzeit keine KI nötig.

Der Harvester-Prototyp `shab_harvester/analysis.py` bleibt unangetastet; Heuristiken dort dienen nur als **Seed** für YAML-Regeln.

---

## Speicher (Server)

Raw und strukturierte Daten liegen auf **zwei Volumes**. Raw wird nicht auf das zweite Volume kopiert.

| Rolle | Mount | Symlink | Stand |
|-------|--------|---------|--------|
| Harvest Raw | `/mnt/HC_Volume_106139937` | `/opt/shab-raw` | ~129 GB / 246 GB |
| Analyzer + Warehouse | `/mnt/HC_Volume_106976683` | `/opt/shab-structured` | ~233 GB frei; `analyzer/`, `warehouse/postgres/` |

fstab persistiert beide Platten (`scsi-0HC_Volume_…`, `nofail`).

---

## Architektur

```
Raw XML (read-only)
  → XML-Mapper (commonsNew vs commonsActual)
  → Personenregeln auf publicationText (DE/FR)
  → analyzer_event (Linsen-Keys)
  → fact_event in Postgres (oder SQLite)
  → Dashboard-Linse: Person / PLZ / Kanton / Org
```

Entwicklungsprozess für Lücken:

```
Quarantäne → ähnliche Fälle → KI schlägt deklarative Regel vor
  → Golden Test → volle Regression → kontrolliertes Promote
```

### Zwei Ebenen (kein „eine Regex für die ganze Meldung“)

1. **Regelprofil** — Auswahl über Sprache, Meldungsart, Rechtsform (falls da), Überschriften/Keywords, Struktur.  
   Zustände: `PROFILE_SELECTED` | `NO_PROFILE` | `MULTIPLE_PROFILES`  
   Beispiele: `de_mutation_v1`, `fr_mutation_v1`, `it_mutation_v1`, `de_ag_new_registration_v1`, …

2. **Event-Regeln** — innerhalb des Profils alle passenden Regeln; eine Meldung → 0..n Changes  
   (Name, Adresse, Sitz, Zweck, Kapital, Officers, Signing Authority, Liquidation, …).  
   Dieselben Event-`type`-Werte in allen Sprachen; nur Scope/Patterns/Phrasen sind sprachspezifisch.

---

## Entscheidungen (fest)

| Thema | Wahl |
|-------|------|
| Package | Neu unter `SHAB-ANALYZER/shab_analyzer/` |
| Analyzer-DB | Eigene `shab_analyzer.sqlite` (Harvester-DB nur read-only — Lock-Schutz) |
| Input | `raw_xml` zuerst; HTML nur Fallback |
| Warehouse | Nur Postgres (`fact_event` + Dimensionen). Kein Neo4j. |
| Dashboard | Eine Linse (Person, PLZ, Kanton, Org, event_type), Rest über `published_at` |
| Regeln | Versioniertes YAML-Rulebook, keine KI-generierte Python-Ausführung |
| Runtime | Rein deterministisch |
| KI | CLI `propose-rule` + Provider-Interface; Default Mock / manuell |
| Sprachen | **DE + FR + IT von Anfang an** im gleichen Rulebook. Router wählt sprachspezifische Profile; Event-Typen und Projektion sind sprachneutral. |
| MVP-Schnitt | Mutationen in **DE/FR/IT**: UID/Metadaten, Name, Adresse/Sitz, Personen add/remove/role, Signing Authority, Multi-Change — parallel Fixtures und Regeln je Sprache |
| Enrichment (ZEFIX etc.) | **Optional / nachrangig.** Aktueller Unternehmenszustand kommt primär aus **Delta-Projektion** über die Event-Historie. ZEFIX spiegelt den Ist-Stand und hilft eher zum Abgleich, Bootstrapping ohne Historie oder Fremddimensionen (LEI, …) — in den meisten Fällen mit voller SHAB-Historie nicht nötig. |

---

## Harvester-`analyze` heute (Prototyp)

Liegt in `SHAB-harvester/shab_harvester/analysis.py`, CLI: `python -m shab_harvester.app analyze`.

| | Verhalten |
|---|-----------|
| Input | Nur `shab_publication_raw` (v. a. `body_text`), Raw unverändert |
| Methode | Keyword/Regex, „erster Treffer gewinnt“ → **ein** Event pro Meldung |
| Output | Aggregate-Tabellen in derselben Harvester-DB: `organizations`, `persons`, `person_roles`, `cases`, … |
| Sprachen | DE Personen-Regex; FR teils Keywords; IT kaum |
| Projektion | Kein sauberes `get_company_state(uid, at)` über Event-Historie |
| Rolle im Plan | **Bleibt als Alt-Prototyp**; wird nicht zur Produktions-Rule-Engine ausgebaut. Phrasen dort nur als Seed für YAML-Regeln. Ablösung = SHAB-ANALYZER. |

---

## Datenmodell (Kurz)

Notice mindestens: `notice_id`, `uid`, `company_name_at_publication`, `published_at`, `effective_at` (nur wenn explizit, sonst `null`), `observed_at`, `language`, `canton`, `source_hash`, `parser_version`, `profile_id`, `changes[]`.

Changes: Pydantic, über `type` diskriminiert; jedes Feld mit Evidence-Span (`text`, `start`, `end`) und `rule_id`.

Zeichnungsarten normalisieren (`individual`, `collective_two`, …) **plus** Originalformulierung. Personen nicht nur per Name mergen (Wohnort, Heimatort, Geburtsjahr, Funktion, …). Quell-Events und abgeleitete Korrelation getrennt halten.

---

## Package-Struktur

```
SHAB-ANALYZER/
  shab_analyzer/
    parse.py xml_map.py persons.py store.py warehouse.py api.py app.py
  sql/fact_event.postgres.sql
  tests/fixtures/*.xml
```

CLI: `shab-parser parse` / `parse-dir` / `warehouse-load` / `lens` / `serve`.

---

## Pipeline pro Meldung

1. XML lesen, Raw unverändert.  
2. Diff `commonsNew` / `commonsActual` → Org-Events mit `org_uid`, `plz`, `canton`, `published_at`.  
3. Personen aus `publicationText` (DE-Listen, FR-Narrativ).  
4. Replay nach `fact_event`. Linse filtert eine Dimension, aggregiert den Rest über die Zeit.

---

## Event Store und Linsen

- `analyzer_event` append-only, Replay nach `fact_event`.  
- API: `GET /lens/{person|plz|canton|org|event_type}/{key}?mode=timeline|pulse`.  
- Person: Timeline plus `related_org_events`. PLZ: Pulse plus `people`.

---

## CLI

```bash
shab-parser parse <xml>
shab-parser parse-dir <dir>
shab-parser warehouse-load
shab-parser lens plz 6340 --mode pulse
shab-parser serve
```

Promote nur wenn: neuer Fall ok, alle Golden Tests grün, keine Profil-/Regelkonflikte, keine stillen Event-Regressionen, Schema ok.

---

## Tests

- Unit: Normalize, Router, Regeln, Konflikte, Completeness, Idempotenz, Projection-Replay  
- Golden/Snapshot pro Fixture  
- Multi-Change, Unknown/Partial, kaputtes HTML  
- Regression über gesamten Fixture-Bestand (parallel wo sinnvoll)

Fixture-Layout: `tests/fixtures/<notice-id>/input.html|normalized.txt|expected.json`.

---

## KI-Rule-Proposal (Offline)

Input: problematische Meldung, normalisierter Text, Router-Ergebnis, angewandte Regeln, Events, unverarbeitete Spans, ähnliche Erfolge, bestehende Regeln, Schema.

Output-Typen: `ADD_PROFILE` | `MODIFY_PROFILE` | `ADD_RULE` | `MODIFY_RULE` | `ADD_NORMALIZER` | `REQUIRES_MANUAL_REVIEW` — als **Kandidat**, nicht auto-aktiv.

Keine API-Keys im Repo; Mock + Provider-Interface im MVP.

---

## MVP-Reihenfolge

1. Skeleton (pyproject, config, models, CLI stub, Analyzer-SQLite).  
2. Normalize + Router mit **DE/FR/IT**-Mutationsprofilen + Kernregeln (Name, Adresse/Sitz, Personen, Signing) aus realen Fixtures je Sprache.  
3. Completeness, Quarantäne, Store, `parse` / `report`.  
4. Projektion + Golden/Regression grün (Fixtures DE **und** FR **und** IT).  
5. Proposal-Mock + Coverage-Report **nach Sprache** / Typ / Regel.  
6. README an dieses Plan anbinden; alte LLM-Runtime-Passagen als deprecated markieren.

Seed-Phrasen (Harvester-Prototyp + reale HTML):

| Event | DE | FR | IT (Beispiele) |
|-------|----|----|----------------|
| Name | Firma neu / Firma bisher | Nouvelle raison sociale | Nuova ragione sociale |
| Adresse/Sitz | Neue Adresse / Sitzwechsel | Nouvelle adresse / Nouveau siège | Nuovo indirizzo / Trasferimento di sede |
| Personen | Eingetragene / Ausgeschiedene Personen | personnes inscrites / radiées | persone iscritte / cancellate |
| Unterschrift | Einzel- / Kollektivunterschrift | signature individuelle / collective | firma individuale / collettiva |

### Bewusst später

- Weitere Meldungstypen (Neugründung, Konkurs, …) in allen drei Sprachen  
- Optionales Enrichment nur wo Deltas nicht reichen (Abgleich, LEI, …)  
- Harvester-`analyze` abschalten/deprecaten, sobald Analyzer Coverage trägt  
- BI-Warehouse: Postgres `fact_event`, Linsen Person/PLZ (kein Neo4j)
---

## Abgrenzung zu BI

Analyzer liefert **vertrauenswürdige strukturierte Events** (+ Quarantäne-Metriken).  
SHAB-BI liest den Event Store / Export und macht Visualisierung, Aggregation, Produkte — **ohne** Parsing-Logik erneut zu erfinden.

---

## Risiken

- Anfänglich niedrige `FULLY_PARSED`-Rate → Quarantäne steuert Roadmap.  
- Harvester-DB-Locks → kurze RO-Queries / HTML-first, eigene Analyzer-DB.  
- Regex-ReDoS → Timeouts in der Engine.  
- Alte Docs (LLM-second) nicht versehentlich wieder einbauen.

## Erfolgsmetrik MVP

- Vertikaler Mutations-Schnitt **DE + FR + IT** mit Multi-Change end-to-end.  
- Regression über Fixtures aller drei Sprachen grün.  
- Coverage-Report nach Sprache; Lücken steuern nächste Regeln, nicht „Sprache später“.  
- Runtime ohne KI; Proposal-Pfad dokumentiert und mockbar.
