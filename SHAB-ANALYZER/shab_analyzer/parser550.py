from __future__ import annotations

import re
from datetime import datetime

from .parser111 import _FR_ASSET_TRANSFER_NO_LIABILITIES_CASH
from .parser180 import _FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH
from .parser253 import _event
from .parser267 import DATE, MONEY, NAME, UID

_LEGACY = (_FR_ASSET_TRANSFER_NO_LIABILITIES_CASH,
           _FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH)
_TRANSFER = re.compile(
    rf'Transfert de patrimoine: selon contrat du (?P<date>{DATE}), '
    rf'la société a transféré des actifs pour CHF (?P<assets>{MONEY}) '
    r'et aucun passif envers les tiers à '
    rf'(?P<recipient>{NAME}), à (?P<recipient_place>{NAME}) '
    rf'\((?P<recipient_uid>{UID})\)\. Contre-prestation: CHF '
    rf'(?P<consideration>{MONEY})\.?'
)


def extract_parser550_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the evidenced cash transfer without a comma before the recipient."""
    if language != 'fr' or any(p.search(text) for p in _LEGACY):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        date = datetime.strptime(match['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton, 'assets_transferred',
        'fr.text.company_asset_transfer_no_liabilities_cash_without_comma.v1',
        {**match.groupdict(), 'date': date, 'liabilities': '0', 'currency': 'CHF'},
    )], ''
