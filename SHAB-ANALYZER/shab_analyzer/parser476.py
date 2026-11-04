from __future__ import annotations

import re

from .parser253 import _person_event
from .parser273 import extract_parser273_leftovers

_VICE_PRESIDENT_CONTINUED_SIGNING = re.compile(
    r'(?P<name>[^,.;]+(?: [A-Z]\.)?), nommé vice-président, '
    r'continue à signer collectivement à deux\.?'
)


def extract_parser476_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract the evidenced vice-president appointment with continued signing."""
    if language != 'fr':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    # The related administrator rule is defined inline in parser273.
    old_events, old_rest = extract_parser273_leftovers(text, language, *context, source_text=source_text)
    if old_events or old_rest != text:
        return [], text
    match = _VICE_PRESIDENT_CONTINUED_SIGNING.fullmatch(text)
    if not match:
        return [], text
    return [_person_event(
        *context, 'officer_changed', 'fr.persons.vice_president_continued_signing.v1',
        match['name'], role='vice-président', signing='Kollektivunterschrift zu zweien',
        extra={'signing_continued': True},
    )], ''
