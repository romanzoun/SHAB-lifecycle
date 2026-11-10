from __future__ import annotations

import re

from .parser130 import _person_event

_NAME = r'[^,;.\[\]\n]+?'
_CORRECTION = re.compile(
    rf'(?<!\S)Le nom de famille exact du membre du conseil de fondation '
    rf'(?P<previous_name>{_NAME}) est (?P<name>{_NAME})(?:\.(?=\s|$)|$)'
)


def extract_parser517_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested standalone foundation member surname correction."""
    if language != 'fr':
        return [], text
    match = _CORRECTION.search(text)
    if not match:
        return [], text
    event = _person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.foundation_member_family_name_corrected.v1',
        match['name'], role='membre du conseil de fondation',
        extra={'action': 'family_name_corrected',
               'previous_name': match['previous_name'], 'corrected': True},
    )
    return [event], (text[:match.start()] + text[match.end():]).strip()
