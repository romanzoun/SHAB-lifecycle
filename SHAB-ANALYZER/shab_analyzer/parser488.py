from __future__ import annotations

import re
from datetime import datetime

from .parser93 import _FR_ASSET_TRANSFER_UID_BEFORE_PLACE
from .parser253 import _event
from .parser267 import COUNT, DATE, MONEY, NAME, UID

_FR_BUILDING_RIGHT_TRANSFER = re.compile(
    rf'Transfert de patrimoine: selon contrat du (?P<date>{DATE}), '
    r'la société a transféré le droit de superficie distinct et permanent '
    rf'DDP (?P<right_number>{COUNT}) de la commune de (?P<municipality>{NAME}) '
    rf'à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), '
    rf'à (?P<recipient_place>{NAME}) \((?P<recipient_canton>[A-Z]{{2}})\)\. '
    rf'Contre-prestation: CHF (?P<consideration>{MONEY})\.?'
)


def extract_parser488_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize the attested building right transfer without claiming asset totals."""
    if language != 'fr' or _FR_ASSET_TRANSFER_UID_BEFORE_PLACE.search(text):
        return [], text
    match = _FR_BUILDING_RIGHT_TRANSFER.fullmatch(text)
    if not match:
        return [], text
    try:
        date = datetime.strptime(match['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload = {
        **match.groupdict(), 'date': date, 'currency': 'CHF',
        'consideration': 'CHF ' + match['consideration'],
        'asset_kind': 'distinct_permanent_building_right',
    }
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'assets_transferred', 'fr.text.building_right_transfer.v1', payload)], ''
