from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .parser60 import _FR_SHARE_TRANSFER_RESTRICTION
from .parser103 import _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID, extract_parser103_leftovers
from .parser119 import _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND
from .parser247 import _FR_NOMINATIVE_SHARE_SPLIT
from .parser249 import _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED


_FR_SPLIT_NEW_RESTRICTIONS = re.compile(
    r"Division des (?P<from_count>[\d']+) actions de CHF "
    r"(?P<from_nominal>[\d'.]+), nominatives, en "
    r"(?P<to_count>[\d']+) actions de CHF (?P<to_nominal>[\d'.]+), "
    r"nominatives, lesquelles sont désormais \. Capital-actions: CHF "
    r"(?P<total>[\d'.]+), entièrement libéré, divisé en "
    r"(?P=to_count) actions de CHF (?P=to_nominal), nominatives,\s*\.?"
)
_LEGACY_PATTERNS = (
    _FR_SHARE_TRANSFER_RESTRICTION,
    _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID,
    _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND,
    _FR_NOMINATIVE_SHARE_SPLIT,
    _FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED,
)


def extract_parser457_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete the evidenced split after the existing restriction extractor."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in _LEGACY_PATTERNS):
        return [], text
    match = _FR_SPLIT_NEW_RESTRICTIONS.fullmatch(text.strip())
    if not match:
        return [], text
    source_clause = (
        f"Division des {match['from_count']} actions de CHF {match['from_nominal']}, "
        f"nominatives, en {match['to_count']} actions de CHF {match['to_nominal']}, "
        "nominatives, lesquelles sont désormais liées selon statuts."
    )
    if source_clause not in source_text:
        return [], text
    amount = lambda value: Decimal(value.replace("'", ''))
    try:
        valid = (amount(match['from_count']) < amount(match['to_count'])
            and amount(match['to_nominal']) > 0
            and amount(match['from_count']) * amount(match['from_nominal'])
            == amount(match['to_count']) * amount(match['to_nominal'])
            == amount(match['total']))
    except InvalidOperation:
        return [], text
    if not valid:
        return [], text
    canonical = (
        f"Division des {match['from_count']} actions de CHF {match['from_nominal']}, "
        f"nominatives, en {match['to_count']} actions de CHF {match['to_nominal']}. "
        f"Capital-actions: CHF {match['total']}, entièrement libéré, divisé en "
        f"{match['to_count']} actions de CHF {match['to_nominal']}, nominatives, liées selon statuts"
    )
    events, rest = extract_parser103_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 1 or rest:
        return [], text
    events[0].rule_id = 'fr.text.registered_share_split_new_restrictions.v1'
    return events, ''


def needs_legacy_restriction_pass(text, language):
    if language != 'fr':
        return False
    match = _FR_SHARE_TRANSFER_RESTRICTION.search(text)
    return bool(match and _FR_SPLIT_NEW_RESTRICTIONS.fullmatch(
        (text[:match.start()] + text[match.end():]).strip()))
