from __future__ import annotations

import re

from .parser253 import _person_event
from .parser63 import _DE_MIXED_PERSON_CHANGES
from .parser68 import _DE_PERSON_REPLACEMENT_SINGULAR
from .parser95 import _DE_MIXED_PERSON_REPLACEMENT

_REPLACEMENT = re.compile(
    r"Gelöschte Person: (?P<removed>[^,.;]+), Stiftungsratsmitglied, ohne Unterschrift\. "
    r"Neu eingetragene Person: (?P<added>[^,.;]+), von und in (?P<place>[^,.;]+), "
    r"Stiftungsratsmitglied, ohne Unterschrift\.?"
)


def extract_parser473_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the complete unsigned foundation board replacement only."""
    if language not in ('de', 'fr'):
        return [], text
    if any(pattern.search(text) for pattern in (_DE_MIXED_PERSON_CHANGES, _DE_PERSON_REPLACEMENT_SINGULAR, _DE_MIXED_PERSON_REPLACEMENT)):
        return [], text
    match = _REPLACEMENT.fullmatch(text)
    if not match:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'de.persons.unsigned_foundation_board_replacement.v1'
    return [
        _person_event(*context, 'officer_removed', rule, match['removed'],
                      role='Stiftungsratsmitglied', signing='ohne Unterschrift',
                      extra={'action': 'removed'}),
        _person_event(*context, 'officer_changed', rule, match['added'], place=match['place'],
                      role='Stiftungsratsmitglied', signing='ohne Unterschrift',
                      extra={'action': 'appointed', 'heimat': match['place']}),
    ], ''
