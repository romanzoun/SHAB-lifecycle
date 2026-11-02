from __future__ import annotations

import re
from datetime import datetime

from .parser97 import _DE_BANKRUPTCY_COMPANY_REINSTATED, extract_parser97_leftovers
from .parser101 import _DE_BANKRUPTCY_COMPANY_REINSTATED_WITH_HISTORY
from .parser102 import _DE_BANKRUPTCY_COMPANY_REINSTATED_DATE_ONLY
from .parser213 import _DE_BANKRUPTCY_COMPANY_REINSTATED_AND_PROCEEDINGS_REOPENED
from .parser224 import _DE_BANKRUPTCY_COMPANY_REINSTATED_SOURCE_TYPO

_LEGACY = (
    _DE_BANKRUPTCY_COMPANY_REINSTATED,
    _DE_BANKRUPTCY_COMPANY_REINSTATED_WITH_HISTORY,
    _DE_BANKRUPTCY_COMPANY_REINSTATED_DATE_ONLY,
    _DE_BANKRUPTCY_COMPANY_REINSTATED_AND_PROCEEDINGS_REOPENED,
    _DE_BANKRUPTCY_COMPANY_REINSTATED_SOURCE_TYPO,
)
_DE_REINSTATED_FORMER_LAW = re.compile(
    r'Diese Gesellschaft, welche am (?P<deleted_date>\d{2}\.\d{2}\.\d{4}) '
    r'infolge Konkurses im Sinne von (?P<legal_basis>Art\. 159 aHRegV) gelöscht wurde, '
    r'wird gemäss Entscheid des (?P<authority>Einzelrichters am Kantonsgericht) vom '
    r'(?P<decision_date>\d{2}\.\d{2}\.\d{4}) wieder als durch Konkurs aufgelöst '
    r'in das Handelsregister eingetragen\. Datum der Konkurseröffung: '
    r'(?P<day>\d{1,2})\. April (?P<year>\d{4}), '
    r'(?P<bankruptcy_time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr\.?'
)


def extract_parser463_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'de' or any(pattern.search(text.strip()) for pattern in _LEGACY):
        return [], text
    match = _DE_REINSTATED_FORMER_LAW.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('deleted_date', 'decision_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
        opening = datetime(int(match['year']), 4, int(match['day'])).strftime('%d.%m.%Y')
    except ValueError:
        return [], text
    canonical = (
        f"Diese Gesellschaft, welche am {match['deleted_date']} infolge Konkurses im Sinne "
        f"von Art. 159 HRegV gelöscht wurde, wird gemäss Entscheid des {match['authority']} "
        f"vom {match['decision_date']} wieder als durch Konkurs aufgelöst in das Handelsregister "
        f"eingetragen. Datum der Konkurseröffnung: {opening}, {match['bankruptcy_time']} Uhr"
    )
    events, rest = extract_parser97_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 1 or rest.strip(' .'):
        return [], text
    events[0].rule_id = 'de.text.bankruptcy_company_reinstated_former_law.v1'
    events[0].payload['legal_basis'] = match['legal_basis']
    events[0].payload['source_typo'] = 'Konkurseröffung'
    return events, ''
