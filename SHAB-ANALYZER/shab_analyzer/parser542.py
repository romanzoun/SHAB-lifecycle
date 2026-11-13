from __future__ import annotations

import re
from datetime import datetime

from .models import Event
from .parser74 import _IT_CONDITIONAL_CAPITAL_CLAUSE
from .text_extras import _IT_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED


# Reuse the established clause grammar, bounded by the attested change note
# and the removed historical clause. Standalone clauses retain their owner.
_CLAUSE = _IT_CONDITIONAL_CAPITAL_CLAUSE.pattern.removeprefix('^').removesuffix('$')
_NOMINAL_CHANGE = re.compile(
    r"\[Modifica dell'ammontare nominale del capitale condizionale\] "
    + _CLAUSE.replace('(?P<date>', '(?P<decision_date>')
    + r' \[radiati: '
    + _CLAUSE.replace('(?P<date>', '(?P<original_decision_date>')
    + r'\]\.?',
    _IT_CONDITIONAL_CAPITAL_CLAUSE.flags,
)


def extract_parser542_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Italian conditional-capital nominal change with removed clause history."""
    if (language != 'it'
            or _IT_CONDITIONAL_CAPITAL_CLAUSE.search(text.strip())
            or _IT_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED.search(text)):
        return [], text
    match = _NOMINAL_CHANGE.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(value, '%d.%m.%Y').date().isoformat()
                 for key, value in match.groupdict().items()}
    except ValueError:
        return [], text
    return [Event(
        publication_id=publication_id, published_at=published_at,
        org_uid=org_uid, plz=plz, canton=canton,
        event_type='capital_changed',
        rule_id='it.text.conditional_capital_nominal_amount_changed_history.v1',
        payload={
            'kind': 'conditional_capital_clause_modified', 'action': 'modified',
            **dates, 'details_in_statutes': True,
            'nominal_amount_changed': True, 'previous_entry_removed': True,
        },
    )], ''
