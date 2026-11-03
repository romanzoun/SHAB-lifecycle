from __future__ import annotations

import re

from .parser253 import _event


# Deliberately excludes the older «La clause ... l'art.» formulations.
_CONTRIBUTION_DISPOSITION_REPEALED = re.compile(
    r"(?:^|(?<=\. ))La disposition statutaire relative à l'apport en nature "
    r"est abrogée conformément à l'article 628 al\. 4 CO\.?$"
)


def extract_parser469_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only the evidenced final sentence, preserving preceding residue."""
    if language != 'fr':
        return [], text
    match = _CONTRIBUTION_DISPOSITION_REPEALED.search(text)
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'fr.text.contribution_in_kind_disposition_repealed.v1',
        {'action': 'contribution_in_kind_clause_repealed',
         'legal_basis': 'article 628 al. 4 CO'},
    )], text[:match.start()]
