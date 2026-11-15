from __future__ import annotations

import re

from .parser194 import _FR_SECRETARY_SIGNING_CHANGED
from .parser220 import _FR_BOARD_PRESIDENT_AND_TWO_MEMBERS
from .parser253 import _person_event

_PERSON = r"[^,.;\[\]\n]+?"
_BOARD = re.compile(
    rf"L'administratrice (?P<name1>{_PERSON}), jusqu'ici présidente, nommé "
    r"secrétaire, signe désormais collectivement à deux; ses pouvoirs sont "
    rf"modifiés en ce sens\. (?P<name2>{_PERSON}), d'(?P<origin2>{_PERSON}), "
    rf"à (?P<place2>{_PERSON}), présidente et (?P<name3>{_PERSON}), "
    rf"d'(?P<origin3>{_PERSON}), à (?P<place3>{_PERSON}), vice-présidente, "
    r"sont membres du conseil d'administration"
)


def extract_parser560_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the attested board change after legacy group-signing extraction."""
    if language != 'fr' or any(pattern.fullmatch(text.strip()) for pattern in (
        _FR_SECRETARY_SIGNING_CHANGED, _FR_BOARD_PRESIDENT_AND_TWO_MEMBERS,
    )):
        return [], text
    match = _BOARD.fullmatch(text.strip().removesuffix('.'))
    if not match:
        return [], text
    # The removed group-signing clause must be evidenced in the original text.
    if not re.search(re.escape(match[0]) + r', avec signature collective à deux\.(?:$|\s)', source_text):
        return [], text
    if len({match[f'name{i}'] for i in (1, 2, 3)}) != 3:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [
        _person_event(
            *context, 'officer_changed',
            'fr.persons.board_president_secretary_and_two_appointments.v1',
            match[f'name{i}'], place=match[f'place{i}'] if i > 1 else None,
            role=('Sekretär des Verwaltungsrates', 'Präsident des Verwaltungsrates',
                  'Vizepräsident des Verwaltungsrates')[i - 1],
            signing='Kollektivunterschrift zu zweien',
            extra=({'action': 'role_and_signing_changed',
                    'previous_role': 'Präsident des Verwaltungsrates',
                    'powers_modified': True} if i == 1 else
                   {'action': 'appointed', 'origin': match[f'origin{i}']}),
        ) for i in (1, 2, 3)
    ], ''
