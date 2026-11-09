from __future__ import annotations

import re

from .parser82 import _FR_ADMINISTRATION_THREE_POWERS_CHANGED
from .parser119 import _FR_BOARD_THREE_WITH_CHANGED_SIGNING
from .parser130 import _person_event


_BOARD = re.compile(
    r"Administration: (?P<name1>[^,.;\n]+), de (?P<origin1>[^,.;\n]+), "
    r"à (?P<place1>[^,.;\n]+), président, (?P<name2>[^,.;\n]+), "
    r"de et à (?P<place2>[^,.;\n]+), secrétaire, et (?P<name3>[^,.;\n]+), "
    r"lesquels signent collectivement à deux; les pouvoirs de (?P=name3) "
    r"sont modifiés en ce sens\.?"
)


def extract_parser514_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested three-director board with shared origin/residence."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_ADMINISTRATION_THREE_POWERS_CHANGED, _FR_BOARD_THREE_WITH_CHANGED_SIGNING,
    )):
        return [], text
    match = _BOARD.fullmatch(text.strip())
    if not match:
        return [], text
    events = []
    for i, role in ((1, 'administrateur président'),
                    (2, 'administrateur secrétaire'),
                    (3, "membre du conseil d'administration")):
        extra = {'action': 'signing_changed' if i == 3 else 'details_recorded'}
        if i < 3:
            extra['heimat'] = match['origin1'] if i == 1 else match['place2']
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            'officer_changed', 'fr.persons.board_three_shared_origin_residence_signing.v1',
            match[f'name{i}'], place=match[f'place{i}'] if i < 3 else None,
            role=role, signing='Kollektivunterschrift zu zweien', extra=extra,
        ))
    return events, ''
