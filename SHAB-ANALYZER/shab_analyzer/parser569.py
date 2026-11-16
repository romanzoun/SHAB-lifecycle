from __future__ import annotations

import re
from datetime import datetime

from .parser210 import _FR_ADMINISTRATOR_PRESIDENCY_SUPPLEMENT
from .parser215 import _FR_ADMINISTRATOR_ALSO_DIRECTOR_SUPPLEMENT
from .parser236 import _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS
from .parser253 import _person_event

_LEGACY = (_FR_ADMINISTRATOR_PRESIDENCY_SUPPLEMENT,
           _FR_ADMINISTRATOR_ALSO_DIRECTOR_SUPPLEMENT,
           _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS)
_DIRECTOR_SUPPLEMENT = re.compile(
    r"L'inscription no (?P<entry>\d+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"\(FOSC du (?P<notice_date>\d{2}\.\d{2}\.\d{4}) "
    r"p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que "
    r"(?P<name>[^,.;()\[\]\n]+) est directeur\.?"
)


def extract_parser569_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the attested director role supplement with its notice reference."""
    if language != 'fr' or any(p.search(text.strip()) for p in _LEGACY):
        return [], text
    match = _DIRECTOR_SUPPLEMENT.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('entry_date', 'notice_date')}
    except ValueError:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.director_role_supplemented_notice_reference.v1', match['name'],
        role='directeur', extra={
            'action': 'entry_supplemented', 'entry': match['entry'], **dates,
            'notice_ref': match['notice_ref'],
        },
    )], ''
