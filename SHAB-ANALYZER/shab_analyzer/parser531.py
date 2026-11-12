from __future__ import annotations

import re

from .parser74 import _FR_ASSOCIATE_MANAGERS_AFTER_TRANSFER
from .parser110 import _FR_SHARE_TRANSFER_AND_ASSOCIATE_MANAGERS
from .parser253 import _person_event

_NAME = r'[^,;.\[\]\n]+?'
_TRANSFER = re.compile(
    rf'(?P<seller>{_NAME}) a cédé (?P<count>\d+) parts de CHF '
    rf"(?P<nominal>\d+(?:'\d{{3}})*) au nouvel associé (?P<buyer>{_NAME}), "
    rf'de (?P<origin>{_NAME}), à (?P<place>{_NAME})\. Associés-gérants: '
    r'(?P=seller) pour (?P<remaining>\d+) parts de CHF (?P=nominal) et '
    r'(?P=buyer) pour (?P=count) parts de CHF (?P=nominal), nommé président, tous deux\.?'
)


def extract_parser531_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Record the explicit transfer and holdings, without inferring signing rights."""
    if language != 'fr' or any(p.search(text.strip()) for p in (
        _FR_ASSOCIATE_MANAGERS_AFTER_TRANSFER,
        _FR_SHARE_TRANSFER_AND_ASSOCIATE_MANAGERS,
    )):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match or any(int(match[k].replace("'", '')) <= 0
                        for k in ('count', 'nominal', 'remaining')):
        return [], text
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    context = (publication_id, published_at, org_uid, plz, canton)
    rule = 'fr.persons.transfer_new_associate_manager_president.v1'
    return [
        _person_event(*context, 'officer_changed', rule, match['seller'],
                      role='associé-gérant', extra={**common,
                      'shares_count': int(match['remaining']),
                      'shares_transferred': int(match['count'])}),
        _person_event(*context, 'officer_changed', rule, match['buyer'],
                      place=match['place'], role='associé-gérant président',
                      extra={**common, 'shares_count': int(match['count']),
                             'heimat': match['origin']}),
    ], ''
