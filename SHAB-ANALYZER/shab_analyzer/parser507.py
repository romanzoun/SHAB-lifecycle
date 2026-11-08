from __future__ import annotations

import re

from .parser128 import _FR_BOARD_MEMBER_COUNTRY
from .parser154 import _FR_BOARD_MEMBER_WITHOUT_SIGNATURE
from .parser253 import _person_event


_LEGACY = (_FR_BOARD_MEMBER_COUNTRY, _FR_BOARD_MEMBER_WITHOUT_SIGNATURE)
_MEMBER = re.compile(
    r'(?P<name>[^,.;\[\]\n]+), de et au (?P<place>[^,.;\[\]\n]+), '
    r'est membre du conseil'
)


def extract_parser507_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the attested shared origin/domicile board appointment."""
    if language != 'fr' or any(p.search(text.strip()) for p in _LEGACY):
        return [], text
    match = _MEMBER.fullmatch(text.strip().rstrip('.'))
    if not match:
        return [], text
    # Signing was consumed separately upstream; require the original evidence.
    evidence = match.group() + ' avec signature collective à deux.'
    if evidence not in source_text:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.board_member_shared_origin_au.v1', match['name'],
        place=match['place'], role='membre du conseil',
        extra={'action': 'appointed', 'heimat': match['place']},
    )], ''
