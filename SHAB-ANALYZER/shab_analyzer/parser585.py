from __future__ import annotations

import re
from datetime import datetime

from .parser202 import _DE_AUTHORIZED_CAPITAL_INTRODUCED
from .parser253 import _event
from .parser267 import DATE
from .parser313 import extract_parser313_leftovers

_REPLACED_AUTHORIZATION = re.compile(
    rf'\[Streichung der Statutenbestimmung über die mit Beschluss vom '
    rf'(?P<authorization_date>{DATE}) eingeführte genehmigte Kapitalerhöhung '
    rf'infolge Fristablauf\.\] \. Die Gesellschaft hat mit Beschluss vom '
    rf'(?P<resolution_date>{DATE}) eine genehmigte Kapitalerhöhung gemäss '
    rf'näherer Umschreibung in den Statuten beschlossen\.?'
)


def extract_parser585_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'de':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    if (_DE_AUTHORIZED_CAPITAL_INTRODUCED.search(text.strip()) or
            extract_parser313_leftovers(text, language, *context)[0]):
        return [], text
    match = _REPLACED_AUTHORIZATION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        for date in match.groupdict().values():
            datetime.strptime(date, '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(*context, 'organization_changed',
                   'de.text.expired_authorized_capital_replaced.v2',
                   {'action': 'expired_authorized_capital_replaced', **match.groupdict()})], ''
