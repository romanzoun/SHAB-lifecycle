from __future__ import annotations

import re

from .parser120 import (
    _FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED,
    _person_event,
)
from .parser134 import _FR_NEW_LIMITED_PARTNER_WITH_PROCURATION
from .parser251 import _FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED as _OLD_COMBINED


# Only the attested standalone organization appointment with a colon after 'de'.
_FR_ORGANIZATION_LIMITED_PARTNER = re.compile(
    r"^Nouvelle associée commanditaire\s*:\s*(?P<name>[^,;()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*avec une commandite de:\s*CHF\s+"
    r"(?P<contribution>\d{1,3}(?:'\d{3})*|\d+)\.?$",
    re.I | re.UNICODE,
)


def extract_parser534_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    if language != 'fr':
        return [], text
    if any(pattern.search(text.strip()) for pattern in (
        _FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED,
        _FR_NEW_LIMITED_PARTNER_WITH_PROCURATION, _OLD_COMBINED,
    )):
        return [], text
    match = _FR_ORGANIZATION_LIMITED_PARTNER.fullmatch(text.strip())
    if not match or int(match['contribution'].replace("'", '')) <= 0:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'officer_changed', 'fr.persons.organization_limited_partner_colon.v1',
        match['name'], place=match['place'], uid=match['uid'],
        role='associée commanditaire', extra={
            'action': 'appointed', 'uid': match['uid'],
            'limited_partnership_contribution': match['contribution'],
            'currency': 'CHF',
        },
    )], ''
