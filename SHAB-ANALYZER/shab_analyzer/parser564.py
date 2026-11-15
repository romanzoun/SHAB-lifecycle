from __future__ import annotations

import re

from .parser253 import _event
from .parser409 import NAME

_PREVIOUS_AUDITOR = re.compile(
    rf'Der korrekte Bishertext der Revisionsstelle wäre: \[bisher: '
    rf'(?P<name>{NAME}) '
    r'\((?P<previous_registry_id>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\.?'
)


def extract_parser564_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read a historical auditor correction without inferring a current auditor."""
    if language != 'de':
        return [], text
    # Closing immediately after the registry ID excludes parser415's existing
    # form with a place and role, even when that parser is disabled in tests.
    match = _PREVIOUS_AUDITOR.fullmatch(text.strip())
    if not match:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', 'de.text.auditor_previous_text_supplemented_short.v1',
        {'action': 'auditor_previous_text_supplemented',
         **match.groupdict(), 'corrected': True},
    )], ''
