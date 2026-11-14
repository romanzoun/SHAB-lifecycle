from __future__ import annotations

import re

from .parser200 import _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING
from .parser253 import _count, _person_event
from .parser267 import COUNT, MONEY

_NAME = r'[^,.;\[\]\n]+?'
_TRANSFER = re.compile(
    rf"L'associée (?P<seller>{_NAME}) détient maintenant (?P<remaining>{COUNT}) "
    rf'parts de CHF (?P<nominal>{MONEY}), par suite de cession de '
    rf'(?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{_NAME}), '
    rf'du (?P<origin>{_NAME}), à (?P<place>{_NAME}), nouvel associé pour '
    rf'(?P<received>{COUNT}) parts de CHF (?P=nominal)'
)
_SOURCE = re.compile(_TRANSFER.pattern + r', avec signature individuelle\.?$')


def extract_parser552_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the attested female associate transfer after signing extraction."""
    if language != 'fr' or _FR_MANAGER_TRANSFER_NEW_ASSOCIATE_REMAINING.search(text.strip()):
        return [], text
    match = _TRANSFER.fullmatch(text.strip().removesuffix('.'))
    source = _SOURCE.search(source_text.strip())
    if not match or not source or source.groupdict() != match.groupdict():
        return [], text
    transferred, received, remaining = (_count(match[k]) for k in ('count', 'received', 'remaining'))
    if transferred <= 0 or received != transferred or remaining <= 0:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.female_associate_transfer_new_individual_signer.v1'
    common = {'share_nominal': match['nominal'], 'currency': 'CHF'}
    return [
        _person_event(*context, 'officer_changed', rule, match['seller'], role='associée',
                      extra={**common, 'action': 'shares_transferred',
                             'counterparty': match['buyer'], 'shares_transferred': transferred,
                             'shares_count': remaining}),
        _person_event(*context, 'officer_changed', rule, match['buyer'],
                      place=match['place'], role='associé', signing='Einzelunterschrift',
                      extra={**common, 'action': 'shares_received', 'new_associate': True,
                             'origin': match['origin'], 'counterparty': match['seller'],
                             'shares_received': received, 'shares_count': received}),
    ], ''
