from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .parser155 import (
    _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY,
    extract_parser155_leftovers,
)
from .parser267 import MONEY


# Retain the established transfer structure; only the consideration differs.
_TRANSFER = re.compile(
    _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.pattern.split(r'Gegenleistung:')[0]
    + rf'Als Gegenleistung setzt die (?P=recipient) den Nennwert des durch die '
      rf'Gesellschaft gehaltenen Stammanteils von CHF (?P<nominal_before>{MONEY}) '
      rf'um CHF (?P<nominal_increase>{MONEY}) auf CHF (?P<nominal_after>{MONEY}) herauf\.?$'
)


def extract_parser540_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Asset transfer compensated by increasing a held share's nominal value."""
    if language != 'de' or _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.search(text.strip()):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('agreement_date', 'inventory_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
        amounts = {key: Decimal(match[key].replace("'", '')) for key in (
            'assets', 'liabilities', 'nominal_before', 'nominal_increase', 'nominal_after')}
        if any(value < 0 for value in amounts.values()):
            return [], text
        if amounts['nominal_before'] <= 0 or amounts['nominal_increase'] <= 0:
            return [], text
        if amounts['nominal_before'] + amounts['nominal_increase'] != amounts['nominal_after']:
            return [], text
    except (ValueError, InvalidOperation):
        return [], text
    prefix = match[0].split('Als Gegenleistung setzt die ', 1)[0]
    events, rest = extract_parser155_leftovers(
        prefix + 'Gegenleistung: CHF ' + match['nominal_increase'],
        language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 1 or rest:
        return [], text
    event = events[0]
    event.rule_id = 'de.text.asset_transfer_held_share_nominal_increase.v1'
    event.payload.update(
        consideration_kind='held_share_nominal_increase',
        **{key: match[key] for key in ('nominal_before', 'nominal_increase', 'nominal_after')},
    )
    return events, ''
