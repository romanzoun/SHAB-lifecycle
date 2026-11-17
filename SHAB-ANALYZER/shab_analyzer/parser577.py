from __future__ import annotations

import re
from datetime import datetime

from .parser117 import _IT_MERGER_FULLY_OWNED
from .parser253 import _event
from .parser267 import DATE, MONEY, NAME, UID

_NOTICE = re.compile(
    rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>[^,;()]+), '
    rf'in (?P<absorbed_place>[^,;()]+) \((?P<absorbed_uid>{UID})\), '
    rf'secondo il contratto di fusione del (?P<agreement_date>{DATE}) '
    rf'e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF '
    rf'(?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. '
    r'La società assuntrice detiene tutte le azioni della società trasferente, '
    r'per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni\.?'
)


def extract_parser577_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Handle the attested dotted-name subsidiary merger, preserving old ownership."""
    if language != 'it' or _IT_MERGER_FULLY_OWNED.search(text.strip()):
        return [], text
    match = _NOTICE.fullmatch(text.strip())
    if not match:
        return [], text
    # Parser382 already owns this wording for names supported by its NAME pattern.
    if all(re.fullmatch(NAME, match[key]) for key in ('absorbed_name', 'absorbed_place')):
        return [], text
    payload = match.groupdict()
    try:
        for key in ('agreement_date', 'balance_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload.update(kind='absorption', currency='CHF', all_shares_held_by_acquirer=True,
                   capital_increase=False, share_allocation=False)
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'company_merged', 'it.text.merger_fully_owned_dotted_name.v1', payload)], ''
