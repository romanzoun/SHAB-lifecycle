from __future__ import annotations

import re

from .parser73 import _FR_SIGNATURES_REPLACING_PROXY
from .parser253 import _person_event

# Keep the marriage-name abbreviation as part of the name, including its dot.
_NAME = r'[^,.;\n]+?(?: ép\. [^,.;\n]+?)?'
_PAIR = re.compile(
    rf'Signature collective à deux a été conférée à (?P<name1>{_NAME}) et '
    rf'(?P<name2>{_NAME}), leur procuration est radiée\.?'
)


def extract_parser558_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the comma-separated pair of signatures replacing procurations."""
    if language != 'fr' or _FR_SIGNATURES_REPLACING_PROXY.search(text.strip()):
        return [], text
    match = _PAIR.fullmatch(text.strip())
    if not match or match['name1'] == match['name2']:
        return [], text
    # Names cannot stand for a list of three or more people.
    if any(' et ' in match[key] for key in ('name1', 'name2')):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [
        _person_event(
            *context, 'signing_authority_changed',
            'fr.persons.two_collective_signatures_proxy_revoked_comma.v1', match[key],
            signing='Kollektivunterschrift zu zweien',
            extra={'action': 'signing_replaced', 'previous_signing': 'procuration',
                   'previous_signing_revoked': True},
        ) for key in ('name1', 'name2')
    ], ''
