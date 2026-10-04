"""Second-pass aggregation layer on top of `shab_publication_raw`.

This is explicitly heuristic (keyword/regex based on the German/French SHAB
commercial-register phrasing observed in practice), not a legal parser. It
never modifies the raw harvester tables — it only reads `shab_publication_raw`
and writes into the aggregate-layer tables (organizations, persons, cases).
Re-running `analyze` is idempotent: per-publication aggregate rows are deleted
and rebuilt from the current raw row, so any change to the heuristics is
applied to all publications on the next run.
"""
from __future__ import annotations

import re

from . import db
from .utils import UID_RE, now_iso

DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

# Ordered: first matching keyword wins. (regex, event_type, case_type or None)
EVENT_KEYWORDS = [
    (re.compile(r"Konkurs(?:verfahren)?.{0,40}eröffnet|ouverture de la faillite", re.I), "BANKRUPTCY_OPENED", "BANKRUPTCY"),
    (re.compile(r"mangels Aktiven eingestellt|faute d'actif", re.I), "BANKRUPTCY_CLOSED_NO_ASSETS", "BANKRUPTCY"),
    (re.compile(r"Schluss des Konkursverfahrens|clôture de la faillite", re.I), "BANKRUPTCY_CLOSED", "BANKRUPTCY"),
    (re.compile(r"Nachlassverfahren|sursis concordataire", re.I), "COMPOSITION_PROCEEDINGS", "COMPOSITION"),
    (re.compile(r"in Liquidation|en liquidation|in liquidazione", re.I), "LIQUIDATION", "LIQUIDATION"),
    (re.compile(r"Eingetragene Personen|Ausgeschiedene Personen|inscrites? comme|radiée?s? comme", re.I), "ORG_PERSON_MUTATION", None),
    (re.compile(r"Firma neu|Nouvelle raison sociale", re.I), "ORG_NAME_CHANGE", None),
    (re.compile(r"Neue Adresse|Nouvelle adresse|Sitzwechsel|Nouveau siège", re.I), "ORG_ADDRESS_CHANGE", None),
    (re.compile(r"Zweck neu|Nouveau but", re.I), "ORG_PURPOSE_CHANGE", None),
]

CASE_OFFICE_RE = re.compile(
    r"(Konkursamt[^,.;]+|Konkursrichter[^,.;]+|Bezirksgericht[^,.;]+|Betreibungsamt[^,.;]+|"
    r"office des faillites[^,.;]+|tribunal[^,.;]+)",
    re.I,
)

# "Eingetragene Personen neu oder mutierend: Fitzi, Richard, von Gais, in Altstätten,
#  Mitglied des Verwaltungsrates und Liquidator, mit Einzelunterschrift."
PERSON_LABEL_RE = re.compile(
    r"(Eingetragene Personen[^:]*|Ausgeschiedene Personen[^:]*):\s*(?P<body>[^.]*\.)", re.I
)
PERSON_ENTRY_RE = re.compile(
    r"([A-ZÄÖÜ][\wÀ-ÿ'\-]+),\s*([A-ZÄÖÜ][\wÀ-ÿ'\-]+),\s*von\s+([^,]+),\s*in\s+([^,]+),\s*"
    r"([^,]+(?:,\s*[^,]+){0,2}?),\s*mit\s+(Einzelunterschrift|Kollektivunterschrift[^;.\[]*)"
)


def normalize_key(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9äöüàéèç]+", " ", text)
    return " ".join(text.split())


def classify_event(category: str | None, subcategory: str | None, title: str | None, body_text: str | None) -> dict:
    """Best-effort event classification. Falls back to category/subcategory."""
    # Search body_text first (where events are actually described) so a
    # matched keyword's position can later be used to find the *nearest*
    # date, not just the first one (which is often an old SHAB reference
    # date quoted in parentheses, e.g. "(SHAB Nr. 98 vom 22.05.2014)").
    for pattern, event_type, case_type in EVENT_KEYWORDS:
        m = pattern.search(body_text or "")
        if m:
            return {"event_type": event_type, "case_type": case_type, "confidence": "keyword", "match_start": m.start()}
    for pattern, event_type, case_type in EVENT_KEYWORDS:
        if pattern.search(title or ""):
            return {"event_type": event_type, "case_type": case_type, "confidence": "keyword", "match_start": None}

    if subcategory:
        sub = subcategory.lower()
        if "new" in sub or "nouvelle inscription" in sub:
            return {"event_type": "ORG_NEW", "case_type": None, "confidence": "metadata", "match_start": None}
        if "cancel" in sub or "delet" in sub or "radiation" in sub:
            return {"event_type": "ORG_DELETION", "case_type": None, "confidence": "metadata", "match_start": None}
        if "change" in sub:
            return {"event_type": "ORG_MUTATION_OTHER", "case_type": None, "confidence": "metadata", "match_start": None}

    return {"event_type": "OTHER", "case_type": None, "confidence": "fallback", "match_start": None}


def extract_event_date(body_text: str | None, near_pos: int | None = None) -> str | None:
    """dd.MM.yyyy date found in the body text, converted to ISO.

    If `near_pos` is given (the character offset of a matched event
    keyword), picks the date closest to it — otherwise the first date in
    the text, which is frequently a stale reference date instead of the
    actual event date."""
    if not body_text:
        return None
    matches = list(DATE_RE.finditer(body_text))
    if not matches:
        return None
    chosen = matches[0] if near_pos is None else min(matches, key=lambda m: abs(m.start() - near_pos))
    day, month, year = chosen.group(0).split(".")
    return f"{year}-{month}-{day}"


def extract_case_office(body_text: str | None) -> str | None:
    if not body_text:
        return None
    m = CASE_OFFICE_RE.search(body_text)
    return m.group(0).strip() if m else None


def extract_persons(body_text: str | None) -> list[dict]:
    """Best-effort extraction of person entries from labelled mutation sentences.
    Only matches the fairly regular German phrasing; anything else is skipped
    rather than guessed at."""
    if not body_text:
        return []

    results = []
    for label_match in PERSON_LABEL_RE.finditer(body_text):
        label = label_match.group(1)
        mutation_action = "removed" if "Ausgeschiedene" in label or "radiée" in label.lower() else "added"
        segment = label_match.group("body")
        for entry in PERSON_ENTRY_RE.finditer(segment):
            lastname, firstname, heimatort, wohnort, role, signature = entry.groups()
            full_name = f"{lastname.strip()}, {firstname.strip()}"
            results.append(
                {
                    "full_name": full_name,
                    "place": wohnort.strip(),
                    "role": role.strip(),
                    "signing_authority": signature.strip(),
                    "mutation_action": mutation_action,
                }
            )
    return results


def build_org_key(raw_row) -> tuple[str, str | None, str]:
    """Returns (org_key, uid, match_confidence)."""
    uid = raw_row["uid"]
    if uid:
        return f"uid:{uid}", uid, "HIGH"

    name = raw_row["company_block_text"] or raw_row["title"] or ""
    norm = normalize_key(name)
    canton = raw_row["canton"] or ""
    return f"cand:{norm}|{canton}", None, "LOW"


def process_publication(conn, raw_row, log=lambda msg: None) -> None:
    publication_id = raw_row["publication_id"]
    db.delete_publication_aggregates(conn, publication_id)

    org_key, uid, confidence = build_org_key(raw_row)
    classification = classify_event(raw_row["category"], raw_row["subcategory"], raw_row["title"], raw_row["body_text"])
    event_date = extract_event_date(raw_row["body_text"], classification.get("match_start")) or raw_row["publication_date"]

    db.upsert_organization(
        conn,
        {
            "org_key": org_key,
            "uid": uid,
            "match_confidence": confidence,
            "name_current": raw_row["company_block_text"] or raw_row["title"],
            "legal_seat": None,
            "canton": raw_row["canton"],
            "legal_form": None,
            "zefix_url": raw_row["zefix_url"],
            "event_date": event_date,
        },
    )
    db.upsert_organization_publication(
        conn, org_key, publication_id, classification["event_type"], event_date, classification["confidence"]
    )
    db.recompute_organization_publication_count(conn, org_key)

    for person in extract_persons(raw_row["body_text"]):
        person_key = f"{normalize_key(person['full_name'])}|{normalize_key(person['place'])}"
        db.upsert_person(conn, person_key, person["full_name"], normalize_key(person["full_name"]), person["place"])
        db.insert_person_role(
            conn,
            person_key,
            org_key,
            publication_id,
            person["role"],
            person["signing_authority"],
            person["mutation_action"],
            raw_row["publication_date"],
        )

    if classification["case_type"]:
        case_id = f"{org_key}:{classification['case_type']}"
        is_opened = classification["event_type"] in ("BANKRUPTCY_OPENED",)
        is_closed = classification["event_type"] in ("BANKRUPTCY_CLOSED", "BANKRUPTCY_CLOSED_NO_ASSETS")
        db.upsert_case(
            conn,
            {
                "case_id": case_id,
                "case_type": classification["case_type"],
                "org_key": org_key,
                "debtor_name": raw_row["company_block_text"] or raw_row["title"],
                "office": extract_case_office(raw_row["body_text"]),
                "case_reference": raw_row["previous_publication_number"] or raw_row["journal_number"],
                "opened_date": event_date if is_opened else None,
                "closed_date": event_date if is_closed else None,
                "status": "closed" if is_closed else ("open" if is_opened else None),
            },
        )
        db.insert_case_publication(conn, case_id, publication_id, classification["event_type"], event_date)

    log(f"[analyze] {publication_id}: org={org_key} event={classification['event_type']}")


def run_aggregate(conn, log=lambda msg: None, limit: int | None = None, force: bool = False) -> int:
    if force:
        db.reset_aggregates(conn)
        conn.commit()
    rows = db.pending_aggregate_publications(conn, limit, force)
    for row in rows:
        process_publication(conn, row, log)
        db.mark_aggregate_processed(conn, row["publication_id"], row["content_hash"])
        conn.commit()
    return len(rows)
