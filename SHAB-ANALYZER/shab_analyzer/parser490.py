from __future__ import annotations

import re

from .parser171 import _IT_ASSET_ACQUISITION_PRICE_CORRECTED
from .parser253 import _event
from .parser267 import MONEY

_IT_ACQUISITION_CURRENCY_CORRECTED = re.compile(
    r'Fatti particolari: Intenzione di assunzione beni: la società intende acquistare '
    r'(?P<asset>[^\[\]\r\n]+?) per il prezzo di (?P<currency>EUR) '
    rf'(?P<price>{MONEY}) \[no: Intenzione di assunzione beni: la società intende acquistare '
    r'(?P=asset) per il prezzo di (?P<previous_incorrect_currency>CHF) (?P=price)\]\.?'
)


def extract_parser490_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested currency correction without claiming an actual purchase."""
    if language != 'it' or _IT_ASSET_ACQUISITION_PRICE_CORRECTED.search(text):
        return [], text
    match = _IT_ACQUISITION_CURRENCY_CORRECTED.fullmatch(text)
    if not match:
        return [], text
    payload = dict(match.groupdict(), kind='asset_acquisition_intention_clause', action='currency_corrected')
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'statutes_changed', 'it.text.asset_acquisition_currency_corrected.v1', payload)], ''
