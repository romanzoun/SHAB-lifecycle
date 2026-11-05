from __future__ import annotations

import re
from datetime import datetime

from .parser67 import _FR_ASSET_TRANSFER_CREDIT_CONSIDERATION
from .parser111 import _FR_ASSET_TRANSFER_NO_LIABILITIES_CASH
from .parser180 import _FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH
from .parser253 import _event
from .parser267 import DATE, MONEY, NAME, UID

_LEGACY_PATTERNS = (
    _FR_ASSET_TRANSFER_CREDIT_CONSIDERATION,
    _FR_ASSET_TRANSFER_NO_LIABILITIES_CASH,
    _FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH,
)
_FR_NO_LIABILITIES_RECEIVABLE = re.compile(
    rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), '
    rf'la société a transféré des actifs pour CHF (?P<assets>{MONEY}) '
    r'et aucun passif envers les tiers, à '
    rf'(?P<recipient>{NAME}) à (?P<recipient_place>{NAME}) '
    rf'\((?P<recipient_canton>[A-Z]{{2}})\) \((?P<recipient_uid>{UID})\)\. '
    rf'Contre-prestation: une créance de CHF (?P<consideration_amount>{MONEY})\.?'
)


def extract_parser484_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested receivable variant while preserving legacy ownership."""
    if language != 'fr' or any(pattern.search(text) for pattern in _LEGACY_PATTERNS):
        return [], text
    match = _FR_NO_LIABILITIES_RECEIVABLE.fullmatch(text)
    if not match:
        return [], text
    try:
        agreement_date = datetime.strptime(match['agreement_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload = {
        **match.groupdict(), 'agreement_date': agreement_date,
        'source_kind': 'company', 'liabilities': '0',
        'liabilities_kind': 'third_party_liabilities', 'currency': 'CHF',
        'consideration_kind': 'receivable',
    }
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'assets_transferred', 'fr.text.company_asset_transfer_no_liabilities_receivable.v1',
                   payload)], ''
