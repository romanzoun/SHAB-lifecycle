from __future__ import annotations

import re

from .parser51 import _IT_SHARE_TRANSFER_RESTRICTION
from .parser64 import _IT_SHARE_TRANSFER_RESTRICTION_REMOVED_LEGACY
from .parser141 import _IT_SHARE_TRANSFER_RESTRICTION_CANCELLED
from .parser253 import _event


_LEGACY = (_IT_SHARE_TRANSFER_RESTRICTION,
           _IT_SHARE_TRANSFER_RESTRICTION_REMOVED_LEGACY,
           _IT_SHARE_TRANSFER_RESTRICTION_CANCELLED)
_RESTRICTION_REMOVED = re.compile(
    r'\[La restrizione della trasferibilità delle azioni nominative è cancellata, '
    r'in quanto è stata eliminata dallo statuto\.\]\.?'
)


def extract_parser506_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Parse the attested statutory deletion of registered-share restrictions."""
    if language != 'it' or any(pattern.search(text.strip()) for pattern in _LEGACY):
        return [], text
    if not _RESTRICTION_REMOVED.fullmatch(text.strip()):
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'it.text.share_transfer_restriction_deleted_from_statutes.v1',
        {'kind': 'share_transfer_restricted', 'action': 'removed',
         'share_kind': 'azioni nominative'},
    )], ''
