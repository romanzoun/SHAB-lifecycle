from __future__ import annotations

import re

from .parser110 import (
    _IT_COMPANY_TRANSLATIONS_REMOVED,
    extract_parser110_leftovers,
)


_IT_DITTA_TRANSLATIONS_REMOVED = re.compile(
    r"Traduzioni della ditta:\s*\[Le traduzioni saranno radiate dal Registro di commercio\]\.?"
)


def extract_parser539_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Handle the attested ditta heading with parser110's established payload."""
    if language != 'it' or _IT_COMPANY_TRANSLATIONS_REMOVED.search(text.strip()):
        return [], text
    if not _IT_DITTA_TRANSLATIONS_REMOVED.fullmatch(text.strip()):
        return [], text
    normalized = text.strip().replace(
        'Traduzioni della ditta:', 'Nuove traduzioni della ragione sociale:', 1,
    )
    events, rest = extract_parser110_leftovers(
        normalized, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 1 or rest:
        return [], text
    events[0].rule_id = 'it.text.ditta_translations_removed.v1'
    return events, ''
