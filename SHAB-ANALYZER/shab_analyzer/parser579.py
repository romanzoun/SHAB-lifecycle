from __future__ import annotations

import re

from .parser181 import _DE_COMPANY_DURATION_CHANGED, _event

_DURATION = re.compile(r'Dauer der Gesellschaft neu:\s*maximal Ende (?P<year>\d{4})\.?', re.I)


def extract_parser579_leftovers(text, language, publication_id, published_at,
                                org_uid, plz, canton):
    if language != 'de' or _DE_COMPANY_DURATION_CHANGED.fullmatch(text.strip()):
        return [], text
    match = _DURATION.fullmatch(text.strip())
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.company_duration_maximum_end_year.v1',
        {'kind': 'company_duration', 'action': 'changed',
         'until_year': int(match['year']), 'maximum_end_of_year': True},
    )], ''
