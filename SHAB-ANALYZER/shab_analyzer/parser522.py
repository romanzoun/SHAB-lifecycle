from __future__ import annotations

import re
from datetime import datetime

from .parser110 import _IT_DEFINITIVE_MORATORIUM_EXTENDED
from .parser146 import _IT_COMPOSITION_MORATORIUM_EXTENDED
from .parser253 import _event
from .parser267 import DATE

_LEGACY = (_IT_DEFINITIVE_MORATORIUM_EXTENDED,
           _IT_COMPOSITION_MORATORIUM_EXTENDED)
_PROVISIONAL_EXTENSION = re.compile(
    rf'Con decisione del (?P<decision_date>{DATE}), la '
    r'(?P<authority>Pretura del Distretto di [^,;.\[\]\n]+) '
    r'ha concesso la proroga della moratoria provvisoria a scopo di '
    r'concordato di (?P<duration_months>[1-9]\d*) mesi a partire dal '
    rf'(?P<effective_date>{DATE})\.?'
)


def extract_parser522_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the attested provisional composition moratorium extension."""
    if language != 'it' or any(p.fullmatch(text.strip()) for p in _LEGACY):
        return [], text
    match = _PROVISIONAL_EXTENSION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y')
                 for key in ('decision_date', 'effective_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'it.text.provisional_composition_moratorium_extended.v1',
        {'kind': 'composition_moratorium_extended', 'moratorium_type': 'provisional',
         'authority': match['authority'],
         'duration_months': int(match['duration_months']),
         **{key: value.date().isoformat() for key, value in dates.items()}},
    )], ''
