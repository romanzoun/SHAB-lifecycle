from __future__ import annotations

import re

from .parser192 import _FR_BOARD_PRESIDENCY_SWAPPED
from .parser197 import _FR_BOARD_SECRETARY_CHANGED_PAIR_CONTINUES_SIGNING
from .parser253 import _person_event

_PAIR = re.compile(
    r"Les membres du conseil (?P<name1>[^,.;\n]+), jusqu'ici secrétaire, "
    r"nommée vice-présidente, et (?P<name2>[^,.;\n]+), nommée secrétaire, "
    r"continuent à signer collectivement à deux avec un membre du conseil\.?"
)


def extract_parser568_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the attested board role changes with retained restricted signing."""
    if language != 'fr':
        return [], text
    clause = text.strip()
    if any(pattern.search(clause) for pattern in (
        _FR_BOARD_PRESIDENCY_SWAPPED,
        _FR_BOARD_SECRETARY_CHANGED_PAIR_CONTINUES_SIGNING,
    )):
        return [], text
    match = _PAIR.fullmatch(clause)
    if not match or match['name1'] == match['name2']:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [_person_event(
        *context, 'officer_changed',
        'fr.persons.board_vice_president_secretary_retained_restricted_signing.v1',
        match[f'name{index}'], role=role,
        signing='Kollektivunterschrift zu zweien', extra={
            'action': 'role_changed', 'signing_continues': True,
            'signing_restriction': 'avec un membre du conseil',
            **({'previous_role': 'secrétaire'} if index == 1 else {}),
        },
    ) for index, role in ((1, 'vice-présidente'), (2, 'secrétaire'))], ''
