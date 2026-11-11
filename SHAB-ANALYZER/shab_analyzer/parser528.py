from __future__ import annotations

import re

from .parser253 import _person_event
from .parser83 import _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_PAIR
from .parser128 import _FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE
from .parser216 import _FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE as _DE_ET_A_PAIR

# The shared origin and residence apply to both explicitly named members.
_NAME = r'[^,;.\[\]\n]+?'
_MEMBERS = re.compile(
    rf'(?<!\S)Nouveaux membres du conseil de fondation sans signature: '
    rf'(?P<name1>{_NAME}) et (?P<name2>{_NAME}), '
    rf'toutes deux de et à (?P<place>{_NAME})(?:\.(?=\s|$)|$)'
)


def extract_parser528_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Extract the attested pair with a shared origin and residence."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE_PAIR,
        _FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE, _DE_ET_A_PAIR,
    )):
        return [], text
    match = _MEMBERS.search(text)
    if not match:
        return [], text
    events = [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.foundation_pair_shared_origin_residence.v1',
        match[f'name{i}'], place=match['place'],
        role='membre du conseil de fondation',
        signing='ohne Zeichnungsberechtigung', extra={'heimat': match['place'], 'action': 'appointed',
               'without_signature': True},
    ) for i in (1, 2)]
    return events, (text[:match.start()] + text[match.end():]).strip()
