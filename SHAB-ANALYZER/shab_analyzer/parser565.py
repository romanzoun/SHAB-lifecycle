from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE
from .parser409 import NAME
from .parser114 import _DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED
from .parser121 import _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED

_APPEAL = re.compile(
    rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das '
    rf'(?P<authority>[^,;\n]+?) der Beschwerde gegen den Entscheid des '
    rf'Konkursrichters des (?P<court>{NAME}) vom (?P<bankruptcy_date>{DATE}) '
    r'betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\. '
    r'Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. '
    r'\[gestrichen: Über die Inhaberin dieses Einzelunternehmens ist mit Entscheid '
    r'des Konkursrichters des (?P=court) vom (?P=bankruptcy_date) mit Wirkung ab dem '
    rf'(?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, '
    r'der Konkurs eröffnet worden\.\]\.?' 
)


def extract_parser565_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read the female-owner decision variant with an explicit deleted entry."""
    if language != 'de':
        return [], text
    clause = text.strip()
    if any(p.fullmatch(clause) for p in (
        _DE_OWNER_BANKRUPTCY_EFFECT_SUSPENDED,
        _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED,
    )):
        return [], text
    match = _APPEAL.fullmatch(clause)
    if not match:
        return [], text
    try:
        for key in ('decision_date', 'bankruptcy_date', 'effective_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton, 'status_changed',
        'de.text.owner_bankruptcy_appeal_entry_removed_female_decision.v1',
        {'action': 'owner_bankruptcy_appeal_entry_removed_female_decision',
         **match.groupdict(), 'bankruptcy_suspended': True,
         'bankruptcy_entry_removed': True},
    )], ''
