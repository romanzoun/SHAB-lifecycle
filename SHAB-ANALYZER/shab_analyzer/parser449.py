from __future__ import annotations

import re
from datetime import datetime

from .parser122 import _FR_ADMIN_DOMICILE_CORRECTION_NOTICE
from .parser142 import _FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL
from .parser224 import _FR_LIMITED_AUDIT_WAIVED
from .parser253 import _event, _person_event
from .parser267 import COUNT, DATE, NAME


LEGACY = (_FR_ADMIN_DOMICILE_CORRECTION_NOTICE,
          _FR_DOMICILE_CORRECTED_NOTICE_PARENTHETICAL, _FR_LIMITED_AUDIT_WAIVED)


def extract_parser449_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete evidenced clauses while preserving historical ownership."""
    if language != 'fr' or any(pattern.search(text.strip()) for pattern in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    m = re.fullmatch(rf'(?P<name1>{NAME}) est nommé président, (?P<name2>{NAME}) est nommé secrétaire, et (?P<name3>{NAME}) est nommé trésorier\.?', text.strip())
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.persons.three_officers_roles_appointed.v1', m[f'name{i}'], role=role, extra={'action': 'appointed'})
                for i, role in enumerate(('président', 'secrétaire', 'trésorier'), 1)], ''

    m = re.fullmatch(rf'Seon déclaration du (?P<date>{DATE}), est renoncé à un contrôle restreint\.?', text.strip())
    if m:
        try:
            date = datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat()
        except ValueError:
            return [], text
        return [_event(*context, 'audit_requirement_changed', 'fr.text.limited_audit_waived_seon_typo.v1', {
            'kind': 'limited_audit_waiver', 'action': 'declared',
            'declaration_date': date, 'limited_audit_waived': True,
        })], ''

    m = re.fullmatch(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>[^(),.;]+?) est à (?P<place>[^(),.;]+? \([A-Z]{{2}}\)) \(et non à (?P<previous_place>[^();]+?) comme publié\)\.?", text.strip())
    if m:
        payload = {**m.groupdict(), 'action': 'domicile_corrected'}
        try:
            for key in ('entry_date', 'notice_date'):
                payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        except ValueError:
            return [], text
        return [_person_event(*context, 'officer_changed', 'fr.persons.domicile_corrected_notice_canton.v1', m['name'], place=m['place'], extra=payload)], ''
    return [], text
