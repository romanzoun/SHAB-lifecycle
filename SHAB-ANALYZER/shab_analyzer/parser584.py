from __future__ import annotations

import re

from .parser239 import _FR_PROXY_CHANGES
from .parser253 import _person_event

_PROXY_WITH_PRESIDENT = re.compile(
    r'(?P<name>[^,.;\n\[\]]+?)\s+continue de signer par procuration '
    r'collectivement à deux,\s*mais désormais avec le président\.?'
)


def extract_parser584_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    leftover = text.strip()
    if language != 'fr' or _FR_PROXY_CHANGES.fullmatch(leftover):
        return [], text
    match = _PROXY_WITH_PRESIDENT.fullmatch(leftover)
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'signing_authority_changed', 'fr.persons.proxy_with_president.v1',
        match['name'], role='fondé de procuration',
        signing='Kollektivprokura zu zweien', extra={
            'action': 'signing_restriction_changed',
            'signing_restriction': 'avec le président',
            'signing_continues': True,
        },
    )], ''
