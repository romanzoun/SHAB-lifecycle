from __future__ import annotations

import re

from .parser82 import _FR_ADMINISTRATION_THREE_POWERS_CHANGED
from .parser119 import _FR_BOARD_THREE_WITH_CHANGED_SIGNING
from .parser253 import _person_event

_BOARD = re.compile(
    r"Administration: (?P<name1>[^,.;\n]+), nommé président, "
    r"(?P<name2>[^,.;\n]+), jusqu'ici président, et (?P<name3>[^,.;\n]+), "
    r"lesquels signent collectivement à deux; les pouvoirs des deux derniers "
    r"sont modifiés en ce sens\.?"
)


def extract_parser554_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the evidenced presidency change and last-two signing change."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_ADMINISTRATION_THREE_POWERS_CHANGED, _FR_BOARD_THREE_WITH_CHANGED_SIGNING,
    )):
        return [], text
    match = _BOARD.fullmatch(text.strip())
    if not match:
        return [], text
    events = []
    for i in (1, 2, 3):
        extra = {'action': 'role_changed' if i < 3 else 'signing_changed'}
        if i == 2:
            extra['previous_role'] = 'administrateur président'
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            'officer_changed', 'fr.persons.board_presidency_last_two_signing_changed.v1',
            match[f'name{i}'],
            role='administrateur président' if i == 1 else "membre du conseil d'administration",
            signing='Kollektivunterschrift zu zweien', extra=extra,
        ))
    return events, ''
