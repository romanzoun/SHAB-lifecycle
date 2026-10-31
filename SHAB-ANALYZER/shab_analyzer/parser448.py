from __future__ import annotations

import re

from .parser85 import _FR_MANAGER_APPOINTED_PROXY_REVOKED
from .parser95 import _FR_SHARE_TRANSFER_AND_PRESIDENCY
from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, NAME


LEGACY = (_FR_MANAGER_APPOINTED_PROXY_REVOKED, _FR_SHARE_TRANSFER_AND_PRESIDENCY)


def extract_parser448_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only the evidenced complete variants; keep historical ownership."""
    if language != 'fr' or any(p.search(text.strip()) for p in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def person(m, name, role, **extra):
        return _person_event(*context, 'officer_changed', 'fr.persons.' + extra.pop('rule') + '.v1', name, role=role, extra=extra)

    m = re.fullmatch(rf"(?P<name>{NAME}) a été nommé membre et président du conseil d'administration ; sa procuration est radiée\.?", text.strip())
    if m:
        return [person(m, m['name'], "membre et président du conseil d'administration", rule='board_president_appointed_proxy_revoked', action='appointed', procuration_revoked=True)], ''

    base = rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), '
    unsigned = base + rf'de et à (?P<place>{NAME}), nouvelle associée sans signature, avec (?P=count) parts de CHF (?P=nominal); (?P=seller) reste titutlaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
    president = base + rf'de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant avec (?P=count) parts de CHF (?P=nominal)\. (?P=seller), qui reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal), est nommé président'
    for pattern, variant in ((unsigned, 'unsigned_associate_holding_typo'), (president, 'associate_manager_transfer_period_presidency')):
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if not m:
            continue
        values = {key: int(m[key].replace("'", '')) for key in ('count', 'before', 'remaining')}
        if values['count'] <= 0 or values['remaining'] < 0 or values['before'] != values['count'] + values['remaining']:
            return [], text
        events = [_event(*context, 'ownership_changed', 'fr.text.' + variant + '.v1', {**m.groupdict(), 'action': 'partial_transfer', 'currency': 'CHF'})]
        buyer = _person_event(*context, 'officer_changed', 'fr.persons.' + variant + '.v1', m['buyer'], place=m['place'], role='associée' if variant == 'unsigned_associate_holding_typo' else 'associé-gérant', signing='ohne Zeichnungsberechtigung' if variant == 'unsigned_associate_holding_typo' else None, extra={'action': 'appointed'})
        events.append(buyer)
        if variant == 'associate_manager_transfer_period_presidency':
            events.append(person(m, m['seller'], 'président', rule='transfer_seller_president_appointed', action='appointed'))
        return events, ''
    return [], text
