from __future__ import annotations

import re
from datetime import datetime

from .parser93 import _FR_ASSET_TRANSFER_UID_BEFORE_PLACE
from .parser253 import _event
from .parser267 import DATE, MONEY, UID
from .parser395 import ASSET_TRANSFER_NO_CONSIDERATION_PATTERN

_LEGACY = (_FR_ASSET_TRANSFER_UID_BEFORE_PLACE,
           re.compile(ASSET_TRANSFER_NO_CONSIDERATION_PATTERN + r'\.?'))
_NAME = r'[^,;\[\]\n]+?'
_TRANSFER = re.compile(
    rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), '
    rf'la société a transféré des actifs pour CHF (?P<assets>{MONEY}) '
    rf'et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), à '
    rf'(?P<recipient>{_NAME}) \((?P<recipient_uid>{UID})\), '
    rf'à (?P<recipient_place>{_NAME})\. Contre-prestation: aucune\.?'
)


def extract_parser504_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested company transfer without consideration or net total."""
    if language != 'fr' or any(p.search(text) for p in _LEGACY):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        date = datetime.strptime(match['agreement_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload = {**match.groupdict(), 'agreement_date': date, 'currency': 'CHF',
               'source_kind': 'company', 'liabilities_kind': 'third_party_liabilities',
               'consideration': 'aucune', 'consideration_kind': 'none'}
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'assets_transferred', 'fr.text.company_asset_transfer_no_consideration.v1',
                   payload)], ''
