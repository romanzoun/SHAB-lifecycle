from __future__ import annotations

import re

from .parser129 import _DE_BUSINESS_OFFICE_ADDED, extract_parser129_leftovers


_OFFICE = re.compile(
    r'^Weitere Geschäftsstelle \((?P<office_kind>Jugendherberge)\): '
    r'(?P<office_name>[^,;.\[\]\n]+), (?P<street>[^,;.\[\]\n]+), '
    r'(?P<postal_code>\d{4}) (?P<locality>[^,;.\[\]\n]+?)\.?$'
)


def extract_parser541_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Additional named youth-hostel business office, with the established address payload."""
    if language != 'de' or _DE_BUSINESS_OFFICE_ADDED.search(text.strip()):
        return [], text
    match = _OFFICE.fullmatch(text.strip())
    if not match:
        return [], text
    events, rest = extract_parser129_leftovers(
        f"Geschäftsstelle: {match['street']}, {match['postal_code']} {match['locality']}",
        language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 1 or rest:
        return [], text
    events[0].rule_id = 'de.text.additional_youth_hostel_business_office_added.v1'
    events[0].payload.update(office_kind=match['office_kind'], office_name=match['office_name'])
    return events, ''
