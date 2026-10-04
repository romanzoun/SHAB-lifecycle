# SHAB-lifecycle

Pipeline für Schweizerische Handelsamtsblatt-Meldungen (SHAB): Rohdaten sammeln, deterministisch strukturieren, später Business Intelligence.

```
SHAB-harvester          SHAB-ANALYZER                      SHAB-BI
(raw HTML/XML)    →     (Regeln → Events)            →     (Warehouse / Views)
```

| Paket | Aufgabe |
| --- | --- |
| [SHAB-harvester](SHAB-harvester/) | Harvest von shab.ch. Raw HTML/XML/SQLite unverändert, nichts löschen. |
| [SHAB-ANALYZER](SHAB-ANALYZER/) | XML-first, versionierte Parser (DE/FR/IT). Eine Meldung wird zu 0…n Events (Personen, Sitz, Adresse, Zweck, Kapital, Unterschrift, …). Runtime ohne LLM. |
| [SHAB-BI](SHAB-BI/) | Konsum der strukturierten Events (Pläne). Postgres/Linsen später. |

Der Analyzer erzeugt ein Ereignis-Ledger ab der geharvesteten Historie (ca. ab 2018). Aktueller HR-Stand zum Abgleich kommt von UID-Register/ZEFIX, nicht aus diesem Repo.

## Nutzung und Lizenz

Dieses Repository ist **nicht** Open Source. Quelltext auf GitHub ist keine Erlaubnis zur Nutzung.

Wer den Code klonen, ausführen, anpassen oder sonst verwenden will:

1. Per E-Mail anmelden: **roman.zoun@gmail.com**
2. Warten auf **schriftliche Bestätigung** der Erlaubnis durch Roman Zoun (E-Mail gilt als schriftlich)
3. Erst danach nutzen, im Rahmen der Bestätigung

Ohne diese Bestätigung ist jede Nutzung untersagt. Details: [LICENSE](LICENSE).

## Kontakt

Roman Zoun — roman.zoun@gmail.com
