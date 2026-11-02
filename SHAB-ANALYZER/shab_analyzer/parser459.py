from __future__ import annotations

import re
from datetime import datetime

from .parser79 import _IT_FUSION_WITH_DEFICIT_COVERAGE, _event

# Same merger structure, but the confirmation refers only to the shortfall.
_IT_FUSION_WITH_SHORTFALL_COVERAGE = re.compile(
    _IT_FUSION_WITH_DEFICIT_COVERAGE.pattern.replace(
        'scoperto e del sovraindebitamento', 'scoperto',
    ),
    _IT_FUSION_WITH_DEFICIT_COVERAGE.flags,
)


def extract_parser459_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    if language != 'it' or _IT_FUSION_WITH_DEFICIT_COVERAGE.search(text.strip()):
        return [], text
    match = _IT_FUSION_WITH_SHORTFALL_COVERAGE.fullmatch(text.strip())
    if not match:
        return [], text
    payload = {key: value.strip() for key, value in match.groupdict().items()}
    try:
        for key in ('agreement_date', 'balance_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    payload.update({
        'kind': 'absorption', 'currency': 'CHF',
        'all_shares_held_by_acquirer': True, 'capital_increase': False,
        'share_allocation': False, 'deficit_coverage_confirmed_by_auditor': True,
    })
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'company_merged', 'it.text.fusion_with_shortfall_coverage.v1', payload,
    )], ''
