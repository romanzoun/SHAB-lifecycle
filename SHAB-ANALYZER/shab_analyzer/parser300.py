from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY

UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser300_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; preserve unsupported input."""
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

    def event(rule, action, m):
        return _event(*context, 'organization_changed', rule, {'action': action, **m.groupdict()})

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    m = match(rf'Das (?P<court>{NAME}) hat mit Entscheid vom (?P<decision_date>{DATE}) die Wiedereintragung der am (?P<deletion_date>{DATE}) gelöschten Gesellschaft in das Handelsregister angeordnet, (?P<name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), als Liquidator eingesetzt und folgende Adresse als Liquidationsdomizil bestimmt: (?P<address>c/o [^;]+?, [^;]+?, \d{{4}} {NAME})', 'de')
    if m:
        rule = 'de.text.reinstatement_liquidator_domicile.v1'
        return [event(rule, 'organization_reinstated', m), person(rule, m['name'], place=m['place'], role='Liquidator', extra={'origin': m['origin']})], ''

    m = match(rf"(?P<name1>{NAME}), (?P<name2>{NAME}) ne sont plus associés ni gérants; leurs pouvoirs sont radiés; leurs (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) ont été cédées à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante pour (?P=count) parts de CHF (?P=nominal), avec signature individuelle", 'fr')
    if m:
        rule = 'fr.persons.associate_managers_transfer.v1'
        return [person(rule, m[k], role='associé, gérant', signing='ohne Unterschrift', extra={'action': 'removed'}) for k in ('name1', 'name2')] + [person(rule, m['name'], place=m['place'], role='associée-gérante', signing='Einzelunterschrift', extra={k: m[k] for k in ('origin', 'count', 'nominal')})], ''

    m = match(rf"Les pouvoirs d'(?P<name1>{NAME}) et (?P<name2>{NAME}) sont radiés", 'fr')
    if m:
        rule = 'fr.persons.two_powers_removed.v1'
        return [person(rule, m[k], signing='ohne Unterschrift', extra={'action': 'powers_removed'}) for k in ('name1', 'name2')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le contrat d'apport date du (?P<contract_date>{DATE}) et non pas du (?P<previous_date>{DATE})", 'fr')
    if m:
        return [event('fr.text.contribution_contract_date_corrected.v1', 'contribution_contract_date_corrected', m)], ''

    months = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12}
    written_date = r'\d{1,2} (?:' + '|'.join(months) + r') \d{4}'
    m = match(rf"Par décision rendue le (?P<decision>{written_date}), le président du (?P<court>{NAME}) a prolongé de six mois le sursis concordataire définitif accordé à la société, soit jusqu'au (?P<deadline>{written_date})", 'fr')
    if m:
        try:
            dates = {}
            for key in ('decision', 'deadline'):
                day, month, year = m[key].split()
                dates[key + '_date'] = datetime(int(year), months[month], int(day)).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        e = event('fr.text.definitive_moratorium_extended_six_months.v1', 'definitive_moratorium_extended', m)
        e.payload.update(dates, months=6)
        return [e], ''

    m = match(rf'Bei der nachfolgenden Mutation wurde der bisherige Wohnort von (?P<given>{NAME}) (?P<surname>[^ ,;]+) nicht publiziert\. Der Eintrag müsste wie folgt lauten: (?P=surname), (?P=given), von (?P<origin>{NAME}), in (?P<place>{NAME}), Präsident des Vorstandes, Liquidator, mit Einzelunterschrift \[bisher: in (?P<previous_place>{NAME}), Präsident des Vorstandes, mit Einzelunterschrift \(nicht bisher: Präsident des Vorstandes, mit Einzelunterschrift\]', 'de')
    if m:
        return [person('de.persons.liquidator_previous_residence_corrected.v1', m['surname'] + ', ' + m['given'], place=m['place'], role='Präsident des Vorstandes, Liquidator', signing='Einzelunterschrift', extra={k: m[k] for k in ('origin', 'previous_place')})], ''

    clause = rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte {{kind}} Kapitalerhöhung abgeändert gemäss näherer Umschreibung in den Statuten\.'
    def capital(kind, prefix):
        return clause.replace('{kind}', kind).replace('(?P<', '(?P<' + prefix + '_')
    pattern = capital('genehmigte', 'authorized') + r' \. ' + capital('bedingte', 'conditional') + r' \. '
    for i, kind in enumerate(('bedingte', 'bedingte', 'genehmigte')):
        pattern += r'\[gestrichen: ' + capital(kind, f'deleted{i}') + r'\]' + (r'\. ' if i < 2 else '')
    m = match(pattern, 'de')
    if m:
        return [event('de.text.capital_provisions_changed_deleted.v1', 'capital_provisions_changed', m)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<contract_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) die Betriebssparte (?P<division>{NAME}) mit Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine', 'de')
    if m:
        e = event('de.text.business_division_transfer_no_consideration.v1', 'asset_transfer', m)
        e.payload['consideration'] = 'keine'
        return [e], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est associé avec (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non (?P=count) parts de CHF (?P<previous_nominal>{MONEY}) comme publié\)", 'fr')
    if m:
        return [person('fr.persons.associate_share_nominal_corrected.v1', m['name'], role='associé', extra={k: v for k, v in m.groupdict().items() if k != 'name'})], ''

    m = match(rf"Fatti particolari: \. Conferimento in natura e assunzione di beni: la società assume un veicolo (?P<asset>{NAME}), contro attribuzione di (?P<count>{COUNT}) quote sociali da CHF (?P<nominal>{MONEY})\. L'importo di CHF (?P<claim>{MONEY}) è iscritto a bilancio quale credito verso la società\. Contratto: (?P<contract_date>{DATE})", 'it')
    if m:
        return [event('it.text.vehicle_contribution_claim.v1', 'contribution_in_kind', m)], ''

    m = match(rf"(?P<previous1>{NAME}) \((?P<uid1>{UID})\) et (?P<previous2>{NAME}) \((?P<uid2>{UID})\), lesquelles ne sont plus associées, cèdent leurs (?P<previous_count>{COUNT}) parts respectives de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée avec (?P<count>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m:
        if int(m['previous_count'].replace("'", '')) * 2 != int(m['count'].replace("'", '')):
            return [], leftover
        return [event('fr.text.two_corporate_associates_share_transfer.v1', 'share_transfer', m)], ''

    m = match(rf"Nouveau numéro d'identification du siège principal: (?P<head_office_uid>{UID}) \[précédemment: Numéro d'identification du siège principal: (?P<previous_uid>CH-\d{{3}}-\d{{7}}-\d)\]", 'fr')
    if m:
        return [event('fr.text.head_office_uid_changed.v1', 'head_office_uid_changed', m)], ''

    return [], leftover
