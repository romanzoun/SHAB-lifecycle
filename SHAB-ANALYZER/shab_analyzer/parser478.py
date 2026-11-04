from __future__ import annotations

import re

from .parser253 import _event
from .parser65 import _DE_PREVIOUS_BRANCH_REGISTER
from .parser85 import _DE_LEGACY_PREVIOUS_BRANCH
from .text_extras import (
    _DE_BRANCH_ADDED, _DE_BRANCH_ADDED_CONTINUATION,
    _DE_BRANCH_SEAT_CHANGED, _DE_BRANCH_SIMPLE_SEAT_CHANGED,
)

_PREVIOUS_PLACE = re.compile(r'\[bisher: (?P<place>[^\[\](),;:.]+)\]\.?')
LEGACY = (_DE_PREVIOUS_BRANCH_REGISTER, _DE_LEGACY_PREVIOUS_BRANCH,
          _DE_BRANCH_SEAT_CHANGED, _DE_BRANCH_SIMPLE_SEAT_CHANGED)


def extract_parser478_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Preserve a previous branch place after the existing branch additions."""
    if language != 'de' or any(pattern.search(text) for pattern in LEGACY):
        return [], text
    match = _PREVIOUS_PLACE.fullmatch(text)
    if not match or any(pattern.search(source_text) for pattern in LEGACY):
        return [], text
    # Require the exact branch continuation context, not an isolated historic place.
    first = _DE_BRANCH_ADDED.search(source_text)
    continuation = _DE_BRANCH_ADDED_CONTINUATION.match(source_text[first.end():]) if first else None
    if not continuation:
        return [], text
    suffix = source_text[first.end() + continuation.end():].strip()
    if suffix.rstrip('.') != text.rstrip('.'):
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'branch_changed', 'de.text.previous_branch_place_reference.v1',
        {'action': 'previous_branch_reference', 'previous_place': match['place'].strip()},
    )], ''
