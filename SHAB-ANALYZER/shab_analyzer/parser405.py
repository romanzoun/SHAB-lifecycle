from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from . import parser100, parser112, parser132, parser134, parser140, parser165, parser175, parser177, parser186, parser191, parser197, parser205, parser214

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser100, parser112, parser132, parser134, parser140, parser165, parser175, parser177, parser186, parser191, parser197, parser205, parser214)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser405_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed residual variants, preserving prior events and rule ownership."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', evidence=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if evidence:
            source = re.search(evidence, source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
        try:
            for date in re.findall(DATE, m[0]):
                datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) demeure gérant")
    if m:
        return [person('manager_retained_entry_corrected', m, m['name'], 'gérant', corrected=True, role_continued=True)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que Monsieur (?P<name>{NAME}) signe individuellement")
    if m:
        return [person('individual_signing_entry_supplemented', m, m['name'], signing='Einzelunterschrift', supplemented=True)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est domiciliée à (?P<place>{NAME}), (?P<country>[A-Z])")
    if m:
        return [person('foreign_domicile_entry_corrected_short', m, m['name'], place=m['place'], country=m['country'], corrected=True)], ''

    m = match(rf'Le gérant (?P<seller>{NAME}) a cédé ses (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l\'associé-gérant (?P<buyer>{NAME}) qui possède désormais (?P<received>{COUNT}) parts de CHF (?P=nominal)')
    if m and Decimal(m['received'].replace("'", '')) >= Decimal(m['transferred'].replace("'", '')):
        return [event('manager_all_shares_transfer_existing_associate', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}), président et (?P<name2>{NAME}), nommée vice-présidente, signent désormais individuellement\. (?P<name3>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), a été nommé secrétaire hors conseil, sans signature sociale')
    if m:
        return [person('board_pair_individual_signing_external_secretary', m, m['name1'], 'administrateur président', 'Einzelunterschrift'), person('board_pair_individual_signing_external_secretary', m, m['name2'], 'administratrice vice-présidente', 'Einzelunterschrift'), person('external_secretary_without_signing', m, m['name3'], 'secrétaire hors conseil', 'ohne Unterschrift', m['place'])], ''

    m = match(rf'Die Bestimmung über die Sacheinlage bei der Gründung vom (?P<foundation_date>{DATE}) ist aus den Statuten gestrichen worden', 'de')
    if m:
        return [event('foundation_contribution_clause_removed', m, clause_removed=True)], ''

    pattern = r'\((?P<german_name>[^()\n]+ in Liquidation)\) \((?P<italian_name>[^()\n]+ in liquidazione)\) \((?P<english_name>[^()\n]+ in liquidation)\)'
    m = match(pattern, evidence=r'La liquidation est opérée sous la raison de commerce: [^()\n]+ ' + pattern + r'\.')
    if m:
        return [event('liquidation_name_three_translations', m, 'company_name_changed', translations={lang: m[key] for lang, key in (('de', 'german_name'), ('it', 'italian_name'), ('en', 'english_name'))})], ''

    pattern = rf'eingetragenen Einzelunternehmen (?P<source_name>{NAME}) in (?P<place>{NAME}), (?P<goods>medizinische Geräte, EDV-Geräte inkl\. Software sowie Praxismobiliar) zum Preis von höchstens CHF (?P<maximum_price>{MONEY}) zu übernehmen'
    m = match(pattern, 'de', evidence=rf'Beabsichtigte Sachübernahme: In nachträglicher Offenlegung zur Gründung vom {DATE} , beabsichtigt die Gesellschaft von dem nicht im Handelsregister ' + pattern + r'\.')
    if m:
        return [event('intended_asset_purchase_unregistered_sole_trader', m, 'statutes_changed', kind='intended_asset_acquisition', currency='CHF', intended=True, maximum=True)], ''

    m = match(rf"Par arrêt du (?P<order_date>{DATE}), le (?P<court>Tribunal cantonal de Fribourg) a accordé l'effet suspensif au recours interjeté le (?P<appeal_date>{DATE}) contre la décision du (?P<decision_date>{DATE}) \((?P<legal_basis>art\. 159, al\. 1 let\.b ORC)\)")
    if m:
        return [event('appeal_suspensive_effect_orc_159_1_b', m, suspensive_effect=True)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}), page (?P<notice_ref>\d+/\d+)\) est rectifiée comme suit: L'assemblée générale du (?P<decision_date>{DATE}) a modifié la clause statutaire relative à l'augmentation conditionnelle du capital-actions prise par décision du (?P<previous_date>{DATE}); pour les détails, voir les statuts \((?P<article>art\. 3b al\. 2)\)")
    if m:
        return [event('conditional_capital_clause_entry_corrected', m, 'publication_corrected', kind='conditional_capital_clause')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la signature collective à deux conférée à (?P<name1>{NAME}) et (?P<name2>{NAME}) ainsi que la procuration collective à deux conférée à (?P<name3>{NAME}) ne sont pas limitées à l'établissement principal")
    if m:
        return [person('signing_main_establishment_restriction_corrected', m, m[f'name{i}'], signing='Kollektivprokura zu zweien' if i == 3 else 'Kollektivunterschrift zu zweien', corrected=True, limited_to_main_establishment=False) for i in (1, 2, 3)], ''

    m = match(rf"Con verbale di udienza del (?P<decision_date>{DATE}) della (?P<court>Pretura del Distretto di Mendrisio-Sud) la nomina di (?P<name>{NAME}) quale commissario è prorogata fino al (?P<until_date>{DATE})\. \[finora: Con decisione del (?P<previous_date>{DATE}), la (?P=court) ha prorogato la nomina del commissario (?P=name) fino al (?P<previous_until_date>{DATE})\.\]\. \[radiati: Con decisione supercautelare del (?P<interim_date>{DATE}), la (?P=court) ha prorogato la nomina del commissario (?P=name) fino all'emanazione della decisione cautelare\.\]\. \[radiati: Con decisione cautelare del (?P<confirmation_date>{DATE}), la (?P=court) ha confermato la nomina del commissario (?P=name) fino all'emanazione della decisione di merito\. \]", 'it')
    if m and datetime.strptime(m['until_date'], '%d.%m.%Y') >= datetime.strptime(m['decision_date'], '%d.%m.%Y'):
        return [person('commissioner_appointment_extended_hearing', m, m['name'], 'commissario', until_date=m['until_date'])], ''
    return [], text
