from __future__ import annotations

import re
from datetime import datetime

from .parser155 import (
    _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY,
    extract_parser155_leftovers,
)

# Only the evidenced first UID separator differs from parser155's clause.
_DE_COMPANY_ASSET_TRANSFER_APOSTROPHE_UID = re.compile(
    _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.pattern.replace(
        r'CHE-\d{3}\.\d{3}\.\d{3}', r"CHE-\d{3}'\d{3}\.\d{3}"
    ),
    _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.flags,
)


def extract_parser453_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle the evidenced UID punctuation variant without claiming legacy input."""
    if language != 'de' or _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.search(text.strip()):
        return [], text
    match = _DE_COMPANY_ASSET_TRANSFER_APOSTROPHE_UID.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for key in ('agreement_date', 'inventory_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    raw_uid = match['uid']
    start, end = match.span('uid')
    canonical = match[0][:start] + raw_uid.replace("'", '.') + match[0][end:]
    events, rest = extract_parser155_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if not events or rest:
        return [], text
    for event in events:
        event.rule_id = 'de.text.company_asset_transfer_inventory_apostrophe_uid.v1'
        event.payload = {**event.payload, 'recipient_uid_raw': raw_uid}
    return events, ''
