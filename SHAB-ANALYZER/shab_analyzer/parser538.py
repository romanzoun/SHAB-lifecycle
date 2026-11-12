from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _count
from .parser267 import COUNT, MONEY
from .parser162 import _FR_REGISTERED_SHARE_STRUCTURE_CORRECTED as _OLD_STRUCTURE
from .parser202 import _FR_REGISTERED_SHARE_STRUCTURE_CORRECTED as _OLD_RESTRICTED
from .parser116 import _FR_SHARE_CAPITAL_DIVISION_CORRECTED as _OLD_DIVISION


_FR_NEW_SHARE_COUNT_CORRECTED = re.compile(
    rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}), p\. (?P<notice_ref>\d+/\d+)\) "
    rf"est rectifiée en ce sens que le nouveau capital-actions est divisé en "
    rf"(?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), "
    r"(?:avec restrictions quant à la transmissibilité selon statuts )?"
    rf"\(et non (?P<previous_count>{COUNT}) actions nominatives de CHF "
    rf"(?P<previous_nominal>{MONEY}) comme publié\)\.?"
)


def extract_parser538_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested new-capital count correction without inferring a total."""
    if language != 'fr' or any(p.search(text.strip()) for p in (
        _OLD_STRUCTURE, _OLD_RESTRICTED, _OLD_DIVISION,
    )):
        return [], text
    match = _FR_NEW_SHARE_COUNT_CORRECTED.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {k: datetime.strptime(match[k], '%d.%m.%Y').date().isoformat()
                 for k in ('entry_date', 'notice_date')}
    except ValueError:
        return [], text
    if any(Decimal(match[k].replace("'", '')) <= 0 for k in (
        'count', 'nominal', 'previous_count', 'previous_nominal',
    )):
        return [], text
    payload = {
        'kind': 'share_structure', 'action': 'corrected', 'currency': 'CHF',
        'shares_count': _count(match['count']), 'share_nominal': match['nominal'],
        'share_kind': 'actions nominatives',
        'previous_shares_count': _count(match['previous_count']),
        'previous_share_nominal': match['previous_nominal'],
        'entry': match['entry'], 'notice_ref': match['notice_ref'], **dates,
    }
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'capital_changed', 'fr.text.new_share_count_corrected.v1', payload)], ''
