from __future__ import annotations

import re

from .persons import _FR_N_EST_PLUS, extract_persons


_FR_MANAGER_REMOVED_MISSING_PLUS = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+) n'est gérant; sa signature est radiée\.?"
)


def extract_parser458_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle the evidenced missing 'plus', preserving legacy person payloads."""
    if language != 'fr' or _FR_N_EST_PLUS.search(text):
        return [], text
    match = _FR_MANAGER_REMOVED_MISSING_PLUS.fullmatch(text.strip())
    if not match:
        return [], text
    name = match['name']
    canonical = f"{name} n'est plus gérant; La signature de {name} est radiée"
    events, rest = extract_persons(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if len(events) != 2 or rest.strip(' ;.,'):
        return [], text
    for event in events:
        event.rule_id = event.rule_id.replace('.v1', '_missing_plus.v1')
    return events, ''
