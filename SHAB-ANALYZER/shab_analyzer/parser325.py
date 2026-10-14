from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser325_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append bounded, sample-supported residual events, preserving legacy payloads."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date') and value is not None:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, suffix='', role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'+suffix], place=m.groupdict().get('place'), role=role, signing=signing, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient_name>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<recipient_place>{NAME})\. Gegenleistung: Forderung von CHF (?P<consideration>{MONEY})\. Zudem werden bei der Sachübernehmerin CHF (?P<reserves>{MONEY}) den Reserven zugewiesen', 'de')
    if m:
        return [event('asset_transfer_receivable_and_reserves', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a supprimé la clause statutaire relative à l'augmentation autorisée du capital-actions introduite par décision du (?P<authorized_date>{DATE}) et l'a remplacée par une nouvelle clause d'augmentation autorisée; pour les détails, voir les statuts\. Par décision du (?P=decision_date), l'assemblée générale a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-actions introduite par décision du (?P<conditional_date>{DATE}); pour les détails, voir les statuts")
    if m:
        return [event('authorized_and_conditional_capital_clauses_changed', m, authorized_clause_replaced=True, conditional_clause_changed=True)], ''

    m = match(rf'Signature collective à deux, sans autre restriction, a été conférée à (?P<name>{NAME}), ses pouvoirs sont modifiés en ce sens')
    if m:
        return [person('collective_signing_restrictions_removed', m, signing='Kollektivunterschrift zu zweien', other_restrictions_removed=True)], ''

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom de l'administratrice est (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('administrator_name_corrected', m, role='Verwaltungsrätin')], ''

    m = match(rf"L'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'administrateur (?P<name>{NAME}) est domicilié à (?P<place>{NAME})")
    if m:
        return [person('administrator_residence_corrected', m, role='Verwaltungsrat')], ''

    m = match(r"La clause statutaire relative à la reprise de biens envisagée à la constitution et réalisée ultérieurement est supprimée conformément à l'art\. (?P<article>628, al\. 4, CO)")
    if m:
        return [event('historical_asset_acquisition_clause_removed', m, previous_clause_removed=True)], ''

    m = match(rf"L'inscription N° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom de famille du gérant unique est (?P<surname>{NAME}) \(et non pas (?P<previous_surname>{NAME})\)")
    if m:
        # The sample supplies a surname only: do not invent a full person identity.
        return [event('sole_manager_surname_corrected', m, 'officer_changed')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée par la radiation du titre de secrétaire générale de (?P<name>{NAME}), non soumis à inscription")
    if m:
        return [person('unregistrable_secretary_title_removed', m, removed_title='secrétaire générale')], ''

    m = match(rf'eingetragenen Einzelunternehmens (?P<transferor_name>{NAME}), in (?P<transferor_place>{NAME}) \((?P<transferor_uid>{UID})\), gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}), wofür (?P<shares>\d+) Namenaktien zu CHF (?P<nominal>{MONEY}) ausgegeben und CHF (?P<receivable>{MONEY}) als Forderung gutgeschrieben werden', 'de')
    if m:
        clause = 'Sacheinlage/Sachübernahme: Die Gesellschaft übernimmt bei der Gründung das Geschäft des im Handelsregister ' + leftover + '.'
        if 'Qualifizierte Tatbestände neu: ' + clause + ' [nicht: Sacheinlage/Sachübernahme:' in source_text:
            return [event('formation_contribution_corrected', m, 'capital_changed', currency='CHF', corrected=True)], ''

    # This sample has French XML metadata but an explicitly German merger clause.
    m = match(rf'Fusion: Übernahme der Aktiven und der Passiven der (?P<absorbed_name>{NAME}) \((?P<absorbed_uid>{UID})\), in (?P<absorbed_place>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft sämtliche Stammanteile der übertragenden Gesellschaft hält, findet weder eine Kapitalerhöhung noch ein Aktienzuteilung statt')
    if m:
        return [event('merger_wholly_owned_subsidiary_no_allocation', m, 'company_merged', kind='merger', currency='CHF', capital_increase=False, share_allocation=False)], ''

    m = match(rf'Signature collective à deux est conférée à (?P<name1>{NAME}) et (?P<name2>{NAME}), tous deux de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        return [person('two_persons_collective_signing', m, str(i), signing='Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Mit dem im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Eintrag (?P<entry>\d+/\d{{4}}) fehlte der Auflösungsbeschluss, welcher hiermit nachgetragen wird', 'de')
    if m:
        return [event('dissolution_resolution_reference_added', m, supplementary_entry=True)], ''

    return [], leftover
