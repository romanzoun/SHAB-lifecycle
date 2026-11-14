from __future__ import annotations

import re
from datetime import datetime

from .parser247 import _DE_AUTHORIZED_CAPITAL_EXHAUSTED
from .parser253 import _event
from .parser267 import DATE

_CREATED_WITH_PREVIOUS_EXHAUSTION = re.compile(
    rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) '
    r'genehmigtes Aktienkapital gemäss näherer Umschreibung in den Statuten geschaffen\. '
    r'\[bisher: \[(?P<previous_clause>Streichung der Statutenbestimmung über die mit '
    rf'Ermächtigungsbeschluss vom {DATE} eingeführte genehmigte Kapitalerhöhung '
    r'infolge Ausschöpfung des Erhöhungsbetrages\.)\]'
)


def extract_parser548_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the attested nested historical note without treating it as current removal."""
    if language != 'de' or _DE_AUTHORIZED_CAPITAL_EXHAUSTED.fullmatch(text.strip()):
        return [], text
    match = _CREATED_WITH_PREVIOUS_EXHAUSTION.fullmatch(text.strip())
    if not match:
        return [], text
    previous = _DE_AUTHORIZED_CAPITAL_EXHAUSTED.fullmatch(match['previous_clause'])
    if not previous:
        return [], text
    try:
        datetime.strptime(match['decision_date'], '%d.%m.%Y')
        authorization_date = datetime.strptime(previous['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton, 'capital_changed',
        'de.text.authorized_share_capital_created_previous_exhaustion.v1',
        {'action': 'authorized_share_capital_created_statutes',
         'decision_date': match['decision_date'],
         'previous_clause': {'kind': 'authorized_capital_clause',
                             'action': 'removed_after_exhaustion',
                             'authorization_date': authorization_date,
                             'reason': 'increase_amount_exhausted'}},
    )], ''
