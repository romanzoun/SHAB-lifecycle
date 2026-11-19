from __future__ import annotations

import re

from .parser81 import _FR_ASSOCIATE_MANAGERS_TRANSFER_TRUNCATED
from .parser95 import _FR_SHARE_TRANSFER_SIGNATURE_REMAINING
from .parser253 import _person_event

_LEGACY = (_FR_ASSOCIATE_MANAGERS_TRANSFER_TRUNCATED,
           _FR_SHARE_TRANSFER_SIGNATURE_REMAINING)
_TRANSFER = re.compile(
    r"(?P<seller>[^,.;\[\]\n]+) a cédé 1 part de CHF "
    r"(?P<nominal>[\d']+(?:\.\d+)?) au nouvel associé "
    r"(?P<buyer>[^,.;\[\]\n]+), de (?P<origin>[^,.;\[\]\n]+), "
    r"à (?P<place>[^,.;\[\]\n]+)\. (?P=seller) est maintenant associé pour "
    r"(?P<remaining>[\d']+) parts de CHF (?P=nominal)\.?"
)


def extract_parser589_leftovers(text, language, publication_id, published_at,
                                org_uid, plz, canton):
    """Recognize the attested single-share transfer and remaining holding."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in _LEGACY):
        return [], text
    match = _TRANSFER.fullmatch(text.strip())
    if not match or match['seller'] == match['buyer'] or int(match['remaining'].replace("'", '')) < 1:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    seller, buyer = match['seller'], match['buyer']
    rule = 'fr.persons.single_share_transfer_new_associate_remaining.v1'
    return [
        _person_event(*context, 'officer_changed', rule, seller, role='associé',
                      extra={'action': 'shares_transferred', 'counterparty': buyer,
                             'shares_transferred': 1,
                             'shares_count': int(match['remaining'].replace("'", '')),
                             'shares_nominal': match['nominal']}),
        _person_event(*context, 'officer_changed', rule, buyer, place=match['place'],
                      role='associé', extra={'action': 'shares_received',
                          'heimat': match['origin'], 'counterparty': seller,
                          'shares_received': 1, 'shares_count': 1,
                          'shares_nominal': match['nominal'], 'new_associate': True}),
    ], ''
