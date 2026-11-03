from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event
from .parser267 import DATE, MONEY, NAME, UID


_COMPANY_ASSETS_TWO_CONTRACT_DATES = re.compile(
    rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom '
    rf'(?P<agreement_date1>{DATE})/(?P<agreement_date2>{DATE}) Aktiven von CHF '
    rf'(?P<assets>{MONEY}) an die (?P<recipient>{NAME}), in (?P<place>{NAME}) '
    rf'\((?P<recipient_uid>{UID})\)\. Gegenleistung: keine\.?'
)


def extract_parser468_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume the evidenced assets-only transfer with two contract dates."""
    if language != 'de':
        return [], text
    match = _COMPANY_ASSETS_TWO_CONTRACT_DATES.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('agreement_date1', 'agreement_date2'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    if Decimal(match['assets'].replace("'", '')) <= 0:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.company_assets_two_contract_dates_no_consideration.v1',
        {'action': 'company_assets_two_contract_dates_no_consideration',
         **match.groupdict(), 'currency': 'CHF', 'consideration': 'keine'},
    )], ''
