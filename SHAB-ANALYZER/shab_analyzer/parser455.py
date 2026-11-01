from __future__ import annotations

import re

from .parser50 import _FR_ADMINISTRATION_PAIR, extract_parser50_leftovers


_FR_ADMINISTRATION_PAIR_SHARED_ORIGIN_RESIDENCE = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommée présidente,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?"
)


def extract_parser455_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Resolve the evidenced shared origin/residence variant using legacy payloads."""
    if language != 'fr' or _FR_ADMINISTRATION_PAIR.search(text):
        return [], text
    match = _FR_ADMINISTRATION_PAIR_SHARED_ORIGIN_RESIDENCE.fullmatch(text.strip())
    if not match or any(' et ' in match[key] for key in ('name1', 'name2')):
        return [], text
    place = match['place']
    canonical = (f"Administration: {match['name1']}, nommée présidente, et "
                 f"{match['name2']}, de {place}, à {place}, "
                 "lesquels signent individuellement")
    events, rest = extract_parser50_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 4 or rest:
        return [], text
    # The shared place includes its article; parser50's origin preposition
    # alternative would otherwise absorb "La" from "de La ...".
    for event in events:
        if 'heimat' in event.payload:
            event.payload = {**event.payload, 'heimat': place}
        event.rule_id = event.rule_id.replace('administration_pair', 'administration_pair_shared_origin_residence')
    return events, ''
