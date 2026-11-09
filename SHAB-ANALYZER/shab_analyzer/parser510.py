from __future__ import annotations

import re
from decimal import Decimal

from .parser227 import _FR_FOREIGN_COMPANY_SHARE_TRANSFER
from .parser253 import _person_event
from .parser267 import COUNT, MONEY, NAME


_TRANSFER = re.compile(
    rf"L'associé (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) de ses "
    rf'(?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à '
    rf'"(?P<buyer>[^"(),;\n]+)" \((?P<registry>n° \d{{3}} \d{{3}} \d{{3}} R\.C\.S)\), '
    rf'à (?P<place>{NAME}), (?P<country>F), nouvelle associée\.?'
)


def extract_parser510_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested partial transfer to a foreign registered company."""
    if language != 'fr' or _FR_FOREIGN_COMPANY_SHARE_TRANSFER.search(text.strip()):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match:
        return [], text
    count = int(match['count'].replace("'", ''))
    before = int(match['before'].replace("'", ''))
    if not 0 < count < before or Decimal(match['nominal'].replace("'", '')) <= 0:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.partial_share_transfer_foreign_registered_company.v1'
    common = {'currency': 'CHF', 'share_nominal': match['nominal']}
    return [
        _person_event(*context, 'officer_changed', rule, match['seller'], role='associé',
                      extra={**common, 'action': 'shares_transferred',
                             'shares_before': before, 'shares_transferred': count,
                             'shares_count': before - count, 'counterparty': match['buyer']}),
        _person_event(*context, 'officer_changed', rule, match['buyer'],
                      place=match['place'], role='associée',
                      extra={**common, 'action': 'appointed_and_shares_received',
                             'shares_received': count, 'shares_count': count,
                             'registry_id': match['registry'], 'country': match['country'],
                             'counterparty': match['seller']}),
    ], ''
