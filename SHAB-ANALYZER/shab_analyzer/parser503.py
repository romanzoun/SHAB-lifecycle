from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .text_extras import _FR_CAPITAL_CLAUSE_INTRODUCED


_REST = re.compile(r'\[non:\s*\]\.?')
_PREVIOUS = re.compile(r'\[non: (?P<clause>[^\[\]\n]+)\]\.?$')


def extract_parser503_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Annotate the evidenced correction after legacy capital clause extraction.

    Complete clauses remain exclusively owned by the existing text rule. Only
    its empty correction wrapper is consumed, with both source clauses checked
    using that rule's pattern. Historical events and payloads stay intact.
    """
    if language != 'fr' or not _REST.fullmatch(text.strip()):
        return [], text
    source = source_text.strip()
    previous = _PREVIOUS.search(source)
    if not previous:
        return [], text
    old = _FR_CAPITAL_CLAUSE_INTRODUCED.fullmatch(previous['clause'])
    corrected = next((m for m in _FR_CAPITAL_CLAUSE_INTRODUCED.finditer(source)
                      if m.end() <= previous.start()
                      and not source[m.end():previous.start()].strip()), None)
    if (not old or not corrected or old['kind'].lower() != 'autorisée'
            or corrected['kind'].lower() != 'conditionnelle'
            or old['date'] != corrected['date']):
        return [], text
    try:
        decision_date = datetime.strptime(corrected['date'], '%d.%m.%Y').date().isoformat()
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'capital_changed', 'fr.text.capital_clause_kind_corrected_annotation.v1',
        {'kind': 'conditional_capital_clause', 'action': 'corrected',
         'previous_kind': 'authorized_capital_clause', 'decision_date': decision_date},
    )], ''
