from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event

_COMPLEMENT = re.compile(
    r"(?<!\S)L'inscription (?P<entry>\d+) du (?P<entry_date>\d{2}\.\d{2}\.\d{4}) "
    r"\(FOSC du (?P<notice_date>\d{2}\.\d{2}\.\d{4}) p\. (?P<notice_reference>(?:0/)?\d+)\) "
    r"est complétée en ce sens que les (?:(?P<count>[\d']+) actions de CHF "
    r"(?P<nominal>[\d'.]+), nominatives,|actions) sont (?=\.(?:\s|$))"
)


def extract_parser518_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Complete the attested entry supplement after restriction extraction."""
    if language != 'fr':
        return [], text
    match = _COMPLEMENT.search(text)
    if not match:
        return [], text
    sentence = match[0] + 'liées selon statuts.'
    if sentence not in source_text:
        return [], text
    try:
        for key in ('entry_date', 'notice_date'):
            datetime.strptime(match[key], '%d.%m.%Y')
    except ValueError:
        return [], text
    action = 'registered_share_transfer_restriction_entry_complemented'
    event = _event(
        publication_id, published_at, org_uid, plz, canton,
        'organization_changed', f'fr.text.{action}.v1',
        {'action': action, **{k: v for k, v in match.groupdict().items() if v is not None},
         'transfer_restriction': 'liées selon statuts'},
    )
    return [event], (text[:match.start()] + text[match.end() + 1:]).strip()
