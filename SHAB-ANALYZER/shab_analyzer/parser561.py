from __future__ import annotations

import re

from .parser142 import _FR_HOLDER_NAME_CORRECTED_NOTICE
from .parser173 import _FR_ROLE_HOLDER_NAME_CORRECTED, _FR_NOTICE_ROLE_HOLDER_NAME_CORRECTED
from .parser223 import _FR_HOLDER_NAME_CORRECTED
from .parser253 import _person_event

_LEGACY = (_FR_HOLDER_NAME_CORRECTED_NOTICE, _FR_ROLE_HOLDER_NAME_CORRECTED,
           _FR_NOTICE_ROLE_HOLDER_NAME_CORRECTED, _FR_HOLDER_NAME_CORRECTED)
_SECOND_NAME = re.compile(
    r'Le second prénom du titulaire, (?P<previous_name>[^,.;\n]+), '
    r'est (?P<second_given_name>[^,.;\n]+)\.?'
)


def extract_parser561_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Record the explicitly supplied second given name of a holder."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in _LEGACY):
        return [], text
    match = _SECOND_NAME.fullmatch(text.strip())
    if not match:
        return [], text
    previous = match['previous_name'].strip()
    second = match['second_given_name'].strip()
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.holder_second_given_name.v1', f'{previous} {second}',
        role='titulaire', extra={'action': 'name_corrected',
                                'previous_name': previous, 'second_given_name': second},
    )], ''
