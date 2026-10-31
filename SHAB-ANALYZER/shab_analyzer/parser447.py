from __future__ import annotations

import re
from datetime import datetime

from .parser93 import _FR_LIQUIDATOR_APPOINTED_AFTER_MOVE
from .parser106 import _FR_MANAGER_APPOINTED_WITH_DOMICILE
from .parser222 import _DE_NATIONALITY_CORRECTED
from .parser253 import _event, _person_event
from .parser267 import COUNT, DATE, NAME


LEGACY = (_FR_LIQUIDATOR_APPOINTED_AFTER_MOVE,
          _FR_MANAGER_APPOINTED_WITH_DOMICILE, _DE_NATIONALITY_CORRECTED)


def extract_parser447_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete evidenced clauses, preserving historical rule ownership."""
    if any(pattern.search(text.strip()) for pattern in LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language not in ((lang,) if isinstance(lang, str) else lang):
            return None
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    m = match(rf'(?P<name>{NAME}), qui est maintenant à (?P<place>{NAME}), est nommé administrateur', 'fr')
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.persons.administrator_appointed_after_move.v1', m['name'], place=m['place'], role='administrateur', extra={'action': 'appointed'})], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat die Aufsichtsbehörde das Mandat des Sachwalters (?P<name>Dr\. Dr\. {NAME}) um weitere drei Monate bis (?P<until_date>{DATE}) verlängert\. \[bisher: Mit Verfügung vom (?P<previous_date>{DATE}) hat die Aufsichtsbehörde (?P=name) als Sachwalter mit Einzelunterschrift eingesetzt\.\]', 'de')
    if m:
        payload = {**m.groupdict(), 'action': 'appointment_extended', 'authority': 'Aufsichtsbehörde', 'duration_months': 3}
        for key in ('decision_date', 'until_date', 'previous_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        return [_person_event(*context, 'officer_changed', 'de.persons.foundation_custodian_mandate_extended.v1', m['name'], role='Sachwalter', signing='Einzelunterschrift', extra=payload)], ''

    m = match(rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt berichtigt: (?P<name>{NAME}), Gesellschafter, Kollektivunterschrift zu zweien, (?P<nationality>britischer Staatsangehöriger) \(und nicht (?P<previous_nationality>Grossbritannischerstaatsangeöriger)\)', ('de', 'fr'))
    if m:
        payload = {**m.groupdict(), 'scope': 'officer_nationality', 'action': 'corrected', 'from': m['previous_nationality'], 'to': m['nationality'], 'role': 'Gesellschafter', 'signing': 'Kollektivunterschrift zu zweien'}
        for key in ('entry_date', 'notice_date'):
            payload[key] = datetime.strptime(payload[key], '%d.%m.%Y').date().isoformat()
        return [_event(*context, 'publication_corrected', 'de.text.associate_nationality_typo_corrected.v1', payload)], ''
    return [], text
