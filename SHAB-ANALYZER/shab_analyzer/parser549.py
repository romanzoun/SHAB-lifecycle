from __future__ import annotations

import re

from .parser253 import _event
from .text_extras import _DE_BRANCH_ADDED, _DE_BRANCH_ADDED_CONTINUATION

_UID_NOTE = re.compile(
    r'\[bisher: (?P<place>[^()\[\]\n]+) '
    r'\((?P<previous_registry_id>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\. '
    r'(?P<continuation>[^\[\]\n]+) '
    r'\[Anpassung der UID der Zweigniederlassung in (?P=place) '
    r'aufgrund geänderter Eintragungsvorschriften\]'
)


def extract_parser549_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the UID note and intervening branch after the legacy branch event."""
    if language != 'de' or _DE_BRANCH_ADDED.search(text):
        return [], text
    note = _UID_NOTE.fullmatch(text.strip().rstrip('.'))
    source = _DE_BRANCH_ADDED.search(source_text)
    if not note or not source or source['place'].strip() != note['place']:
        return [], text
    # Only accept the exact remainder of the legacy-owned source clause.
    if not source_text[source.end():].strip().rstrip('.') == note[0]:
        return [], text
    continuation = _DE_BRANCH_ADDED_CONTINUATION.fullmatch(note['continuation'])
    if not continuation:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    payload = {'action': 'added', 'place': continuation['place'].strip(),
               'branch_uid': continuation['uid']}
    if continuation['place_canton']:
        payload['place_canton'] = continuation['place_canton'].upper()
    return [
        _event(*context, 'branch_changed', 'de.text.branch_added.v1', payload),
        _event(*context, 'organization_changed',
               'de.text.branch_uid_registration_requirements_adjustment.v1',
               {'action': 'branch_uid_registration_requirements_adjustment',
                'place': note['place'], 'previous_registry_id': note['previous_registry_id'],
                'branch_uid': source['uid']}),
    ], ''
