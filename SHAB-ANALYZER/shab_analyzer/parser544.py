from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser236 import _DE_DISSOLUTION_AND_NEW_COMPANY_NAME
from .parser267 import DATE


_DISSOLUTION = re.compile(
    rf'Die Gesellschaft ist laut Beschluss der Generalversammlung vom '
    rf'(?P<decision_date>{DATE}) aufgelöst\. Neue Firma: '
    r'(?P<company>[^();\n]+? in Liquidation) '
    r'\((?P<french_name>[^();\n]+ en liquidation)\) '
    r'\((?P<english_name>[^();\n]+ in liquidation)\)\.?'
)


def extract_parser544_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Dissolution with two fully spelled out liquidation name translations."""
    if language != 'de' or _DE_DISSOLUTION_AND_NEW_COMPANY_NAME.fullmatch(text.strip()):
        return [], text
    match = _DISSOLUTION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['decision_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    action = 'company_dissolved_translated_names'
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', f'de.text.{action}.v1',
        {'action': action, **match.groupdict(), 'in_liquidation': True},
    )], ''
