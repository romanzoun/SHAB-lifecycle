from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .parser135 import _FR_TWO_MANAGERS_TRANSFER_TO_ONE_MANAGER
from .parser253 import _person_event

_HOLDINGS = re.compile(
    r"(?<!\S)(?P<name1>[^,;.\[\]\n]+?) et (?P<name2>[^,;.\[\]\n]+?) "
    r"restent titulaires, chacun, de (?P<count>[\d']+) parts de CHF "
    r"(?P<nominal>\d+(?:\.\d+)?)(?:\.(?=\s|$)|$)"
)


def extract_parser529_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Report explicit individual holdings without inferring transfers or roles."""
    if language != 'fr' or _FR_TWO_MANAGERS_TRANSFER_TO_ONE_MANAGER.search(text.strip()):
        return [], text
    match = _HOLDINGS.search(text)
    if not match:
        return [], text
    try:
        count = int(match['count'].replace("'", ''))
        nominal = Decimal(match['nominal'])
    except (ValueError, InvalidOperation):
        return [], text
    if count <= 0 or nominal <= 0:
        return [], text
    events = [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.two_holders_remaining_shares_each.v1',
        match[f'name{i}'],
        extra={'shares_count': count, 'share_nominal': match['nominal'], 'currency': 'CHF'},
    ) for i in (1, 2)]
    return events, (text[:match.start()] + text[match.end():]).strip()
