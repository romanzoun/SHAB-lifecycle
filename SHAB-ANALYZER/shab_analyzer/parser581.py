from __future__ import annotations

import re

from .parser57 import _FR_ASSOCIATE_TRANSFER_AND_PRESIDENCY
from .parser95 import _FR_SHARE_TRANSFER_AND_PRESIDENCY
from .parser253 import _person_event

_NAME = r'[^,.;\n]+'
_COUNT = r"[\d']+"
_TRANSFER = re.compile(
    rf'(?P<seller>{_NAME}) cède (?P<transferred>{_COUNT}) de ses (?P<before>{_COUNT}) '
    rf'parts de CHF (?P<nominal>{_COUNT}) à '
    rf'(?P<buyer1>{_NAME}), de (?P<origin1>{_NAME}), à (?P<place1>{_NAME}), '
    rf'nouvel associé-gérant avec (?P<count1>{_COUNT}) parts de CHF (?P=nominal), '
    rf'(?P<buyer2>{_NAME}), de (?P<origin2>{_NAME}), à (?P<place2>{_NAME}), '
    rf'nouvel associé sans signature, avec (?P<count2>{_COUNT}) parts de CHF (?P=nominal), '
    rf'et (?P<buyer3>{_NAME}), de (?P<origin3>{_NAME}), à (?P<place3>{_NAME}), '
    rf'nouvel associé sans signature, avec (?P<count3>{_COUNT}) parts de CHF (?P=nominal); '
    rf'(?P=seller), qui reste titulaire de (?P<remaining>{_COUNT}) parts de CHF (?P=nominal), est nommé président\.?'
)


def extract_parser581_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    if language != 'fr' or any(p.search(text.strip()) for p in (
        _FR_ASSOCIATE_TRANSFER_AND_PRESIDENCY, _FR_SHARE_TRANSFER_AND_PRESIDENCY
    )):
        return [], text
    m = _TRANSFER.fullmatch(text.strip())
    if not m:
        return [], text
    number = lambda key: int(m[key].replace("'", ''))
    before, transferred, remaining, c1, c2, c3, nominal = (
        number(k) for k in ('before', 'transferred', 'remaining', 'count1', 'count2', 'count3', 'nominal')
    )
    if (min(before, transferred, remaining, c1, c2, c3, nominal) <= 0
            or transferred != c1 + c2 + c3 or before != transferred + remaining
            or len({m['seller'], m['buyer1'], m['buyer2'], m['buyer3']}) != 4):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    rule = 'fr.persons.transfer_three_associates_presidency.v1'
    common = {'share_nominal': m['nominal'], 'currency': 'CHF'}
    events = [_person_event(*context, 'officer_changed', rule, m['seller'], role='président',
        extra={**common, 'action': 'shares_transferred', 'shares_before': before,
               'shares_transferred': transferred, 'shares_count': remaining})]
    for i, count in ((1, c1), (2, c2), (3, c3)):
        events.append(_person_event(*context, 'officer_changed', rule, m[f'buyer{i}'],
            place=m[f'place{i}'], role='associé-gérant' if i == 1 else 'associé',
            signing=None if i == 1 else 'ohne Zeichnungsberechtigung',
            extra={**common, 'action': 'appointed', 'new_associate': True,
                   'heimat': m[f'origin{i}'], 'shares_received': count, 'shares_count': count,
                   'transfer_total': transferred}))
    return events, ''
