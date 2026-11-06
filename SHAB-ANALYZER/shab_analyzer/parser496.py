from __future__ import annotations

import re
from datetime import datetime

from .parser78 import _FR_CANTONAL_COURT_BANKRUPTCY_SUSPENDED
from .parser195 import _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_ORDINAL_DATE
from .parser253 import _event

_FR_CANTONAL_BANKRUPTCY_SUSPENDED_NUMERIC_DATE = re.compile(
    r"(?P<authority>Le président de la Cour des poursuites et faillites du Tribunal cantonal) "
    r"a prononcé l'effet suspensif de la procédure de faillite le "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?"
)


def extract_parser496_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested cantonal bankruptcy suspension with numeric date."""
    if language != 'fr' or any(pattern.fullmatch(text) for pattern in (
        _FR_CANTONAL_COURT_BANKRUPTCY_SUSPENDED,
        _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED_ORDINAL_DATE,
    )):
        return [], text
    match = _FR_CANTONAL_BANKRUPTCY_SUSPENDED_NUMERIC_DATE.fullmatch(text)
    if not match:
        return [], text
    try:
        date = datetime.strptime(match['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'fr.text.cantonal_bankruptcy_suspended_numeric_date.v1',
        {'kind': 'bankruptcy_effect_suspended', 'action': 'suspended',
         'date': date, 'authority': match['authority']},
    )], ''
