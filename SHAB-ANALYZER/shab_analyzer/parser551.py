from __future__ import annotations

import re

from .parser141 import _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER
from .parser253 import _count, _person_event
from .parser267 import COUNT, MONEY, NAME

_PREFIX = (
    rf'(?P<seller>{NAME}), laquelle est nommé présidente et signe maintenant '
    rf'collectivement à deux, cède (?P<transferred>{COUNT}) de ses '
    rf'(?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à '
    rf'(?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), '
    r'nouvel associé-gérant et secrétaire'
)
_END = (
    rf' avec (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. '
    rf'(?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)\.?'
)
_TRANSFER = re.compile(_PREFIX + _END)
_SOURCE = re.compile(_PREFIX + r' avec signature collective à deux,' + _END)


def extract_parser551_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the attested transfer after the existing group signing rule."""
    if language != 'fr' or _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER.search(text.strip()):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    source = _SOURCE.search(source_text.strip())
    if (not match or not source or source.end() != len(source_text.strip())
            or source.groupdict() != match.groupdict()):
        return [], text
    before, transferred, received, remaining = (
        _count(match[key]) for key in ('before', 'transferred', 'buyer_count', 'remaining')
    )
    if transferred != received or before != transferred + remaining:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.president_transfer_new_manager_secretary.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    return [
        _person_event(*context, 'officer_changed', rule, match['seller'],
                      role='présidente', signing='Kollektivunterschrift zu zweien',
                      extra={**common, 'action': 'appointed_president_and_shares_transferred',
                             'counterparty': match['buyer'], 'shares_before': before,
                             'shares_transferred': transferred, 'shares_count': remaining}),
        _person_event(*context, 'officer_changed', rule, match['buyer'],
                      place=match['place'], role='associé-gérant et secrétaire',
                      signing='Kollektivunterschrift zu zweien',
                      extra={**common, 'action': 'appointed_manager_and_shares_received',
                             'counterparty': match['seller'], 'heimat': match['origin'],
                             'shares_received': received, 'shares_count': received}),
    ], ''
