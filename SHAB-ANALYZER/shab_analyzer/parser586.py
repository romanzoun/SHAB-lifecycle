from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import COUNT, DATE, MONEY
from .parser369 import extract_parser369_leftovers

_CONVERSION = re.compile(
    rf'Aktienkapital neu: CHF (?P<capital>{MONEY}), vollständig liberiert, '
    rf'eingeteilt in (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) '
    rf'\(bisher (?P<previous_count>{COUNT}) Inhaberaktien zu CHF (?P<previous_nominal>{MONEY})\)\. '
    rf'Die Übertragbarkeit der Namenaktien ist nach Massgabe der Statuten beschränkt\. '
    rf'Mitteilung an die Aktionäre: per Brief, E-Mail oder Telefax\. '
    rf'Statuten geändert am (?P<statutes_date>{DATE})\.?'
)


def extract_parser586_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'de':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    if extract_parser369_leftovers(text, language, *context)[0]:
        return [], text
    match = _CONVERSION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['statutes_date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(*context, 'organization_changed',
                   'de.text.bearer_to_registered_shares_statutes_changed.v2',
                   {'action': 'bearer_to_registered_shares_statutes_changed',
                    **match.groupdict(), 'currency': 'CHF', 'fully_paid': True,
                    'security_kind': 'Namenaktien', 'previous_security_kind': 'Inhaberaktien',
                    'transfer_restricted': True, 'communication': 'Brief, E-Mail oder Telefax'})], ''
