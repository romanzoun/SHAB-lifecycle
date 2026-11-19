from __future__ import annotations

import re

from .parser253 import _event
from .parser50 import _FR_INTERMEDIATED_BEARER_SHARES
from .text_extras import _FR_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES

_PARTICIPATION = re.compile(
    r"La société est autorisée à avoir des bons de participation au porteur car "
    r"ils sont tous émis sous forme de titres intermédiés au sens de la loi fédérale "
    r"sur les titres intermédiés\.?", re.I,
)


def extract_parser590_leftovers(text, language, publication_id, published_at,
                                org_uid, plz, canton):
    if language != 'fr' or any(pattern.search(text) for pattern in (
        _FR_INTERMEDIATED_BEARER_SHARES,
        _FR_BEARER_SHARES_AS_INTERMEDIATED_SECURITIES,
    )) or not _PARTICIPATION.fullmatch(text.strip()):
        return [], text
    return [_event(publication_id, published_at, org_uid, plz, canton,
                   'capital_changed',
                   'fr.text.bearer_participation_certificates_intermediated_authorized.v1',
                   {'action': 'bearer_participation_certificates_intermediated_authorized',
                    'intermediated': True})], ''
