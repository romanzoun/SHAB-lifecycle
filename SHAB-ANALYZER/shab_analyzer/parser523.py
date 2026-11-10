from __future__ import annotations

import re

from .parser224 import _FR_DELEGATED_ADMINISTRATOR_NOW_PROXY
from .parser253 import _person_event

_FOUNDATION_MEMBER_NOW_PROXY = re.compile(
    r"(?P<name>[^,;.\[\]\n]+), jusqu'ici "
    r"(?P<previous_role>membre du conseil de fondation), "
    r"signe désormais par procuration collective à deux; "
    r"ses pouvoirs sont modifiés en ce sens\.?"
)


def extract_parser523_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Read the attested former foundation member's collective proxy."""
    if language != 'fr' or _FR_DELEGATED_ADMINISTRATOR_NOW_PROXY.fullmatch(text.strip()):
        return [], text
    match = _FOUNDATION_MEMBER_NOW_PROXY.fullmatch(text.strip())
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'signing_authority_changed', 'fr.persons.foundation_member_now_proxy.v1',
        match['name'], signing='Kollektivprokura zu zweien', extra={
            'action': 'role_and_signing_changed',
            'previous_role': match['previous_role'], 'powers_modified': True,
        },
    )], ''
