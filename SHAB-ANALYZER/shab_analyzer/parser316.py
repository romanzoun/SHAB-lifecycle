from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser316_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; retain unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def amount(m, key):
        return Decimal(m[key].replace("'", ''))

    def event(rule, m, **extra):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict(), **extra})

    def person(rule, m, key, role, signing=None, place_key=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, rule, m[key], place=m[place_key] if place_key else None, role=role, signing=signing, extra={**m.groupdict(), **extra})

    m = match(rf'Umwandlung: Die Gesellschaft mit beschränkter Haftung hat mit Beschluss der Generalversammlung vom (?P<capital_date>{DATE}) ihr Stammkapital auf CHF (?P<capital>{MONEY}) erhöht\. Mit Beschluss der Generalversammlung vom (?P<resolution_date>{DATE}) wird die Gesellschaft mit beschränkter Haftung gemäss Umwandlungsplan vom (?P<plan_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) in eine Aktiengesellschaft umgewandelt\. Die Gesellschafter erhalten für ihre bisherigen Stammanteile (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY})', 'de')
    if m:
        if amount(m, 'capital') != amount(m, 'count') * amount(m, 'nominal'):
            return [], leftover
        return [event('de.text.capital_increased_gmbh_converted_ag.v1', m, previous_legal_form='GmbH', legal_form='AG')], ''

    m = match(rf'(?P<name>{NAME}), associé-gérant président, cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), gérante, nouvelle associée avec (?P=transferred_count) parts de CHF (?P=nominal)\. (?P=name) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)', 'fr')
    if m:
        if amount(m, 'transferred_count') + amount(m, 'remaining_count') != amount(m, 'previous_count'):
            return [], leftover
        rule = 'fr.text.partial_shares_transferred_existing_manager.v1'
        return [event(rule, m), person(rule, m, 'recipient', 'Gesellschafterin und Geschäftsführerin')], ''

    m = match(rf'(?P<name1>{NAME}), des (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>{NAME}), sont membres du conseil de fondation avec signature collective à deux', 'fr')
    if m:
        rule = 'fr.text.two_foundation_members_foreign_residence.v1'
        return [person(rule, m, f'name{i}', 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', place_key=f'place{i}') for i in (1, 2)], ''

    m = match(rf"Administration : (?P<name1>{NAME}), maintenant domicilié à (?P<place1>{NAME}), nommé président, (?P<name2>{NAME}) jusqu'ici directeur, nommé secrétaire, et (?P<name3>{NAME}), jusqu'ici directeur, qui tous continuent à signer individuellement", 'fr')
    if m:
        rule = 'fr.text.administrators_president_secretary_signing_continued.v1'
        return [person(rule, m, 'name1', 'Präsident des Verwaltungsrates', 'Einzelunterschrift', 'place1'), person(rule, m, 'name2', 'Sekretär des Verwaltungsrates', 'Einzelunterschrift'), person(rule, m, 'name3', 'Mitglied des Verwaltungsrates', 'Einzelunterschrift')], ''

    # This supplied French-language publication contains a German clause.
    m = match(rf'Neue Firma: (?P<name>{NAME}) in Liquidation\. Mit Entscheid vom (?P<decision_date>{DATE}) hat der Präsident des (?P<court>{NAME}), in (?P<place>{NAME}), mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<hour>\d{{2}})\.(?P<minute>\d{{2}}) Uhr, über die Gesellschaft den Konkurs eröffnet', 'fr')
    if m:
        if int(m['hour']) > 23 or int(m['minute']) > 59:
            return [], leftover
        return [event('de.text.bankruptcy_opened_french_publication.v1', m, dissolved_by_bankruptcy=True, legal_name=m['name'] + ' in Liquidation')], ''

    # This supplied German-language publication contains Italian person sections.
    italian_name = r'[^,;]+?'
    m = match(rf'Persone dimissionarie e firme cancellate: (?P<surname1>{italian_name}), (?P<given1>{italian_name}), da (?P<origin1>{italian_name}), in (?P<place1>{italian_name}), direttore, con firma collettiva a due; (?P<surname2>{italian_name}), Dott\. (?P<given2>{italian_name}), da (?P<origin2>{italian_name}), in (?P<place2>{italian_name}), con procura collettiva a due\. Nuove persone iscritte o modifiche: (?P<surname3>{italian_name}), (?P<given3>{italian_name}), da (?P<origin3>{italian_name}), in (?P<place3>{italian_name}), delegato, direttore, con firma collettiva a due \[finora: direttore, con firma collettiva a due\]; (?P<surname4>{italian_name}), (?P<given4>{italian_name}), da (?P<origin4>{italian_name}), in (?P<place4>{italian_name}), membro, direttore, con firma collettiva a due \[finora: delegato e direttore, con firma collettiva a due\]; (?P<surname5>{italian_name}), (?P<given5>{italian_name}), da (?P<origin5>{italian_name}), in (?P<place5>{italian_name}), direttore, con firma collettiva a due; (?P<surname6>{italian_name}), (?P<given6>{italian_name}), da (?P<origin6>{italian_name}), in (?P<place6>{italian_name}), direttrice, con firma collettiva a due; (?P<surname7>{italian_name}), (?P<given7>{italian_name}), da (?P<origin7>{italian_name}), in (?P<place7>{italian_name}), vice-direttore, con firma collettiva a due', 'de')
    if m:
        rule = 'it.text.officers_removed_changed_german_publication.v1'
        roles = ['Direktor', 'Prokurist', 'Delegierter des Verwaltungsrates und Direktor', 'Mitglied des Verwaltungsrates und Direktor', 'Direktor', 'Direktorin', 'Vizedirektor']
        events = []
        for i, role in enumerate(roles, 1):
            removed = i <= 2
            events.append(_person_event(*context, 'officer_removed' if removed else 'officer_changed', rule, m[f'surname{i}'] + ', ' + m[f'given{i}'], place=m[f'place{i}'], role=role, signing='ohne Zeichnungsberechtigung' if removed else 'Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'removed': removed}))
        return events, ''

    m = match(rf"L'associée-gérante (?P<name>{NAME}) détient désormais (?P<recipient_count>{COUNT}) parts de CHf (?P<nominal>{MONEY}) par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P=nominal) (?P<transferor>[^;\n]+?) \((?P<registration_number>B\d+)\), associée désormais pour (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        if amount(m, 'recipient_count') < amount(m, 'transferred_count'):
            return [], leftover
        return [event('fr.text.shares_transferred_missing_preposition.v1', m)], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>{NAME}), sont membres du comité, avec signature collective à trois, avec le président et un vice-président ou avec les deux vice-présidents', 'fr')
    if m:
        rule = 'fr.text.committee_members_joint_three_restricted.v1'
        signing = 'Kollektivunterschrift zu dreien mit dem Präsidenten und einem Vizepräsidenten oder mit den beiden Vizepräsidenten'
        return [person(rule, m, f'name{i}', 'Mitglied des Vorstandes', signing, f'place{i}') for i in (1, 2)], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(p\.0/(?P<notice_id>\d+)\) est rectifiée en ce sens que l'associée-gérante (?P<name>{NAME}) a la signature collective à deux \(non individuelle\)", 'fr')
    if m:
        rule = 'fr.text.associate_manager_signing_corrected_notice.v1'
        return [person(rule, m, 'name', 'Gesellschafterin und Geschäftsführerin', 'Kollektivunterschrift zu zweien', previous_signing='Einzelunterschrift')], ''

    m = match(rf'Aktien neu: (?P<count>{COUNT}) Inhaberaktien zu CHF (?P<nominal>{MONEY}) \[bisher: (?P=count) Namenaktien zu CHF (?P=nominal)\]\. Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) angeordnet, den vor der Eintragung der Beschlüsse der Generalversammlung vom (?P<resolution_date>{DATE}) \(SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE})\) geltenden Zustand wieder in das Handelsregister einzutragen', 'de')
    if m:
        return [event('de.text.bearer_shares_previous_register_state_restored.v1', m, share_type='Inhaberaktien', previous_share_type='Namenaktien')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\.0/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) continue à signer individuellement \(et non pas collectivement à deux\)", 'fr')
    if m:
        rule = 'fr.text.individual_signing_continued_corrected_notice.v1'
        return [person(rule, m, 'name', None, 'Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), avec signature collective à deux, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>{NAME}), lequel n'exerce pas la signature sociale, sont membres du conseil d'administration", 'fr')
    if m:
        rule = 'fr.text.two_administrators_second_unsigned.v1'
        return [person(rule, m, 'name1', 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', 'place1'), person(rule, m, 'name2', 'Mitglied des Verwaltungsrates', 'ohne Zeichnungsberechtigung', 'place2')], ''

    return [], leftover
