from __future__ import annotations

import re
from datetime import datetime

from .parser101 import _FR_ASSET_TRANSFER_DUPLICATE_CURRENCY
from .parser253 import _event
from .parser267 import COUNT, DATE, MONEY, NAME, UID


def extract_parser445_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses, leaving legacy transfers alone."""
    if language != 'fr' or _FR_ASSET_TRANSFER_DUPLICATE_CURRENCY.search(text):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d-%m-%Y' if '-' in value else '%d.%m.%Y')
            except ValueError:
                return None
        return m

    m = match(rf'Transfert de patrimoine: selon contrat du (?P<date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à (?P<recipient>{NAME}), à (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: CHF (?P<consideration>{MONEY})')
    if m:
        payload = {**m.groupdict(), 'date': datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat(), 'currency': 'CHF'}
        return [_event(*context, 'assets_transferred', 'fr.text.asset_transfer_cash_without_comma.v1', payload)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>\d{{2}}-\d{{2}}-\d{{4}}) est modifiée en ce sens que la société en nom collectif a été transformée en société à responsabilité limitée conformément au projet de transformation du (?P<plan_date>{DATE}) et bilan au (?P<balance_date>{DATE}), présentant des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), contre attribution aux associés de (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non (?P=count) parts de CHF (?P<previous_nominal>{MONEY})\)")
    if m:
        payload = {**m.groupdict(), 'action': 'transformed_and_corrected', 'correction': True, 'from_legal_form': 'société en nom collectif', 'to_legal_form': 'société à responsabilité limitée', 'currency': 'CHF', 'social_parts_issued': int(m['count'].replace("'", '')), 'social_part_nominal': m['nominal'], 'transformation_plan_date': datetime.strptime(m['plan_date'], '%d.%m.%Y').date().isoformat(), 'balance_sheet_date': datetime.strptime(m['balance_date'], '%d.%m.%Y').date().isoformat()}
        return [_event(*context, 'legal_form_changed', 'fr.text.partnership_to_llc_nominal_corrected.v1', payload)], ''

    m = match(rf'Les (?P<count>{COUNT}) actions au porteur de CHF (?P<nominal>{MONEY}) sont converties en (?P=count) actions nominatives de CHF (?P=nominal)')
    if m:
        return [_event(*context, 'capital_changed', 'fr.text.bearer_to_registered_same_count_nominal.v1', {'kind': 'share_class_conversion', 'action': 'converted', 'count': int(m['count'].replace("'", '')), 'nominal': m['nominal'], 'previous_kind': 'au porteur', 'share_kind': 'nominatives', 'currency': 'CHF'})], ''
    return [], text
