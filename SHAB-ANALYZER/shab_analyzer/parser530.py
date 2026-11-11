from __future__ import annotations

import re

from .parser253 import _person_event
from .parser56 import _MIXED_DE_PERSON_SECTIONS
from .parser139 import _DE_MIXED_REMOVED_CHANGED_AND_ADDED_PERSONS

_NAME = r'[^,;.\[\]\n]+?'
_PERSON_BLOCK = re.compile(
    rf'Gelöschte Personen: (?P<removed1>{_NAME}), Verwaltungsratsmitglied, '
    rf'Kollektivunterschrift zu zweien; (?P<removed2>{_NAME}), '
    rf'Kollektivunterschrift zu zweien\. Eingetragene Personen geändert: '
    rf'(?P<changed1>{_NAME}), Verwaltungsratsmitglied, Präsident, Einzelunterschrift, '
    rf'neu Verwaltungsratsmitglied, Einzelunterschrift; (?P<changed2>{_NAME}), '
    rf'Kollektivunterschrift zu zweien, neu Einzelunterschrift\.?'
)


def extract_parser530_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Handle the attested mixed-language block without inferring missing roles."""
    if language not in ('fr', 'de') or any(pattern.search(text.strip()) for pattern in (
        _MIXED_DE_PERSON_SECTIONS, _DE_MIXED_REMOVED_CHANGED_AND_ADDED_PERSONS,
    )):
        return [], text
    match = _PERSON_BLOCK.fullmatch(text.strip())
    if not match:
        return [], text
    rule = 'de.persons.two_removed_two_changed_board_signing.v1'

    def person(group, event_type, role, signing, extra):
        return _person_event(
            publication_id, published_at, org_uid, plz, canton,
            event_type, rule, match[group], role=role, signing=signing, extra=extra,
        )

    return [
        person('removed1', 'officer_removed', 'Verwaltungsratsmitglied',
               'Kollektivunterschrift zu zweien', {'action': 'removed'}),
        person('removed2', 'officer_removed', None,
               'Kollektivunterschrift zu zweien', {'action': 'removed'}),
        person('changed1', 'officer_changed', 'Verwaltungsratsmitglied',
               'Einzelunterschrift', {'action': 'role_changed',
                'previous_role': 'Verwaltungsratsmitglied, Präsident',
                'previous_signing': 'Einzelunterschrift'}),
        person('changed2', 'officer_changed', None,
               'Einzelunterschrift', {'action': 'signing_changed',
                'previous_signing': 'Kollektivunterschrift zu zweien'}),
    ], ''
