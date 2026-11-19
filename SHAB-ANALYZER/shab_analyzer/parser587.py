from __future__ import annotations

import re

from .parser85 import _FR_LIQUIDATOR_APPOINTED_AFTER_MOVE
from .parser253 import _person_event
from .parser377 import extract_parser377_leftovers

_DIRECTOR_AFTER_MOVE = re.compile(
    r'^(?P<name>[^,;.()]+),\s*maintenant à\s+(?P<place>[^,;.()]+),\s*'
    r'est nommée directrice\.?$'
)


def extract_parser587_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'fr':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    if _FR_LIQUIDATOR_APPOINTED_AFTER_MOVE.fullmatch(text.strip()) or extract_parser377_leftovers(text, language, *context)[0]:
        return [], text
    match = _DIRECTOR_AFTER_MOVE.fullmatch(text.strip())
    if not match:
        return [], text
    return [_person_event(*context, 'officer_changed', 'fr.persons.director_appointed_after_move.v1',
                          match['name'], place=match['place'], role='directrice',
                          extra={'action': 'appointed'})], ''
