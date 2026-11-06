from __future__ import annotations

import re
from datetime import datetime

from .parser177 import _IT_MERGER_ALL_QUOTAS
from .parser224 import _IT_MERGER_ALL_INTERESTS_OWNED
from .parser236 import _IT_MERGER_ACQUIRER_OWNS_ALL_QUOTAS
from .parser253 import _event
from .parser267 import DATE, MONEY, UID

LEGACY = (_IT_MERGER_ALL_QUOTAS, _IT_MERGER_ALL_INTERESTS_OWNED,
          _IT_MERGER_ACQUIRER_OWNS_ALL_QUOTAS)
_ALL_QUOTAS_DEL_CAPITALE = re.compile(
    rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>[^,;()]+), '
    rf'in (?P<absorbed_place>[^,;()]+) \((?P<absorbed_uid>{UID})\), '
    rf'secondo il contratto di fusione del (?P<agreement_date>{DATE}) '
    rf'e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF '
    rf'(?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. '
    r'La società assuntrice detiene tutte le quote della società trasferente, '
    r'per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni\.?'
)


def extract_parser497_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only the attested quota merger with del capitale wording."""
    if language != 'it' or any(pattern.search(text) for pattern in LEGACY):
        return [], text
    match = _ALL_QUOTAS_DEL_CAPITALE.fullmatch(text)
    if not match:
        return [], text
    payload = match.groupdict()
    try:
        for key in ('agreement_date', 'balance_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload.update(currency='CHF', ownership_interests='quote',
                   all_interests_held_by_acquirer=True, capital_increase=False,
                   shares_allocated=False)
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'company_merged', 'it.text.merger_all_quotas_no_capital_increase.v1',
                   payload)], ''
