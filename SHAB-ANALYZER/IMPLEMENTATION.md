# SHAB-ANALYZER — Implementierungsplan

Technischer Leitfaden für Package-Struktur, Pipeline, Regex/LLM-Layer, Enrichment und DB-Schema.

---

## 1. Projektstruktur

```
SHAB-ANALYZER/
  PLAN.md
  IMPLEMENTATION.md
  pyproject.toml
  requirements.txt
  .env.example

  shab_analyzer/
    __init__.py
    app.py                  # CLI entry point
    config.py               # Env vars, thresholds, API keys

    # --- Input ---
    reader.py               # Read raw from harvester SQLite (read-only)
    models.py                 # Dataclasses: RawPublication, StructuredEvent, ...

    # --- Extraction pipeline ---
    pipeline.py             # Orchestrator: regex → xml → llm → merge
    confidence.py           # Scoring logic

    extractors/
      __init__.py
      base.py               # CaseExtractor protocol, EventMatch dataclass
      registry.py           # EXTRACTORS list, extract_all()
      regex_events.py       # Legacy/orchestrator — delegates to cases/
      regex_persons.py
      regex_fields.py
      cases/                # Ein Modul pro Case — je von Agent implementiert
        __init__.py
        org_new.py
        org_deletion.py
        org_name_change.py
        org_address_change.py
        org_purpose_change.py
        org_capital_change.py
        org_legal_form_change.py
        org_merger.py
        person_mutation.py    # DE/FR/IT intern
        bankruptcy.py
        liquidation.py
        composition.py
        fields.py             # UID, Datum, Kapital, Sitz
      xml_parser.py         # Parse raw_xml/*.xml
      metadata_fallback.py  # category/subcategory mapping
      llm_extractor.py      # LLM structured extraction
      merger.py             # Combine regex + xml + llm results

    # --- Enrichment ---
    enrich/
      __init__.py
      base.py               # Enricher protocol + rate limiting
      uid_bfs.py            # BFS SOAP Public Services
      zefix.py              # ZEFIX REST API
      gleif.py              # GLEIF REST API
      geocode.py            # Nominatim
      sanctions.py          # OpenSanctions (Phase 3)

  # --- Storage ---
    db.py                   # Schema, migrations, upserts
    state.py                # analyzed_state, llm_cache, enrichment_queue

    # --- Jobs ---
    jobs.py                 # analyze_pending, enrich_pending, status

  tests/
    conftest.py
    fixtures/               # Sample body_text, XML, expected output
    test_regex_events.py
    test_regex_persons.py
    test_xml_parser.py
    test_confidence.py
    test_merger.py
    test_pipeline.py
    test_llm_extractor.py    # mocked LLM responses

  scripts/
    run_analyze.sh
    stats.sh
    sample_for_case.sh      # body_text Samples aus Harvester-DB → fixtures/

  docs/
    agents/
      TASK_TEMPLATE.md      # Briefing für Cursor/Claude-Agenten pro Case
      WAVE_1.md             # Agent-Tasks Wave 1 (DE + Insolvency)
      WAVE_2.md             # FR/IT Personen + Lücken aus stats
    cases/                  # Pro Case: dokumentierte Phrasen, Edge Cases
```

---

## 2. CLI

```bash
# Analyse
python -m shab_analyzer.app analyze                    # pending publications
python -m shab_analyzer.app analyze --limit 1000
python -m shab_analyzer.app analyze --force            # reprocess all
python -m shab_analyzer.app analyze-llm --limit 500 --delay 3   # nur LLM-Queue (Subscription-CLI)
python -m shab_analyzer.app analyze --no-llm           # regex/xml only

# LLM separat (Nacht-Batch, Subscription-CLI)
python -m shab_analyzer.app analyze-llm --limit 500 --delay 3
python -m shab_analyzer.app analyze-llm --backend claude-cli
python -m shab_analyzer.app analyze-llm --backend cursor-cli
python -m shab_analyzer.app analyze --publication-id <uuid>

# Enrichment
python -m shab_analyzer.app enrich                     # pending UIDs
python -m shab_analyzer.app enrich --source zefix
python -m shab_analyzer.app enrich --uid CHE-123.456.789

# Status & Stats
python -m shab_analyzer.app status
python -m shab_analyzer.app stats                      # regex/llm/other breakdown
python -m shab_analyzer.app review-queue               # low-confidence items
```

---

## 3. Konfiguration

```python
# shab_analyzer/config.py

# Paths
HARVESTER_DB_PATH = env("SHAB_HARVESTER_DB", "data/shab_harvester.sqlite")
RAW_XML_DIR = env("SHAB_RAW_XML_DIR", "data/raw_xml")
RAW_HTML_DIR = env("SHAB_RAW_HTML_DIR", "data/raw_html")

# Pipeline thresholds
CONFIDENCE_LLM_THRESHOLD = float(env("CONFIDENCE_LLM_THRESHOLD", "0.7"))
CONFIDENCE_ACCEPT_THRESHOLD = float(env("CONFIDENCE_ACCEPT_THRESHOLD", "0.5"))

# LLM — Subscription-CLI (kein Pay-per-Token)
# Backends: claude-cli | cursor-cli | codex-cli | api (Fallback)
LLM_BACKEND = env("LLM_BACKEND", "claude-cli")
LLM_CLI_PATH = env("LLM_CLI_PATH")                     # optional: absoluter Pfad zu claude/cursor/codex
LLM_CLI_TIMEOUT = int(env("LLM_CLI_TIMEOUT", "120"))   # Sekunden pro Call
LLM_BATCH_LIMIT = int(env("LLM_BATCH_LIMIT", "500"))   # max Calls pro Run (Abo schonen)
LLM_DELAY_SECONDS = float(env("LLM_DELAY_SECONDS", "2"))  # Pause zwischen Calls
LLM_MAX_RETRIES = int(env("LLM_MAX_RETRIES", "2"))

# Nur für LLM_BACKEND=api (Fallback, falls kein CLI-Abo)
LLM_API_PROVIDER = env("LLM_API_PROVIDER", "openai")
LLM_API_KEY = env("LLM_API_KEY")
LLM_API_MODEL = env("LLM_API_MODEL", "gpt-4o-mini")

# Enrichment
ZEFIX_API_USER = env("ZEFIX_API_USER")
ZEFIX_API_PASSWORD = env("ZEFIX_API_PASSWORD")
NOMINATIM_URL = env("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
ENRICHMENT_PAUSE = float(env("ENRICHMENT_PAUSE", "0.5"))  # seconds between API calls

# Versioning
ANALYZER_VERSION = "1.0.0"   # bump on breaking schema/prompt changes
```

`.env.example` mit allen Variablen und Erklärungen.

---

## 4. Datenbank-Schema

Analyzer schreibt in dieselbe SQLite-DB wie der Harvester **oder** eine eigene `shab_analyzer.sqlite`. Empfehlung: **gleiche DB**, neues Schema — Raw bleibt unberührt, Aggregate-Tabellen werden erweitert.

### 4.1 State Tracking

```sql
-- Welche Publikationen wurden analysiert?
CREATE TABLE IF NOT EXISTS analyzed_state (
    publication_id    text PRIMARY KEY,
    content_hash      text NOT NULL,
    analyzer_version  text NOT NULL,
    extraction_method text NOT NULL,    -- regex | xml | llm | mixed
    confidence        real NOT NULL,
    event_count       int DEFAULT 0,
    person_count      int DEFAULT 0,
    processed_at      text NOT NULL,
    llm_backend       text,                -- claude-cli | cursor-cli | codex-cli | api
    llm_duration_ms   int DEFAULT 0
);

-- LLM-Cache: gleicher body_text → gleiche Antwort
CREATE TABLE IF NOT EXISTS llm_cache (
    content_hash      text PRIMARY KEY,
    prompt_version    text NOT NULL,
    response_json     text NOT NULL,
    model             text NOT NULL,
    backend           text NOT NULL,       -- welches CLI hat geantwortet
    duration_ms       int,
    created_at        text NOT NULL
);

-- Enrichment Queue
CREATE TABLE IF NOT EXISTS enrichment_queue (
    uid               text PRIMARY KEY,
    sources_pending   text NOT NULL,    -- JSON: ["zefix","bfs","gleif"]
    priority          int DEFAULT 0,    -- höher = zuerst
    last_enriched_at  text,
    created_at        text NOT NULL
);
```

### 4.2 Strukturierte Output-Tabellen

Erweiterung der bestehenden Harvester-Tabellen (`organizations`, `persons`, etc.) plus neue:

```sql
-- Events (NEU — ersetzt flaches organization_publications.event_type)
CREATE TABLE IF NOT EXISTS events (
    event_id          text PRIMARY KEY,     -- sha256(pub_id + event_type + seq)
    publication_id    text NOT NULL,
    org_key           text NOT NULL,
    event_type        text NOT NULL,
    event_category    text NOT NULL,        -- lifecycle | structure | person | insolvency
    event_date        date,
    summary_de        text,
    summary_short     text,
    confidence        real NOT NULL,
    extraction_method text NOT NULL,        -- regex | xml | metadata | llm | mixed
    payload           text,                 -- JSON
    created_at        text NOT NULL
);

CREATE INDEX idx_events_pub ON events(publication_id);
CREATE INDEX idx_events_org ON events(org_key, event_date);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_date ON events(event_date);

-- organization_publications bleibt als Link-Tabelle
-- (org_key, publication_id) → events via publication_id

-- Enrichment Snapshots
CREATE TABLE IF NOT EXISTS enrichment_zefix (
    id            integer PRIMARY KEY AUTOINCREMENT,
    uid           text NOT NULL,
    fetched_at    text NOT NULL,
    name          text,
    legal_form    text,
    seat          text,
    purpose       text,
    status        text,
    sogc_pub_json text,       -- JSON array
    raw_json      text,
    UNIQUE(uid, fetched_at)
);

CREATE TABLE IF NOT EXISTS enrichment_uid_bfs (
    id              integer PRIMARY KEY AUTOINCREMENT,
    uid             text NOT NULL,
    fetched_at      text NOT NULL,
    uid_status      text,
    vat_registered  integer,    -- boolean
    noga_code       text,
    address_json    text,
    raw_xml         text
);

CREATE TABLE IF NOT EXISTS enrichment_gleif (
    id            integer PRIMARY KEY AUTOINCREMENT,
    uid           text,
    lei           text NOT NULL,
    fetched_at    text NOT NULL,
    legal_name    text,
    parent_lei    text,
    children_json text,
    entity_level  integer,
    raw_json      text
);

CREATE TABLE IF NOT EXISTS organization_geo (
    org_key       text PRIMARY KEY,
    lat           real NOT NULL,
    lng           real NOT NULL,
    seat_text     text,
    source        text DEFAULT 'nominatim',
    geocoded_at   text
);

-- Review Queue (optional)
CREATE TABLE IF NOT EXISTS review_queue (
    publication_id  text PRIMARY KEY,
    reason          text,           -- low_confidence | llm_other | conflict
    confidence      real,
    events_json     text,           -- was extrahiert wurde
    created_at      text NOT NULL,
    reviewed_at     text,
    reviewer_notes  text
);
```

### 4.3 Migration vom Harvester-Prototyp

Bestehende Tabellen (`organizations`, `persons`, `person_roles`, `cases`, `aggregate_state`) bleiben kompatibel. Migration:

1. `aggregate_state` → `analyzed_state` (umbenennen + Felder erweitern)
2. `organization_publications.event_type` → zusätzlich in `events` Tabelle
3. `events` wird Source of Truth; `organization_publications` bleibt als FK-Link

---

## 5. Pipeline-Implementierung

### 5.1 Orchestrator (`pipeline.py`)

```python
def analyze_publication(raw: RawPublication) -> AnalysisResult:
    results = []

    # Stage 1: XML (if available)
    xml_result = None
    if raw.xml_path and raw.xml_path.exists():
        xml_result = XmlExtractor().extract(raw)
        if xml_result.confidence >= CONFIDENCE_LLM_THRESHOLD:
            results.append(xml_result)

    # Stage 2: Regex
    regex_result = RegexExtractor().extract(raw)
    results.append(regex_result)

    # Stage 3: Metadata fallback (always, as baseline)
    meta_result = MetadataFallback().extract(raw)
    results.append(meta_result)

    # Merge regex + xml + metadata
    merged = Merger().merge(results)

    # Stage 4: LLM (only if needed)
    if merged.confidence < CONFIDENCE_LLM_THRESHOLD:
        if should_call_llm(merged, raw):
            cached = llm_cache_get(raw.content_hash)
            if cached:
                llm_result = cached
            else:
                llm_result = LlmExtractor().extract(raw)
                llm_cache_set(raw.content_hash, llm_result)
            merged = Merger().merge([merged, llm_result])

    # Validate
    merged = validate(merged)

    # Build structured output
    return build_analysis_result(raw, merged)
```

### 5.2 Case-Extractor Protocol + Registry

Jeder Regex-Case ist ein **eigenes Modul** in `extractors/cases/`, implementiert durch einen Agenten:

```python
# shab_analyzer/extractors/base.py
@dataclass
class EventMatch:
    event_type: str
    event_category: str
    case_type: str | None
    match_start: int
    confidence: float
    payload: dict

class CaseExtractor(Protocol):
    case_id: str                    # z.B. "bankruptcy"
    supported_languages: set[str]   # {"de", "fr", "it"}

    def match(self, body_text: str, lang: str) -> list[EventMatch]: ...
```

```python
# shab_analyzer/extractors/registry.py
from .cases.bankruptcy import BankruptcyExtractor
from .cases.person_mutation import PersonMutationExtractor
# ...

EXTRACTORS: list[CaseExtractor] = [
    BankruptcyExtractor(),
    LiquidationExtractor(),
    PersonMutationExtractor(),
    # ... Agent fügt hier ein
]

def extract_all(body_text: str, lang: str) -> list[EventMatch]:
    matches = []
    for ext in EXTRACTORS:
        if lang in ext.supported_languages:
            matches.extend(ext.match(body_text, lang))
    return deduplicate_by_position(matches)
```

### 5.3 Agent-Implementierung (Workflow)

**1. Samples ziehen** (`scripts/sample_for_case.sh`):

```bash
#!/usr/bin/env bash
# Usage: sample_for_case.sh "Konkurs.*eröffnet" 30 de bankruptcy_opened
PATTERN="$1" LIMIT="$2" LANG="$3" CASE="$4"
sqlite3 -readonly "$SHAB_RAW_DB" <<SQL
.mode list
SELECT body_text FROM shab_publication_raw
WHERE body_text REGEXP '$PATTERN'
  AND (language = '$LANG' OR language IS NULL)
LIMIT $LIMIT;
SQL | split -p '---PUBLICATION---' > "tests/fixtures/${CASE}_${LANG}/samples.txt"
```

**2. Agent-Task** (aus `docs/agents/TASK_TEMPLATE.md`):

- Input: Samples + Referenz `analysis.py` + Case-Spec aus `PLAN.md`
- Output: `cases/{case}.py` + `tests/test_{case}_{lang}.py` + `docs/cases/{case}.md`
- PR/Commit pro Case — nie alle Cases in einem Riesen-Diff

**3. Review-Kriterien pro Agent-Delivery:**

- [ ] Min. 5 positive Fixtures (echte SHAB-Texte)
- [ ] Min. 3 negative Fixtures (kein False Positive)
- [ ] Mehrere Matches pro Text wo sinnvoll
- [ ] `event_date` = nächstes Datum nach Match-Position
- [ ] FR/IT: mindestens 3 Samples aus DB getestet

**4. Integration:** Agent registriert Extractor in `registry.py` — Pipeline braucht sonst keine Änderung.

### 5.4 Regex Event Extractor (Orchestrator)

Port + Erweiterung von `analysis.py` — delegiert an Registry:

```python
class RegexEventExtractor:
    def extract(self, raw: RawPublication) -> ExtractionResult:
        lang = detect_language(raw)  # de | fr | it aus raw.language oder Heuristik
        matches = extract_all(raw.body_text or "", lang)
        events = [match_to_event(m, raw) for m in matches]
        return ExtractionResult(events=events, confidence=max_confidence(events))
```

### 5.5 Stats & Mess-Phase (`app stats`)

```python
def compute_stats(conn) -> StatsReport:
    """Nach analyze --no-llm: Abdeckung messen, llm_queue_size ableiten."""
    total = count_analyzed(conn)
    regex_ok = count_where(conn, "extraction_method IN ('regex','xml','mixed') AND confidence >= 0.7")
    needs_llm = count_where(conn, "confidence < 0.7 OR event_type = 'OTHER'")
    by_lang = group_by(conn, "language", metrics=["regex_ok_rate", "llm_rate"])
    by_event = group_by(conn, "event_type", metrics=["count", "other_rate", "person_miss_rate"])
    return StatsReport(total, regex_ok, needs_llm, by_lang, by_event)
```

CLI-Ausgabe — **`llm_queue_size`** ist die Zahl für Hardware-Planung:

```
python -m shab_analyzer.app stats
python -m shab_analyzer.app stats --by-language
python -m shab_analyzer.app stats --gaps   # Top event_types mit hoher OTHER/miss Rate
```

Entscheidungsregel: LLM-Backend und Hardware **erst nach** `stats` auf Voll-Corpus (`--no-llm`).

### 5.6 XML Parser (`extractors/xml_parser.py`)

```python
class XmlExtractor:
    """Parse eCH-structured commercial register XML when available."""

    def extract(self, raw: RawPublication) -> ExtractionResult:
        tree = ET.parse(raw.xml_path)
        # eCH-0097 / SOGC XML structure
        org = extract_org_from_xml(tree)
        persons = extract_persons_from_xml(tree)
        events = infer_events_from_xml(tree, raw)

        return ExtractionResult(
            events=events,
            persons=persons,
            org_fields=org,
            confidence=0.85,
            method="xml",
        )
```

XML-Struktur aus echten `raw_xml/*.xml` Samples ableiten (Fixture in Tests).

### 5.7 LLM Extractor — Subscription-CLI Backends

Statt API-Calls: **Subprocess zu CLI-Tools**, die über bestehende Abos laufen.

```
shab_analyzer/llm/
  __init__.py
  schema.py              # EXTRACTION_SCHEMA (JSON Schema Datei)
  prompts.py             # System + User Prompt Templates
  backends/
    __init__.py
    base.py              # LlmBackend Protocol
    claude_cli.py        # claude --bare -p (empfohlen)
    cursor_cli.py        # cursor_sdk Agent.prompt
    codex_cli.py         # codex CLI (optional)
    api.py               # OpenAI/Anthropic API (nur Fallback)
  client.py              # get_backend() → LlmBackend
```

#### Backend-Protocol

```python
class LlmBackend(Protocol):
    name: str

    def extract(self, system: str, user: str, schema: dict) -> tuple[dict, int]:
        """Returns (structured_output, duration_ms). Raises LlmError on failure."""
```

#### Claude CLI (empfohlen)

```python
class ClaudeCliBackend:
    """Uses Claude Code subscription via headless CLI."""

    name = "claude-cli"

    def extract(self, system: str, user: str, schema: dict) -> tuple[dict, int]:
        schema_path = write_temp_json(schema)
        prompt = f"{system}\n\n{user}"

        cmd = [
            self.cli_path or "claude",
            "--bare",
            "-p", prompt,
            "--output-format", "json",
            "--json-schema", f"file://{schema_path}",
            "--max-turns", "1",
            "--permission-mode", "dontAsk",
        ]
        start = time.monotonic()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=LLM_CLI_TIMEOUT)
        duration_ms = int((time.monotonic() - start) * 1000)

        if result.returncode != 0:
            raise LlmError(f"claude exited {result.returncode}: {result.stderr}")

        payload = json.loads(result.stdout)
        structured = payload.get("structured_output") or payload.get("result")
        if isinstance(structured, str):
            structured = json.loads(structured)
        jsonschema.validate(structured, schema)
        return structured, duration_ms
```

**Voraussetzung auf dem Server:** `claude` CLI installiert + eingeloggt (`claude auth login`).

#### Cursor CLI / SDK

```python
class CursorCliBackend:
    """Uses Cursor subscription via cursor_sdk."""

    name = "cursor-cli"

    def extract(self, system: str, user: str, schema: dict) -> tuple[dict, int]:
        from cursor_sdk import Agent

        prompt = f"{system}\n\n{user}\n\nAntworte NUR mit JSON gemäss Schema:\n{json.dumps(schema)}"
        start = time.monotonic()
        result = Agent.prompt(prompt, local={"cwd": "/tmp"})
        duration_ms = int((time.monotonic() - start) * 1000)

        structured = json.loads(extract_json_from_text(result.result))
        jsonschema.validate(structured, schema)
        return structured, duration_ms
```

**Voraussetzung:** Cursor CLI/SDK installiert, Subscription aktiv. Kein separater API-Key wenn über lokale Auth.

#### Codex CLI (optional)

```python
class CodexCliBackend:
    """OpenAI Codex CLI wenn im Abo verfügbar — gleiches Pattern wie Claude."""

    name = "codex-cli"

    def extract(self, system: str, user: str, schema: dict) -> tuple[dict, int]:
        # codex -p "..." oder projektspezifisches CLI
        # Prompt enthält JSON-Schema, stdout parsen
        ...
```

Falls `codex` CLI bei dir anders heisst — Backend ist austauschbar via `LLM_BACKEND`.

#### API Fallback (nur wenn nötig)

```python
class ApiBackend:
    """Pay-per-Token — nur wenn kein CLI-Abo auf dem Server."""
    name = "api"
    # openai / anthropic SDK mit response_format json_schema
```

#### Client + Retry

```python
def call_llm(system: str, user: str, schema: dict) -> tuple[dict, int]:
    backend = get_backend(LLM_BACKEND)  # aus config
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            return backend.extract(system, user, schema)
        except (LlmError, json.JSONDecodeError, jsonschema.ValidationError) as e:
            if attempt == LLM_MAX_RETRIES:
                raise
            time.sleep(LLM_DELAY_SECONDS * (attempt + 1))
    raise LlmError("unreachable")
```

#### LLM Extractor

```python
SYSTEM_PROMPT = """Du extrahierst strukturierte Events aus Schweizer SHAB-Publikationen
(Handelsregister). Antworte NUR mit validem JSON gemäss Schema.
Sprachen: Deutsch, Französisch, Italienisch."""

class LlmExtractor:
    def extract(self, raw: RawPublication) -> ExtractionResult:
        prompt = build_user_prompt(raw)
        structured, duration_ms = call_llm(SYSTEM_PROMPT, prompt, EXTRACTION_SCHEMA)
        result = ExtractionResult.from_llm(structured)
        result.llm_duration_ms = duration_ms
        return result
```

#### Batch-Strategie für Subscription-Limits

```bash
# Nacht-Job: langsam, sequentiell, Abo-schonend
python -m shab_analyzer.app analyze --llm-limit 2000 --llm-delay 3

# Oder dedizierte LLM-Queue (nur pending_llm, Regex schon durch)
python -m shab_analyzer.app analyze-llm --limit 500 --delay 5
```

| Parameter | Empfehlung | Warum |
|-----------|------------|-------|
| `--llm-workers` | **1** | Abo-Limits, kein Parallel-Spam |
| `--llm-delay` | **2–5 s** | Rate-Limit der Subscription |
| `--llm-limit` | **500–2000/Run** | Über Nächte verteilen |
| Cache | **immer an** | 390k unique texts << 390k calls |

**EXTRACTION_SCHEMA** (JSON Schema für Structured Output):

```json
{
  "type": "object",
  "required": ["events"],
  "properties": {
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["event_type", "event_date"],
        "properties": {
          "event_type": { "type": "string", "enum": ["ORG_NEW", "..."] },
          "event_date": { "type": "string", "format": "date" },
          "summary_de": { "type": "string" },
          "persons": { "type": "array", "items": { "$ref": "#/person" } },
          "capital": { "type": "string" },
          "new_name": { "type": "string" },
          "new_address": { "type": "string" }
        }
      }
    },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "language": { "type": "string", "enum": ["de", "fr", "it"] }
  }
}
```

### 5.5 Merger (`extractors/merger.py`)

```python
class Merger:
    def merge(self, results: list[ExtractionResult]) -> ExtractionResult:
        # Sort by confidence descending
        ranked = sorted(results, key=lambda r: r.confidence, reverse=True)
        primary = ranked[0]

        merged_events = list(primary.events)
        merged_persons = list(primary.persons)

        for other in ranked[1:]:
            # Add events not already covered (by type + date)
            for event in other.events:
                if not event_covered(event, merged_events):
                    if other.confidence >= primary.confidence * 0.8:
                        merged_events.append(event)

            # Fill person gaps
            if not merged_persons and other.persons:
                merged_persons = other.persons

        return ExtractionResult(
            events=deduplicate_events(merged_events),
            persons=merged_persons,
            confidence=primary.confidence,
            method="mixed" if len(ranked) > 1 else primary.method,
        )
```

---

## 6. Enrichment-Implementierung

### 6.1 Queue-basiert

```python
def enqueue_enrichment(uid: str, priority: int = 0):
    """Called after analyze when UID is present."""
    upsert_enrichment_queue(uid, sources=["bfs", "zefix", "gleif"], priority=priority)

def run_enrichment(limit: int = 100, source: str | None = None):
    items = get_pending_enrichment(limit, source)
    for item in items:
        uid = item["uid"]
        for src in item["sources_pending"]:
            enricher = ENRICHERS[src]  # uid_bfs, zefix, gleif, geocode
            try:
                enricher.enrich(uid)
                mark_source_done(uid, src)
            except RateLimitError:
                break  # stop batch, retry later
            time.sleep(ENRICHMENT_PAUSE)
```

### 6.2 Enricher: UID-BFS (`enrich/uid_bfs.py`)

```python
class UidBfsEnricher:
    WSDL = "https://www.uid-wse.admin.ch/V5.0/PublicServices.svc?wsdl"

    def enrich(self, uid: str) -> None:
        client = ZeepClient(self.WSDL)
        result = client.service.GetOrganisationDetails(uid=format_uid(uid))
        insert_enrichment_uid_bfs(uid, parse_bfs_response(result))
        merge_org_fields(uid, noga=..., vat=..., status=...)
```

### 6.3 Enricher: ZEFIX (`enrich/zefix.py`)

```python
class ZefixEnricher:
    BASE = "https://www.zefix.admin.ch/ZefixPublicREST/api/v1"

    def enrich(self, uid: str) -> None:
        resp = requests.get(
            f"{self.BASE}/company/uid/{uid}",
            auth=(ZEFIX_API_USER, ZEFIX_API_PASSWORD),
        )
        data = resp.json()
        insert_enrichment_zefix(uid, data)
        merge_org_fields(uid, legal_form=..., seat=..., purpose=...)
        cross_check_sogc_pub(uid, data.get("sogcPub", []))
```

### 6.4 Enricher: GLEIF (`enrich/gleif.py`)

```python
class GleifEnricher:
    BASE = "https://api.gleif.org/api/v1"

    def enrich(self, uid: str) -> None:
        # Search by registration authority (RA000548 = Switzerland)
        resp = requests.get(f"{self.BASE}/lei-records", params={
            "filter[registration.authority.id]": "RA000548",
            "filter[registration.initialRegistrationId]": uid.replace("CHE-", "").replace(".", ""),
        })
        records = resp.json()["data"]
        if records:
            insert_enrichment_gleif(uid, records[0])
```

### 6.5 Cross-Check: SHAB vs. ZEFIX sogcPub

```python
def cross_check_sogc_pub(uid: str, sogc_pub: list[dict]) -> None:
    """Flag publications in SHAB not in ZEFIX sogcPub and vice versa."""
    our_events = get_events_for_uid(uid)
    zefix_dates = {p["sogcDate"] for p in sogc_pub}
    our_dates = {e.event_date for e in our_events}

    missing_in_ours = zefix_dates - our_dates
    missing_in_zefix = our_dates - zefix_dates

    if missing_in_ours or missing_in_zefix:
        log_warning(f"UID {uid}: sogc mismatch. missing_ours={missing_in_ours}")
```

---

## 7. Reader (Input aus Harvester)

```python
class HarvesterReader:
    """Read-only access to harvester SQLite."""

    def __init__(self, db_path: Path):
        # URI mode=ro prevents accidental writes and avoids lock conflicts
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def pending_publications(self, limit: int | None = None, force: bool = False) -> list[RawPublication]:
        if force:
            query = "SELECT * FROM shab_publication_raw ORDER BY publication_date"
        else:
            query = """
                SELECT r.* FROM shab_publication_raw r
                LEFT JOIN analyzed_state a ON a.publication_id = r.publication_id
                WHERE a.publication_id IS NULL
                   OR a.content_hash != r.content_hash
                   OR a.analyzer_version != ?
                ORDER BY r.publication_date
            """
        # ...

    def raw_xml_path(self, publication_id: str, publication_date: str) -> Path | None:
        year, month = publication_date[:4], publication_date[5:7]
        path = RAW_XML_DIR / year / month / f"{publication_id}.xml"
        return path if path.exists() else None
```

**Wichtig:** `mode=ro` — Analyzer läuft parallel zum Scraper ohne Lock-Konflikte. Writes gehen über separate Write-Connection.

---

## 8. Jobs & Remote-Ausführung

### 8.1 analyze_pending Job

```python
def analyze_pending(limit: int | None = None, force: bool = False, llm_limit: int | None = None, no_llm: bool = False):
    reader = HarvesterReader(HARVESTER_DB_PATH)
    writer = AnalyzerWriter(HARVESTER_DB_PATH)  # write connection
    llm_calls = 0

    for raw in reader.pending_publications(limit, force):
        result = analyze_publication(raw, no_llm=no_llm or (llm_limit and llm_calls >= llm_limit))
        writer.save_result(result)
        if result.llm_used:
            llm_calls += 1
        if raw.uid:
            enqueue_enrichment(raw.uid, priority=priority_for(raw))
        writer.commit()
```

### 8.2 Remote Script

```bash
# scripts/run_analyze.sh
#!/usr/bin/env bash
# Analog zu scrape-all.sh — läuft in tmux auf dem Server
source scripts/remote/_common.sh

"${SSH[@]}" bash -s <<'EOF'
cd /opt/shab-analyzer
source .venv/bin/activate
while true; do
  python -m shab_analyzer.app analyze --limit 5000
  remaining=$(python -m shab_analyzer.app status --pending)
  echo "remaining: $remaining"
  [ "$remaining" -eq 0 ] && break
  sleep 10
done
EOF
```

Analyzer kann **parallel zum Scraper** laufen — verarbeitet bereits gescrapte Publikationen während Scrape weiterläuft.

---

## 9. Tests

### 9.1 Fixture-basiert (kein LLM, kein Netzwerk)

```
tests/fixtures/
  de_person_mutation.txt          # body_text sample
  de_bankruptcy.txt
  fr_person_mutation.txt
  de_name_change.txt
  multi_event.txt                 # Name + Person in einer Publikation
  sample.xml                      # eCH XML
  expected/
    de_person_mutation.json       # expected extraction output
```

### 9.2 Test-Kategorien

| Test | Was |
|------|-----|
| `test_regex_events.py` | Jedes Event-Keyword matcht + nicht-matcht |
| `test_regex_persons.py` | DE/FR Personen-Extraktion |
| `test_xml_parser.py` | XML → Events + Persons |
| `test_confidence.py` | Scoring-Logik |
| `test_merger.py` | Regex + LLM Merge-Regeln |
| `test_pipeline.py` | End-to-End mit Fixtures |
| `test_llm_extractor.py` | Mocked LLM, Schema-Validierung |
| `test_db.py` | Idempotenz, content_hash skip, force rebuild |

### 9.3 LLM-Tests mit Mock

```python
@pytest.fixture
def mock_llm(monkeypatch):
    def fake_call(system, user, schema):
        return FIXTURES["llm_response_de_person.json"]
    monkeypatch.setattr("shab_analyzer.extractors.llm_extractor.call_llm", fake_call)
```

---

## 10. Output für SHAB-BI

Analyzer-Output ist direkt kompatibel mit SHAB-BI Silver Layer:

| Analyzer Tabelle | SHAB-BI Tabelle | Sync |
|------------------|-----------------|------|
| `events` | `silver.events` | 1:1 |
| `organizations` | `silver.organizations` | 1:1 |
| `persons` + `person_roles` | `silver.persons` + `silver.person_roles` | 1:1 |
| `cases` | (in events + payload) | 1:1 |
| `organization_geo` | `silver.organization_geo` | 1:1 |
| `enrichment_*` | `bronze.enrichment_*` | 1:1 |

SHAB-BI `sync_sqlite.py` liest diese Tabellen incremental → Postgres.

**Zusätzlich baut Analyzer** `org_timeline_states` (für animierte Timeline):

```python
def build_org_timeline(org_key: str, writer: AnalyzerWriter):
    events = writer.get_events(org_key, order="event_date")
    state = empty_org_state()
    for i, event in enumerate(events):
        state = apply_event_delta(state, event)
        writer.upsert_timeline_state(org_key, i, event, state)
```

---

## 11. Performance-Schätzung

| Schritt | Durchsatz | 2.6M Publikationen |
|---------|-----------|---------------------|
| Regex only | ~500/s | ~1.5 h |
| + XML (30 % haben XML) | ~200/s | ~3.5 h |
| LLM (Anteil aus `llm_queue_size`) | variabel | erst nach Mess-Phase schätzen |
| Enrichment ZEFIX (500k UIDs) | ~2/s | ~70 h |
| Enrichment BFS | ~5/s | ~28 h |
| GLEIF (~150k LEIs) | ~3/s | ~14 h |

\*LLM über Nächte/Wochen verteilt (`--llm-limit 2000/night`). Mit aggressivem Cache oft deutlich weniger Calls. **$0 Token-Kosten** — Limit ist Abo-Kontingent, nicht Budget.

**Gesamt erster Durchlauf:** ~3–5 Tage (parallelisierbar). Incremental danach: Minuten pro Tag.

### Parallelisierung

```bash
# 4 Worker, Publication-ID-Range split
python -m shab_analyzer.app analyze --worker 0 --workers 4
python -m shab_analyzer.app analyze --worker 1 --workers 4
# ...
```

Jeder Worker: eigene Publication-ID-Range, eigene Write-Connection. Kein Lock da verschiedene Rows.

---

## 12. Implementierungsreihenfolge

### Sprint 0 (Woche 1): Fundament + Agent-Setup

- [ ] `pyproject.toml`, `config.py`, `models.py`, `CaseExtractor` Protocol
- [ ] `registry.py` + leere `cases/` Struktur
- [ ] `reader.py`, `db.py` Schema
- [ ] `docs/agents/TASK_TEMPLATE.md`, `WAVE_1.md`
- [ ] `scripts/sample_for_case.sh`
- [ ] `stats` CLI (by_language, by_event_type, llm_queue_size)
- [ ] **Agent Wave 1:** bankruptcy, liquidation, composition, org_name/address (DE/FR/IT)

### Sprint 1 (Woche 2–3): Regex via Agenten

- [ ] **Agent Wave 1 fertig** + Tests + Fixtures pro Case
- [ ] **Agent Wave 2:** person_mutation FR/IT, org_capital, org_merger, fields
- [ ] `pipeline.py --no-llm`, Multi-Event
- [ ] Sample-Lauf 10k → stats → Lücken-Report → Wave-2-Prioritäten

### Sprint 2 (Woche 4–5): XML + Voll-Messung

- [ ] **Agent Wave 3:** xml_parser.py
- [ ] `merger.py`, `confidence.py`, `metadata_fallback.py`
- [ ] Voll-Corpus `analyze --no-llm` → **gemessene llm_queue_size**
- [ ] Hardware/LLM-Entscheid dokumentieren

### Sprint 3 (Woche 6–7): LLM (nur Rest-Queue)

- [ ] LLM-Backend (NuExtract3 / lmstudio / claude-cli / GEX44) nach Messung
- [ ] `analyze-llm` auf `llm_queue` only
- [ ] `llm_cache`, Rate-Limiting

### Sprint 4 (Woche 8–9): Enrichment + BI

- [ ] ZEFIX, BFS, GLEIF, Geocode
- [ ] SHAB-BI Schema-Export
- [ ] Remote Deployment

---

## 13. Abhängigkeiten

```txt
# requirements.txt
zeep>=4.2              # BFS SOAP
requests>=2.31
jsonschema>=4.20       # LLM output validation
python-dotenv>=1.0

# Optional — nur für LLM_BACKEND=cursor-cli
# cursor-sdk>=0.1

# Optional — nur für LLM_BACKEND=api (Fallback)
# openai>=1.0
```

Kein Playwright, kein Browser, **kein OpenAI/Anthropic SDK nötig** wenn Subscription-CLI genutzt wird.

---

## 14. Monitoring & Stats

```bash
python -m shab_analyzer.app stats
```

Ausgabe:

```
Analyzed:        1'245'000 / 2'613'340  (47.6%)
Pending:         1'368'340

Extraction method:
  regex:           892'000  (71.6%)
  xml:               186'000  (14.9%)
  metadata:           62'000  ( 5.0%)
  llm:                78'000  ( 6.3%)
  mixed:              27'000  ( 2.2%)

Event types:
  ORG_PERSON_MUTATION:  412'000
  ORG_NEW:              198'000
  ORG_MUTATION_OTHER:   156'000
  OTHER:                 89'000  (7.1%)
  ...

Enrichment:
  UIDs queued:       340'000
  ZEFIX done:        125'000
  BFS done:          130'000
  GLEIF done:         45'000

LLM (subscription CLI):
  Backend:           claude-cli
  Calls total:        78'000
  Cache hits:        312'000  (80% saved)
  Avg duration:       3.2s/call
  Est. token cost:    $0.00 (subscription)
```
