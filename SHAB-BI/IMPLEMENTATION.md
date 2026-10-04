# SHAB-BI — Implementierungsplan

Technischer Leitfaden für Datenbank, ETL, API, Frontend, Auth und Billing.

---

## 1. Gesamtarchitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGEST (bestehend)                       │
│  SHAB-harvester (SQLite remote)  │  Enrichment APIs (HTTP)      │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     ETL / ORCHESTRATION                         │
│  sync_sqlite.py  │  enrich_*.py  │  geocode.py  │  dbt run      │
│  Scheduler: cron / systemd timer / GitHub Actions                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              PostgreSQL 16 + PostGIS 3.4                        │
│  Bronze → Silver → Gold  │  Auth/Billing tables                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     FastAPI (Read API)                          │
│  REST + JWT  │  Rate limits per tier  │  Pre-aggregated endpoints│
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Next.js 15 (App Router)                     │
│  MapLibre GL  │  Framer Motion  │  TanStack Query  │  Stripe     │
└─────────────────────────────────────────────────────────────────┘
```

**Prinzipien:**
- Harvester-SQLite bleibt **Operations-DB** — Analytics läuft nur auf Postgres
- Dashboard fragt **nie** Bronze-Tabellen direkt ab — nur Gold + wenige Silver-Views
- Geo-Events sind **vorberechnet** — Karte lädt Tiles/Chunks, nicht 2.6M Punkte live
- Auth/Billing in derselben Postgres-Instanz (eigenes Schema `app`)

---

## 2. Infrastruktur

### Empfohlenes Setup (Start)

| Komponente | Lösung | Warum |
|------------|--------|-------|
| DB | PostgreSQL 16 + PostGIS auf Hetzner / Supabase / Neon | PostGIS native, günstig |
| API | FastAPI + uvicorn | Python-Ökosystem, passt zu ETL |
| Frontend | Next.js auf Vercel | SSR, Edge, gut für Maps |
| Auth | Clerk oder Auth.js + Postgres | Schnell, OAuth, Magic Link |
| Billing | Stripe Subscriptions | Trial + monatlich |
| ETL | Python-Skripte + dbt | Gleiche Sprache wie Harvester |
| Object Storage | S3 / Hetzner Object Storage | Raw-HTML-Archive optional |
| Cache | Redis (optional Phase 2) | API-Response-Cache für Pulse |

### Docker Compose (lokal)

```yaml
# infra/docker-compose.yml (geplant)
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: shab_bi
      POSTGRES_USER: shab_bi
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

PostGIS-Extension beim ersten Start:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- Fuzzy-Suche
CREATE EXTENSION IF NOT EXISTS btree_gin;
```

---

## 3. Datenbank-Schema

Medallion-Architektur in Postgres-Schemas:

```
bronze.*   — Rohimport (1:1 aus Quellen)
silver.*   — Normalisierte Entitäten
gold.*     — Aggregates für Dashboard/API
app.*      — Users, Subscriptions, Usage
```

### 3.1 Bronze (Raw Import)

```sql
CREATE SCHEMA bronze;

-- Aus SHAB-harvester SQLite (incremental sync)
CREATE TABLE bronze.shab_publication_raw (
  publication_id    text PRIMARY KEY,
  publication_date  date,
  uid               text,
  canton            text,
  category          text,
  subcategory       text,
  title             text,
  company_name_raw  text,
  body_text         text,
  zefix_url         text,
  xml_url           text,
  content_hash      text,
  scraped_at        timestamptz,
  synced_at         timestamptz DEFAULT now()
);

CREATE TABLE bronze.import_day (...);  -- Harvester-Progress, optional

-- Enrichment Snapshots (versioniert, nie überschreiben)
CREATE TABLE bronze.enrichment_zefix (
  id          bigserial PRIMARY KEY,
  uid         text NOT NULL,
  fetched_at  timestamptz NOT NULL,
  name        text,
  legal_form  text,
  seat        text,
  purpose     text,
  status      text,
  sogc_pub    jsonb,
  raw_json    jsonb,
  UNIQUE (uid, fetched_at)
);

CREATE TABLE bronze.enrichment_uid_bfs (
  id              bigserial PRIMARY KEY,
  uid             text NOT NULL,
  fetched_at      timestamptz NOT NULL,
  uid_status      text,
  vat_registered  boolean,
  noga_code       text,
  address_json    jsonb,
  raw_xml         text
);

CREATE TABLE bronze.enrichment_gleif (
  id              bigserial PRIMARY KEY,
  uid             text,
  lei             text NOT NULL,
  fetched_at      timestamptz NOT NULL,
  legal_name      text,
  parent_lei      text,
  children        jsonb,
  entity_level    int,
  raw_json        jsonb
);

CREATE TABLE bronze.enrichment_opencorp (...);
CREATE TABLE bronze.enrichment_sanctions (...);
CREATE TABLE bronze.enrichment_six (...);
CREATE TABLE bronze.enrichment_patents (...);
```

**Regel:** Bronze ist append-only. `fetched_at` + `uid`/`lei` = Version. Gold-Views nehmen immer `MAX(fetched_at)`.

### 3.2 Silver (Normalisiert)

```sql
CREATE SCHEMA silver;

-- Organisationen (aus analyze + Enrichment merged)
CREATE TABLE silver.organizations (
  org_key           text PRIMARY KEY,     -- uid:CHE-... oder cand:...
  uid               text UNIQUE,
  lei               text,
  name_current      text NOT NULL,
  legal_form        text,
  legal_seat        text,
  canton            text,
  noga_code         text,
  uid_status        text,
  zefix_status      text,
  vat_registered    boolean,
  match_confidence  text,                 -- HIGH / LOW
  first_seen_at     date,
  last_seen_at      date,
  publication_count int DEFAULT 0,
  zefix_url         text,
  wikidata_qid      text,
  is_listed_six     boolean DEFAULT false,
  is_finma_regulated boolean DEFAULT false,
  on_sanctions_list boolean DEFAULT false,
  updated_at        timestamptz DEFAULT now()
);

CREATE INDEX idx_orgs_uid ON silver.organizations(uid);
CREATE INDEX idx_orgs_canton ON silver.organizations(canton);
CREATE INDEX idx_orgs_noga ON silver.organizations(noga_code);
CREATE INDEX idx_orgs_name_trgm ON silver.organizations
  USING gin (name_current gin_trgm_ops);

-- Geo: ein Punkt pro Organisation (aus Geocoding des Sitzes)
CREATE TABLE silver.organization_geo (
  org_key     text PRIMARY KEY REFERENCES silver.organizations(org_key),
  seat_text   text,
  lat         double precision NOT NULL,
  lng         double precision NOT NULL,
  geom        geography(POINT, 4326) NOT NULL,  -- PostGIS
  geocode_source text DEFAULT 'nominatim',
  geocoded_at timestamptz
);

CREATE INDEX idx_org_geo_geom ON silver.organization_geo USING gist(geom);

-- Events (Kern für Timeline + Karte)
CREATE TABLE silver.events (
  event_id          text PRIMARY KEY,     -- hash(org_key + publication_id + event_type)
  org_key           text REFERENCES silver.organizations(org_key),
  publication_id    text,
  event_date        date NOT NULL,
  event_type        text NOT NULL,        -- ORG_NEW, BANKRUPTCY_OPENED, PERSON_ADDED, ...
  event_category    text NOT NULL,        -- lifecycle | person | structure | insolvency
  summary_de        text,
  summary_short     text,
  confidence        text,
  payload           jsonb,                -- Deltas, Personen, etc.
  created_at        timestamptz DEFAULT now()
);

CREATE INDEX idx_events_date ON silver.events(event_date);
CREATE INDEX idx_events_org ON silver.events(org_key, event_date);
CREATE INDEX idx_events_type ON silver.events(event_type);
CREATE INDEX idx_events_category ON silver.events(event_category);

-- Geo-Events: Events mit Koordinaten für die Karte
CREATE TABLE silver.geo_events (
  event_id      text PRIMARY KEY REFERENCES silver.events(event_id),
  org_key       text NOT NULL,
  event_date    date NOT NULL,
  event_type    text NOT NULL,
  event_category text NOT NULL,
  lat           double precision NOT NULL,
  lng           double precision NOT NULL,
  geom          geography(POINT, 4326) NOT NULL,
  name          text,                     -- Firmenname für Tooltip
  color         text                      -- vordefiniert pro category
);

CREATE INDEX idx_geo_events_geom ON silver.geo_events USING gist(geom);
CREATE INDEX idx_geo_events_date ON silver.geo_events(event_date);
CREATE INDEX idx_geo_events_type ON silver.geo_events(event_type);

-- Personen
CREATE TABLE silver.persons (
  person_key        text PRIMARY KEY,
  full_name         text NOT NULL,
  normalized_name   text,
  place             text
);

CREATE TABLE silver.person_roles (
  id                    bigserial PRIMARY KEY,
  person_key            text REFERENCES silver.persons(person_key),
  org_key               text REFERENCES silver.organizations(org_key),
  publication_id        text,
  role                  text,
  signing_authority     text,
  mutation_action       text,             -- added | removed
  valid_from            date,
  event_id              text REFERENCES silver.events(event_id)
);

-- Konzernstruktur (aus GLEIF)
CREATE TABLE silver.corporate_group (
  lei             text PRIMARY KEY,
  org_key         text REFERENCES silver.organizations(org_key),
  parent_lei      text,
  entity_level    int,
  legal_name      text
);

CREATE INDEX idx_corp_parent ON silver.corporate_group(parent_lei);

-- Firmen-Timeline: vorberechnete States
CREATE TABLE silver.org_timeline_states (
  org_key       text NOT NULL,
  event_index   int NOT NULL,             -- 0-basiert, chronologisch
  event_id      text REFERENCES silver.events(event_id),
  event_date    date NOT NULL,
  state_json    jsonb NOT NULL,           -- { name, status, directors[], ... }
  PRIMARY KEY (org_key, event_index)
);
```

### 3.3 Gold (Dashboard/API)

```sql
CREATE SCHEMA gold;

-- Schweiz Pulse: tägliche Aggregationen
CREATE TABLE gold.daily_stats (
  stat_date       date PRIMARY KEY,
  org_new         int DEFAULT 0,
  bankruptcy      int DEFAULT 0,
  liquidation     int DEFAULT 0,
  person_mutation int DEFAULT 0,
  other           int DEFAULT 0,
  total           int DEFAULT 0
);

-- Monatliche Stats (für Charts)
CREATE TABLE gold.monthly_stats (
  year_month      date PRIMARY KEY,       -- ersten des Monats
  org_new         int,
  bankruptcy      int,
  liquidation     int,
  by_canton       jsonb,                  -- { "ZH": 412, "ZG": 198, ... }
  by_noga         jsonb,
  by_legal_form   jsonb
);

-- Top-Listen (täglich/refreshed)
CREATE TABLE gold.top_lists (
  list_id         text NOT NULL,          -- most_changes_30d, newest_companies, ...
  as_of           date NOT NULL,
  rank            int NOT NULL,
  org_key         text,
  person_key      text,
  metric_value    numeric,
  payload         jsonb,
  PRIMARY KEY (list_id, as_of, rank)
);

-- Karten-Tiles: voraggregierte Event-Counts pro Gitterzelle + Zeitraum
-- Alternative zu 2.6M einzelnen Punkten auf niedrigem Zoom
CREATE TABLE gold.map_grid_daily (
  grid_date       date NOT NULL,
  event_category  text NOT NULL,
  cell_x          int NOT NULL,           -- Web-Mercator Tile oder H3
  cell_y          int NOT NULL,
  event_count     int NOT NULL,
  sample_events   jsonb,                  -- max 5 Event-IDs für Drill-Down
  PRIMARY KEY (grid_date, event_category, cell_x, cell_y)
);

-- Personen-Aggregate
CREATE TABLE gold.person_stats (
  person_key          text PRIMARY KEY,
  full_name           text,
  active_mandate_count int,
  total_mandate_count  int,
  solo_sig_count       int,
  org_keys             text[]
);
```

### 3.4 App-Schema (Auth & Billing)

```sql
CREATE SCHEMA app;

CREATE TABLE app.users (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email           text UNIQUE NOT NULL,
  name            text,
  clerk_id        text UNIQUE,            -- oder auth.js subject
  created_at      timestamptz DEFAULT now(),
  trial_ends_at   timestamptz,            -- created_at + 30 days
  stripe_customer_id text
);

CREATE TYPE app.subscription_tier AS ENUM ('trial', 'free', 'premium', 'cancelled');

CREATE TABLE app.subscriptions (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid REFERENCES app.users(id),
  tier                app.subscription_tier NOT NULL DEFAULT 'trial',
  stripe_subscription_id text,
  current_period_end  timestamptz,
  created_at          timestamptz DEFAULT now(),
  updated_at          timestamptz DEFAULT now()
);

-- Usage Tracking für Free-Limits
CREATE TABLE app.usage (
  user_id       uuid REFERENCES app.users(id),
  usage_date    date NOT NULL,
  org_views     int DEFAULT 0,            -- Firmen-Timeline Views
  searches      int DEFAULT 0,
  exports       int DEFAULT 0,
  PRIMARY KEY (user_id, usage_date)
);
```

---

## 4. PostGIS & Geo-Daten

### Warum PostGIS?

- **`geography(POINT, 4326)`** — korrekte Distanzen auf der Erdkugel (Meter)
- **GIST-Index** — räumliche Queries in Millisekunden
- **ST_Within, ST_DWithin** — „Events im Kanton ZH"
- **ST_ClusterKMeans** — Heatmap-Aggregation serverseitig
- Kompatibel mit MapLibre / deck.gl / Leaflet

### Geocoding-Strategie

```
1. Sitz-Text aus ZEFIX oder SHAB (legal_seat, company_block_text)
2. Nominatim API: "{seat}, Switzerland" → lat/lng
3. Speichern in silver.organization_geo
4. Fallback: Kanton-Zentroid (weniger genau, aber Karte funktioniert)
```

**Rate Limit Nominatim:** max 1 req/s — Batch-Job über Nacht für alle Orgs.

**Caching:** Einmal geocodiert = für immer (Sitz ändert sich selten). Bei Adress-Change-Event neu geocodieren.

### Karten-Performance: Zwei Ebenen

| Zoom | Datenquelle | Punkte |
|------|-------------|--------|
| 0–8 (ganze CH) | `gold.map_grid_daily` | ~500 Grid-Zellen |
| 9–12 (Kanton) | `silver.geo_events` gefiltert nach BBox + Datum | ~1k–10k |
| 13+ (Stadt) | `silver.geo_events` einzelne Punkte | ~100–1k |

**API-Pattern:**

```
GET /api/map/events?from=2024-01-01&to=2024-01-31&category=org_new&bbox=8.5,47.3,8.6,47.4&zoom=11
```

Server entscheidet anhand `zoom`:
- `zoom < 9` → Grid-Aggregation
- `zoom >= 9` → einzelne Events mit `ST_Within(geom, ST_MakeEnvelope(...))`

### H3 als Alternative (optional)

Uber H3 Hexagone statt Web-Mercator-Grid — schöner für Heatmaps:

```sql
-- Mit h3-pg Extension
UPDATE silver.geo_events SET h3_cell = h3_lat_lng_to_cell(lat, lng, 7);
```

Für Phase 1 reicht ein einfaches Lat/Lng-Grid.

---

## 5. ETL-Pipelines

### 5.1 Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│ Job                    │ Frequenz    │ Dauer (geschätzt)   │
├────────────────────────┼─────────────┼─────────────────────┤
│ sync_sqlite            │ 1h          │ 5–15 min incremental│
│ run_analyze (remote)   │ 6h          │ läuft auf Harvester │
│ build_silver_events    │ nach sync   │ 10–30 min           │
│ enrich_uid_bfs         │ täglich     │ ~3h für 500k UIDs   │
│ enrich_zefix           │ täglich     │ ~6h (rate limited)  │
│ enrich_gleif           │ täglich     │ ~2h                 │
│ geocode_new            │ täglich     │ ~1h (1/s limit)     │
│ enrich_sanctions       │ wöchentlich │ 30 min              │
│ dbt run (gold)         │ nach silver │ 5–10 min            │
│ refresh_top_lists      │ täglich     │ 2 min               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 sync_sqlite.py

Incremental Sync Harvester → Postgres Bronze:

```python
# etl/sync_sqlite.py (Pseudocode)
def sync():
    remote_db = fetch_sqlite_from_server()  # oder SSH + sqlite3
    watermark = get_watermark("shab_publication_raw")  # max scraped_at in Postgres

    new_rows = sqlite_query(
        "SELECT * FROM shab_publication_raw WHERE scraped_at > ?", watermark
    )
    upsert_bronze("bronze.shab_publication_raw", new_rows)

  # Auch: organizations, persons, person_roles, cases aus analyze
    sync_aggregate_tables(remote_db)

    set_watermark("shab_publication_raw", max_scraped_at)
```

**Wichtig:** SQLite-Lock auf Harvester vermeiden — Sync nur lesend (`sqlite3 URI mode=ro`).

### 5.3 build_silver_events.py

Transformiert Bronze + analyze-Output → `silver.events` + `silver.geo_events`:

```python
def build_events():
    for pub in pending_publications():
        classification = classify_event(pub)  # aus analysis.py
        event = {
            "event_id": hash_id(pub),
            "org_key": build_org_key(pub),
            "event_date": classification.event_date,
            "event_type": classification.event_type,
            "event_category": map_category(classification.event_type),
            "summary_de": generate_summary(pub, classification),
            "payload": build_payload(pub, classification),
        }
        upsert("silver.events", event)

        geo = get_org_geo(event["org_key"])
        if geo:
            upsert("silver.geo_events", {**event, **geo, "color": COLOR_MAP[...]})
```

### 5.4 build_org_timeline.py

Pro Organisation chronologisch States berechnen:

```python
def build_timeline(org_key):
    events = get_events(org_key, order="event_date")
    state = empty_state()
    for i, event in enumerate(events):
        state = apply_delta(state, event.payload)
        upsert("silver.org_timeline_states", {
            "org_key": org_key,
            "event_index": i,
            "event_id": event.event_id,
            "event_date": event.event_date,
            "state_json": state,
        })
```

### 5.5 enrich_*.py Jobs

Jeder Enrichment-Job folgt demselben Pattern:

```python
def enrich_zefix(batch_size=100, pause=0.5):
    uids = get_uids_without_recent_enrichment("zefix", max_age_days=7)
    for uid in uids:
        data = zefix_api.get_company(uid)
        insert_bronze("bronze.enrichment_zefix", uid, data)
        merge_into_silver_organizations(uid, data)
        time.sleep(pause)
```

**Priorität:** UIDs die in den letzten 30 Tagen SHAB-Events hatten zuerst.

### 5.6 dbt (Gold Layer)

```bash
dbt/
  models/
    gold/
      daily_stats.sql
      monthly_stats.sql
      top_most_changes_30d.sql
      top_newest_companies.sql
      top_serial_directors.sql
      map_grid_daily.sql
  dbt_project.yml
```

Beispiel `daily_stats.sql`:

```sql
SELECT
  event_date AS stat_date,
  COUNT(*) FILTER (WHERE event_type = 'ORG_NEW') AS org_new,
  COUNT(*) FILTER (WHERE event_category = 'insolvency') AS bankruptcy,
  ...
FROM {{ ref('events') }}
GROUP BY 1
```

### 5.7 Orchestrierung

**Einfach (Start):** systemd timer oder cron auf dem Hetzner-Server:

```bash
# /etc/cron.d/shab-bi
0 * * * *  shab-bi /opt/shab-bi/etl/run_hourly.sh
0 3 * * *  shab-bi /opt/shab-bi/etl/run_daily.sh
```

**run_hourly.sh:** sync_sqlite → build_silver_events → dbt run

**run_daily.sh:** enrich_* → geocode_new → refresh_top_lists

**Später:** Dagster oder Prefect wenn Pipelines komplexer werden.

---

## 6. API (FastAPI)

### 6.1 Struktur

```
api/
  main.py
  auth/
    dependencies.py      # get_current_user, require_premium
    middleware.py
  routes/
    pulse.py             # GET /api/pulse/daily, /api/pulse/monthly
    map.py               # GET /api/map/events (BBox + zoom aware)
    orgs.py              # GET /api/orgs/{key}, /api/orgs/{key}/timeline
    persons.py           # GET /api/persons/{key}/network
    search.py            # GET /api/search?q=...
    billing.py           # POST /api/billing/checkout, webhook
  services/
    map_query.py         # Grid vs. points logic
    tier_limits.py       # Free vs. Premium checks
```

### 6.2 Wichtige Endpoints

```
GET  /api/pulse/summary?from=&to=              → KPI-Counter für Scrubber
GET  /api/map/events?from=&to=&category=&bbox=&zoom=  → Karten-Events
GET  /api/orgs/{org_key}                       → Org-Detail + Enrichment
GET  /api/orgs/{org_key}/timeline              → events[] + states[] (vorberechnet)
GET  /api/search?q=&type=org|person            → Volltext
GET  /api/top/{list_id}?as_of=                 → Top-Listen
GET  /api/persons/{person_key}                 → Person + Mandate
GET  /api/persons/{person_key}/network         → Graph-Daten (Premium)

POST /api/billing/create-checkout-session      → Stripe
POST /api/billing/webhook                      → Stripe Events
GET  /api/me                                   → User + Tier + Usage
```

### 6.3 Tier-Limits in der API

```python
FREE_LIMITS = {
    "org_timeline_views_per_month": 10,
    "map_date_range_months": 12,
    "search_results": 20,
}

async def get_org_timeline(org_key: str, user: User):
    if user.tier not in ("trial", "premium"):
        await check_and_increment_usage(user, "org_views", limit=10)
    if user.tier == "free":
        raise HTTPException(403, "Premium required")
    return load_timeline(org_key)
```

### 6.4 Performance

- **Connection Pool:** `asyncpg` mit pool_size=20
- **Response Cache:** Redis, TTL 5 min für `/api/pulse/*` und `/api/top/*`
- **Pagination:** Cursor-based für Search
- **Compression:** gzip/brotli für JSON
- **Read Replica:** optional wenn Traffic wächst

---

## 7. Frontend (Next.js)

### 7.1 Stack

| Tool | Zweck |
|------|-------|
| **Next.js 15** App Router | SSR, Routing, API Routes als BFF |
| **MapLibre GL JS** | Karte (Open Source, kein Mapbox-Token nötig) |
| **deck.gl** (optional) | HexagonLayer für Heatmaps |
| **Framer Motion** | Timeline-Animation, State-Morphing |
| **TanStack Query** | Data Fetching, Cache, Prefetch |
| **Zustand** | Globaler Scrubber-State (currentDate) |
| **Recharts** | Zeitreihen-Charts |
| **Tailwind CSS** | Styling |
| **Clerk** oder **Auth.js** | Login |

### 7.2 Scrubber als globaler State

```tsx
// stores/timeline.ts
import { create } from 'zustand';

interface TimelineStore {
  startDate: Date;       // 2018-09-03
  endDate: Date;         // heute
  currentDate: Date;
  isPlaying: boolean;
  playbackSpeed: 1 | 2 | 5 | 10;
  setCurrentDate: (d: Date) => void;
  play: () => void;
  pause: () => void;
}

// Alle Komponenten (Karte, Counter, Charts) subscriben auf currentDate
```

### 7.3 Karten-Performance

**Problem:** 2.6M Events auf einmal = Browser stirbt.

**Lösung — mehrstufig:**

1. **API liefert nur sichtbaren Zeitraum + BBox + Zoom-Level**
2. **Beim Scrubben:** Debounce 150ms, dann neu fetchen
3. **Niedriger Zoom:** Grid-Aggregation (deck.gl HexagonLayer oder CircleLayer mit count)
4. **Hoher Zoom:** Einzelpunkte mit `circle-radius: 6`
5. **Neue Punkte animieren:** Nur `currentDate === event.event_date` bekommen Pulse
6. **Alte Punkte bleiben:** `event_date <= currentDate` als gedimmte Punkte
7. **WebGL Layer:** MapLibre native — kein DOM pro Punkt

```tsx
function EventMap() {
  const { currentDate, startDate, endDate } = useTimelineStore();
  const bounds = useMapBounds();

  const { data } = useQuery({
    queryKey: ['map-events', currentDate, bounds, zoom],
    queryFn: () => fetchMapEvents({ to: currentDate, bbox: bounds, zoom }),
    staleTime: 30_000,
    placeholderData: keepPreviousData,  // kein Flackern beim Scrubben
  });

  // GeoJSON Source updaten, nicht React-Komponenten pro Punkt
  useEffect(() => {
    map.getSource('events').setData(toGeoJSON(data));
  }, [data]);
}
```

### 7.4 Firmen-Timeline Performance

- **Ein API-Call** lädt komplette Timeline: `events[]` + `states[]` (~5–50 KB pro Firma)
- **Scrubbing ist clientseitig** — kein Server-Call pro Frame
- **Framer Motion `AnimatePresence`** für VR-Liste und Name-Change
- **Prefetch:** Bei Hover auf Karten-Punkt Timeline vorladen

### 7.5 Code-Splitting

```tsx
// Lazy load schwere Komponenten
const EventMap = dynamic(() => import('@/components/EventMap'), { ssr: false });
const OrgTimeline = dynamic(() => import('@/components/OrgTimeline'));
const PersonNetwork = dynamic(() => import('@/components/PersonNetwork'), { ssr: false });
```

### 7.6 Seitenstruktur

```
web/
  app/
    (marketing)/
      page.tsx              # Landing
      pricing/page.tsx
    (auth)/
      sign-in/page.tsx
      sign-up/page.tsx
    (app)/
      layout.tsx            # Auth guard + Sidebar
      pulse/page.tsx        # Schweiz Pulse + Karte
      orgs/[key]/page.tsx   # Firmen-Timeline
      persons/[key]/page.tsx
      search/page.tsx
      settings/page.tsx     # Billing, Account
  components/
    map/EventMap.tsx
    timeline/Scrubber.tsx
    timeline/OrgTimeline.tsx
    timeline/StatePanel.tsx
    charts/MonthlyChart.tsx
  lib/
    api.ts
    auth.ts
```

---

## 8. Auth & Billing

### 8.1 Auth-Flow (Clerk empfohlen)

```
Sign Up → Clerk → Webhook → app.users + trial_ends_at = now() + 30 days
Login  → JWT → FastAPI validiert Clerk JWT
```

**Warum Clerk:** OAuth (Google), Magic Link, MFA — in 1 Tag integriert. Auth.js geht auch, mehr Aufwand.

### 8.2 Stripe Subscriptions

**Produkte in Stripe:**

| Product | Preis | Intervall |
|---------|-------|-----------|
| SHAB-BI Premium | CHF 39 | monatlich |
| SHAB-BI Premium Jahres | CHF 390 | jährlich (2 Monate gratis) |

**Trial-Logik:**

```
Tag 0:   Sign Up → tier = 'trial', trial_ends_at = +30d
Tag 1–30: Voller Zugang
Tag 30:  tier → 'free' (eingeschränkt) ODER Stripe Checkout Prompt
Tag 30+: Premium nur mit aktiver Subscription
```

**Stripe Webhook Events:**

```
checkout.session.completed  → tier = 'premium'
customer.subscription.updated → tier anpassen
customer.subscription.deleted → tier = 'free'
invoice.payment_failed      → Email + Grace Period 3 Tage
```

### 8.3 Paywall-UX

- Trial-Banner: „Noch 23 Tage Premium — jetzt abonnieren"
- Bei Limit: Modal mit Feature-Vergleich, Stripe Checkout Button
- Keine harte Paywall auf Landing/Pulse — das ist Marketing
- Firmen-Timeline ab dem 11. View im Free-Tier: „Premium für unbegrenzten Zugang"

---

## 9. Deployment

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Hetzner Server  │     │  Vercel         │     │  Stripe         │
│ - Harvester     │     │  - Next.js      │     │  - Billing      │
│ - ETL cron      │     │  - Edge         │     └─────────────────┘
│ - FastAPI       │     └─────────────────┘
│ - Postgres+GIS  │              │
└─────────────────┘              │
         │                       │
         └─────── API ───────────┘
```

**Alternativ alles auf Hetzner:** Günstiger bei hohem Traffic, mehr Ops-Aufwand.

**DB:** Hetzner Managed Postgres oder selbst auf Volume (wie Harvester-Daten).

### Env-Variablen

```bash
# API
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CLERK_SECRET_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# ETL
SQLITE_REMOTE_SSH=...
ZEFIX_API_USER=...
ZEFIX_API_PASSWORD=...
NOMINATIM_URL=https://nominatim.openstreetmap.org

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://api.shab-bi.ch
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...
```

---

## 10. Implementierungsreihenfolge

### Sprint 1–2: Fundament (2 Wochen)

- [ ] Docker Compose mit PostGIS lokal
- [ ] DB-Migrations (Alembic oder dbmate): bronze + silver + gold + app schemas
- [ ] `sync_sqlite.py` — incremental Bronze-Sync
- [ ] `build_silver_events.py` — Events aus analyze-Output
- [ ] `geocode.py` — Nominatim Batch
- [ ] FastAPI Grundgerüst + `/api/pulse/summary` + `/api/map/events`

### Sprint 3–4: Kern-UI (2 Wochen)

- [ ] Next.js Setup + Auth (Clerk)
- [ ] Scrubber-Komponente (Zustand Store)
- [ ] EventMap mit MapLibre (Grid + Points)
- [ ] Pulse-Page: Karte + Counter + Scrubber
- [ ] `build_org_timeline.py` + `/api/orgs/{key}/timeline`
- [ ] OrgTimeline-Page mit State Panel

### Sprint 5–6: Enrichment + Billing (2 Wochen)

- [ ] `enrich_uid_bfs.py`, `enrich_zefix.py`, `enrich_gleif.py`
- [ ] Silver-Org-Merge mit Enrichment-Daten
- [ ] dbt Gold Models (daily_stats, top_lists)
- [ ] Stripe Integration + Trial-Logik
- [ ] Tier-Limits in API + Paywall-UI

### Sprint 7–8: Polish + Premium (2 Wochen)

- [ ] Suche (Postgres FTS + trigram)
- [ ] Top-Listen Page
- [ ] `enrich_sanctions.py` + Compliance-Badges
- [ ] Personen-Netzwerk (Premium)
- [ ] Konzern-Baum GLEIF
- [ ] Export CSV/PDF (Premium)

---

## 11. Performance-Checkliste

### Datenbank
- [ ] GIST-Index auf allen `geography`-Spalten
- [ ] BRIN-Index auf `event_date` (Zeitreihen)
- [ ] `pg_trgm` für Namenssuche
- [ ] Gold-Tabellen statt Live-Aggregation
- [ ] `EXPLAIN ANALYZE` auf alle Map-Queries < 50ms

### API
- [ ] Connection Pooling (asyncpg)
- [ ] Redis-Cache für Pulse/Top-Listen
- [ ] BBox + Zoom-aware Queries (nie alle Events)
- [ ] gzip Compression

### Frontend
- [ ] Scrubbing clientseitig wo möglich (Firmen-Timeline)
- [ ] `placeholderData: keepPreviousData` beim Karten-Fetch
- [ ] WebGL/MapLibre statt DOM-Marker
- [ ] Code-Splitting für Map + Network-Graph
- [ ] Debounce Scrubber → API (150ms)
- [ ] Prefetch Org-Timeline on Hover

### ETL
- [ ] Incremental Sync (watermark), nie Full-Reload
- [ ] Enrichment priorisiert aktive UIDs
- [ ] Geocode-Cache, nie doppelt
- [ ] dbt incremental models für Gold

---

## 12. Monitoring

| Was | Tool |
|-----|------|
| API Latency | Sentry / Betterstack |
| ETL Job Failures | Cron email + Sentry |
| DB Size / Slow Queries | pg_stat_statements |
| Stripe Webhooks | Stripe Dashboard + Logs |
| Map API p99 | Custom metric < 200ms |

---

## Anhang: Nützliche Queries

### Events in BBox für Karte

```sql
SELECT event_id, event_type, event_category, lat, lng, name, color
FROM silver.geo_events
WHERE event_date BETWEEN :from AND :to
  AND event_category = :category
  AND geom && ST_MakeEnvelope(:west, :south, :east, :north, 4326)::geography
ORDER BY event_date
LIMIT 10000;
```

### Grid-Aggregation (niedriger Zoom)

```sql
SELECT
  floor(lng / 0.1) AS cell_x,
  floor(lat / 0.1) AS cell_y,
  COUNT(*) AS event_count,
  jsonb_agg(jsonb_build_object('id', event_id, 'name', name) ORDER BY event_date DESC)
    FILTER (WHERE row_number() OVER (PARTITION BY floor(lng/0.1), floor(lat/0.1) ORDER BY event_date DESC) <= 3)
    AS samples
FROM silver.geo_events
WHERE event_date BETWEEN :from AND :to
GROUP BY 1, 2;
```

### Org-Timeline laden

```sql
SELECT e.*, s.state_json
FROM silver.events e
JOIN silver.org_timeline_states s
  ON s.org_key = e.org_key AND s.event_id = e.event_id
WHERE e.org_key = :org_key
ORDER BY e.event_date, s.event_index;
```
