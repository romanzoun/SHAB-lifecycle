from __future__ import annotations

import re

from .parser78 import _DE_PROFIT_CERTIFICATE_SINGULAR
from .parser253 import _event


_CERTIFICATE = re.compile(
    r'Genussscheine neu: (?P<count>1) Genussschein mit Rechten auf '
    r'(?P<rights>Anteil am Bilanzgewinn und am Liquidationserlös) gemäss Statuten\.?'
)


def extract_parser509_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested singular certificate without the legacy comma."""
    if language != 'de' or _DE_PROFIT_CERTIFICATE_SINGULAR.search(text.strip()):
        return [], text
    match = _CERTIFICATE.fullmatch(text.strip())
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'de.text.profit_participation_certificate_profit_liquidation.v1',
        {'kind': 'profit_participation_certificate', 'count': int(match['count']),
         'rights': match['rights'], 'details': 'statutes'},
    )], ''
