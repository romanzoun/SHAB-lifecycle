from __future__ import annotations

import re
from datetime import datetime

from .parser55 import _FR_STANDALONE_GROUP_SIGNING
from .parser117 import _FR_DIRECTOR_DELETION_CORRECTED, _person_event
from .parser267 import DATE


_CORRECTION = re.compile(
    rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) "
    r"est rectifiée en ce sens que (?P<name>[^,.;\n]+?) est "
    r"(?P<role>membre du conseil d'administration) ; elle n'est donc pas radiée\.?"
)


def extract_parser513_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested correction retaining a director after existing signing extraction."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_DIRECTOR_DELETION_CORRECTED, _FR_STANDALONE_GROUP_SIGNING,
    )):
        return [], text
    match = _CORRECTION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        entry_date = datetime.strptime(match['entry_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.director_deletion_corrected_after_signing.v1',
        match['name'], role=match['role'],
        extra={
            'action': 'deletion_reversed', 'remains_registered': True,
            'entry': match['entry'], 'entry_date': entry_date,
        },
    )], ''
