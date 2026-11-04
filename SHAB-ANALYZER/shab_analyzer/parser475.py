from __future__ import annotations

import re

from .parser249 import _DE_PERSON_SIGNING_CHANGED
from .parser61 import _DE_PERSON_ROLE_AND_SIGNING_CHANGED
from .parser253 import _person_event

_DIRECTOR_FROM_PROCURATION = re.compile(
    r'Eingetragene Person geändert: (?P<name>[^,.;]+), '
    r'(?P<previous_signing>Kollektivprokura zu zweien), neu '
    r'(?P<role>Direktor), (?P<signing>Kollektivunterschrift zu zweien)\.?'
)


def extract_parser475_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the complete procuration-to-director change from the supplied fixture."""
    if language != 'de' or any(pattern.search(text) for pattern in (
        _DE_PERSON_SIGNING_CHANGED, _DE_PERSON_ROLE_AND_SIGNING_CHANGED,
    )):
        return [], text
    match = _DIRECTOR_FROM_PROCURATION.fullmatch(text)
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'de.persons.director_from_joint_procuration.v1', match['name'],
        role=match['role'], signing=match['signing'],
        extra={'action': 'changed', 'previous_signing': match['previous_signing']},
    )], ''
