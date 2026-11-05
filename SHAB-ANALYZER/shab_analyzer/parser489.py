from __future__ import annotations

import re
from datetime import datetime

from .parser79 import _FR_ASSET_TRANSFER_WITH_LIABILITIES
from .parser93 import _FR_ASSET_TRANSFER_UID_BEFORE_PLACE
from .parser253 import _event
from .parser267 import DATE, MONEY, NAME, UID
from .text_extras import _FR_SOLE_PROPRIETOR_ASSET_TRANSFER

_FR_ASSET_TRANSFER_REDUCED = re.compile(
    rf'Transfert de patrimoine: Une partie des actifs dont le transfert était prévu par contrat du (?P<date>{DATE}), '
    rf'à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), se sont révélés incessibles selon la LDFR\. '
    rf"Selon l'avenant au contrat du (?P<amendment_date>{DATE}), les actifs concernés ne sont plus transférés "
    rf'et la valeur des actifs transférés est réduite à CHF (?P<assets>{MONEY})\. '
    rf'La titulaire a ainsi transféré des actifs pour CHF (?P=assets) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), '
    rf'soit un actif net de CHF (?P<net_assets>{MONEY})\. Contre-prestation: une créance de CHF (?P<consideration_amount>{MONEY})\.?'
)


def extract_parser489_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Capture the amended transfer totals; do not infer excluded asset values."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_ASSET_TRANSFER_WITH_LIABILITIES, _FR_ASSET_TRANSFER_UID_BEFORE_PLACE,
        _FR_SOLE_PROPRIETOR_ASSET_TRANSFER,
    )):
        return [], text
    match = _FR_ASSET_TRANSFER_REDUCED.fullmatch(text)
    if not match:
        return [], text
    payload = match.groupdict()
    try:
        for key in ('date', 'amendment_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload.update(currency='CHF', consideration='une créance de CHF ' + payload['consideration_amount'],
                   consideration_kind='claim', amendment_reason='non_transferable_assets_under_ldfr')
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'assets_transferred', 'fr.text.asset_transfer_reduced_by_amendment.v1', payload)], ''
