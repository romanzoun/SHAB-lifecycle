from __future__ import annotations

import re
from datetime import datetime

from .parser190 import _FR_INTENDED_ASSET_ACQUISITION_COMPLETED_SINGLE_DATE
from .parser253 import _event

_FR_PROPERTY_AND_MORTGAGE_ACQUISITION_COMPLETED = re.compile(
    r"La reprise de biens envisagée à la constitution relative aux "
    r"(?P<assets>biens immobiliers et aux dettes hypothécaires rattachées aux immeubles) "
    r"a été réalisée par contrat du (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) "
    r"pour le prix de CHF (?P<price>\d{1,3}(?:'\d{3})*|\d+)\.?"
)


def extract_parser494_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Record completion of the planned property and mortgage acquisition."""
    if language != 'fr' or _FR_INTENDED_ASSET_ACQUISITION_COMPLETED_SINGLE_DATE.fullmatch(text):
        return [], text
    match = _FR_PROPERTY_AND_MORTGAGE_ACQUISITION_COMPLETED.fullmatch(text)
    if not match:
        return [], text
    try:
        datetime.strptime(match['agreement_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'ownership_changed', 'fr.text.planned_property_acquisition_completed.v1',
        {'action': 'planned_property_acquisition_completed',
         **match.groupdict(), 'currency': 'CHF'},
    )], ''
