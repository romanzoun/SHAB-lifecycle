from __future__ import annotations

import re

from .parser253 import _event
from .parser50 import _FR_SHARE_RESTRICTION_WITH_CAPITAL
from .parser54 import _FR_SHARE_CAPITAL_STRUCTURE
from .parser114 import _FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE

_LEGACY = (_FR_SHARE_RESTRICTION_WITH_CAPITAL, _FR_SHARE_CAPITAL_STRUCTURE,
           _FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE)
_STRUCTURE = re.compile(
    r"Les actions nominatives sont désormais \. Capital-actions: CHF (?P<total>\d+(?:'\d{3})*), "
    r"libéré à concurrence de CHF (?P<paid>\d+(?:'\d{3})*), divisé en (?P<count>\d+(?:'\d{3})*) "
    r"actions de CHF (?P<nominal>\d+(?:'\d{3})*), nominatives, liées selon statuts\.?"
)


def extract_parser472_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Add the capital structure after the existing restriction rule has run."""
    if language != 'fr' or any(pattern.search(text) for pattern in _LEGACY):
        return [], text
    match = _STRUCTURE.fullmatch(text)
    if not match:
        return [], text
    # The blank clause alone is not evidence of a transfer restriction.
    original = text.replace('sont désormais .', 'sont désormais liées selon statuts.', 1)
    if original.rstrip('.') not in source_text:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'fr.text.registered_share_capital_after_restriction.v1',
        {'kind': 'share_structure', 'currency': 'CHF', 'capital_total': match['total'],
         'paid': match['paid'], 'paid_in_full': match['paid'] == match['total'],
         'shares_count': int(match['count'].replace("'", '')), 'nominal': match['nominal'],
         'share_kind': 'actions nominatives'},
    )], ''
