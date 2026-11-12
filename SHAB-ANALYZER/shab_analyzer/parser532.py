from __future__ import annotations

import re

from .parser376 import extract_parser376_leftovers
from .parser69 import (
    _DE_COMPANY_REINSTATED_FOR_LIQUIDATION,
    extract_parser69_leftovers,
)

# Reuse the established grammar and payload; only the joined spelling is new.
_REINSTATED = re.compile(
    _DE_COMPANY_REINSTATED_FOR_LIQUIDATION.pattern.replace('auf Grund', 'aufgrund'),
    _DE_COMPANY_REINSTATED_FOR_LIQUIDATION.flags,
)


def extract_parser532_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested joined spelling without taking older formulations."""
    if language != 'de' or '[' in text or _DE_COMPANY_REINSTATED_FOR_LIQUIDATION.search(text.strip()):
        return [], text
    if not _REINSTATED.fullmatch(text.strip()):
        return [], text
    # The joined judgment formulation already belongs to parser376, including
    # when that rule is disabled in the surrounding pipeline. Reuse its grammar
    # through the extractor rather than duplicating its locally defined pattern.
    if extract_parser376_leftovers(
        text, language, publication_id, published_at, org_uid, plz, canton,
        source_text=source_text,
    )[0]:
        return [], text
    normalized = re.sub(r'\baufgrund\b', 'auf Grund', text.strip(), count=1, flags=re.I)
    events, rest = extract_parser69_leftovers(
        normalized, language, publication_id, published_at, org_uid, plz, canton,
    )
    if not events or rest.strip(' .'):
        return [], text
    for event in events:
        event.rule_id = 'de.text.company_reinstated_for_liquidation_joined_spelling.v1'
    return events, ''
