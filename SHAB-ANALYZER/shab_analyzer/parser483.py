from __future__ import annotations

import re

from .parser253 import _event
from .parser267 import UID

_DE_EXISTING_BRANCHES_REGISTRATION_REQUIREMENTS = re.compile(
    r'\[bisher: (?P<previous_place1>[^\[\]\n]+)\]\. '
    r'\[gestrichen: (?P<struck_place>[^\[\]\n]+)\]\. '
    rf'(?P<place>[^,.;\[\]\n]+) \((?P<branch_uid>{UID})\) '
    r'\[bisher: (?P<previous_place2>[^\[\]\n]+)\]\. '
    r'\[Anpassung bei den bestehenden Zweigniederlassungen aufgrund '
    r'geänderter Eintragungsvorschriften\]\.?'
)


def extract_parser483_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Record the attested registration adjustment, without inferring branch closures."""
    if language != 'de':
        return [], text
    match = _DE_EXISTING_BRANCHES_REGISTRATION_REQUIREMENTS.fullmatch(text)
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.existing_branches_registration_requirements.v1',
        {'action': 'existing_branches_registration_requirements_adjustment', **match.groupdict()},
    )], ''
