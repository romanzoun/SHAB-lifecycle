from __future__ import annotations

import re
from datetime import datetime

from .parser131 import _DE_DEFINITIVE_MORATORIUM_EXTENDED
from .parser253 import _event
from .parser267 import DATE

_NAME = r'[^,;\[\]\n]+?'
_EXTENSION = re.compile(
    rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das '
    rf'(?P<court>Zivilgericht [^,;.\[\]\n]+) die mit Entscheid vom '
    rf'(?P<grant_date>{DATE}) für die Dauer von (?P<months>6) Monaten '
    r'bewilligte definitive Nachlassstundung und Einsetzung von '
    rf'(?P<commissioner>lic\.iur\. {_NAME}), (?P<profession>Advokat), '
    rf'c/o (?P<care_of>{_NAME}), (?P<street>{_NAME}), Postfach, '
    rf'CH-(?P<postal_code>\d{{4}}) (?P<place>[^,;.\[\]\n]+), als Sachwalter '
    rf'bis zum (?P<until_date>{DATE}) verlängert\. '
    rf'\[bisher: Mit Entscheid vom (?P=grant_date) hat das (?P=court) '
    rf'der Gesellschaft für die Dauer von (?P=months) Monaten, d\.h\. bis '
    rf'(?P<previous_until_date>{DATE}), die definitive Nachlassstundung '
    r'bewilligt und als Sachwalter (?P=commissioner), (?P=profession), '
    r'c/o (?P=care_of), (?P=street), Postfach, CH-(?P=postal_code) '
    r'(?P=place), eingesetzt\.\]\.?'
)


def extract_parser516_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested joint extension of moratorium and commissioner."""
    if language != 'de' or _DE_DEFINITIVE_MORATORIUM_EXTENDED.search(text.strip()):
        return [], text
    match = _EXTENSION.fullmatch(text.strip())
    if not match:
        return [], text
    try:
        dates = {key: datetime.strptime(value, '%d.%m.%Y').date()
                 for key, value in match.groupdict().items() if key.endswith('_date')}
    except ValueError:
        return [], text
    if dates['until_date'] < dates['decision_date']:
        return [], text
    return [_event(
        publication_id, published_at, org_uid, plz, canton,
        'status_changed', 'de.text.definitive_moratorium_and_commissioner_extended.v1',
        {'kind': 'composition_moratorium', 'action': 'extended', 'definitive': True,
         **{key: value for key, value in match.groupdict().items()
            if key not in dates and key != 'months'},
         **{key: value.isoformat() for key, value in dates.items()},
         'commissioner_mandate_extended': True},
    )], ''
