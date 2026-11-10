from __future__ import annotations

import re

from .parser267 import UID
from .parser401 import extract_parser401_leftovers

_BRANCH_IDENTIFIER_AFTER_MOVE = re.compile(
    r"Le numéro d'identification (?P<previous_registry_id>CH-\d{3}-\d{7}-\d) "
    r"de la succursale à (?P<place>[^,;.\[\]\n]+), qui a transféré son siège à "
    r"(?P<new_place>[^,;.\[\]\n]+), est remplacé par le numéro "
    rf"d'identification des entreprises \(IDE/UID\) (?P<branch_uid>{UID})\.?"
)


def extract_parser520_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested branch identifier replacement after relocation."""
    if language != 'fr':
        return [], text
    match = _BRANCH_IDENTIFIER_AFTER_MOVE.fullmatch(text.strip())
    if not match:
        return [], text
    canonical = (
        f"L'identification de la succursale de {match['place']} sous le numéro "
        f"{match['previous_registry_id']} est remplacée par le numéro "
        f"d'identification des entreprises (IDE/UID) {match['branch_uid']}"
    )
    events, rest = extract_parser401_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 1 or rest:
        return [], text
    events[0].rule_id = 'fr.text.branch_registry_id_replaced_by_uid_after_move.v1'
    events[0].payload['new_place'] = match['new_place']
    return events, ''
