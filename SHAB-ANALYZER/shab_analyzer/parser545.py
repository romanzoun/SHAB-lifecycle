from __future__ import annotations

import re

from .parser99 import _FR_TWO_BOARD_MEMBERS
from .parser165 import _FR_BOARD_MEMBERS, _french_board_members
from .parser253 import _person_event


_PAIR = re.compile(
    r"(?P<name1>[^,.;\n]+), de (?P<origin1>[^,.;\n]+), à "
    r"(?P<place1>[^,.;\n]+), signature collective à deux, et "
    r"(?P<name2>[^,.;\n]+), de (?P<origin2>[^,.;\n]+), à "
    r"(?P<place2>[^,.;\n]+), signature collective à deux, "
    r"sont membres du conseil d'administration\.?"
)


def extract_parser545_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Two board members with a separate explicit signing clause each."""
    if language != 'fr' or _FR_TWO_BOARD_MEMBERS.search(text.strip()):
        return [], text
    legacy = _FR_BOARD_MEMBERS.fullmatch(text.strip())
    if legacy and _french_board_members(legacy['members']):
        return [], text
    match = _PAIR.fullmatch(text.strip())
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.board_pair_separate_collective_signing.v1',
        match[f'name{i}'], role='Verwaltungsrat',
        signing='Kollektivunterschrift zu zweien', place=match[f'place{i}'],
        extra={'action': 'appointed', 'origin': match[f'origin{i}']},
    ) for i in (1, 2)], ''
