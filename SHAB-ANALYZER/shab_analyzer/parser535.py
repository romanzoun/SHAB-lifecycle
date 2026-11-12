from __future__ import annotations

import re
from decimal import Decimal

from .parser253 import _event
from .parser267 import COUNT, MONEY
from .parser96 import _FR_SHARE_CONSOLIDATION
from .parser302 import extract_parser302_leftovers
from .parser460 import _FR_FORMERLY_PRIVILEGED_CONSOLIDATION


_FR_TWO_CLASS_CONSOLIDATION = re.compile(
    rf"Réunion des (?P<previous_count>{COUNT}) actions de CHF "
    rf"(?P<previous_nominal>{MONEY}), nominatives, en "
    rf"(?P<ordinary_count>{COUNT}) actions ordinaires de CHF "
    rf"(?P<ordinary_nominal>{MONEY}) et (?P<voting_count>{COUNT}) actions de CHF "
    rf"(?P<voting_nominal>{MONEY}), privilégiées quant au droit de vote\. "
    rf"Capital-actions: CHF (?P<capital>{MONEY}), libéré à concurrence de CHF "
    rf"(?P<paid>{MONEY}), divisé en (?P=ordinary_count) actions ordinaires de CHF "
    rf"(?P=ordinary_nominal) et (?P=voting_count) actions de CHF "
    rf"(?P=voting_nominal), privilégiées quant au droit de vote, toutes nominatives\.?"
)


def extract_parser535_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    if language != 'fr':
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    if (_FR_SHARE_CONSOLIDATION.search(text.strip())
            or _FR_FORMERLY_PRIVILEGED_CONSOLIDATION.fullmatch(text.strip())
            or extract_parser302_leftovers(text, language, *context, source_text=source_text)[0]):
        return [], text
    match = _FR_TWO_CLASS_CONSOLIDATION.fullmatch(text.strip())
    if not match:
        return [], text
    amounts = {key: Decimal(value.replace("'", '')) for key, value in match.groupdict().items()}
    if not (all(value > 0 for value in amounts.values())
            and amounts['previous_count'] > amounts['ordinary_count'] + amounts['voting_count']
            and amounts['previous_count'] * amounts['previous_nominal']
            == amounts['ordinary_count'] * amounts['ordinary_nominal']
            + amounts['voting_count'] * amounts['voting_nominal']
            == amounts['capital']
            and amounts['paid'] <= amounts['capital']):
        return [], text
    payload = dict(match.groupdict(), action='registered_shares_consolidated')
    return [_event(*context, 'organization_changed',
                   'fr.text.registered_shares_consolidated_two_classes.v1', payload)], ''
