from __future__ import annotations

import re
from datetime import datetime

from .parser226 import (
    _FR_ASSOCIATION_DISSOLVED_COLLECTIVE_LIQUIDATORS,
    extract_parser226_leftovers,
)

# Only the evidenced two committee roles; the role-free form belongs to 226.
_PAIR = re.compile(
    r"L'association est dissoute par décision de l'assemblée générale du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\. Liquidateurs: les membres du comité "
    r"(?P<name1>[^,.;\n]+), président et (?P<name2>[^,.;\n]+), secrétaire, "
    r"lesquels continuent à signer collectivement à deux\.?"
)


def extract_parser465_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'fr' or _FR_ASSOCIATION_DISSOLVED_COLLECTIVE_LIQUIDATORS.search(text.strip()):
        return [], text
    match = _PAIR.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        datetime.strptime(match['date'], '%d.%m.%Y')
    except ValueError:
        return [], text
    canonical = (
        f"L'association est dissoute par décision de l'assemblée générale du {match['date']}. "
        f"Liquidateurs: les membres du comité {match['name1']} et {match['name2']}, "
        "lesquels continuent à signer collectivement à deux"
    )
    events, rest = extract_parser226_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton)
    if len(events) != 3 or rest:
        return [], text
    for event in events:
        event.rule_id = 'fr.persons.association_dissolved_two_committee_roles.v1'
    for event, role in zip(events[1:], ('président', 'secrétaire')):
        event.payload['committee_role'] = role
    return events, ''
