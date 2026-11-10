from __future__ import annotations

import re
from datetime import datetime

from .parser61 import _DE_PERSON_ROLE_AND_SIGNING_CHANGED
from .parser165 import _DE_DISSOLUTION_PERSON_AND_ADDRESS
from .parser253 import _event, _person_event
from .parser267 import DATE

_DISSOLUTION = re.compile(
    rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom '
    rf'(?P<decision_date>{DATE}) aufgelöst\. Neue Firma: '
    r'(?P<liquidation_name>[^,;.\n]+ in Liquidation)\. '
    r'Eingetragene Person geändert: (?P<name>[^,;.\n]+), '
    r'Gesellschafter, Geschäftsführer, Einzelunterschrift, neu '
    r'Gesellschafter, Geschäftsführer, Liquidator, Einzelunterschrift\.?'
)


def extract_parser515_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested dissolution without share counts or an address."""
    if language != 'de' or any(pattern.search(text.strip()) for pattern in (
        _DE_PERSON_ROLE_AND_SIGNING_CHANGED, _DE_DISSOLUTION_PERSON_AND_ADDRESS,
    )):
        return [], text
    match = _DISSOLUTION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['decision_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'de.text.dissolution_new_name_associate_manager_liquidator.v1'
    return [
        _event(*context, 'status_changed', rule, {
            'action': 'dissolution_new_name_associate_manager_liquidator',
            'decision_date': match['decision_date'], 'dissolved': True,
        }),
        _event(*context, 'company_name_changed', rule, {
            'action': 'liquidation_name', 'liquidation_name': match['liquidation_name'],
        }),
        _person_event(*context, 'officer_changed', rule, match['name'],
                      role='Gesellschafter, Geschäftsführer, Liquidator',
                      signing='Einzelunterschrift'),
    ], ''
