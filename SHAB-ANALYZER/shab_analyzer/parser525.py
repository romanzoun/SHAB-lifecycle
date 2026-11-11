from __future__ import annotations

import re

from .parser253 import _person_event

_ADMINISTRATOR_NOW_MANAGEMENT_MEMBER = re.compile(
    r"(?P<name>[^,;.\[\]\n]+), jusqu'ici (?P<previous_role>administratrice), "
    r"maintenant (?P<role>membre de la direction), "
    r"continue à signer collectivement à deux\.?"
)


def extract_parser525_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Extract the attested administrator's role change with continued signing."""
    if language != 'fr':
        return [], text
    match = _ADMINISTRATOR_NOW_MANAGEMENT_MEMBER.fullmatch(text.strip())
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.administrator_now_management_member.v1',
        match['name'], role=match['role'], signing='Kollektivunterschrift zu zweien',
        extra={'previous_role': match['previous_role'], 'signing_continued': True},
    )], ''
