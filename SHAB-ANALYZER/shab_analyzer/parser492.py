from __future__ import annotations

import re

from .parser63 import _FR_PRESIDENCY_CHANGED_PAIR
from .parser90 import _FR_PRESIDENCY_CHANGED_OLD_FIRST
from .parser102 import _FR_PRESIDENCY_CHANGED_ADMINISTRATORS
from .parser253 import _person_event

_FR_MANAGER_PRESIDENCY_CHANGED = re.compile(
    r"Gérants: (?P<old_president>[^,.;\r\n]+), jusqu'ici présidente, et "
    r"(?P<new_president>[^,.;\r\n]+), nommé président, lesquels continuent de "
    r"signer collectivement à deux\.?"
)


def extract_parser492_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Record a manager presidency change with explicitly continued signing."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_PRESIDENCY_CHANGED_PAIR, _FR_PRESIDENCY_CHANGED_OLD_FIRST,
        _FR_PRESIDENCY_CHANGED_ADMINISTRATORS,
    )):
        return [], text
    match = _FR_MANAGER_PRESIDENCY_CHANGED.fullmatch(text)
    if not match:
        return [], text
    rule = 'fr.persons.manager_presidency_changed_collective.v1'
    events = []
    for name, role, extra in (
        (match['old_president'], 'gérante', {'action': 'presidency_ended', 'previous_role': 'présidente'}),
        (match['new_president'], 'gérant président', {'action': 'appointed_president'}),
    ):
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            'officer_changed', rule, name, role=role,
            signing='Kollektivunterschrift zu zweien', extra=extra,
        ))
    return events, ''
