# Agent Task — Regex Case Extractor

Copy this template for each Cursor/Claude agent task. One agent = one case scope (optionally one language if large, e.g. `person_mutation_fr`).

## Task

Implement regex extractor for **`{CASE_ID}`** in languages: **`{LANGS}`** (de / fr / it).

## Context

- SHAB-ANALYZER reads `body_text` from harvested commercial register publications
- Regex first, LLM second — your module must be deterministic, fast, testable
- Multiple events per publication are allowed
- Reference: `SHAB-harvester/shab_harvester/analysis.py` (DE prototype)

## Inputs

1. Run `./scripts/sample_for_case.sh "{SQL_PATTERN}" 30 {lang} {case_id}` against harvester DB
2. Read samples in `tests/fixtures/{case_id}_{lang}/`
3. Case spec in `SHAB-ANALYZER/PLAN.md` → Regex-Layer table

## Deliverables

| File | Purpose |
|------|---------|
| `shab_analyzer/extractors/cases/{case_id}.py` | `CaseExtractor` implementation |
| `tests/test_{case_id}_{lang}.py` | ≥5 positive, ≥3 negative fixtures |
| `tests/fixtures/{case_id}_{lang}/*.txt` | Real SHAB snippets (gitcommitted) |
| `docs/cases/{case_id}.md` | Phrases matched, edge cases, known gaps |
| Register in `shab_analyzer/extractors/registry.py` | Add to `EXTRACTORS` list |

## API Contract

```python
class {CaseId}Extractor:
    case_id = "{case_id}"
    supported_languages = {"de", "fr", "it"}  # subset ok

    def match(self, body_text: str, lang: str) -> list[EventMatch]:
        ...
```

`EventMatch` fields: `event_type`, `event_category`, `case_type`, `match_start`, `confidence`, `payload`.

## Rules

- Regex + string ops only — no LLM
- `event_date`: nearest `dd.MM.yyyy` after `match_start` (helper in `extractors/base.py`)
- Confidence scoring per `PLAN.md`
- Do not modify raw harvester tables
- Do not implement unrelated cases in the same PR

## Done when

- [ ] `pytest tests/test_{case_id}_*.py -q` passes
- [ ] Registered in `registry.py`
- [ ] `docs/cases/{case_id}.md` documents FR/IT phrases if applicable
- [ ] No false positives on negative fixtures
