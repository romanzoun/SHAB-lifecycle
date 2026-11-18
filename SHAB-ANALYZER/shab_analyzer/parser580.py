from __future__ import annotations

import re

from .parser91 import _FR_SPLIT_TRANSFER_TO_TWO_NEW_MANAGERS
from .parser253 import _person_event

_NAME = r'[^,.;\n]+'
_COUNT = r"[\d']+"
_TRANSFER = re.compile(
    rf'(?P<seller>{_NAME}) cède (?P<transferred>{_COUNT}) de ses (?P<before>{_COUNT}) '
    rf'parts de CHF (?P<nominal>{_COUNT}), par (?P<part1>{_COUNT}) parts à '
    rf'(?P<buyer1>{_NAME}), du (?P<origin1>{_NAME}), à (?P<place1>{_NAME}), '
    rf'nouvel associé avec (?P<received1>{_COUNT}) parts de CHF (?P=nominal), '
    rf'et par (?P<part2>{_COUNT}) parts à (?P<buyer2>{_NAME}), de (?P<origin2>{_NAME}), '
    rf'à (?P<place2>{_NAME}), nouvel associé avec signature individuelle, '
    rf'avec (?P<received2>{_COUNT}) parts de CHF (?P=nominal)\. '
    rf'(?P=seller) reste titulaire de (?P<remaining>{_COUNT}) parts de CHF (?P=nominal)\.?'
)


def extract_parser580_leftovers(text, language, publication_id, published_at,
                                org_uid, plz, canton):
    if language != 'fr' or _FR_SPLIT_TRANSFER_TO_TWO_NEW_MANAGERS.search(text.strip()):
        return [], text
    m = _TRANSFER.fullmatch(text.strip())
    if not m:
        return [], text
    count = lambda key: int(m[key].replace("'", ''))
    before, transferred, remaining, part1, part2, received1, received2 = (
        count(k) for k in ('before', 'transferred', 'remaining', 'part1', 'part2', 'received1', 'received2')
    )
    if (min(before, transferred, remaining, part1, part2, received1, received2, count('nominal')) <= 0
            or transferred != part1 + part2 or part1 != received1 or part2 != received2
            or before != transferred + remaining
            or len({m['seller'], m['buyer1'], m['buyer2']}) != 3):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.split_transfer_two_new_associates.v1'
    common = {'share_nominal': m['nominal'], 'currency': 'CHF'}
    events = [_person_event(*context, 'officer_changed', rule, m['seller'],
        extra={**common, 'action': 'shares_transferred', 'shares_before': before,
               'shares_transferred': transferred, 'shares_count': remaining})]
    for i, received in ((1, received1), (2, received2)):
        events.append(_person_event(*context, 'officer_changed', rule, m[f'buyer{i}'],
            place=m[f'place{i}'], role='associé',
            signing='Einzelunterschrift' if i == 2 else None,
            extra={**common, 'action': 'appointed', 'new_associate': True,
                   'heimat': m[f'origin{i}'], 'shares_received': received,
                   'shares_count': received, 'transfer_total': transferred}))
    return events, ''
