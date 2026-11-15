from __future__ import annotations

import re

from .parser57 import _FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE
from .parser58 import _FR_ADMINISTRATION_PAIR
from .parser253 import _person_event

_LEGACY = (_FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE, _FR_ADMINISTRATION_PAIR)
_POWERS = re.compile(r'les pouvoirs de (?P<name>[^,.;\n]+) sont modifiés en ce sens\.?')


def extract_parser562_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete an explicit powers change following a legacy board pair clause."""
    if language != 'fr' or any(pattern.search(text) for pattern in _LEGACY):
        return [], text
    match = _POWERS.fullmatch(text.strip())
    if not match:
        return [], text
    # Require the attested president/secretary clause and its own powers suffix.
    # The pair itself belongs to the legacy rule, including in isolation tests.
    evidence = _FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE.search(source_text)
    if (not evidence or evidence['name1'].strip() != match['name'].strip()
            or evidence['role1'].strip() != 'président'
            or evidence['role2'].strip() != 'secrétaire'
            or evidence['sign'] != 'individuellement'
            or not re.match(r';\s*' + re.escape(match[0].rstrip('.'))
                            + r'\.(?:\s|$)', source_text[evidence.end():])):
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton, 'officer_changed',
        'fr.persons.board_pair_president_powers_modified.v1', match['name'],
        role='Präsident des Verwaltungsrates', signing='Einzelunterschrift',
        extra={'action': 'signing_changed', 'powers_modified': True},
    )], ''
