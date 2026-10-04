# SHAB-BI — Produktplan

## Vision

SHAB-BI verbindet **SHAB als Event-Stream** mit **offiziellen Registerdaten** (ZEFIX, UID, GLEIF) und weiteren Quellen zu einer Analytics-Plattform, die keine einzelne Behörde allein bietet:

- Schweiz-weite Pulse-Ansichten (Gründungen, Konkurse, Mutationen auf der Karte)
- Firmen-Lebenslauf mit animiertem Zeitstrahl
- Personen-Netzwerk und Compliance-Screening
- Branchen- und Regionalanalysen

**Unique Selling Point:** Historische SHAB-Events (2018+) × Enrichment × Zeitstrahl-Visualisierung.

---

## Enrichment-Quellen

### Tier 1 — Must-have

| Quelle | Daten | Join-Key | API |
|--------|-------|----------|-----|
| **SHAB** (Harvester) | Publikationen, Events, Personen, Cases | `publication_id`, `uid` | Eigener Scraper |
| **ZEFIX** | Name, Rechtsform, Sitz, Zweck, Status, `sogcPub[]` | UID | REST (Credentials EHRA) |
| **UID-Register (BFS)** | UID-Status, MWST, NOGA-Branche, Adresse | UID | SOAP Public Services (kein Login) |
| **GLEIF** | LEI, Parent/Child, Konsolidierungslevel | UID via `registrationAuthorityEntityID` | REST `api.gleif.org` |

### Tier 2 — Should-have

| Quelle | Daten | Nutzen |
|--------|-------|--------|
| **Geocoding** (Nominatim/OSM) | Lat/Lng des Sitzes | Karten, Heatmaps |
| **OpenSanctions** | Sanktionslisten, PEP | Compliance-Filter |
| **OpenCorporates** | Internationale Cross-Refs | Auslandsbezug |
| **Wikidata** | Wikipedia, Logo, QID | UI-Enrichment |
| **ZEFIX Linked Data** (SPARQL) | Bulk-Download | Initial-Sync |

### Tier 3 — Premium / später

| Quelle | Daten | Nutzen |
|--------|-------|--------|
| **SIX Swiss Exchange** | ISIN, Market Cap, Listing-Datum | Börsennotierte Firmen |
| **FINMA-Register** | Banken, Versicherer, Vermögensverwalter | Regulierte Entitäten |
| **EPO / Swissreg** | Patente pro Firma | Innovations-Metrik |

### Enrichment-Pipeline (Reihenfolge)

```
UID aus SHAB
  ├─1─► UID-Register (BFS)     — Status, NOGA, MWST
  ├─2─► ZEFIX by UID           — Handelsregister + sogcPub
  ├─3─► GLEIF by UID/Name      — LEI + Konzernstruktur
  ├─4─► Geocode (Sitz)         — PostGIS-Punkte
  ├─5─► OpenSanctions          — Compliance
  └─6─► Wikidata / SIX / EPO   — optional
```

---

## Analytics-Fragen

### Schweiz-weit (Makro)

**Wirtschaft & Lebenszyklus**
- Wie viele Firmen wurden diesen Monat neu gegründet — und wo?
- Welcher Kanton hat die höchste Gründungsrate?
- Gibt es eine Konkurswelle? In welcher Branche?
- Welche Branchen schrumpfen vs. wachsen?
- Durchschnittliche Lebensdauer einer GmbH bis Liquidation
- Rechtsform-Trends (AG vs. GmbH)
- Saisonalität bei Gründungen/Löschungen

**Geografie**
- Heatmap: Konkurse nach Region
- Churn-Rate pro Region (Löschungen/Gründungen)
- Zürich vs. Zug vs. Genf — Aktivitätsvergleich

**Branchen (NOGA)**
- Top-Branchen Neugründungen / Konkurse
- Fintech-, Pharma-, Tech-Cluster

**Konzernlandschaft (GLEIF)**
- Globale Konzerne mit den meisten CH-Tochtergesellschaften
- SHAB-Aktivität pro Konzern-Gruppe
- LEI-Adoption über Zeit

**Compliance**
- SHAB-Firmen/Personen auf Sanktionslisten
- FINMA-regulierte Entitäten mit SHAB-Änderungen
- Inkonsistenzen (Konkurs + noch MWST-pflichtig)

**Innovation & Kapitalmarkt**
- Patent-Aktivität nach Branche/Region
- Börsennotierte Firmen mit SHAB-Mutationen

**Personen (einzigartig)**
- Serial Directors (meiste VR-Mandate)
- Meiste Einzelunterschriften
- Personen gleichzeitig in Konkurs- und Gründungs-Firmen
- Personen auf Sanktionslisten in CH-VR

### Pro Firma (Mikro)

**Identität & Status**
- UID, LEI, ISIN, ZEFIX, Wikipedia
- Aktiv / Liquidation / Konkurs / gelöscht
- MWST-pflichtig, NOGA-Branche, FINMA-reguliert, Sanktionsliste

**Lebenslauf (Killer-Feature)**
- Animierter Zeitstrahl: Gründung → VR-Wechsel → Name Change → Liquidation
- Mutations-Velocity (wie oft ändert sich die Firma?)
- Warnsignale vor Konkurs (VR-Wechsel, Adresswechsel)
- SHAB-Historie vs. ZEFIX sogcPub (Datenqualität)

**Struktur & Eigentum**
- Muttergesellschaft, Tochtergesellschaften (GLEIF)
- Internationale Schwestergesellschaften

**Governance**
- Aktueller VR, Ein-/Austritte, Unterschriftsarten
- VR-Mitglied auf Sanktionsliste?
- Andere Mandate derselben Person

**Vergleich**
- Aktivität vs. Branchendurchschnitt (NOGA Peer Group)
- Patent-Portfolio, Kartenposition

### Wow-Fragen (nur mit Kombination möglich)

1. **Frühwarnsystem** — 3+ VR-Wechsel in 6 Monaten + Branche mit vielen Konkursen
2. **Konzern-Radar** — Alle Tochtergesellschaften von X mit SHAB-Aktivität (30d)
3. **Personen-Netzwerk** — Netzwerk von Person Y über Firmen und Status
4. **Compliance-Screening** — Firma als Kunde: Sanktionen, FINMA, Konkurs, MWST
5. **Markt-Intelligence** — Börsennotierte Pharma mit Patenten + VR-Wechsel
6. **Regional-Pulse** — Live-Feed Zug: Gründungen, Konkurse auf Karte
7. **Lifecycle-Vergleich** — Firma A vs. B nebeneinander

---

## Zeitstrahl — welche Fragen profitieren davon?

### Drei Modi

| Modus | Beschreibung | Beispiel |
|-------|--------------|----------|
| **Snapshot** | Zahl/Badge, kein Scrubber | „Auf Sanktionsliste?" |
| **Timeline-enhanced** | Statisch ok, animiert besser | Branchen-Trends |
| **Timeline-native** | Ohne Scrubber sinnlos | Gründungswelle auf Karte |

### Timeline-native (Scrubber = Feature)

| Frage | Visualisierung beim Scrubben |
|-------|------------------------------|
| Neugründungen — wo? | Grüne Punkte flackern auf Karte, Counter tickt |
| Konkurse — wo? | Rote Punkte, Heatmap baut sich auf |
| Liquidationen | Orange Punkte |
| Saisonalität Gründungen | Play Jan→Dez, Cluster sichtbar |
| Konkurswelle wann? | Q2 2020 explodiert beim Scrubben |
| Gründungswellen pro Kanton | Multi-Line-Chart baut sich auf |
| Mutations-Aktivität CH | Farbige Punkte, Herbst = hektisch |
| VR-Wechsel | Blaue Punkte, Cluster um GV-Saison |
| Patent-Anmeldungen | Lila Punkte, Basel leuchtet |

### Timeline-enhanced

| Frage | Mit Zeitstrahl |
|-------|----------------|
| Branche schrumpft/wächst | Linien pro NOGA 2018→2026 |
| Rechtsform-Trends | Gestapeltes Area Chart |
| Konzern-Aktivität | Punkte pro Tochter, gruppiert nach Mutter |
| Serial Directors | Netzwerk-Graph wächst |
| MWST vs. Gründungen | Zwei Linien, 3-Monats-Lag sichtbar |
| Sanktions-Treffer | Rote Icons, neu vs. alt erkennbar |

### Firmen-Timeline (pro Org)

| Frage | Beim Scrubben |
|-------|---------------|
| Kompletter Lebenslauf | State Panel morpht (Name, VR, Status) |
| VR Ein-/Austritte | Personen grün rein, rot raus |
| Warnsignale vor Konkurs | Rückwärts scrubben vom Konkurs |
| Mutations-Velocity | Balken pro Jahr unter Timeline |
| Firma A vs. B | Zwei parallele Timelines |
| SHAB vs. ZEFIX sogcPub | Zwei Spuren, Lücken rot |

### Drill-Down: Makro → Meso → Mikro

```
Schweiz-Karte (Scrubber)
  → Klick auf Punkt
    → Firmen-Timeline
      → Klick auf VR-Person
        → Personen-Netzwerk
```

---

## Screens (geplant)

### 1. Schweiz Pulse (Landing, Free)

- KPI-Counter (Gründungen/Konkurse/Liquidationen) — zählt beim Scrubben
- Schweiz-Karte mit Event-Punkten
- Zeitraum-Scrubber 2018→heute
- Top-Listen (Snapshot, filterbar)

### 2. Konkurs-Radar (Free eingeschränkt / Premium)

- Rote Punkte auf Karte
- Branchen-Filter (NOGA)
- Frühwarnungs-Firmen mit Timeline

### 3. Gründungs-Welle (Free)

- Grüne Punkte, Kanton-Ranking animiert

### 4. Firmen-Lebenslauf (Free: 3/Monat, Premium: unbegrenzt)

- State Panel, VR-Liste, Konzern-Baum
- Animierter Zeitstrahl
- Peer-Vergleich (Premium)

### 5. Personen-Netzwerk (Premium)

- Graph Person → Firmen, zeitlich animiert

### 6. Suche (Free basic, Premium advanced)

- Volltext: Firma, UID, Person, Kanton, NOGA

---

## Zielgruppen

| Persona | Top-Use-Case |
|---------|--------------|
| Treuhänder / Anwälte | Firmen-Timeline, Compliance-Screening |
| Investoren / VC | Branchen-Trends, Konzern-Subsidiaries |
| Journalisten | Konkurs-Wellen, Story-Finding |
| Compliance / KYC | Sanctions, FINMA, VR-Checks |
| Wirtschaftsförderung | Regional-Pulse, Gründungstrends |

---

## Freemium-Modell

| | Free (1 Monat Trial) | Premium |
|---|---------------------|---------|
| Schweiz Pulse | ✓ | ✓ |
| Karte + Scrubber | ✓ (letzte 12 Monate) | ✓ (komplett 2018→heute) |
| Firmen-Timeline | 10 Firmen/Monat | Unbegrenzt |
| Suche | Basic | Advanced + Filter |
| Personen-Netzwerk | — | ✓ |
| Konzern-Baum (GLEIF) | — | ✓ |
| Compliance-Screening | — | ✓ |
| Export (CSV/PDF) | — | ✓ |
| API-Zugang | — | ✓ (optional höheres Tier) |

**Preis:** CHF 29–49/Monat (nach 30 Tagen Trial ohne Kreditkarte oder mit — siehe Implementation).

---

## Phasen-Roadmap

| Phase | Inhalt | Abhängigkeit |
|-------|--------|--------------|
| **0** | Harvest + analyze fertig | SHAB-harvester |
| **1** | Postgres, ETL, Pulse-Karte, Firmen-Timeline | Phase 0 |
| **2** | ZEFIX/BFS/GLEIF Enrichment, Auth, Stripe | Phase 1 |
| **3** | OpenSanctions, Personen-Netzwerk, Premium-Features | Phase 2 |
| **4** | SIX, EPO, FINMA, API-Tier | Phase 3 |
