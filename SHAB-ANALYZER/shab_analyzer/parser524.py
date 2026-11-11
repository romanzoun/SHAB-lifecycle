from __future__ import annotations

import re
from datetime import datetime

from .parser90 import _DE_STATUTES_DATE_ENTERED_INCORRECTLY
from .parser161 import _DE_ERRONEOUS_STATUTES_DATE
from .parser253 import _event
from .parser267 import COUNT, DATE

_ERRONEOUS_STATUTES_DATE_ENTRY = re.compile(
    rf'Beim Tagesregistereintrag (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) '
    rf'wurde irrtümlich das Statutendatum (?P<erroneous_date>{DATE}) eingetragen\.?'
)


def extract_parser524_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Note an erroneous statutes date without inferring a replacement date."""
    if language != 'de' or any(pattern.fullmatch(text.strip()) for pattern in (
        _DE_STATUTES_DATE_ENTERED_INCORRECTLY, _DE_ERRONEOUS_STATUTES_DATE,
    )):
        return [], text
    match = _ERRONEOUS_STATUTES_DATE_ENTRY.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('entry_date', 'erroneous_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'publication_corrected', 'de.text.erroneous_statutes_date_register_entry.v1',
        {'kind': 'statutes_date', 'action': 'erroneous_entry_noted',
         'entry': match['entry'], **dates},
    )], ''
