from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser296_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, sample-backed clauses; retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, event_type='officer_changed', **payload):
        return _person_event(*context, event_type, rule, name, **payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"L'inscription n°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital-social est de CHF (?P<capital>{MONEY}), divisé en (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), et non de (?P<previous_count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m and number(m['capital']) == number(m['count']) * number(m['nominal']):
        return [event('fr.text.share_count_capital_corrected.v1', action='capital_corrected', **m.groupdict())], ''

    m = match(rf'\[gestrichen: (?P<place>[^()]+) \((?P<uid>CHE-\d{{3}} \.\d{{3}}\.\d{{3}})\)\]', 'de')
    if m and 'Zweigniederlassung neu:' in source_text and m[0] in source_text:
        return [event('de.text.deleted_branch_uid_spacing.v1', action='branch_removed', uid_normalized=m['uid'].replace(' ', ''), **m.groupdict())], ''

    # The supplied XML labels this German clause as French.
    m = match(rf'Ausgeschiedene Personen und erloschene Unterschriften: (?P<name>[^;]+?), (?P<origin>{NAME}) Staatsangehöriger, in (?P<place>[^;]+?), mit Kollektivunterschrift zu zweien', 'fr')
    if m:
        return [person('de.persons.departure_fr_xml.v1', m['name'], 'officer_removed', place=m['place'], extra={'origin': m['origin'], 'previous_signing': 'Kollektivunterschrift zu zweien'})], ''

    m = match(r'Die Gesellschaft ist ohne Rechtsdomizil\. \[bisher: Die Gesellschaft ist nun ohne Verwaltungsorgan und ohne Rechtsdomizil\.\]', 'de')
    if m:
        return [event('de.text.no_domicile_previous_no_board.v1', action='no_legal_domicile', previous_no_board=True)], ''

    # French text with a German XML language code, as supplied.
    m = match(rf'(?P<name>{NAME}) est désormais à (?P<place>{NAME})', 'de')
    if m:
        return [person('fr.persons.residence_changed_de_xml.v1', m['name'], place=m['place'])], ''

    m = match(rf'Aufgrund unvollständiger Beleglage ist die Wahl von (?P<name>{NAME}), (?P<origin>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), zum Vizepräsidenten des Verwaltungsrates ohne Zeichnungsberechtigung nicht erstellt\. Die Eintragungen sind irrtümlich erfolgt und werden deshalb in allen Teilen widerrufen', 'de')
    if m:
        return [person('de.persons.unproven_board_election_revoked.v1', m['name'], 'officer_removed', role='Vizepräsident des Verwaltungsrates', place=m['place'], extra={'origin': m['origin'], 'action': 'election_revoked', 'previous_signing': 'ohne Zeichnungsberechtigung'})], ''

    m = match(rf'Les pouvoifrs de (?P<name>{NAME}) sont radiés', 'fr')
    if m:
        return [person('fr.persons.powers_revoked_typo.v1', m['name'], 'officer_removed', extra={'action': 'powers_revoked'})], ''

    m = match(rf'Con decreto della (?P<court>{NAME}) del (?P<decision_date>{DATE}), la moratoria definitiva a scopo di concordato è stata prorogata di ulteriori due mesi', 'it')
    if m:
        return [event('it.text.definitive_moratorium_extended_two_months.v1', action='moratorium_extended', months=2, **m.groupdict())], ''

    m = match(rf'Das Einzelunternehmen wurde mit TR-Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}), publiziert im SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}), irrtümlich gelöscht\. Der genannte Löschungseintrag wird deshalb widerrufen\. \[bisher: Der Geschäftsbetrieb hat aufgehört\. Das Einzelunternehmen wird von Amtes wegen gelöscht\.\]', 'de')
    if m and datetime.strptime(m['entry_date'], '%d.%m.%Y') <= datetime.strptime(m['notice_date'], '%d.%m.%Y'):
        return [event('de.text.sole_proprietorship_deletion_revoked.v1', action='deletion_revoked', **m.groupdict())], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die "(?P<recipient>[^";]+)" \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: Lebenslängliche und kautionsfreie Nutzniessung an Parzelle (?P<parcel>{COUNT}), Grundbuch (?P<land_register>{NAME}) und ein unverzinsliches und sicherstellungsfreies Darlehen zu Gunsten von (?P<beneficiaries>{NAME}) im Betrag von CHF (?P<loan>{MONEY})', 'de')
    if m:
        return [event('de.text.asset_transfer_usufruct_loan.v1', action='asset_transfer', consideration_kind='usufruct_and_loan', **m.groupdict())], ''

    m = match(rf"\[Nella rubrica dei fatti particolari, i dati personali del socio (?P<partner>{NAME}) sono stati erroneamente pubblicati\.\] Fatti particolari corretti: Conferimento in natura e assunzione di beni: la società assume attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) della società semplice per l'edificazione delle part\. RFD (?P<parcel1>{COUNT}) e RFD (?P<parcel2>{COUNT}) (?P<place>{NAME}) composta da (?P=partner), (?P<partner2>{NAME}), (?P<partner3>{NAME}) \(non iscritta a registro di commercio\) sulla base del bilancio al (?P<balance_date>{DATE}), contro attribuzione di (?P<shares>{COUNT}) azioni nominative da CHF (?P<nominal>{MONEY})\. L'importo di CHF (?P<credit>{MONEY}) verrà iscritto a bilancio quale credito verso la società\. Contratto: (?P<agreement_date>{DATE})", 'it')
    if m and number(m['assets']) - number(m['liabilities']) == number(m['shares']) * number(m['nominal']) + number(m['credit']) and datetime.strptime(m['balance_date'], '%d.%m.%Y') <= datetime.strptime(m['agreement_date'], '%d.%m.%Y'):
        return [event('it.text.contribution_partnership_corrected.v1', action='contribution_corrected', **m.groupdict())], ''

    component = rf'(?P<name>[^,;]+), à (?P<place>{NAME}), \((?P<uid>{UID})\), présentant des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}|{COUNT}\x27\d{{2}})'
    m = match(rf"Fusion: Selon contrat de fusion du (?P<agreement_date>{DATE}) et bilan au (?P<balance_date>{DATE}), reprise des actifs et passifs de la (?P<components>.+), soit un actif net total de CHF (?P<net_assets>{MONEY})\. Dès lors que le capital-actions des sociétés qui fusionnent est détenu par le même actionnaire, sauf le capital de la société (?P<subsidiary>{NAME}) qui est détenu par la société reprenante, la fusion ne donne pas lieu à une augmentation de capital, ni à une attribution d'actions\. Nouvel administrateur: (?P<director>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), ITA, avec signature collective à deux", 'fr')
    if m and source_text.endswith(m[0].rstrip('.') + '.'):
        parts = re.split(r', (?:et de |de la )', m['components'])
        companies = [re.fullmatch(component, part) for part in parts]
        if len(companies) == 9 and all(companies):
            rows = [c.groupdict() for c in companies]
            # Preserve the printed amount. Normalize its final apostrophe only
            # when the complete nine-company balance proves the interpretation.
            for row in rows:
                value = row['liabilities']
                row['liabilities_normalized'] = re.sub(r"'(\d{2})$", r'.\1', value)
            total = sum((number(row['assets']) - number(row['liabilities_normalized']) for row in rows), Decimal(0))
            if total == number(m['net_assets']) and rows[-1]['name'] == m['subsidiary'] and datetime.strptime(m['balance_date'], '%d.%m.%Y') <= datetime.strptime(m['agreement_date'], '%d.%m.%Y'):
                rule = 'fr.text.nine_company_merger_balance_typo.v1'
                return [event(rule, action='merger', companies=rows, agreement_date=m['agreement_date'], balance_date=m['balance_date'], net_assets=m['net_assets'], subsidiary=m['subsidiary'], capital_increase=False, shares_allocated=False), person(rule, m['director'], role='administrateur', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'], 'country': 'ITA'})], ''

    return [], leftover
