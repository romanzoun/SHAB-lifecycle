from __future__ import annotations

import re
from datetime import datetime

from .parser131 import _DE_DEFINITIVE_MORATORIUM_EXTENDED
from .parser253 import _event
from .parser267 import DATE

_DE_EXTENSION_WITH_INCLUSIVE_END = re.compile(
    rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das '
    r'(?P<court>Gerichtspräsidium [^,.;]+) die gewährte definitive '
    r'Nachlassstundung um (?P<months>\d+) Monate, bis und mit '
    rf'(?P<until_date>{DATE}), verlängert\.?'
)


def extract_parser486_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the supplied extension with an explicit inclusive end date."""
    if language != 'de' or _DE_DEFINITIVE_MORATORIUM_EXTENDED.search(text):
        return [], text
    match = _DE_EXTENSION_WITH_INCLUSIVE_END.fullmatch(text)
    if not match:
        return [], text
    try:
        decision = datetime.strptime(match['decision_date'], '%d.%m.%Y').date()
        until = datetime.strptime(match['until_date'], '%d.%m.%Y').date()
        months = int(match['months'])
    except ValueError:
        return [], text
    if months <= 0 or until < decision:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'de.text.definitive_moratorium_extended_inclusive_end.v1',
        {'kind': 'composition_moratorium', 'action': 'extended', 'definitive': True,
         'decision_date': decision.isoformat(), 'court': match['court'],
         'extension_months': months, 'until_date': until.isoformat()},
    )], ''
