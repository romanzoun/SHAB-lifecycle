from __future__ import annotations

import re
from datetime import datetime

from .parser120 import _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED
from .parser253 import _person_event
from .parser267 import COUNT, DATE, MONEY, NAME, UID

_FR_ASSOCIATE_ORGANIZATION_CORRECTED_TYPO = re.compile(
    rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) "
    rf"\(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) "
    rf"est rectitiée en ce sens qu'une associée est (?P<name>{NAME}) \((?P<uid>{UID})\), "
    rf"à (?P<place>{NAME}), avec (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), "
    rf"et non (?P<previous_name>{NAME}) \((?P<previous_uid>{UID})\), "
    rf"à (?P<previous_place>{NAME}), comme publié\.?"
)


def extract_parser491_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Capture the attested corporate associate correction, including its typo."""
    if language != 'fr' or _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED.search(text):
        return [], text
    match = _FR_ASSOCIATE_ORGANIZATION_CORRECTED_TYPO.fullmatch(text)
    if not match:
        return [], text
    payload = match.groupdict()
    try:
        for key in ('entry_date', 'notice_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    name, place = payload.pop('name'), payload.pop('place')
    payload.update(action='associate_corrected', correction=True, currency='CHF',
                   count=int(payload['count'].replace("'", '')), source_wording='rectitiée')
    return [_person_event(publication_id, published_at, org_uid, plz, canton,
                          'officer_changed', 'fr.persons.associate_organization_corrected_typo.v1',
                          name, place=place, role='associée', extra=payload)], ''
