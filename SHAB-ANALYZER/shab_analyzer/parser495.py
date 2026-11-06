from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser74 import _FR_ASSOCIATE_ORGANIZATION_NAME_CORRECTED
from .parser77 import _FR_ASSOCIATE_NAME_CORRECTION_AND_MANAGER_SIGNING
from .parser120 import _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED
from .parser253 import _person_event
from .parser267 import COUNT, DATE, MONEY, NAME, UID

_LEGACY = (_FR_ASSOCIATE_ORGANIZATION_NAME_CORRECTED,
           _FR_ASSOCIATE_NAME_CORRECTION_AND_MANAGER_SIGNING,
           _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED)
_FR_ASSOCIATE_AND_MANAGER_CORRECTED = re.compile(
    rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) "
    rf'est rectifiée en ce sens que l\'associée de la société est "(?P<name>[^"\r\n]+)" '
    rf"\((?P<uid>{UID})\), à (?P<place>{NAME}), avec (?P<count>{COUNT}) "
    rf"parts sociales de CHF (?P<nominal>{MONEY}), et que (?P<manager>{NAME}) est gérant\.?"
)


def extract_parser495_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete the corporate associate and manager correction after signing extraction."""
    if language != 'fr' or any(p.search(text) for p in _LEGACY):
        return [], text
    match = _FR_ASSOCIATE_AND_MANAGER_CORRECTED.fullmatch(text)
    if not match:
        return [], text
    # The signing clause was already consumed; require its attested source wording.
    source_clause = text.rstrip('.') + ' avec signature individuelle.'
    if source_clause not in source_text:
        return [], text
    try:
        entry_date = datetime.strptime(match['entry_date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    count = int(match['count'].replace("'", ''))
    if count <= 0 or Decimal(match['nominal'].replace("'", '')) <= 0:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    common = {'action': 'corrected', 'entry': match['entry'], 'entry_date': entry_date}
    rule = 'fr.persons.corporate_associate_and_manager_corrected.v1'
    return [
        _person_event(*context, 'officer_changed', rule, match['name'],
                      role='associée', place=match['place'], extra={
                          **common, 'uid': match['uid'], 'shares_count': count,
                          'shares_nominal': match['nominal'], 'currency': 'CHF'}),
        _person_event(*context, 'officer_changed', rule, match['manager'],
                      role='gérant', signing='Einzelunterschrift', extra=common),
    ], ''
