from __future__ import annotations

import re
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY
from .parser409 import NAME
from .parser117 import _FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER
from .parser160 import _FR_TWO_MANAGERS_PRESIDENT_SECRETARY_SIGN_INDIVIDUALLY


_FR_TRANSFER_MANAGER_SECRETARY = re.compile(
    rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) '
    rf'parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), '
    rf'de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée, '
    rf'gérante secrétaire\. (?P=seller), qui est nommé président, reste titulaire '
    rf'de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)\.?'
)


def extract_parser537_leftovers(text, language, publication_id, published_at,
                               org_uid, plz, canton, *, source_text=''):
    """Recognize the attested residual transfer with a manager-secretary role."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in (
        _FR_THREE_SELLERS_TRANSFER_TO_NEW_MANAGER,
        _FR_TWO_MANAGERS_PRESIDENT_SECRETARY_SIGN_INDIVIDUALLY,
    )):
        return [], text
    match = _FR_TRANSFER_MANAGER_SECRETARY.fullmatch(text.strip())
    if not match:
        return [], text
    values = {k: Decimal(match[k].replace("'", ''))
              for k in ('count', 'before', 'remaining', 'nominal')}
    if (not all(v > 0 for v in values.values())
            or values['count'] + values['remaining'] != values['before']):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton
    payload = dict(match.groupdict(), action='share_transfer_manager_secretary', currency='CHF')
    # Signing is already represented by the existing pipeline event. Do not infer it.
    return [
        _event(*context, 'ownership_changed', 'fr.text.share_transfer_manager_secretary.v1', payload),
        _person_event(*context, 'officer_changed', 'fr.persons.new_associate_manager_secretary.v1',
                      match['buyer'], place=match['place'], role='gérante secrétaire',
                      extra={'action': 'appointed', 'origin': match['origin']}),
        _person_event(*context, 'officer_changed', 'fr.persons.transfer_seller_president.v1',
                      match['seller'], role='président', extra={'action': 'appointed'}),
    ], ''
