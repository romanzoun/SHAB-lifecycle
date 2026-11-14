from __future__ import annotations

import re
from datetime import datetime

from .parser150 import _DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE
from .parser253 import _person_event
from .parser267 import DATE, COUNT

_NAME = r'[^,.;()\n]+?'
_OWNER_NAME_CORRECTED = re.compile(
    rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) '
    rf'\(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) '
    rf'ist wie folgt berichtigt: (?P<name>{_NAME}), Inhaber, '
    rf'Einzelunterschrift \(und nicht (?P<previous_name>{_NAME})\)\.?'
)


def extract_parser553_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested owner full-name correction with notice reference."""
    if language != 'de' or _DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE.search(text.strip()):
        return [], text
    match = _OWNER_NAME_CORRECTED.fullmatch(text.strip())
    if not match:
        return [], text
    payload = match.groupdict()
    try:
        for key in ('entry_date', 'notice_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload['action'] = 'name_corrected'
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'de.persons.owner_full_name_corrected_with_reference.v1',
        match['name'], role='Inhaber', signing='Einzelunterschrift', extra=payload,
    )], ''
