from __future__ import annotations

import re

from .parser50 import _DE_FORMER_DOMICILE, extract_parser50_leftovers

# Keep the established address grammar and payload, extending only the preposition.
_FORMER_DOMICILE_AN = re.compile(
    _DE_FORMER_DOMICILE.pattern.replace('nicht mehr am', 'nicht mehr an'),
    _DE_FORMER_DOMICILE.flags,
)


def extract_parser533_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    if language != 'de' or _DE_FORMER_DOMICILE.search(text):
        return [], text
    if not _FORMER_DOMICILE_AN.fullmatch(text.strip()):
        return [], text
    normalized = re.sub(r'\bnicht mehr an\b', 'nicht mehr am', text.strip(),
                        count=1, flags=re.I)
    events, rest = extract_parser50_leftovers(
        normalized, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 1 or rest.strip(' .'):
        return [], text
    events[0].rule_id = 'de.text.domicile_removed_preposition_an.v1'
    return events, ''
