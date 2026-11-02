from __future__ import annotations

import re
from datetime import datetime

from .parser207 import _DE_COMPANY_REINSTATED_AFTER_ART155_DELETION
from .parser220 import _DE_COMPANY_REINSTATED_FOR_LIQUIDATION
from .parser253 import _event

_DATE = r'\d{2}\.\d{2}\.\d{4}'
_DE_REINSTATED_FOR_CREDIT_REALIZATION = re.compile(
    rf'Die am (?P<deletion_date>{_DATE}) gelöschte Gesellschaft wird auf Grund '
    rf'des Urteils des (?P<authority>Einzelrichters des Bezirksgerichts [^,;.]+) '
    rf'vom (?P<decision_date>{_DATE}) Zwecks Verwertung eines Guthabens wieder '
    r'in das Handelsregister eingetragen und besteht entsprechend den früheren '
    r'Eintragungen weiter\. \[bisher: (?P<previous>Nachdem kein begründeter '
    r'Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne '
    r'von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.)\]'
)


def extract_parser461_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'de':
        return [], text
    # Original formulations stay with their existing rules even in isolation.
    if any(pattern.fullmatch(text.strip()) for pattern in (
        _DE_COMPANY_REINSTATED_AFTER_ART155_DELETION,
        _DE_COMPANY_REINSTATED_FOR_LIQUIDATION,
    )):
        return [], text
    match = _DE_REINSTATED_FOR_CREDIT_REALIZATION.fullmatch(text.strip())
    if not match:
        return [], text
    payload = match.groupdict()
    try:
        for key in ('deletion_date', 'decision_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload.update(kind='registration_reinstated', action='reinstated',
                   reason='credit_realization', company_continues=True, registry_reinstated=True)
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'status_changed', 'de.text.company_reinstated_credit_realization.v1', payload)], ''
