from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .parser58 import _FR_SHARE_SPLIT, extract_parser58_leftovers
from .parser103 import _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID
from .parser119 import _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND
from .parser247 import _FR_NOMINATIVE_SHARE_SPLIT
from .parser249 import _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED
from .parser462 import _FR_COMPLEMENTED_SHARE_SPLIT

_RESTRICTED_SPLIT = re.compile(
    r"Division des (?P<from_count>[\d']+) actions de CHF "
    r"(?P<from_nominal>[\d'.]+), nominatives, liées selon statuts, en "
    r"(?P<to_count>[\d']+) actions de CHF (?P<to_nominal>[\d'.]+)\. "
    r"Capital-actions: CHF (?P<total>[\d'.]+), libéré à concurrence de CHF "
    r"(?P<paid>[\d'.]+), divisé en (?P=to_count) actions de CHF "
    r"(?P=to_nominal), nominatives, liées selon statuts\.?"
)


def extract_parser519_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested restricted, partially paid registered share split."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_SHARE_SPLIT, _FR_COMPLEMENTED_SHARE_SPLIT,
        _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID,
        _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND,
        _FR_NOMINATIVE_SHARE_SPLIT, _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED,
    )):
        return [], text
    match = _RESTRICTED_SPLIT.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        values = {key: Decimal(value.replace("'", ''))
                  for key, value in match.groupdict().items()}
    except InvalidOperation:
        return [], text
    if not (0 < values['from_count'] < values['to_count']
            and values['to_nominal'] > 0
            and values['from_count'] * values['from_nominal']
            == values['to_count'] * values['to_nominal'] == values['total']
            and 0 <= values['paid'] <= values['total']):
        return [], text
    canonical = (
        f"Division des {match['from_count']} actions de CHF {match['from_nominal']}, "
        f"nominatives, en {match['to_count']} actions de CHF {match['to_nominal']}, "
        f"nominatives. Capital-actions: CHF {match['total']}, libéré à concurrence "
        f"de CHF {match['paid']}, divisé en {match['to_count']} actions de CHF "
        f"{match['to_nominal']}, nominatives"
    )
    events, rest = extract_parser58_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 1 or rest:
        return [], text
    events[0].rule_id = 'fr.text.restricted_registered_share_split.v1'
    events[0].payload['transfer_restricted'] = True
    return events, ''
