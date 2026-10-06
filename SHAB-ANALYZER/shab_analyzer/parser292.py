from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser292_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed clauses; preserve unsupported text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for k, v in m.groupdict().items():
                    if k.endswith('date'):
                        datetime.strptime(v, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"Liquidateurs: (?P<name1>{NAME}) et (?P<name2>{NAME}), membres du conseil d'administration, lesquels continuent de signer individuellement")
    if m:
        return [person('fr.persons.board_liquidators_individual.v1', m[k], role="membre du conseil d'administration liquidateur", signing='Einzelunterschrift') for k in ('name1', 'name2')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Änderung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<previous_date>{DATE}) das bedingte Aktienkapital gemäss näherer Umschreibung in den Statuten erhöht\.\]', 'de')
    if m and m['decision_date'] != m['previous_date'] and datetime.strptime(m['previous_date'], '%d.%m.%Y') < datetime.strptime(m['decision_date'], '%d.%m.%Y'):
        return [event('de.text.conditional_capital_amended.v1', action='conditional_capital_amended', **m.groupdict())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée à propos de la traduction allemande de la raison de commerce; la raison de commerce a pour teneur: (?P<company>[^\[\];]+?) \[(?P<translation>[^\[\]]+)\] et non (?P=company) \((?P<previous_translation>[^()]+)\)")
    if m and m['translation'] != m['previous_translation']:
        return [event('fr.text.branch_german_name_corrected.v1', action='company_translation_corrected', **m.groupdict())], ''

    # German clauses in the French-labelled fixture. Require every member of
    # the four-person structure, including previous roles/signing restrictions.
    m = match(rf'Eingetragene Personen neu oder mutierend: (?P<name1>{NAME}, {NAME}), von (?P<origin1>{NAME}), in (?P<place1>{NAME}), Präsident des Verwaltungsrates, mit Kollektivunterschrift zu zweien \[bisher: Mitglied, mit Kollektivunterschrift zu zweien mit dem Präsidenten\]; (?P<name2>{NAME}, {NAME}), von (?P<origin2>{NAME}), in (?P<place2>{NAME}), Mitglied des Verwaltungsrates, mit Kollektivunterschrift zu zweien \[bisher: (?P<previous_name2>{NAME}, {NAME}), Mitglied, mit Kollektivunterschrift zu zweien mit dem Präsidenten\]; (?P<name3>{NAME}, {NAME}), von (?P<origin3>{NAME}), in (?P<place3>{NAME}), Mitglied des Verwaltungsrates, ohne Zeichnungsberechtigung \[bisher: Präsident, mit Kollektivunterschrift zu zweien\]; (?P<name4>{NAME}, {NAME}), von (?P<origin4>{NAME}, {NAME} und {NAME}), in (?P<place4>{NAME}), mit Kollektivunterschrift zu zweien \[bisher: ohne eingetragene Funktion, mit Kollektivunterschrift zu zweien mit dem Präsidenten\]')
    if m:
        rule = 'de.persons.board_roles_signing_name_corrected.v1'
        roles = ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Mitglied des Verwaltungsrates', None]
        events = []
        for i, role in enumerate(roles, 1):
            extra = {'origin': m[f'origin{i}'], 'previous_role': ['Mitglied', 'Mitglied', 'Präsident', 'ohne eingetragene Funktion'][i-1], 'previous_signing': 'Kollektivunterschrift zu zweien' + ('' if i == 3 else ' mit dem Präsidenten')}
            if i == 2:
                extra['previous_name'] = m['previous_name2']
            events.append(person(rule, m[f'name{i}'], place=m[f'place{i}'], role=role, signing='ohne Zeichnungsberechtigung' if i == 3 else 'Kollektivunterschrift zu zweien', extra=extra))
        return events, ''

    m = match(rf'(?P<second_date>{DATE})\. Die Generalversammlung hat mit Beschluss vom (?P<first_date>{DATE})/(?P=second_date) eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt', 'de')
    if m and datetime.strptime(m['first_date'], '%d.%m.%Y') <= datetime.strptime(m['second_date'], '%d.%m.%Y'):
        if re.search(r'Statutenänderung: ' + re.escape(m['first_date']) + r'\. ' + re.escape(leftover) + r'\.?$', source_text):
            return [event('de.text.authorized_capital_two_decision_dates.v1', action='authorized_capital_introduced', **m.groupdict())], ''

    m = match(r'Bei der weiteren Adresse ist der Stiftungsname "(?P<foundation>[^"\n]+)" wegzulassen', 'de')
    if m:
        return [event('de.text.additional_address_foundation_name_removed.v1', action='additional_address_name_removed', **m.groupdict())], ''

    m = match(rf"L'associé (?P<name>{NAME}) a été nommé gérant et président avec signature individuelle")
    if m:
        return [person('fr.persons.associate_manager_president_appointed.v1', m['name'], role='gérant président', signing='Einzelunterschrift', extra={'associate': True})], ''

    m = match(rf'Procuration collective à deux, toutefois pas entre eux ni avec (?P<excluded>{NAME}, {NAME}, {NAME} et {NAME}) est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        excluded = re.split(r', | et ', m['excluded'])
        return [person('fr.persons.procuration_mutual_named_restrictions.v1', m[f'name{i}'], place=m[f'place{i}'], signing='Kollektivprokura zu zweien', extra={'origin': m[f'origin{i}'], 'excluded_signing_partners': excluded + [m[f'name{3-i}']]}) for i in (1, 2)], ''

    m = match(rf'(?P<transferor>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature, titulaire de (?P=transferred) parts de CHF (?P=nominal)\. (?P=transferor) a désormais (?P<remaining>{COUNT}) parts de CHF (?P=nominal); est nommé gérant président avec signature individuelle')
    if m and number(m['transferred']) > 0 and number(m['remaining']) > 0 and number(m['nominal']) > 0 and number(m['transferred']) + number(m['remaining']) == number(m['before']):
        rule = 'fr.persons.partial_share_transfer_manager_president.v1'
        return [event(rule, action='share_transfer', currency='CHF', **m.groupdict()), person(rule, m['recipient'], role='associé', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'shares': m['transferred'], 'nominal': m['nominal'], 'origin': m['origin']}), person(rule, m['transferor'], role='gérant président', signing='Einzelunterschrift', extra={'shares': m['remaining'], 'nominal': m['nominal']})], ''

    # German text in the Italian-labelled fixture; retain corporate register ID.
    m = match(rf'Eingetragene Personen neu oder mutierend: (?P<company>{NAME}) \((?P<register_id>\d+)\), in (?P<company_place>{NAME}), Gesellschafterin, mit (?P<count>{COUNT}) Stammanteilen zu je CHF (?P<nominal>{MONEY}); (?P<name1>{NAME}, {NAME}), britischer Staatsangehöriger, in (?P<place1>{NAME}), Vorsitzender der Geschäftsführung, mit Einzelunterschrift \[bisher: Gesellschafter und Vorsitzender der Geschäftsführung, mit Einzelunterschrift, mit (?P<previous_count1>{COUNT}) Stammanteilen zu je CHF (?P=nominal)\]; (?P<name2>{NAME}, {NAME}), britischer Staatsangehöriger, in (?P<place2>{NAME}), Geschäftsführer, mit Einzelunterschrift \[bisher: Gesellschafter und Geschäftsführer, mit Einzelunterschrift, mit (?P<previous_count2>{COUNT}) Stammanteilen zu je CHF (?P=nominal)\]', 'it')
    if m and min(number(m[k]) for k in ('count', 'nominal', 'previous_count1', 'previous_count2')) > 0 and number(m['count']) == number(m['previous_count1']) + number(m['previous_count2']):
        rule = 'de.persons.corporate_associate_managers_shares_removed.v1'
        return [event(rule, action='corporate_associate_recorded', company=m['company'], register_id=m['register_id'], place=m['company_place'], shares=m['count'], nominal=m['nominal'], currency='CHF')] + [person(rule, m[f'name{i}'], place=m[f'place{i}'], role='Vorsitzender der Geschäftsführung' if i == 1 else 'Geschäftsführer', signing='Einzelunterschrift', extra={'previous_shares': m[f'previous_count{i}'], 'nominal': m['nominal'], 'associate': False, 'nationality': 'britischer Staatsangehöriger'}) for i in (1, 2)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<reference>\d+/\d+)\) est rectifiée en ce sens que la raison sociale de l'associée est: (?P<company>[^();]+) \(et non: (?P<previous_company>[^()]+)\)")
    if m and m['company'] != m['previous_company']:
        return [event('fr.text.associate_company_name_corrected.v1', action='associate_company_name_corrected', **m.groupdict())], ''

    if language == 'de' and leftover in ('Nebenzweckänderung', 'Nebenzweckänderung.'):
        return [event('de.text.secondary_purpose_changed.v1', action='secondary_purpose_changed')], ''

    return [], leftover
