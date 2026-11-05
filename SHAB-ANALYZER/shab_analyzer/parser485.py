from __future__ import annotations

import re
from datetime import datetime

from .parser52 import _FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATES
from .parser150 import _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED
from .parser159 import _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY
from .parser253 import _event
from .parser267 import DATE

_LEGACY_PATTERNS = (
    _FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATES,
    _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED,
    _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY,
)
_FR_TWO_DECISIONS = re.compile(
    rf'Statuts modifiés les (?P<date1>{DATE}) et (?P<date2>{DATE})\. '
    r"L'assemblée générale a modifié une clause statutaire relative à une "
    r'augmentation conditionnelle du capital '
    rf'\(selon décision du (?P<original_date>{DATE})\) '
    r'par décisions des (?P=date1) et (?P=date2)\. '
    r'Pour les détails, voir les statuts\.?'
)


def extract_parser485_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested two-resolution clause, preserving legacy ownership."""
    if language != 'fr' or any(p.search(text) for p in _LEGACY_PATTERNS):
        return [], text
    match = _FR_TWO_DECISIONS.fullmatch(text)
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(value, '%d.%m.%Y').date().isoformat()
                 for key, value in match.groupdict().items()}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'fr.text.conditional_capital_clause_two_decisions.v1',
        {'kind': 'conditional_capital_clause_modified', 'action': 'modified',
         'original_decision_date': dates['original_date'],
         'decision_dates': [dates['date1'], dates['date2']],
         'statutes_dates': [dates['date1'], dates['date2']]},
    )], ''
