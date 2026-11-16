from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE

_SUSPENSION_REVOKED = re.compile(
    rf"Par décision du (?P<decision_date>{DATE}), le "
    r"(?P<authority>Président du Tribunal civil de [^,;.\n]+, à [^,;.\n]+), "
    r"a révoqué la suspension de la procédure de faillite faute d'actif "
    rf"prononcé le (?P<previous_decision_date>{DATE})\.?"
)


def extract_parser567_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the attested revocation of a lack-of-assets suspension."""
    if language != 'fr':
        return [], text
    match = _SUSPENSION_REVOKED.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('decision_date', 'previous_decision_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'fr.text.bankruptcy_suspension_revoked.v1',
        {'kind': 'bankruptcy', 'action': 'suspension_revoked',
         **dates, 'authority': match['authority'],
         'previous_action': 'suspended_for_lack_of_assets'},
    )], ''
