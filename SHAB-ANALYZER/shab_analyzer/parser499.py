from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE
from .parser165 import _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_MISSING_DATE

_CONDITIONAL_PARTICIPATION_CHANGED = re.compile(
    rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) '
    rf'die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte '
    r'Bestimmung betreffend bedingter Erhöhung des Partizipationskapitals '
    r'gemäss näherer Umschreibung in den Statuten geändert\. '
    r'\[bisher: Die Gesellschaft hat mit Beschluss vom (?P=introduction_date) '
    r'eine bedingte Erhöhung des Partizipationskapitals gemäss näherer '
    r'Umschreibung in den Statuten beschlossen\.\](?:\. |\.?$)'
)


def extract_parser499_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume the attested amendment and retain subsequent resolutions."""
    if language != 'de':
        return [], text
    # Keep the historical missing-date formulation with its original owner.
    if _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_MISSING_DATE.fullmatch(text.strip()):
        return [], text
    match = _CONDITIONAL_PARTICIPATION_CHANGED.match(text)
    if not match:
        return [], text
    try:
        for value in match.groupdict().values():
            datetime.strptime(value, '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'de.text.conditional_participation_capital_clause_changed.v1',
        {'action': 'modified', 'kind': 'conditional_participation_capital_clause',
         'details_in_statutes': True, **match.groupdict()},
    )], text[match.end():]
