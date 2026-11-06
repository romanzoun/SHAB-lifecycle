from __future__ import annotations

import re

from .parser66 import _FR_QUALIFIED_FACT_REMOVED
from .parser113 import _FR_REMOVED_QUALIFIED_FACT
from .parser170 import _FR_CONTRIBUTION_AND_ASSET_ACQUISITION_CLAUSE_REPEALED
from .parser253 import _event
from .text_extras import _FR_CONTRIBUTION_RULES_REMOVED

_FR_CONTRIBUTION_CLAUSE_REPEALED_ART628 = re.compile(
    r"Nouveaux faits qualifiés: \[Abrogation selon l'article "
    r"(?P<legal_basis>628, al\. 4, CO), des dispositions statutaires relatives "
    r"aux apports en nature : (?P<previous>La société se propose d'acquérir "
    r"[^\[\]\r\n]+)\]\.?"
)


def extract_parser493_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Record repeal only; the bracketed acquisition describes the old clause."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_QUALIFIED_FACT_REMOVED, _FR_REMOVED_QUALIFIED_FACT,
        _FR_CONTRIBUTION_AND_ASSET_ACQUISITION_CLAUSE_REPEALED,
        _FR_CONTRIBUTION_RULES_REMOVED,
    )):
        return [], text
    match = _FR_CONTRIBUTION_CLAUSE_REPEALED_ART628.fullmatch(text)
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'statutes_changed', 'fr.text.contribution_clause_repealed_art628.v1',
        {'kind': 'contribution_in_kind', 'action': 'removed',
         'previous': match['previous'], 'legal_basis': match['legal_basis']},
    )], ''
