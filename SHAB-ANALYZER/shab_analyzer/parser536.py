from __future__ import annotations

import re
from datetime import datetime

from .parser236 import (
    _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS,
    extract_parser236_leftovers,
)


_FR_REFERENCED_DIRECTOR_SUPPLEMENT = re.compile(
    r"Complément: l'inscription no (?P<entry>\d+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"\(FOSC du (?P<notice_date>\d{2}\.\d{2}\.\d{4}) "
    r"p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que "
    r"(?P<body>[^.;\n]+?)\.?"
)


def extract_parser536_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Handle the attested referenced supplement; retain parser236's role payload."""
    if language != 'fr' or _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS.search(text.strip()):
        return [], text
    match = _FR_REFERENCED_DIRECTOR_SUPPLEMENT.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['entry_date'], '%d.%m.%Y')
        notice_date = datetime.strptime(match['notice_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    normalized = (f"L'inscription {match['entry']} du {match['entry_date']} "
                  f"est complétée en ce sens que {match['body']}")
    if not _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS.fullmatch(normalized):
        return [], text
    events, rest = extract_parser236_leftovers(
        normalized, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 2 or rest:
        return [], text
    for event in events:
        event.rule_id = 'fr.persons.entry_supplemented_two_directors_referenced.v1'
        event.payload.update(notice_date=notice_date, notice_ref=match['notice_ref'])
    return events, ''
