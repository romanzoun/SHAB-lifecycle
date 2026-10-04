# SHAB-BI

Analytics- und Visualisierungsplattform auf Basis von SHAB-Publikationen, angereichert mit ZEFIX, GLEIF, UID-Register und weiteren Quellen.

## Dokumentation

| Datei | Inhalt |
|-------|--------|
| [PLAN.md](PLAN.md) | Produktvision, Enrichment-Quellen, Analytics-Fragen, Zeitstrahl-UX |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Postgres/PostGIS, Schema, ETL, API, Frontend, Auth, Billing |

## Architektur auf einen Blick

```
SHAB-harvester (SQLite, remote)     Enrichment Jobs (ZEFIX, GLEIF, BFS, …)
         │                                        │
         └──────────────┬─────────────────────────┘
                        ▼
              ETL / dbt (Python)
                        ▼
         PostgreSQL + PostGIS (Warehouse)
                        ▼
              FastAPI (Read API + Auth)
                        ▼
         Next.js Frontend (Karte, Timeline, Dashboards)
                        ▼
              Stripe (1 Monat gratis → Premium)
```

## Phasen

1. **Phase 0** — Harvest fertig + `analyze` laufen lassen
2. **Phase 1** — Postgres + ETL + Firmen-Timeline + Schweiz-Pulse (nur SHAB + Geocoding)
3. **Phase 2** — Enrichment (ZEFIX, BFS, GLEIF) + Auth + Billing
4. **Phase 3** — OpenSanctions, SIX, EPO, Personen-Netzwerk, Premium-Features

## Repo-Struktur (geplant)

```
SHAB-BI/
  README.md
  PLAN.md
  IMPLEMENTATION.md
  etl/              # Sync SQLite → Postgres, Enrichment-Jobs
  dbt/              # Silver/Gold SQL-Transformationen
  api/              # FastAPI Read-API + Auth
  web/              # Next.js Frontend
  infra/            # Docker Compose, migrations
```
