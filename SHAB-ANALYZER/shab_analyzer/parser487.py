from __future__ import annotations

import re
from datetime import datetime

from .parser130 import _FR_REPUDIATED_ESTATE_BANKRUPTCY
from .parser253 import _event
from .parser267 import DATE
from .text_extras import _FR_REPUDIATED_ESTATE_LIQUIDATION

_FR_ESTATE_LIQUIDATION_ASSIGNMENT = re.compile(
    rf'Par décision du (?P<date>{DATE}), le '
    r"(?P<authority>Président du Tribunal d'arrondissement de [^,.;]+), "
    r"à (?P<place>[^,.;]+), a chargé l'Office des faillites de procéder "
    r'à la liquidation de la succession répudiée du titulaire\.?'
)


def extract_parser487_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested bankruptcy office assignment, preserving legacy ownership."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_REPUDIATED_ESTATE_BANKRUPTCY, _FR_REPUDIATED_ESTATE_LIQUIDATION,
    )):
        return [], text
    match = _FR_ESTATE_LIQUIDATION_ASSIGNMENT.fullmatch(text)
    if not match:
        return [], text
    try:
        decision_date = datetime.strptime(match['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'fr.text.repudiated_estate_liquidation_assignment.v1',
        {'kind': 'repudiated_estate_liquidation_ordered', 'procedure': 'bankruptcy_office',
         'decision_date': decision_date, 'authority': match['authority'] + ', à ' + match['place'],
         'scope': 'owner_estate'},
    )], ''
