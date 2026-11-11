from __future__ import annotations

import re

from .parser253 import _event
from .parser57 import _FR_CONTRIBUTION_RULES_REMOVED_VARIANT
from .text_extras import _FR_CONTRIBUTION_RULES_REMOVED

_REMOVED_CONTRIBUTION_CLAUSES = re.compile(
    r"Nouveaux faits qualifiés: \[Abrogation des clauses d'apport en nature et de reprise de biens\] "
    r"\[biffé: (?P<previous_contribution>Selon convention des [^\[\]\n]+)\]\. "
    r"\[biffé: (?P<previous_acquisition>Reprise de biens envisagée: [^\[\]\n]+)\]\.?"
)


def extract_parser526_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested bracketed repeal and retain deleted clause details."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_CONTRIBUTION_RULES_REMOVED_VARIANT, _FR_CONTRIBUTION_RULES_REMOVED,
    )):
        return [], text
    match = _REMOVED_CONTRIBUTION_CLAUSES.fullmatch(text.strip())
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'statutes_changed', 'fr.text.bracketed_contribution_rules_removed.v1',
        {'action': 'removed', 'kind': 'contribution_in_kind_and_asset_acquisition',
         **match.groupdict()},
    )], ''
