from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from .parser253 import _event
from .parser267 import COUNT, MONEY
from .parser302 import extract_parser302_leftovers
from .parser96 import _FR_SHARE_CONSOLIDATION

_FR_FORMERLY_PRIVILEGED_CONSOLIDATION = re.compile(
    rf"Réunion des (?P<previous_count>{COUNT}) actions de CHF "
    rf"(?P<previous_nominal>{MONEY}), jusqu'ici privilégiées quant au droit de vote, "
    rf"en (?P<new_count>{COUNT}) actions de CHF (?P<new_nominal>{MONEY}), "
    rf"nominatives, (?P<restriction>liées selon statuts)?\. Capital-actions: CHF "
    rf"(?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) "
    rf"actions de CHF (?P<nominal>{MONEY}), nominatives, liées selon statuts\.?"
)


def extract_parser460_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'fr':
        return [], text
    match = _FR_FORMERLY_PRIVILEGED_CONSOLIDATION.fullmatch(text.strip())
    if not match:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    # Existing consolidation formulations remain owned by their original rules,
    # including when those rules are disabled in pipeline isolation tests.
    if _FR_SHARE_CONSOLIDATION.search(text.strip()) or extract_parser302_leftovers(
        text, language, *context, source_text=source_text,
    )[0]:
        return [], text
    payload = match.groupdict()
    restriction = payload.pop('restriction')
    if restriction is None:
        original_clause = (
            f"Réunion des {match['previous_count']} actions de CHF {match['previous_nominal']}, "
            "jusqu'ici privilégiées quant au droit de vote, "
            f"en {match['new_count']} actions de CHF {match['new_nominal']}, "
            "nominatives, liées selon statuts."
        )
        if original_clause not in source_text:
            return [], text
    try:
        amounts = {key: Decimal(value.replace("'", '')) for key, value in payload.items()}
    except InvalidOperation:
        return [], text
    if not (all(value > 0 for value in amounts.values())
            and amounts['previous_count'] > amounts['new_count']
            and amounts['previous_count'] * amounts['previous_nominal']
            == amounts['new_count'] * amounts['new_nominal']
            <= amounts['capital']
            and amounts['count'] * amounts['nominal'] == amounts['capital']
            and amounts['new_nominal'] == amounts['nominal']):
        return [], text
    payload.update(action='registered_shares_consolidated', previous_voting_privileged=True)
    return [_event(*context, 'organization_changed',
                   'fr.text.formerly_privileged_shares_consolidated.v1', payload)], ''
