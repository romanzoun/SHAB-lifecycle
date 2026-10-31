from __future__ import annotations

import re
from datetime import datetime

from .parser55 import _IT_FUSION_SAME_OWNER
from .parser235 import _FR_TWO_FOREIGN_BOARD_MEMBERS
from .parser253 import _IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE, _event
from .parser267 import DATE, MONEY, NAME, UID

LEGACY = (_IT_FUSION_SAME_OWNER, _IT_MERGER_COMMON_SHAREHOLDER_NO_CAPITAL_INCREASE,
          _FR_TWO_FOREIGN_BOARD_MEMBERS)


def extract_parser451_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete evidenced variants; retain historical rule ownership."""
    if any(pattern.search(text.strip()) for pattern in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        return re.fullmatch(pattern + r'\.?', text.strip()) if language == lang else None

    m = match(r'La société est autorisée à avoir des actions au porteur car elles sont toutes cotées en bourse \(art\. 622 al\. 1bis CO\)', 'fr')
    if m:
        return [_event(*context, 'capital_changed', 'fr.text.bearer_shares_all_listed_permitted.v1', {'action': 'bearer_shares_permitted', 'legal_basis': 'art. 622 al. 1bis CO', 'reason': 'listed_securities', 'all_shares_listed': True})], ''

    m = match(rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale azionario e del capitale sociale delle due società è detenuta dallo stesso azionista, la fusione avviene dunque senza aumento del capitale e senza attribuzione di azioni', 'it')
    if m:
        payload = dict(m.groupdict())
        try:
            for key in ('agreement_date', 'balance_date'):
                payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        except ValueError:
            return [], text
        return [_event(*context, 'company_merged', 'it.text.fusion_same_owner_share_and_social_capital.v1', {**payload, 'kind': 'absorption', 'same_shareholder': True, 'capital_increase': False, 'share_allocation': False})], ''
    return [], text
