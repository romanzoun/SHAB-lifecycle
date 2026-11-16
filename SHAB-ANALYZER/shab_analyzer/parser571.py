from __future__ import annotations

import re

from .parser171 import _FR_BOARD_LIQUIDATORS_AND_TRANSFER_RESTRICTION_REMOVED
from .parser253 import _event, _person_event

_BOARD_PAIR = re.compile(
    r"Liquidateurs: (?P<president>[^,.;\n]+), président, et "
    r"(?P<secretary>[^,.;\n]+), secrétaire, membres du conseil d'administration, "
    r"lesquels continuent de signer collectivement à deux\. "
    r"Les restrictions statutaires liées à la transmissibilité des actions "
    r"sont levées de par la loi\.?"
)


def extract_parser571_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the attested president/secretary liquidators and lifted restrictions."""
    if language != 'fr' or _FR_BOARD_LIQUIDATORS_AND_TRANSFER_RESTRICTION_REMOVED.search(text.strip()):
        return [], text
    match = _BOARD_PAIR.fullmatch(text.strip())
    if not match or match['president'].strip() == match['secretary'].strip():
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.board_president_secretary_liquidators_restrictions_lifted.v1'
    events = [_person_event(
        *context, 'officer_changed', rule, match[key],
        role=role + " du conseil d'administration liquidateur",
        signing='Kollektivunterschrift zu zweien',
    ) for key, role in (('president', 'président'), ('secretary', 'secrétaire'))]
    events.append(_event(*context, 'organization_changed', rule,
                         {'action': 'share_transfer_restrictions_lifted'}))
    return events, ''
