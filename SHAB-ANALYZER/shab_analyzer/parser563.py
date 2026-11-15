from __future__ import annotations

import re

from .parser253 import _event
from .text_extras import _FR_SEAT_BECAME

_SEAT_NOW = re.compile(
    r"^Le siège est maintenant (?P<to>[A-Za-zÀ-ÖØ-öø-ÿ]+"
    r"(?:[ '’\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*(?: \([A-Z]{2}\))?)(?:\.(?=\s|$)|$)"
)


def extract_parser563_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read an explicit current seat without inferring a transfer or its cause."""
    if language != 'fr' or _FR_SEAT_BECAME.search(text):
        return [], text
    match = _SEAT_NOW.match(text.strip())
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton, 'seat_changed',
        'fr.text.seat_now.v1', {'to': match['to']},
    )], text.strip()[match.end():].strip()
