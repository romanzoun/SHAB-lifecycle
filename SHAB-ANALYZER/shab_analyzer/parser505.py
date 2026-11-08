from __future__ import annotations

import re
from datetime import datetime

from .parser186 import _FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT
from .parser236 import _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS
from .parser253 import _person_event


_LEGACY = (_FR_ENTRY_SUPPLEMENTED_BOARD_VICE_PRESIDENT,
           _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS)
_ROLE_SUPPLEMENT = re.compile(
    r"L'inscription no (?P<entry>\d+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"est complétée en ce sens qu'(?P<name>[^,.;\[\]\n]+?) "
    r"est (?P<role>sous-directrice adjointe)\.?"
)


def extract_parser505_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested elided role supplement without inferring signing."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in _LEGACY):
        return [], text
    match = _ROLE_SUPPLEMENT.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        entry_date = datetime.strptime(match['entry_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.deputy_subdirector_role_supplemented.v1', match['name'],
        role=match['role'], extra={'action': 'entry_supplemented',
                                  'entry': match['entry'], 'entry_date': entry_date},
    )], ''
