from __future__ import annotations

import re

from .parser99 import _FR_TWO_BOARD_MEMBERS
from .parser165 import _FR_BOARD_MEMBERS, _french_board_members, extract_parser165_leftovers

# Only the evidenced missing comma between the first domicile and the conjunction.
_PAIR = re.compile(
    r"(?P<name1>[^,.;]+), de (?P<origin1>[^,.;]+), à "
    r"(?P<place1>[^,.;]+?) et (?P<name2>[^,.;]+), de et à "
    r"(?P<place2>[^,.;]+), sont membres du conseil d'administration"
)
_SUFFIX = ', avec signature collective à deux'


def extract_parser464_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'fr' or _FR_TWO_BOARD_MEMBERS.search(text.strip()):
        return [], text
    legacy = _FR_BOARD_MEMBERS.fullmatch(text.strip())
    if legacy and _french_board_members(legacy['members']):
        return [], text
    clause = text.strip().rstrip('.')
    core = clause.removesuffix(_SUFFIX)
    match = _PAIR.fullmatch(core)
    if not match or core + _SUFFIX + '.' not in source_text:
        return [], text
    canonical = (
        f"{match['name1']}, de {match['origin1']}, à {match['place1']}, et "
        f"{match['name2']}, de et à {match['place2']}, sont membres du conseil d'administration"
    )
    events, rest = extract_parser165_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 2 or rest:
        return [], text
    for event in events:
        event.rule_id = 'fr.persons.two_board_members_missing_comma.v1'
    return events, ''
