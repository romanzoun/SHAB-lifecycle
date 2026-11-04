from __future__ import annotations

import re

from .parser50 import _FR_INTERMEDIATED_BEARER_SHARES
from .text_extras import _FR_BEARER_SHARES_AUTHORIZED
from .parser253 import _event
from .parser451 import extract_parser451_leftovers

_LISTED_PARTICIPATION = re.compile(
    r"La société ayant des titres de participation cotés en bourse, "
    r"elle est autorisée à conserver et à émettre des actions au porteur\.?"
)


def extract_parser474_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize permission to retain and issue bearer shares for listed participation titles."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_INTERMEDIATED_BEARER_SHARES, _FR_BEARER_SHARES_AUTHORIZED,
    )):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    # Parser 451 defines its listed-share pattern inline; delegate ownership to it.
    old_events, old_rest = extract_parser451_leftovers(text, language, *context, source_text=source_text)
    if old_events or old_rest != text:
        return [], text
    if not _LISTED_PARTICIPATION.fullmatch(text):
        return [], text
    return [_event(
        *context, 'capital_changed', 'fr.text.listed_participation_bearer_shares_permitted.v1',
        {'action': 'bearer_shares_permitted', 'reason': 'listed_securities',
         'retain_permitted': True, 'issue_permitted': True},
    )], ''
