from __future__ import annotations

import re
from datetime import datetime

from .parser220 import _DE_BANKRUPTCY_COMPANY_REINSTATED_AFTER_REOPENING
from .parser253 import _event
from .parser267 import DATE

_REINSTATED = re.compile(
    r'Diese im Sinne von (?P<legal_basis>Art\. 159 Abs\. 5 HRegV) am '
    rf'(?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft '
    r'wird aufgrund des Entscheids des (?P<authority>[^,;.\n]+) vom '
    rf'(?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\.?'
)


def extract_parser570_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read court-ordered reinstatement without inferring bankruptcy reopening."""
    if language != 'de' or _DE_BANKRUPTCY_COMPANY_REINSTATED_AFTER_REOPENING.fullmatch(text.strip()):
        return [], text
    match = _REINSTATED.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('deletion_date', 'decision_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'de.text.court_decision_official_deletion_reinstated.v1',
        {'action': 'reinstatement', 'legal_basis': match['legal_basis'],
         'authority': match['authority'], **dates},
    )], ''
