from __future__ import annotations

import re

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, NAME
from .parser95 import _FR_SHARE_TRANSFER_AND_PRESIDENCY
from .parser223 import _FR_MANAGER_SHARE_TRANSFER


_LEGACY = (_FR_SHARE_TRANSFER_AND_PRESIDENCY, _FR_MANAGER_SHARE_TRANSFER)
_TRANSFER = re.compile(
    rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) des (?P<before>{COUNT}) '
    rf'parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), '
    rf'à (?P<place>{NAME}), nouvel associé-gérant avec (?P=count) parts de CHF '
    rf'(?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) '
    rf'parts de CHF (?P=nominal)\.?'
)


def extract_parser502_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the evidenced «des» partial transfer, preserving older owners."""
    if language != 'fr' or any(p.fullmatch(text.strip()) for p in _LEGACY):
        return [], text
    m = _TRANSFER.fullmatch(text.strip())
    if not m:
        return [], text
    count, before, remaining = (int(m[k].replace("'", ''))
                                for k in ('count', 'before', 'remaining'))
    if count <= 0 or remaining <= 0 or before != count + remaining:
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    return [
        _event(*context, 'ownership_changed', 'fr.text.partial_transfer_des_new_manager.v1',
               {**m.groupdict(), 'action': 'partial_transfer', 'currency': 'CHF'}),
        _person_event(*context, 'officer_changed', 'fr.persons.partial_transfer_des_new_manager.v1',
                      m['buyer'], place=m['place'], role='associé-gérant',
                      extra={'action': 'appointed', 'origin': m['origin']}),
    ], ''
