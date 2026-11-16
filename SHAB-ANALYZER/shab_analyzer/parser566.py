from __future__ import annotations

import re

from .parser148 import _FR_PAIR_DOMICILE_CHANGED_COUNTRY
from .parser231 import _FR_TWO_PEOPLE_SHARED_DOMICILE
from .parser253 import _person_event
from .parser558 import _NAME

_PAIR = re.compile(
    rf'(?P<name1>{_NAME}) et (?P<name2>{_NAME}) sont maintenant '
    r'domiciliés à (?P<place>[^,.;\n]+), (?P<country>[A-Z]{3})\.?'
)


def extract_parser566_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton):
    """Read a marriage-name pair's shared domicile with a country code."""
    if language != 'fr':
        return [], text
    clause = text.strip()
    # Existing country variants retain ownership even in isolated rule tests.
    if any(pattern.search(clause) for pattern in (
        _FR_PAIR_DOMICILE_CHANGED_COUNTRY, _FR_TWO_PEOPLE_SHARED_DOMICILE,
    )):
        return [], text
    match = _PAIR.fullmatch(clause)
    if not match or match['name1'] == match['name2']:
        return [], text
    if any(' et ' in match[key] for key in ('name1', 'name2')):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [_person_event(
        *context, 'officer_changed',
        'fr.persons.pair_marriage_name_domicile_changed_country.v1', match[key],
        place=match['place'], extra={
            'action': 'domicile_changed', 'domicile_changed': True,
            'country': match['country'],
        },
    ) for key in ('name1', 'name2')], ''
