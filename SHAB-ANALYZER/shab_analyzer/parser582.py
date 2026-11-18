from __future__ import annotations

import re

from .parser129 import _FR_NEW_LIMITED_PARTNER_WITH_PROXY
from .parser253 import _person_event

_NEW_LIMITED_PARTNER = re.compile(
    r"^Nouvel associé commanditaire:\s*(?P<name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"avec une commandite de CHF\s+(?P<contribution>\d{1,3}(?:'\d{3})*|\d+),\s*"
    r"lequel n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)


def extract_parser582_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'fr' or _FR_NEW_LIMITED_PARTNER_WITH_PROXY.search(text.strip()):
        return [], text
    match = _NEW_LIMITED_PARTNER.fullmatch(text.strip())
    if not match or int(match['contribution'].replace("'", '')) <= 0:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.new_limited_partner_without_signing.v1',
        match['name'], place=match['place'], role='associé commanditaire',
        signing='ohne Zeichnungsberechtigung', extra={
            'action': 'appointed', 'new_partner': True,
            'heimat': match['origin'].strip(),
            'limited_partnership_contribution': match['contribution'], 'currency': 'CHF',
        },
    )], ''
