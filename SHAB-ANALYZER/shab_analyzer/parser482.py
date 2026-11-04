from __future__ import annotations

import re
from datetime import datetime

from .parser89 import _FR_BANKRUPTCY_RESTITUTION_REFUSED
from .parser253 import _event
from .parser267 import DATE

_FR_RESTITUTION_REJECTED_BANKRUPTCY_CONFIRMED = re.compile(
    rf'Par décision du (?P<decision_date>{DATE}), '
    r'(?P<court>le Président du Tribunal de l\'arrondissement de La Côte) '
    r'a rejeté la requête en restitution de délai, confirmé le prononcé de '
    r'faillite de la société et dit que celui-ci prend effet le '
    rf'(?P<effective_date>{DATE})\.?'
)


def extract_parser482_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested confirmation without inferring a time or revocation."""
    if language != 'fr' or _FR_BANKRUPTCY_RESTITUTION_REFUSED.fullmatch(text):
        return [], text
    match = _FR_RESTITUTION_REJECTED_BANKRUPTCY_CONFIRMED.fullmatch(text)
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('decision_date', 'effective_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'fr.text.bankruptcy_restitution_rejected_confirmed.v1',
        {'kind': 'bankruptcy', 'action': 'restitution_rejected_bankruptcy_confirmed',
         'restitution_request': 'rejected', 'court': match['court'], **dates},
    )], ''
