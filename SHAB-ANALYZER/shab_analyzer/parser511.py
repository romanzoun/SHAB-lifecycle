from __future__ import annotations

import re
from datetime import datetime

from .parser63 import _DE_PROVISIONAL_MORATORIUM_GRANTED_AND_EXTENDED
from .parser253 import _event
from .parser267 import DATE, NAME, UID


_NOTICE = re.compile(
    rf'Bemerkungen zum Hauptsitz neu: Mit Verfügung vom (?P<grant_date>{DATE}) '
    rf'hatte das (?P<authority>{NAME}) der Gesellschaft die provisorische '
    rf'Nachlassstundung bis zum (?P<grant_until_date>{DATE}) bewilligt und als '
    rf'provisorischen Sachwalter (?P<commissioner>{NAME}), p\.A\. '
    rf'(?P<commissioner_company>{NAME}) \((?P<commissioner_company_uid>{UID})\), '
    rf'(?P<commissioner_address>{NAME}), (?P<commissioner_postal_code>\d{{4}}) '
    rf'(?P<commissioner_place>{NAME}), eingesetzt\. Mit Verfügung vom '
    rf'(?P<publication_order_date>{DATE}) verfügte das (?P=authority), die '
    rf'Publikation der mit Verfügung vom (?P<extension_date>{DATE}) bewilligten '
    rf'Verlängerung der provisorischen Nachlassstundung bis zum (?P<until_date>{DATE})\.?'
)


def extract_parser511_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested head-office grant and extension publication order."""
    if language != 'de' or _DE_PROVISIONAL_MORATORIUM_GRANTED_AND_EXTENDED.search(text.strip()):
        return [], text
    match = _NOTICE.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(value, '%d.%m.%Y').date().isoformat()
                 for key, value in match.groupdict().items() if key.endswith('_date')}
    except ValueError:
        return [], text
    common = {'scope': 'head_office', 'moratorium_type': 'provisional',
              'authority': match['authority']}
    context = publication_id, published_at, org_uid, plz, canton
    return [
        _event(*context, 'status_changed',
               'de.text.head_office_provisional_moratorium_granted.v1', {
                   **common, 'kind': 'composition_moratorium_granted',
                   'decision_date': dates['grant_date'], 'until': dates['grant_until_date'],
                   'commissioner': match['commissioner'], 'commissioner_status': 'provisional',
                   **{key: match[key] for key in (
                       'commissioner_company', 'commissioner_company_uid',
                       'commissioner_address', 'commissioner_postal_code', 'commissioner_place')},
               }),
        _event(*context, 'status_changed',
               'de.text.head_office_provisional_moratorium_extension_publication.v1', {
                   **common, 'kind': 'composition_moratorium_extended',
                   'decision_date': dates['extension_date'], 'until': dates['until_date'],
                   'publication_order_date': dates['publication_order_date'],
               }),
    ], ''
