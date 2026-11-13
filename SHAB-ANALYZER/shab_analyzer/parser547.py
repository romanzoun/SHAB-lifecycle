from __future__ import annotations

import re

from .parser128 import _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER
from .parser253 import _person_event

_NAME = r'[^,;.\[\]\n]+?'
_TRANSFER = re.compile(
    rf'Les associés (?P<seller1>{_NAME}) et (?P<seller2>{_NAME}), '
    r'détiennent désormais (?P<remaining>\d+) parts de CHF (?P<nominal>\d+) chacun, '
    r'par suite de cession de (?P<count>\d+) parts de CHF (?P=nominal) chacun à '
    rf'(?P<buyer>{_NAME}), de et à (?P<place>{_NAME}), nouvelle associée-gérante, '
    r'pour (?P<holding>\d+) parts de CHF (?P=nominal)\.?'
)


def extract_parser547_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the explicit equal transfers and holdings without inferring signing."""
    if language != 'fr' or _FR_TWO_ASSOCIATES_TRANSFER_TO_NEW_MANAGER.search(text):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match or int(match['holding']) != 2 * int(match['count']):
        return [], text
    context = (publication_id, published_at, org_uid, plz, canton)
    rule = 'fr.persons.two_associates_equal_transfer_new_manager.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    sellers = [match[f'seller{i}'].strip() for i in (1, 2)]
    buyer = match['buyer'].strip()
    events = [_person_event(
        *context, 'officer_changed', rule, seller, role='associé', extra={
            **common, 'action': 'shares_transferred', 'counterparty': buyer,
            'shares_transferred': int(match['count']),
            'shares_count': int(match['remaining']),
        },
    ) for seller in sellers]
    events.append(_person_event(
        *context, 'officer_changed', rule, buyer, place=match['place'],
        role='associée-gérante', extra={
            **common, 'action': 'shares_received', 'new_associate': True,
            'origin': match['place'].strip(), 'origin_same_as_place': True,
            'counterparties': sellers, 'shares_received': int(match['holding']),
            'shares_count': int(match['holding']),
        },
    ))
    return events, ''
