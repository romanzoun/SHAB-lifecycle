from __future__ import annotations

import re
from datetime import datetime

from .parser126 import _FR_ADDITIONAL_ADDRESS_CORRECTED
from .parser191 import _FR_OTHER_ADDRESS_CORRECTED
from .parser232 import _FR_OTHER_ADDRESS_CORRECTED as _FR_OTHER_ADDRESS_CORRECTED_STRUCTURED
from .parser253 import _event
from .parser267 import DATE


_CORRECTION = re.compile(
    rf"Rectificatif: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) "
    rf"\(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) "
    r"est rectifiée en ce sens que la nouvelle autre adresse est: "
    r"(?P<address>[^();]+?) \(et non (?P<previous_address>[^();]+?), comme publié\)\.?"
)


def extract_parser512_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested correction of a new additional address."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_ADDITIONAL_ADDRESS_CORRECTED, _FR_OTHER_ADDRESS_CORRECTED,
        _FR_OTHER_ADDRESS_CORRECTED_STRUCTURED,
    )):
        return [], text
    match = _CORRECTION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(match[key], '%d.%m.%Y').date().isoformat()
                 for key in ('entry_date', 'notice_date')}
    except ValueError:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'address_changed', 'fr.text.new_other_address_corrected_notice.v1', {
            'kind': 'other_address', 'action': 'publication_corrected',
            'to': match['address'], 'from': match['previous_address'],
            'entry': match['entry'], **dates, 'notice_ref': match['notice_ref'],
        },
    )], ''
