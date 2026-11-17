from __future__ import annotations

import re
from datetime import datetime

from .parser112 import _FR_SIGNING_CORRECTED_WITH_NOTICE
from .parser253 import _person_event

_CORRECTION = re.compile(
    r"Rectificatif: l'inscription no (?P<entry>\d+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) p\. (?P<notice_ref>\d+/\d+)\) "
    r"est rectifiée en ce sens que (?P<name>[^,;.()\n]+) "
    r"signe collectivement à deux \(et non individuellement comme publié\)\.?"
)


def extract_parser573_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Handle the attested 'no' correction with an unpunctuated FOSC date."""
    if language != 'fr':
        return [], text
    clause = text.strip()
    if _FR_SIGNING_CORRECTED_WITH_NOTICE.search(clause):
        return [], text
    match = _CORRECTION.fullmatch(clause)
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('entry_date', 'notice_date')}
    except ValueError:
        return [], text
    return [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        'signing_authority_changed', 'fr.persons.signing_corrected_no_notice.v1',
        match['name'], signing='Kollektivunterschrift zu zweien',
        extra={'action': 'signing_corrected', 'previous_signing': 'Einzelunterschrift',
               'entry': match['entry'], **dates, 'notice_ref': match['notice_ref']},
    )], ''
