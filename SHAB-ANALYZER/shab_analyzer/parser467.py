from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event
from .parser267 import DATE, MONEY, NAME


_VEHICLE_CONTRIBUTION = re.compile(
    rf'Die Kommanditsumme von (?P<amount>{MONEY}) des Kommanditärs '
    rf'(?P<name>{NAME}) wird durch eine Sacheinlage, '
    rf'(?P<asset>Personenwagen [^,;\n]+), 1\. Inverkehrssetzung '
    rf'(?P<first_registration_date>{DATE}), geleistet\.?'
)


def extract_parser467_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse the evidenced limited partner vehicle contribution clause only."""
    if language != 'de':
        return [], text
    match = _VEHICLE_CONTRIBUTION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['first_registration_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    if Decimal(match['amount'].replace("'", '')) <= 0:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.limited_partner_vehicle_contribution.v1',
        {'action': 'contribution_in_kind', **match.groupdict()},
    )], ''
