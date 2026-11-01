from __future__ import annotations

import re

from .parser50 import _FR_ADMINISTRATION_PAIR, extract_parser50_leftovers


_FR_ADMINISTRATION_SHARED_PLACE_COLLECTIVE = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"lesquels signent collectivement à deux;\s*"
    r"les pouvoirs du président sont modifiés en ce sens\.?"
)


def extract_parser456_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Resolve the evidenced collective-signing pair with legacy payloads."""
    if language != 'fr' or _FR_ADMINISTRATION_PAIR.search(text):
        return [], text
    match = _FR_ADMINISTRATION_SHARED_PLACE_COLLECTIVE.fullmatch(text.strip())
    if not match or any(' et ' in match[key] for key in ('name1', 'name2')):
        return [], text
    place = match['place']
    canonical = (f"Administration: {match['name1']}, nommé président, et "
                 f"{match['name2']}, de {place}, à {place}, "
                 "lesquels signent collectivement à deux")
    events, rest = extract_parser50_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 4 or rest:
        return [], text
    for event in events:
        if 'heimat' in event.payload:
            event.payload = {**event.payload, 'heimat': place}
        event.rule_id = event.rule_id.replace(
            'administration_pair', 'administration_pair_shared_place_collective')
    return events, ''
