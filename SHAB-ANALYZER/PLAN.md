# SHAB-ANALYZER — Produktplan

## Rolle in der Pipeline

SHAB-ANALYZER ist die **Strukturierungsschicht** zwischen Harvesting und Analytics:

```
SHAB-harvester          SHAB-ANALYZER              SHAB-BI
(raw sammeln)    →      (strukturieren + enrich)  →  (warehouse + dashboard)

shab_publication_raw    organizations              PostgreSQL Gold
raw_html / raw_xml      events, persons, cases     Karte, Timeline, Pulse
publication_queue       enrichment_snapshots       Suche, Top-Listen
```

**Harvester** sammelt Rohdaten und verändert sie nie nachträglich.  
**Analyzer** liest nur Raw, extrahiert strukturierte Entitäten und Events, reichert an.  
**BI** aggregiert und visualisiert — keine Parsing-Logik.

Der bestehende `analyze`-Befehl im Harvester (`shab_harvester/analysis.py`) ist ein **Prototyp** desselben Konzepts. SHAB-ANALYZER wird die vollständige, eigenständige Anwendung mit Regex-first / LLM-second und Enrichment.

---

## Kernprinzip: Regex first, LLM second

| Stufe | Methode | Eigenschaften |
|-------|---------|---------------|
| **1. Regex / Rules** | Deterministisch, schnell, kostenlos, testbar | Ziel: **70–90 %** — erst messen, dann LLM planen |
| **2. XML-Parser** | Strukturiertes XML wenn vorhanden | Höhere Genauigkeit als body_text |
| **3. Metadata-Fallback** | category / subcategory aus SHAB | Wenn kein Keyword matcht |
| **4. LLM** | Nur bei niedriger Confidence oder Lücken | Subscription-CLI (kein Token-Budget) — gezielt einsetzen |
| **5. Enrichment** | ZEFIX, UID-BFS, GLEIF per API | Externe Dimensionen anbinden |

**Regel:** LLM wird **nie** für alles aufgerufen. Nur wenn Regex/XML unter einer Confidence-Schwelle liegen oder Felder fehlen, die für den Event-Typ erwartet werden.

---

## Was aus Raw wird

### Input (pro Publikation)

Aus `shab_publication_raw` + optional `raw_xml/{id}.xml` + `raw_html/{id}.html`:

| Feld | Quelle |
|------|--------|
| `publication_id`, `publication_date` | DB |
| `uid`, `canton`, `category`, `subcategory` | DB |
| `title`, `company_name_raw`, `body_text` | DB |
| `zefix_url`, `xml_url` | DB |
| `raw_metadata_json`, `raw_content_json` | DB |
| XML-Struktur | Dateisystem |
| `content_hash` | Für Idempotenz |

### Output (strukturiert)

```
Organization
  └── Event(s)              — 1+ pro Publikation möglich
        ├── event_type      — ORG_NEW, BANKRUPTCY_OPENED, PERSON_ADDED, …
        ├── event_date
        ├── confidence      — regex | xml | metadata | llm
        └── payload         — typ-spezifische Details

Person(s)                   — 0+ pro Publikation
  └── PersonRole            — Rolle, Unterschrift, added/removed

Case(s)                     — 0–1 pro Publikation (Konkurs, Liquidation, …)

EnrichmentSnapshot(s)       — 0+ pro UID (ZEFIX, BFS, GLEIF)
```

Eine Publikation kann **mehrere Events** enthalten (z. B. Name Change + VR-Wechsel). Der Harvester-Prototyp erkennt nur ein Event — das ist eine bewusste Erweiterung in SHAB-ANALYZER.

---

## Extraktions-Pipeline (pro Publikation)

```
┌─────────────┐
│  Raw Input  │
└──────┬──────┘
       ▼
┌─────────────┐     confidence ≥ 0.8
│ XML Parser  │─────────────────────────┐
└──────┬──────┘                         │
       │ kein XML / low confidence      │
       ▼                                │
┌─────────────┐     confidence ≥ 0.7    │
│ Regex Layer │─────────────────────────┤
│ (DE/FR/IT)  │                         │
└──────┬──────┘                         │
       │ confidence < 0.7                │
       ▼                                │
┌─────────────┐                         │
│ Metadata    │─────────────────────────┤
│ Fallback    │                         │
└──────┬──────┘                         │
       │ immer noch Lücken               │
       ▼                                │
┌─────────────┐                         │
│ LLM Extract │─────────────────────────┤
│ (structured)│                         │
└──────┬──────┘                         │
       ▼                                ▼
┌─────────────────────────────────────────┐
│           Merge + Validate              │
│  (Konflikte: Regex schlägt LLM)         │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│         Write Structured Output          │
│  + mark analyzed (content_hash)          │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│      Enrichment (wenn UID vorhanden)    │
│  ZEFIX → BFS → GLEIF (async queue)      │
└─────────────────────────────────────────┘
```

---

## Regex-Layer (Stufe 1)

### Event-Klassifikation

Erweiterung des bestehenden `EVENT_KEYWORDS` aus `analysis.py`:

| Event-Typ | Regex-Signale (DE / FR / IT) |
|-----------|------------------------------|
| `ORG_NEW` | metadata + „Neueintragung", „nouvelle inscription" |
| `ORG_DELETION` | „Löschung", „radiation", „cancellazione" |
| `ORG_NAME_CHANGE` | „Firma neu", „Nouvelle raison sociale" |
| `ORG_ADDRESS_CHANGE` | „Neue Adresse", „Sitzwechsel", „Nouveau siège" |
| `ORG_PURPOSE_CHANGE` | „Zweck neu", „Nouveau but" |
| `ORG_CAPITAL_CHANGE` | „Kapital neu", „capital social", „Kapitalerhöhung" |
| `ORG_LEGAL_FORM_CHANGE` | „Rechtsform neu", „forme juridique" |
| `ORG_MERGER` | „Fusion", „fusion", „fusione" |
| `ORG_PERSON_MUTATION` | „Eingetragene/Ausgeschiedene Personen" |
| `BANKRUPTCY_OPENED` | „Konkurs eröffnet", „ouverture de la faillite" |
| `BANKRUPTCY_CLOSED` | „Schluss des Konkursverfahrens" |
| `BANKRUPTCY_CLOSED_NO_ASSETS` | „mangels Aktiven eingestellt" |
| `LIQUIDATION` | „in Liquidation", „en liquidation" |
| `COMPOSITION_PROCEEDINGS` | „Nachlassverfahren", „sursis concordataire" |
| `OTHER` | Fallback |

**Mehrere Events:** Regex scannt `body_text` nach **allen** Matches, nicht nur dem ersten. Jeder Match → eigenes Event mit eigenem Datum (nächstes Datum nach Match-Position).

### Personen-Extraktion

| Sprache | Pattern | Status |
|---------|---------|--------|
| DE | `Nachname, Vorname, von Heimatort, in Wohnort, Rolle, mit Unterschrift` | Prototyp vorhanden |
| FR | `Nom, Prénom, originaire de …, domicilié(e) à …` | Neu |
| IT | `Cognome, Nome, originario di …, domiciliato a …` | Neu |
| Generisch | LLM-Fallback | Bei nicht gematchtem Format |

### Weitere Regex-Extraktoren

| Feld | Pattern / Quelle |
|------|------------------|
| UID | `CHE-\d{3}\.\d{3}\.\d{3}` (vorhanden) |
| Event-Datum | `dd.MM.yyyy` nächstes zum Keyword (vorhanden) |
| Konkursamt / Gericht | `Konkursamt …`, `Bezirksgericht …` (vorhanden) |
| Kapital | `CHF …`, `Kapital: …` |
| Rechtsform | AG, GmbH, Einzelfirma, Genossenschaft, … |
| Sitz / Adresse | „Sitz: …", „Domizil: …" |

### Confidence-Scoring (Regex)

```
confidence = 0.0

+ 0.5  Keyword-Match in body_text
+ 0.2  Datum gefunden (nahe Keyword)
+ 0.1  UID vorhanden
+ 0.1  category/subcategory konsistent
+ 0.1  Personen extrahiert (wenn PERSON_MUTATION)

≥ 0.7  → akzeptiert, kein LLM
< 0.7  → LLM-Queue (siehe Mess-Phase unten)
```

---

## Regex-Cases mit Agenten implementieren

Regex-Logik wird **nicht monolithisch** in einer Datei gebaut, sondern **pro Case × Sprache** als isoliertes Modul — jeweils von einem **Cursor/Claude-Agenten** implementiert, reviewed und mit Fixtures getestet.

### Warum Agenten pro Case?

| Problem ohne Aufteilung | Lösung mit Agenten |
|-------------------------|-------------------|
| 15+ Event-Typen × 3 Sprachen = 45+ Pattern-Kombinationen | Ein Agent = ein Case-Scope |
| FR/IT-Patterns unbekannt | Agent recherchiert echte SHAB-Texte aus Raw-DB |
| Regression bei Änderung | Jedes Modul hat eigene Tests + Fixtures |
| Parallelisierung | Mehrere Agenten gleichzeitig an verschiedenen Cases |

### Case-Matrix (Implementierungs-Backlog)

Jede Zelle = **ein Agent-Task** mit eigenem Modul + Tests:

| Case | DE | FR | IT | Modul |
|------|----|----|-----|-------|
| `ORG_NEW` | metadata | metadata | metadata | `cases/org_new.py` |
| `ORG_DELETION` | ○ | ○ | ○ | `cases/org_deletion.py` |
| `ORG_NAME_CHANGE` | ○ | ○ | ○ | `cases/org_name_change.py` |
| `ORG_ADDRESS_CHANGE` | ○ | ○ | ○ | `cases/org_address_change.py` |
| `ORG_PURPOSE_CHANGE` | ○ | ○ | ○ | `cases/org_purpose_change.py` |
| `ORG_CAPITAL_CHANGE` | ○ | ○ | ○ | `cases/org_capital_change.py` |
| `ORG_LEGAL_FORM_CHANGE` | ○ | ○ | ○ | `cases/org_legal_form_change.py` |
| `ORG_MERGER` | ○ | ○ | ○ | `cases/org_merger.py` |
| `ORG_PERSON_MUTATION` | ○ (Prototyp) | ○ | ○ | `cases/person_mutation.py` |
| `BANKRUPTCY_*` | ○ | ○ | ○ | `cases/bankruptcy.py` |
| `LIQUIDATION` | ○ | ○ | ○ | `cases/liquidation.py` |
| `COMPOSITION` | ○ | ○ | ○ | `cases/composition.py` |
| Felder: UID, Datum, Kapital, Sitz | ○ | ○ | ○ | `cases/fields.py` |

○ = zu implementieren · Prototyp = aus `analysis.py` portieren

### Agent-Task-Vorlage (pro Case)

Jeder Agent bekommt ein festes Briefing:

```
Task: Implement regex extractor for {CASE} in {LANG}

Input:
  - 20–50 echte body_text Samples aus shab_publication_raw
    (SQL: WHERE body_text LIKE '%{keyword}%' LIMIT 50)
  - Bestehendes analysis.py als Referenz (falls DE)
  - tests/fixtures/{case}_{lang}/

Deliverables:
  1. shab_analyzer/extractors/cases/{case}.py
     → class {Case}Extractor with .match(body_text) -> list[EventMatch]
  2. tests/test_{case}_{lang}.py
     → min. 5 positive + 3 negative Fixtures
  3. docs/cases/{case}.md
     → dokumentierte Phrasen, Edge Cases, bekannte Lücken

Constraints:
  - Nur Regex + string ops, kein LLM
  - Mehrere Matches pro Text erlaubt
  - event_date = nächstes dd.MM.yyyy nach Match-Position
  - confidence-Score gemäss Schema in PLAN.md
```

### Agent-Workflow (Reihenfolge)

```
Wave 1 — Port + DE (parallel, 4 Agenten):
  Agent A: bankruptcy.py + liquidation.py + composition.py (DE/FR/IT Keywords)
  Agent B: org_name/address/purpose_change.py (DE/FR/IT)
  Agent C: person_mutation.py DE (Port aus analysis.py)
  Agent D: fields.py (UID, Datum, Kapital, Sitz, Rechtsform)

Wave 2 — FR/IT (parallel, 3 Agenten):
  Agent E: person_mutation.py FR
  Agent F: person_mutation.py IT
  Agent G: org_* + insolvency FR/IT Patterns ergänzen

Wave 3 — XML + Integration (1 Agent):
  Agent H: xml_parser.py + Merger + Pipeline-Anbindung

Wave 4 — Messung (manuell oder Agent):
  analyze --no-llm --limit 10000 → stats → Lücken-Report
  → fehlende Cases zurück an Wave 1–2
```

### Registry-Pattern

Alle Case-Extractors registrieren sich zentral — Pipeline iteriert darüber:

```python
# shab_analyzer/extractors/registry.py
EXTRACTORS: list[CaseExtractor] = [
    OrgNewExtractor(),
    OrgNameChangeExtractor(),
    PersonMutationExtractor(),  # internally DE/FR/IT
    BankruptcyExtractor(),
    # ...
]

def extract_all(body_text: str, lang: str) -> list[EventMatch]:
    matches = []
    for ext in EXTRACTORS:
        if ext.supports(lang):
            matches.extend(ext.match(body_text))
    return deduplicate(matches)
```

### Fixtures aus echten Daten

Agenten ziehen Samples aus der Harvester-DB:

```bash
# Script: scripts/sample_for_case.sh
# Liefert body_text-Samples für einen Case → tests/fixtures/
./scripts/sample_for_case.sh "Konkurs.*eröffnet" 30 de
./scripts/sample_for_case.sh "ouverture.*faillite" 30 fr
./scripts/sample_for_case.sh "personnes inscrites" 30 fr
```

Fixtures werden **gitcommitted** — Tests laufen ohne DB/Netzwerk.

---

## Mess-Phase vor LLM

**Keine LLM-Planung ohne gemessene Regex-Abdeckung.** Prozentangaben (5 %, 15 %, 20 % LLM) sind Annahmen bis zum ersten `--no-llm` Durchlauf.

### Ablauf

```
Phase A — Sample (1–2 Tage)
  analyze --no-llm --limit 10000
  → stats, by_language, by_event_type

Phase B — Regex erweitern (Agenten Waves 1–2)
  Top-Lücken aus Report → neue Agent-Tasks
  → erneut messen

Phase C — Voll-Corpus Regex-only
  analyze --no-llm auf alle gescraped Publikationen
  → llm_queue_size = echte LLM-Zahl

Phase D — LLM nur auf Rest
  Hardware + Modell + Dauer erst JETZT planen
```

### Metriken (`python -m shab_analyzer.app stats`)

| Metrik | Bedeutung | Ziel (Regex-Phase) |
|--------|-----------|---------------------|
| `regex_ok_rate` | Event-Typ + confidence ≥ 0.7 | > 80 % |
| `other_rate` | `event_type = OTHER` | < 10 % |
| `person_miss_rate` | PERSON_MUTATION, 0 Personen | < 30 % |
| `by_language` | DE / FR / IT getrennt | FR/IT oft schlechter → Agent-Priorität |
| `by_event_type` | Treffer pro Case | Lücken = nächster Agent-Task |
| **`llm_queue_size`** | Publikationen mit confidence < 0.7 | **Basis für LLM-Planung** |
| `xml_coverage` | % mit raw_xml + Parser-Treffer | Tracken |

### Report-Ausgabe (Beispiel)

```
Analyzed:           10'000 (sample)
regex_ok:            8'420  (84.2%)
metadata_only:         612  ( 6.1%)
needs_llm:           968   ( 9.7%)  ← llm_queue_size

By language:
  de:  regex_ok 89%  llm 7%
  fr:  regex_ok 78%  llm 15%
  it:  regex_ok 71%  llm 18%

By event_type (miss rate):
  ORG_PERSON_MUTATION:  person_miss 42%  ← Agent FR/IT
  ORG_CAPITAL_CHANGE:   other 88%       ← Case fehlt
  BANKRUPTCY_OPENED:    regex_ok 95%    ← ok

→ Nächste Agent-Tasks: person_mutation FR/IT, org_capital_change DE/FR/IT
→ LLM-Schätzung: 9.7% × 2.8M ≈ 272k (nicht 420k)
```

### LLM neu schätzen (nach Phase C)

| Gemessene `llm_queue_size` | Anteil | Nächster Schritt |
|----------------------------|--------|------------------|
| < 100k | < 4 % | MacBook + NuExtract3 reicht |
| 100k–300k | 4–11 % | Mac overnight oder GEX44 2–3 Wochen |
| 300k–500k | 11–18 % | GEX44 + Regex nochmal verbessern |
| > 500k | > 18 % | Regex/XML vor LLM ausbauen, nicht LLM skalieren |

Hardware- und Modell-Entscheid (Mac / GEX44 / NuExtract3 / Claude CLI) **erst nach Phase C**.

---

Wenn `raw_xml/{publication_id}.xml` existiert, hat XML **Vorrang** vor body_text-Regex:

- Strukturierte Felder (Firma, Personen, Kapital) direkt aus XML
- Höhere Confidence (0.85+)
- Weniger LLM-Bedarf

XML und Regex werden gemerged; bei Konflikt gewinnt XML.

---

## LLM-Layer (Stufe 4)

### Wann LLM aufgerufen wird

| Bedingung | Beispiel |
|-----------|----------|
| `confidence < 0.7` nach Regex/XML | Unklarer Mutationstext |
| Event-Typ `OTHER` | Kein Keyword, keine Metadata |
| `ORG_PERSON_MUTATION` aber 0 Personen extrahiert | FR/IT-Text, unregelmässiges Format |
| Mehrere widersprüchliche Regex-Matches | Zwei Event-Typen, unklar welcher dominant |
| Explizit `--llm-all` (Debug/Reprocessing) | Force |

### Was LLM **nicht** macht

- Kein LLM für UID-Extraktion (Regex reicht)
- Kein LLM wenn Regex confidence ≥ 0.7 und alle Pflichtfelder da
- Kein LLM für Enrichment (das sind API-Calls, keine Sprachmodelle)

### Structured Output Schema

LLM liefert JSON (JSON Schema validiert):

```json
{
  "events": [
    {
      "event_type": "ORG_PERSON_MUTATION",
      "event_date": "2024-03-15",
      "summary_de": "Richard Fitzi als VR-Mitglied eingetragen",
      "persons": [
        {
          "full_name": "Fitzi, Richard",
          "place": "Altstätten",
          "role": "Mitglied des Verwaltungsrates",
          "signing_authority": "Einzelunterschrift",
          "mutation_action": "added"
        }
      ]
    }
  ],
  "confidence": 0.82,
  "language": "de"
}
```

### Subscription-CLI statt Pay-per-Token API

Statt OpenAI/Anthropic API (Pay-per-Token) nutzen wir **CLI-Tools über bestehende Subscriptions** — marginal **$0**, Limit ist das Abo-Kontingent:

| Backend | CLI / SDK | Subscription | Structured Output |
|---------|-----------|--------------|-------------------|
| **Claude Code** (empfohlen) | `claude --bare -p "..."` | Claude Pro/Max | `--output-format json --json-schema '...'` → `structured_output` |
| **Cursor** | `cursor_sdk` / Cursor Agent CLI | Cursor Pro | `Agent.prompt(...)` mit JSON-Schema im Prompt |
| **Codex** | `codex` CLI (falls verfügbar) | ChatGPT/Codex-Abo | Prompt + JSON-Parsing aus stdout |

**Empfehlung:** Claude Code Headless (`claude -p`) — native `--json-schema`, kein API-Key, läuft auf dem Server.

```
# Beispiel-Aufruf (ein Publikation)
claude --bare -p "$(cat prompt.txt)" \
  --output-format json \
  --json-schema file://extraction_schema.json \
  --max-turns 1 \
  --permission-mode dontAsk
# → jq '.structured_output'
```

**Warum CLI statt API:**
- Subscriptions sind bereits bezahlt (Cursor, Claude, ggf. Codex)
- Kein API-Key-Management, kein `total_cost_usd` pro Run
- `--json-schema` bei Claude = validiertes Structured Output out of the box

**Nachteile / Mitigation:**

| Nachteil | Mitigation |
|----------|------------|
| Langsamer als API (~2–5 s/Call wegen Prozess-Spawn) | Nur ~15 % der Publikationen → akzeptabel |
| Abo-Rate-Limits (Messages/Stunde) | `--llm-rate-limit`, 1 Worker, Batch über Nacht |
| CLI-Output kann brechen | Retry + JSON-Schema-Validierung + Fallback auf Review-Queue |
| ToS: Automation mit Subscription | Kein Massen-Parallelismus; sequentiell, caching aggressiv |

### Kontrolle (Subscription-Limits statt Dollar)

| Massnahme | Wirkung |
|-----------|---------|
| `content_hash`-Cache | Gleicher Text → kein zweiter LLM-Call |
| Batch nur `pending_llm` Queue | Nie Full-Corpus auf einmal |
| `--llm-limit N` pro Run | Abo-Kontingent schonen |
| `--llm-backend claude-cli` | Backend wählbar |
| `--llm-workers 1` | Kein Parallel-Spam gegen Abo-Limits |
| `--llm-delay 3` | Pause zwischen Calls (Sekunden) |
| Statistik: `llm_calls / total` | Ziel: messen nach Regex-Phase — Annahme < 15 % |

LLM-Volumen wird **erst nach Mess-Phase** geplant (siehe oben). Annahme 15 % × 2.8M ≈ 420k ist ein Upper-Bound, nicht der Plan.

### Merge-Regeln (Regex vs. LLM)

```
1. Regex/XML confidence ≥ LLM confidence  →  Regex/XML gewinnt
2. LLM füllt nur Lücken (fehlende Personen, fehlendes Datum)
3. LLM darf event_type nicht überschreiben wenn Regex ≥ 0.8
4. Alles mit method=llm wird in review_queue geschrieben (optional)
```

---

## Enrichment (Stufe 5)

Nach erfolgreicher Strukturierung, **asynchron** pro UID:

| Quelle | Priorität | Daten |
|--------|-----------|-------|
| **UID-Register (BFS)** | 1 | Status, MWST, NOGA, Adresse |
| **ZEFIX** | 2 | Rechtsform, Sitz, Zweck, sogcPub[] |
| **GLEIF** | 3 | LEI, Parent/Child |
| **Geocoding** | 4 | Lat/Lng (Nominatim) |
| **OpenSanctions** | 5 | Sanktions-Check |

Enrichment ist **unabhängig** von der Extraktion — kann parallel laufen. Ergebnisse in `enrichment_*`-Tabellen, verlinkt über UID.

**Priorisierung:** UIDs mit frischen SHAB-Events zuerst. Rest im Hintergrund.

---

## Event-Typen & Kategorien

Für SHAB-BI (Karte, Timeline, Filter):

| Kategorie | Event-Typen | Farbe (Karte) |
|-----------|-------------|---------------|
| `lifecycle` | ORG_NEW, ORG_DELETION | Grün / Grau |
| `structure` | ORG_NAME_CHANGE, ORG_ADDRESS_CHANGE, ORG_PURPOSE_CHANGE, ORG_CAPITAL_CHANGE, ORG_LEGAL_FORM_CHANGE, ORG_MERGER | Orange |
| `person` | ORG_PERSON_MUTATION (+ PERSON_ADDED/REMOVED im payload) | Blau |
| `insolvency` | BANKRUPTCY_*, LIQUIDATION, COMPOSITION_PROCEEDINGS | Rot |

---

## Qualität & Review

### Metriken

| Metrik | Ziel |
|--------|------|
| Regex-only Rate | > 70 % |
| LLM Rate | < 15 % |
| `OTHER` Rate | < 10 % |
| Personen extrahiert bei PERSON_MUTATION | > 60 % |
| UID Match Rate | > 95 % (aus Raw) |
| ZEFIX sogcPub vs. SHAB Events | > 90 % Übereinstimmung |

### Review Queue (optional, Phase 2)

Publikationen mit `confidence < 0.5` oder `method = llm` + `event_type = OTHER` → manuelle Review in kleiner Web-UI. Korrekturen fliessen als Training-Feedback in Regex-Verbesserungen.

---

## Idempotenz & Reprocessing

Wie im Harvester-Prototyp:

- `analyzed_state` Tabelle: `publication_id` + `content_hash` + `analyzer_version`
- Unveränderte Publikation → Skip
- Geänderte Heuristik → `--force` oder Version-Bump → Reprocess
- Regex-Änderung: kein LLM-Cache-Invalidieren nötig (content_hash gleich)
- LLM-Prompt-Änderung: `analyzer_version` bump → selektives Reprocess

---

## Abgrenzung Harvester vs. Analyzer

| | SHAB-harvester | SHAB-ANALYZER |
|---|----------------|---------------|
| Aufgabe | Scrapen, Raw speichern | Strukturieren, Enrichen |
| Browser/Playwright | Ja | Nein |
| LLM | Nein | Ja (selektiv) |
| Raw-Tabellen schreiben | Ja | **Nein** (read-only) |
| Aggregate-Tabellen | Prototyp (`analyze`) | Ja (vollständig) |
| Enrichment APIs | Nein | Ja |
| Läuft während Scrape | Ja (parallel möglich) | Nach Scrape (oder parallel auf bereits gescraped) |

Der `analyze`-Befehl im Harvester kann perspektivisch durch SHAB-ANALYZER ersetzt werden.

---

## Phasen

### Phase 0 — Mess-First Setup (1 Woche)

- Package-Grundgerüst + Registry-Pattern
- `sample_for_case.sh` — Fixtures aus Harvester-DB ziehen
- Agent-Briefing-Templates in `docs/agents/`
- **Wave 1 Agenten:** DE-Port + Insolvency + Structure-Cases
- `analyze --no-llm` + `stats` mit by_language / by_event_type / llm_queue_size
- Sample-Lauf 10k Publikationen → erster Lücken-Report

### Phase 1 — Regex-Core via Agenten (3–4 Wochen)

- **Wave 2:** FR/IT Personen + fehlende Cases aus Report
- **Wave 3:** XML-Parser + Pipeline-Integration
- Multi-Event pro Publikation
- Voll-Corpus `--no-llm` → **gemessene llm_queue_size**
- CLI: `analyze`, `analyze --no-llm`, `analyze --force`, `stats`

### Phase 2 — LLM (nur nach Phase 1 Messung)

- LLM-Backend wählen (NuExtract3 lokal / Subscription-CLI / GEX44)
- Hardware-Entscheid basierend auf **echter** llm_queue_size
- Subscription-CLI oder LM Studio / vLLM
- `analyze-llm` nur auf `llm_queue`
- `content_hash`-Cache

### Phase 3 — Enrichment (3 Wochen)

- ZEFIX, BFS, GLEIF Jobs
- Geocoding
- Cross-Check: SHAB Events vs. ZEFIX sogcPub

### Phase 4 — Integration SHAB-BI (2 Wochen)

- Output-Schema kompatibel mit SHAB-BI Silver Layer
- Sync zu Postgres
- Review-Queue UI (optional)

---

## Erfolgskriterien

1. **> 85 %** `regex_ok_rate` auf Voll-Corpus (vor LLM)
2. **> 60 %** Personen extrahiert bei PERSON_MUTATION (DE; FR/IT iterativ)
3. **`llm_queue_size` gemessen** — LLM-Rate ist Ergebnis, kein Voraussetzung
4. **Timeline-fähig:** Jede Org hat chronologische Events mit Datum + Payload
5. **SHAB-BI-ready:** Output-Schema = `silver.events`, `silver.organizations`, etc.
6. **Jeder Regex-Case:** eigenes Modul + Fixtures + Tests (via Agenten)
