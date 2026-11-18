from __future__ import annotations

import re

from .parser253 import _person_event

_DIRECTOR = re.compile(
    r'(?P<name>[^,.;\n]+),\s*maintenant domicilié à (?P<place>[^,.;\n]+),\s*'
    r'nommé directeur,\s*signe désormais collectivement à deux,\s*'
    r'avec un administrateur;\s*sa procuration est radiée\.?'
)


def extract_parser583_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'fr':
        return [], text
    match = _DIRECTOR.fullmatch(text.strip())
    if not match:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.relocated_director_signing_proxy_revoked.v1',
        match['name'], place=match['place'], role='directeur',
        signing='Kollektivunterschrift zu zweien', extra={
            'action': 'appointed', 'signing_restriction': 'avec un administrateur',
            'procuration_revoked': True,
        },
    )], ''
