from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser69 import _DE_COMPANY_REINSTATED_FOR_LIQUIDATION
from .parser189 import _FR_AUTHORIZED_CAPITAL_REPLACED

NAME = r'[^,;.]+?'
FRENCH_DATE = r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'
MONTHS = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre')


def extract_parser376_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete sample-backed variants; leave earlier rule families untouched."""
    leftover = text.strip()
    legacy = {'de': (_DE_COMPANY_REINSTATED_FOR_LIQUIDATION,),
              'fr': (_FR_AUTHORIZED_CAPITAL_REPLACED,)}
    if any(pattern.fullmatch(leftover) for pattern in legacy.get(language, ())):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        if re.fullmatch(DATE, value):
                            datetime.strptime(value, '%d.%m.%Y')
                        else:
                            day, month, year = value.split()
                            datetime(int(year), MONTHS.index(month) + 1, int(day))
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Mit dem Tagesregister Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) und mit dem SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}) wurde (?P<name>{NAME}, {NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}) versehentlich als mutiert aufgeführt\. Der Eintrag bleibt jedoch unverändert', 'de')
    if m:
        return [event('foreign_officer_erroneous_mutation_corrected', m)], ''

    m = match(rf'Es wird die Eintragung der ausgeschiedenen Revisionsstelle (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\) widerrufen, da die Löschung dieser Revisionsstelle bereits mit TR-Eintragung (?P<entry>{COUNT}) von (?P<entry_date>{DATE}) erfolgte', 'de')
    if m:
        return [event('duplicate_auditor_departure_revoked', m)], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird aufgrund des Urteils des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter', 'de')
    if m:
        return [event('judgment_liquidation_registration_reinstated', m, 'status_changed', action_detail='reinstated_for_liquidation')], ''

    m = match(rf"Rectificati: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que les statuts ont été modifiés le (?P<statutes_date>{FRENCH_DATE}) \(et non le (?P<previous_statutes_date>{FRENCH_DATE}) comme publié\)", 'fr')
    if m:
        return [event('statutes_date_typo_notice_corrected', m)], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. 159 Abs\. 5 HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen, nachdem der Einzelrichter mit Verfügung vom (?P<decision_date>{DATE}) die Wiedereröffnung eines summarischen Verfahrens angeordnet hat', 'de')
    if m:
        return [event('single_judge_summary_bankruptcy_reinstated', m, 'status_changed', dissolved_by_bankruptcy=True)], ''

    m = match(rf'(?P<name1>{NAME}), qui est nommé président, et (?P<name2>{NAME}), qui est est nommée administratrice et dont la procuration est éteinte, sont maintenant à (?P<place>{NAME})', 'fr')
    if m:
        return [person('president_and_female_director_residence_changed', m, m['name1'], m['place'], 'président'), person('president_and_female_director_residence_changed', m, m['name2'], m['place'], 'administratrice', procuration_revoked=True)], ''

    m = match(rf'Gemäss Verwaltungsratserklärung vom (?P<declaration_date>{DATE}) untersteht die Gesellschaft keiner ordentlichen Revision und verzichtet auf eine eingeschränkte Revision', 'de')
    if m:
        return [event('board_declaration_audit_waived', m, 'audit_requirement_changed', ordinary_audit=False, limited_audit_waived=True)], ''

    m = match(rf"L'assemblée générale a supprimé une clause statutaire relative à une augmentation autorisée du capital \(selon décision du (?P<authorization_date>{FRENCH_DATE})\) par décision du (?P<removal_date>{FRENCH_DATE})\. Pour les détails, voir les statuts\. L'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital par décision du (?P<introduction_date>{FRENCH_DATE})\. Pour les détails, voir les statuts", 'fr')
    if m:
        return [event('authorized_capital_replaced_two_detail_notices', m, 'capital_changed')], ''

    address = r'[^,;.]+, \d{4} [^,;.]+?'
    m = match(rf'\[bisher: Weitere Adresse: (?P<previous_address1>{address})\.\]\. Weitere Adresse: (?P<address1>{address})\. Weitere Adresse: (?P<address2>{address})\. Weitere Adresse: (?P<address3>{address})\. \[bisher: Weitere Adresse: (?P<previous_address2>{address})\.\]', 'de')
    if m:
        return [event('three_additional_addresses_two_previous', m, 'address_changed')], ''

    m = match(rf'Le nom exact de (?P<previous_name>{NAME}) est (?P<name>{NAME})', 'fr')
    if m:
        return [person('person_exact_name_corrected', m, m['name'])], ''

    dissolution = rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company>{NAME})'
    shares = rf'(?P<shares>{COUNT} Stammanteile zu CHF {MONEY}, {COUNT} Stammanteil zu CHF {MONEY})'
    m = match(dissolution + rf'\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, {shares}, Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P=shares), Geschäftsführer, Liquidator, Einzelunterschrift, nun in (?P<place>{NAME}) \(Gemeindefusion\)', 'de')
    if m:
        return [event('mixed_shares_liquidation_municipality_merger', m, 'status_changed'), person('mixed_shares_liquidation_municipality_merger', m, m['name'], m['place'], 'Gesellschafter, Geschäftsführer, Liquidator', 'Einzelunterschrift')], ''

    m = match(rf'Vollständige Adresse: (?P<address>{address})\. ' + dissolution + rf"\.\. Eingetragene Personen geändert: (?P<name1>{NAME}), Gesellschafter, (?P<count1>{COUNT}) Stammanteile zu CHF (?P<nominal1>{MONEY}), Kollektivprokura zu zweien, neu Gesellschafter, ohne Unterschrift; (?P<name2>{NAME}), Gesellschafter, (?P<count2>{COUNT}) Stammanteile zu CHF (?P<nominal2>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, Geschäftsführer, Liquidator, Einzelunterschrift", 'fr')
    if m:
        return [event('german_liquidation_french_publication_two_officers', m, 'status_changed'), event('german_liquidation_french_publication_address', m, 'address_changed'), person('german_liquidation_french_publication_two_officers', m, m['name1'], role='Gesellschafter', signing='ohne Zeichnungsberechtigung'), person('german_liquidation_french_publication_two_officers', m, m['name2'], role='Gesellschafter, Geschäftsführer, Liquidator', signing='Einzelunterschrift')], ''
    return [], leftover
