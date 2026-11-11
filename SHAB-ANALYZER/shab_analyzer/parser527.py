from __future__ import annotations

import re

from .parser128 import _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER
from .parser225 import _FR_MANAGER_TRANSFER_TO_TWO_NEW_MANAGERS
from .parser253 import _person_event
from .parser55 import _FR_STANDALONE_GROUP_SIGNING

# Three named sellers and two new managers; amounts are reported independently.
_NAME = r"[^,;.\[\]\n]+?"
_TRANSFER = re.compile(
    rf"^Les associés (?P<seller1>{_NAME}), (?P<seller2>{_NAME}) et (?P<seller3>{_NAME}) "
    r"ont respectivement chacun cédé (?P<count>\d+) parts de CHF (?P<nominal>\d+) "
    rf"aux nouveaux associés-gérants: (?P<buyer1>{_NAME}), de (?P<origin1>{_NAME}), "
    rf"à (?P<place1>{_NAME}), (?P<country1>[A-Z]{{3}}), et (?P<buyer2>{_NAME}), "
    rf"de (?P<origin2>{_NAME}), à (?P<place2>{_NAME}), (?P<country2>[A-Z]{{3}}), "
    r"pour (?P<holding>\d+) parts de CHF (?P=nominal) chacun, tous deux"
    r"(?=\.|$| )"
)


def extract_parser527_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Keep individual transfer amounts separate from the buyers' stated holdings."""
    if language != 'fr' or any(p.search(text) for p in (
        _FR_STANDALONE_GROUP_SIGNING,
        _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER,
        _FR_MANAGER_TRANSFER_TO_TWO_NEW_MANAGERS,
    )):
        return [], text
    match = _TRANSFER.match(text.strip())
    if not match:
        return [], text
    events = []
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    context = (publication_id, published_at, org_uid, plz, canton)
    rule = 'fr.persons.three_associates_transfer_two_new_managers.v1'
    for i in range(1, 4):
        events.append(_person_event(
            *context, 'officer_changed', rule, match[f'seller{i}'], role='associé',
            extra={**common, 'action': 'shares_transferred',
                   'shares_transferred': int(match['count'])},
        ))
    for i in range(1, 3):
        events.append(_person_event(
            *context, 'officer_changed', rule, match[f'buyer{i}'],
            place=match[f'place{i}'], role='associé-gérant',
            extra={**common, 'shares_count': int(match['holding']),
                   'heimat': match[f'origin{i}'], 'country': match[f'country{i}']},
        ))
    return events, text.strip()[match.end():].lstrip(' .')
