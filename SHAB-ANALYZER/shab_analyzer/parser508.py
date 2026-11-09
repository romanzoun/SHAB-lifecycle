from __future__ import annotations

import re

from .keys import person_key
from .parser113 import _FR_AUDITOR_RENAMED_AND_MOVED
from .parser142 import _FR_AUDITOR_RENAMED_AND_MOVED_SAME_UID
from .parser253 import _person_event
from .parser267 import UID


_LEGACY = (_FR_AUDITOR_RENAMED_AND_MOVED,
           _FR_AUDITOR_RENAMED_AND_MOVED_SAME_UID)
_NAME = r'[^,.;()\[\]\n]+'
_RENAMED_MOVED = re.compile(
    rf'(?P<previous_name>{_NAME}) \((?P<uid>{UID})\) '
    rf'qui se nomme maintenant (?P<name>{_NAME}) \((?P=uid)\), '
    rf'est désormais à (?P<place>{_NAME})\.?'
)


def extract_parser508_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested same-UID name and domicile change, without a role guess."""
    if language != 'fr' or any(p.search(text.strip()) for p in _LEGACY):
        return [], text
    match = _RENAMED_MOVED.fullmatch(text.strip())
    if not match:
        return [], text
    event = _person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.legal_entity_renamed_and_moved_same_uid.v1', match['name'],
        place=match['place'],
        extra={'action': 'name_and_domicile_changed',
               'previous_name': match['previous_name'].strip(),
               'uid': match['uid'], 'previous_uid': match['uid']},
    )
    event.person_key = person_key(name=match['name'].strip(), uid=match['uid'])
    return [event], ''
