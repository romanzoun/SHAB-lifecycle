from __future__ import annotations

import re
from datetime import datetime

from .parser78 import _IT_AUDIT_WAIVER_CON_DECLARATION
from .parser253 import _event
from .parser267 import COUNT, DATE, MONEY, NAME


def extract_parser446_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete evidenced variants without consuming legacy audit clauses."""
    context = publication_id, published_at, org_uid, plz, canton
    if language == 'it':
        if _IT_AUDIT_WAIVER_CON_DECLARATION.search(text.strip()):
            return [], text
        m = re.fullmatch(rf'Con dichiarazione del (?P<date>{DATE}), la società non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata\.?', text.strip())
        if m:
            try:
                date = datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat()
            except ValueError:
                return [], text
            return [_event(*context, 'audit_requirement_changed', 'it.text.audit_waiver_comma_declaration.v1', {'kind': 'limited_audit_waiver', 'action': 'granted', 'date': date})], ''
    if language != 'fr':
        return [], text
    m = re.fullmatch(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associé-gérant (?P<name>{NAME}) est titulaire de (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non (?P=count) parts de CHF (?P<previous_nominal>{MONEY}) comme publié\)\.?", text.strip())
    if m:
        try:
            for key in ('entry_date', 'notice_date'):
                datetime.strptime(m[key], '%d.%m.%Y')
        except ValueError:
            return [], text
        return [_event(*context, 'capital_changed', 'fr.text.associate_manager_part_nominal_corrected.v1', {**m.groupdict(), 'kind': 'social_parts', 'action': 'corrected', 'correction': True, 'count': int(m['count'].replace("'", '')), 'currency': 'CHF'})], ''
    m = re.fullmatch(r"Nouveu but: (?P<purpose>acquisition, propriété, gestion et vente d'action; Emission, échange et distribution de jetons\. Acquisition, administration et vente de participations dans toutes entreprises commerciales, industrielles ou financières)\.?", text.strip())
    if m:
        return [_event(*context, 'purpose_changed', 'fr.text.purpose_nouveu_typo.v1', {'purpose': m['purpose']})], ''
    return [], text
