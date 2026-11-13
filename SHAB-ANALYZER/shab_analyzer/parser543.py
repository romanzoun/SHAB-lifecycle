from __future__ import annotations

import re

from .parser57 import _FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE
from .parser58 import _FR_ADMINISTRATION_PAIR, extract_parser58_leftovers


_PAIR = re.compile(
    r"Administration: (?P<name1>[^,.;\n]+), nommé président et "
    r"(?P<name2>[^,.;\n]+), de (?P<origin>[^,.;\n]+), à "
    r"(?P<place>[^,.;\n]+), secrétaire, tous deux"
    r"(?P<signing> avec signature individuelle)?\.?"
)


def extract_parser543_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Resolve the attested president/secretary pair with shared signing."""
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_ADMINISTRATION_PAIR, _FR_ADMINISTRATION_PAIR_WITH_SECOND_ROLE,
    )):
        return [], text
    match = _PAIR.fullmatch(text.strip())
    if not match:
        return [], text
    # Earlier signing extraction may remove the shared suffix. Require the
    # complete attested clause in the source before restoring that information.
    complete = text.strip().rstrip('.') + ' avec signature individuelle'
    if not match['signing'] and not re.search(re.escape(complete) + r'\.(?:\s|$)', source_text):
        return [], text
    canonical = (f"Administration: {match['name1']}, nommé président et "
                 f"{match['name2']}, de {match['origin']}, à {match['place']}, "
                 "secrétaire, lesquels signent individuellement")
    events, rest = extract_parser58_leftovers(
        canonical, language, publication_id, published_at, org_uid, plz, canton,
    )
    if rest or len(events) != 4:
        return [], text
    for event in events:
        event.rule_id = event.rule_id.replace('administration_pair', 'administration_pair_secretary_shared_signing')
    return events, ''
