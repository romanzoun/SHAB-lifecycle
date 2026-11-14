from __future__ import annotations

import re

from .parser128 import _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER
from .parser249 import _FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE
from .parser527 import _TRANSFER as _THREE_SELLERS_TRANSFER
from .parser253 import _person_event

_NAME = r'[^,.;\n]+?'
_TRANSFER = re.compile(
    rf'Les associés (?P<seller1>{_NAME}) et (?P<seller2>{_NAME}) ont respectivement '
    r'cédé (?P<count1>\d+) et (?P<count2>\d+) parts de CHF (?P<nominal>\d+) '
    rf'au nouvel associé (?P<buyer1>{_NAME}), de (?P<origin1>{_NAME}), '
    rf'à (?P<place1>{_NAME}), (?P<country1>[A-Z]{{3}})\. '
    r'(?P=seller2) a également cédé (?P<count3>\d+) parts de CHF (?P=nominal) '
    rf'à la nouvelle associée (?P<buyer2>{_NAME}), du (?P<origin2>{_NAME}), '
    rf'à (?P<place2>{_NAME})\. Les nouveaux associés (?P=buyer1) et (?P=buyer2) '
    r'sont en outre nommés gérants, tous deux'
)
_END = (
    r' Par conséquent, (?P=seller1) et (?P=seller2) sont maintenant respectivement '
    r'titulaires de (?P<remaining1>\d+) et (?P<remaining2>\d+) parts de CHF (?P=nominal)'
)
_REMAINDER = re.compile(_TRANSFER.pattern + _END + r'\.?')
_SOURCE = re.compile(_TRANSFER.pattern + r' avec signature individuelle\.' + _END + r'\.')


def extract_parser555_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Keep separately reported transfers, holdings and management appointments."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER,
        _FR_TWO_SELLERS_TRANSFER_TO_NEW_ASSOCIATE, _THREE_SELLERS_TRANSFER,
    )):
        return [], text
    match = _REMAINDER.fullmatch(text.strip())
    if not match or not any(m.groupdict() == match.groupdict() for m in _SOURCE.finditer(source_text)):
        return [], text
    amounts = {key: int(match[key]) for key in ('count1', 'count2', 'count3', 'remaining1', 'remaining2')}
    if any(value <= 0 for value in amounts.values()) or int(match['nominal']) <= 0:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.two_associates_unequal_transfers_two_new_managers.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    events = []
    for i, transferred in ((1, amounts['count1']), (2, amounts['count2'] + amounts['count3'])):
        events.append(_person_event(
            *context, 'officer_changed', rule, match[f'seller{i}'], role='associé',
            extra={**common, 'action': 'shares_transferred', 'shares_transferred': transferred,
                   'shares_count': amounts[f'remaining{i}']},
        ))
    for i, received in ((1, amounts['count1'] + amounts['count2']), (2, amounts['count3'])):
        extra = {**common, 'action': 'shares_received', 'new_associate': True,
                 'shares_received': received, 'shares_count': received, 'origin': match[f'origin{i}']}
        if i == 1:
            extra['country'] = match['country1']
        events.append(_person_event(
            *context, 'officer_changed', rule, match[f'buyer{i}'], place=match[f'place{i}'],
            role='associé-gérant' if i == 1 else 'associée-gérante',
            signing='Einzelunterschrift', extra=extra,
        ))
    return events, ''
