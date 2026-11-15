from __future__ import annotations

import re

from .parser117 import _FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER
from .parser224 import _FR_THREE_ASSOCIATES_TRANSFER_TO_ONE
from .parser128 import _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER
from .parser249 import _FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE
from .parser527 import _TRANSFER as _THREE_SELLERS_TRANSFER
from .parser253 import _person_event

_NAME = r'[^,.;\n]+?'
_TRANSFER = (
    rf'(?P<seller1>{_NAME}), (?P<seller2>{_NAME}) et (?P<seller3>{_NAME}) '
    r'ont respectivement cédé (?P<count>\d+) parts de CHF (?P<nominal>\d+) '
    rf'au nouvel associé-gérant (?P<buyer>{_NAME}), de et à (?P<place>{_NAME}), '
)
_HOLDINGS = (
    r'Les associés (?P=seller1), (?P=seller2), (?P=seller3) et (?P=buyer) '
    r'sont désormais titulaires de (?P<holding>\d+) parts de CHF (?P=nominal) chacun'
)
_REMAINDER = re.compile(_TRANSFER + _HOLDINGS + r'\.?')
_SOURCE = re.compile(_TRANSFER + r'avec signature individuelle\. ' + _HOLDINGS + r'\.')


def extract_parser556_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Preserve three individual transfers and the four explicitly stated holdings."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER,
        _FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE, _THREE_SELLERS_TRANSFER,
        _FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER, _FR_THREE_ASSOCIATES_TRANSFER_TO_ONE,
    )):
        return [], text
    match = _REMAINDER.fullmatch(text.strip())
    if not match or not any(m.groupdict() == match.groupdict() for m in _SOURCE.finditer(source_text)):
        return [], text
    count, nominal, holding = (int(match[key]) for key in ('count', 'nominal', 'holding'))
    if min(count, nominal, holding) <= 0:
        return [], text
    names = [match[key] for key in ('seller1', 'seller2', 'seller3', 'buyer')]
    if len(set(names)) != 4:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.three_associates_transfer_one_new_manager_equal_holdings.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF', 'shares_count': holding}
    events = [
        _person_event(*context, 'officer_changed', rule, name, role='associé',
                      extra={**common, 'action': 'shares_transferred', 'shares_transferred': count})
        for name in names[:3]
    ]
    events.append(_person_event(
        *context, 'officer_changed', rule, match['buyer'], place=match['place'],
        role='associé-gérant', signing='Einzelunterschrift',
        extra={**common, 'action': 'shares_received', 'shares_received': 3 * count,
               'new_associate': True, 'origin': match['place']},
    ))
    return events, ''
