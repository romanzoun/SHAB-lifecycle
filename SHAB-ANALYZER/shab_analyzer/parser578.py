from __future__ import annotations

import re
from datetime import datetime

from .parser111 import _FR_HEAD_OFFICE_PROXY_PAIR
from .parser226 import _FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION
from .parser253 import _person_event
from .parser480 import _HEAD_OFFICE_PROXY

_NOTICE = re.compile(
    r"L'inscription au journal n° (?P<entry>\d+) du (?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"\(FOSC du (?P<notice_date>\d{2}\.\d{2}\.\d{4}) P/(?P<notice_ref>\d+)\) "
    r"est complétée en ce sens que: Procuration collective à deux, limitée à "
    r"l'établissement principal, a été conférée à (?P<name>[^,.;()\[\]\n]+); "
    r"sa procuration est modifiée en ce sens\.?"
)


def extract_parser578_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Recognize a referenced supplement to an existing head-office procuration."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
            _FR_HEAD_OFFICE_PROXY_PAIR, _FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION,
            _HEAD_OFFICE_PROXY)):
        return [], text
    match = _NOTICE.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('entry_date', 'notice_date')}
    except ValueError:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'signing_authority_changed', 'fr.persons.procuration_supplemented_head_office.v1',
        match['name'], role='fondé de procuration', signing='Kollektivprokura zu zweien',
        extra={'action': 'procuration_changed', 'scope': 'head_office',
               'entry': match['entry'], **dates, 'notice_ref': match['notice_ref']},
    )], ''
