from __future__ import annotations

import re

from .parser200 import _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING
from .parser253 import _count, _person_event
from .parser267 import COUNT, MONEY
from .parser552 import _TRANSFER as _LEGACY_TRANSFER

_NAME = r'[^,;.()\[\]\n]+?'
_TRANSFER = re.compile(
    rf'(?P<seller>{_NAME}) détient maintenant (?P<remaining>{COUNT}) parts de CHF '
    rf'(?P<nominal>{MONEY}), par suite de cession de (?P<count>{COUNT}) parts de CHF '
    rf"(?P=nominal) à (?P<buyer>{_NAME}), jusqu'ici avec procuration collective à deux, "
    rf'nouvel associé pour (?P<received>{COUNT}) parts de CHF (?P=nominal)'
)
_SOURCE = re.compile(_TRANSFER.pattern + r', avec signature collective à deux\.?$')


def extract_parser574_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the evidenced transfer to an associate previously holding procuration."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING, _LEGACY_TRANSFER,
    )):
        return [], text
    match = _TRANSFER.fullmatch(text.strip().removesuffix('.'))
    source = _SOURCE.search(source_text.strip())
    if not match or not source or {k: v.strip() for k, v in source.groupdict().items()} != match.groupdict():
        return [], text
    count, received, remaining = (_count(match[k]) for k in ('count', 'received', 'remaining'))
    if count <= 0 or received != count or remaining <= 0 or match['seller'] == match['buyer']:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.share_transfer_new_associate_previous_joint_procuration.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    return [
        _person_event(*context, 'officer_changed', rule, match['seller'],
                      extra={**common, 'action': 'shares_transferred',
                             'counterparty': match['buyer'], 'shares_transferred': count,
                             'shares_count': remaining}),
        _person_event(*context, 'officer_changed', rule, match['buyer'], role='associé',
                      signing='Kollektivunterschrift zu zweien',
                      extra={**common, 'action': 'shares_received', 'new_associate': True,
                             'previous_signing': 'Kollektivprokura zu zweien',
                             'counterparty': match['seller'], 'shares_received': received,
                             'shares_count': received}),
    ], ''
