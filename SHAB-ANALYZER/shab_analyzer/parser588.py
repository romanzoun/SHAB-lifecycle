from __future__ import annotations

import re

from .parser253 import _person_event
from .parser411 import extract_parser411_leftovers

_BOARD_PRESIDENCY = re.compile(
    r"Les administrateurs (?P<appointed>[^,;.\[\]\n]+), nommée présidente "
    r"et (?P<former>[^,;.\[\]\n]+), jusqu'ici président; "
    r"lesquels continuent à signer collectivement à deux\.?"
)


def extract_parser588_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Recognize the attested presidency change with continuing signatures."""
    if language != 'fr':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    if extract_parser411_leftovers(text, language, *context)[0]:
        return [], text
    match = _BOARD_PRESIDENCY.fullmatch(text.strip())
    if not match or match['appointed'] == match['former']:
        return [], text
    return [
        _person_event(*context, 'officer_changed',
                      'fr.persons.board_presidency_changed_continued_signing.v1',
                      match['appointed'], role='Präsident des Verwaltungsrates',
                      signing='Kollektivunterschrift zu zweien',
                      extra={'action': 'role_changed', 'signing_continues': True}),
        _person_event(*context, 'officer_changed',
                      'fr.persons.board_presidency_changed_continued_signing.v1',
                      match['former'], role='Mitglied des Verwaltungsrates',
                      signing='Kollektivunterschrift zu zweien',
                      extra={'action': 'role_changed', 'previous_role': 'président',
                             'signing_continues': True}),
    ], ''
