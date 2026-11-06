from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE

# The Zeitablaufs formulation remains owned by parser297. Its pattern is
# local to that extractor; this expression deliberately accepts only Fristablaufs.
_AUTHORIZED_PARTICIPATION_EXPIRED = re.compile(
    rf'\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom '
    rf'(?P<decision_date>{DATE}) eingeführte genehmigte Erhöhung des '
    r'Partizipationskapitals infolge Fristablaufs\.\] '
    r'\[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P=decision_date) '
    r'eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer '
    r'Umschreibung in den Statuten beschlossen\.\](?:\. |\.?$)'
)


def extract_parser498_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume the attested expiry clause and preserve subsequent clauses."""
    if language != 'de':
        return [], text
    match = _AUTHORIZED_PARTICIPATION_EXPIRED.match(text)
    if not match:
        return [], text
    try:
        datetime.strptime(match['decision_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.authorized_participation_capital_expired_fristablauf.v1',
        {'action': 'authorized_capital_expired', 'decision_date': match['decision_date']},
    )], text[match.end():]
