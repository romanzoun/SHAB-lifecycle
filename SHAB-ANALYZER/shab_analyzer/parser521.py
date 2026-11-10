from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE
from .parser108 import _DE_REMOVED_BRANCH_LEGACY_ID
from .parser118 import _DE_REMOVED_BRANCH_CANTON_REGISTER
from .parser143 import _DE_BRANCH_REMOVED_NESTED_LABEL

_LEGACY = (_DE_REMOVED_BRANCH_LEGACY_ID, _DE_REMOVED_BRANCH_CANTON_REGISTER,
           _DE_BRANCH_REMOVED_NESTED_LABEL)
_REMOVED = re.compile(
    r'Zweigniederlassung neu: \[gestrichen: (?P<place>[^()\[\];\n]+) '
    r'\((?P<branch_canton>[A-Z]{2})\) '
    rf'\(eingetragen seit (?P<registration_date>{DATE})\)\]\.?'
)


def extract_parser521_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the attested removed branch listing with its registration date."""
    if language != 'de' or any(p.fullmatch(text.strip()) for p in _LEGACY):
        return [], text
    match = _REMOVED.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['registration_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'branch_changed', 'de.text.branch_removed_with_registration_date.v1',
        {'action': 'removed', **match.groupdict()},
    )], ''
