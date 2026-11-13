from __future__ import annotations

import re

from .parser227 import _DE_INHERITANCE_COMMUNITY_MEMBERS
from .parser253 import _event


_TWO_HEIRS = re.compile(
    r'Die Erbengemeinschaft (?P<decedent>[^:;,.\n]+) besteht aus folgenden Erben: '
    r'(?P<name1>[^:;,.\n]+), von (?P<origin1>[^:;,.\n]+), in '
    r'(?P<place1>[^:;,.\n]+); '
    r'(?P<name2>[^:;,.\n]+), von (?P<origin2>[^:;,.\n]+), in '
    r'(?P<place2>[^:;,.\n]+)\.?'
)


def extract_parser546_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Record two explicitly listed heirs without inferring officer roles."""
    if language != 'de' or _DE_INHERITANCE_COMMUNITY_MEMBERS.fullmatch(text.strip()):
        return [], text
    match = _TWO_HEIRS.fullmatch(text.strip())
    if not match:
        return [], text
    members = [
        {key: match[f'{key}{i}'].strip() for key in ('name', 'origin', 'place')}
        for i in (1, 2)
    ]
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.inheritance_community_two_heirs.v1',
        {'kind': 'inheritance_community', 'action': 'members_recorded',
         'decedent': match['decedent'].strip(), 'members': members},
    )], ''
