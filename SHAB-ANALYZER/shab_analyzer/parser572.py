from __future__ import annotations

import re
from datetime import datetime, date

from .parser239 import (
    _DE_DEFINITIVE_MORATORIUM_EXTENSION_GRANTED,
    _DE_DEFINITIVE_MORATORIUM_EXTENDED,
)
from .parser253 import _event
from .parser267 import DATE

_EXTENSION = re.compile(
    rf'Mit Entscheid des (?P<authority>[^,;.\n]+) vom (?P<decision_date>{DATE}) '
    r'hat der Einzelrichter im summarischen Verfahren eine Verlängerung der '
    r'definitiven Nachlassstundung für die Dauer von sechs Monaten bis zum '
    r'(?P<day>\d{1,2})\. Oktober (?P<year>\d{4}) gewährt\.?'
)


def extract_parser572_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the attested court extension without inferring a start date."""
    if language != 'de':
        return [], text
    clause = text.strip()
    if any(pattern.fullmatch(clause) for pattern in (
        _DE_DEFINITIVE_MORATORIUM_EXTENSION_GRANTED,
        _DE_DEFINITIVE_MORATORIUM_EXTENDED,
    )):
        return [], text
    match = _EXTENSION.fullmatch(clause)
    if not match:
        return [], text
    try:
        decision = datetime.strptime(match['decision_date'], '%d.%m.%Y').date()
        until = date(int(match['year']), 10, int(match['day']))
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'de.text.definitive_moratorium_extension_summary_judge.v1',
        {'kind': 'composition_moratorium_extended', 'action': 'extended',
         'moratorium_type': 'definitive', 'decision_date': decision.isoformat(),
         'duration_months': 6, 'until': until.isoformat(),
         'authority': match['authority']},
    )], ''
