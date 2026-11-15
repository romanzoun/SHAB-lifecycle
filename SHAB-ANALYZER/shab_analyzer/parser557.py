from __future__ import annotations

import re

from .parser100 import _FR_TRANSFER_TO_UNSIGNED_MANAGER
from .parser135 import _FR_ASSOCIATE_TRANSFER_NEW_MANAGER_SELLER_PRESIDENT
from .parser231 import _FR_DOMICILE_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT
from .parser253 import _person_event

LEGACY = (_FR_TRANSFER_TO_UNSIGNED_MANAGER,
          _FR_ASSOCIATE_TRANSFER_NEW_MANAGER_SELLER_PRESIDENT,
          _FR_DOMICILE_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT)
_NAME = r'[^,.;\n]+?'
_START = (
    rf'(?P<seller>{_NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF '
    rf'(?P<nominal>\d+) à (?P<buyer>{_NAME}), de (?P<origin>{_NAME}), '
    rf'à (?P<place>{_NAME}), nouvel associé-gérant'
)
_END = (
    r' titulaire de (?P<received>\d+) parts de CHF (?P=nominal); '
    r'(?P=seller), qui reste titulaire de (?P<remaining>\d+) parts de CHF '
    r'(?P=nominal), est nommé président'
)
_REMAINDER = re.compile(_START + _END + r'\.?')
_SOURCE = re.compile(_START + r' avec signature individuelle,' + _END + r'\.')


def extract_parser557_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Handle the explicit 'titulaire de' variant with source signing evidence."""
    if language != 'fr' or any(p.search(text.strip()) for p in LEGACY):
        return [], text
    m = _REMAINDER.fullmatch(text.strip())
    if not m or not any(s.groupdict() == m.groupdict() for s in _SOURCE.finditer(source_text)):
        return [], text
    amounts = {key: int(m[key]) for key in ('count', 'before', 'received', 'remaining', 'nominal')}
    if (min(amounts.values()) <= 0 or amounts['count'] != amounts['received']
            or amounts['before'] != amounts['count'] + amounts['remaining']
            or m['seller'] == m['buyer']):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.transfer_new_manager_explicit_holding_seller_president.v1'
    common = {'share_nominal': m['nominal'], 'currency': 'CHF'}
    return [
        _person_event(*context, 'officer_changed', rule, m['seller'], role='président',
                      extra={**common, 'action': 'shares_transferred_and_appointed_president',
                             'counterparty': m['buyer'], 'shares_before': amounts['before'],
                             'shares_transferred': amounts['count'], 'shares_count': amounts['remaining']}),
        _person_event(*context, 'officer_changed', rule, m['buyer'], place=m['place'],
                      role='associé-gérant', signing='Einzelunterschrift',
                      extra={**common, 'action': 'appointed_and_shares_received',
                             'counterparty': m['seller'], 'origin': m['origin'], 'new_associate': True,
                             'shares_received': amounts['received'], 'shares_count': amounts['received']}),
    ], ''
