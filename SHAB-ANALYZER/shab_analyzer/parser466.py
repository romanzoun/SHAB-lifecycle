from __future__ import annotations

import re
from datetime import datetime

from .parser87 import (
    _FR_ASSOCIATE_MANAGER_NAME_CORRECTION,
    extract_parser87_leftovers,
)
from .parser267 import COUNT, DATE
from .parser288 import extract_parser288_leftovers


# The combined correction is distinct from the standalone correction in 87.
_COMBINED = re.compile(
    rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) "
    rf"est rectifiée en ce sens que les statuts sont datés du (?P<statutes_date>{DATE}) "
    rf"\(et non du (?P<previous_statutes_date>{DATE})\) et "
    r"l'associé-gérant se nomme (?P<name>[^(),.;\n]+) "
    r"\(et non (?P<previous_name>[^(),.;\n]+)\)\.?"
)


def extract_parser466_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle the evidenced joint statutes-date and associate-manager correction."""
    if language != 'fr' or _FR_ASSOCIATE_MANAGER_NAME_CORRECTION.search(text.strip()):
        return [], text
    match = _COMBINED.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('entry_date', 'statutes_date', 'previous_statutes_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    prefix = (
        f"L'inscription no {match['entry']} du {match['entry_date']} "
        "est rectifiée en ce sens que "
    )
    statutes = (
        prefix + f"les nouveaux statuts sont datés du {match['statutes_date']} "
        f"(et non du: {match['previous_statutes_date']})"
    )
    person = (
        prefix + f"l'associé-gérant se nomme {match['name']} "
        f"(et non {match['previous_name']})"
    )
    context = language, publication_id, published_at, org_uid, plz, canton
    statutes_events, statutes_rest = extract_parser288_leftovers(statutes, *context)
    person_events, person_rest = extract_parser87_leftovers(person, *context)
    if len(statutes_events) != 1 or len(person_events) != 1 or statutes_rest or person_rest:
        return [], text
    events = statutes_events + person_events
    for event in events:
        event.rule_id = 'fr.text.statutes_date_and_associate_manager_name_corrected.v1'
    return events, ''
