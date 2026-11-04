from __future__ import annotations

import re

from .parser111 import _FR_HEAD_OFFICE_PROXY_PAIR
from .parser226 import _FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION
from .parser253 import _person_event

_HEAD_OFFICE_PROXY = re.compile(
    r'Procuration collective à deux, limitée au siège principal, est conférée à '
    r'(?P<name>[^,.;]+), de (?P<origin>[^,.;]+), à (?P<place>[^,.;]+)\.?'
)


def extract_parser480_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize a single head-office procuration without further exclusions."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_HEAD_OFFICE_PROXY_PAIR, _FR_HEAD_OFFICE_PROXY_WITH_EXCLUSION,
    )):
        return [], text
    match = _HEAD_OFFICE_PROXY.fullmatch(text)
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'signing_authority_changed', 'fr.persons.head_office_proxy_single.v1', match['name'],
        place=match['place'], role='fondé de procuration', signing='Kollektivprokura zu zweien',
        extra={'action': 'procuration_granted', 'origin': match['origin'].strip(),
               'scope': 'head_office'},
    )], ''
