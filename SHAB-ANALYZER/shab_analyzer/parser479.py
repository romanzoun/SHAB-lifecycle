from __future__ import annotations

import re

from .parser253 import _event
from .parser267 import UID

_IDENTIFIER_REPLACED = re.compile(
    r"L'identification sous le numéro (?P<previous_registry_id>CH-\d{3}-\d{7}-\d) "
    r"est remplacée par le numéro d'identification des entreprises \(IDE/UID\) "
    rf"(?P<uid>{UID})\.?"
)


def extract_parser479_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the organization's own registry identifier replacement only."""
    if language != 'fr':
        return [], text
    match = _IDENTIFIER_REPLACED.fullmatch(text)
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'company_identifier_changed', 'fr.text.registry_id_replaced_by_uid.v1',
        {'scope': 'organization', 'from': match['previous_registry_id'], 'to': match['uid']},
    )], ''
