from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
COUNT = r"\d+(?:'\d{3})*"
NAME = r'[^,.;]+?'
MONEY = r"\d+(?:'\d{3})*(?:\.\d+)?"


def extract_parser266_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed clauses; verify facts consumed upstream."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date') and value:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def source(pattern, m):
        s = re.search(pattern + r'\.?$', source_text) if m else None
        return s if s and all(value is None or s[key].strip() == value.strip() for key, value in m.groupdict().items()) else None

    def event(event_type, rule, **payload):
        return _event(*context, event_type, rule, payload)

    def person(rule, name, *, kind='officer_changed', **kwargs):
        return _person_event(*context, kind, rule, name, **kwargs)

    m = match(r'Uebersetzungen der Bezeichnung neu: (?P<translations>(?:\([^()]+\) ){3}\([^()]+\))')
    if m:
        return [event('company_name_changed', 'de.text.company_name_translations.v1', translations=re.findall(r'\(([^()]+)\)', m['translations']))], ''

    pattern = rf"Nouvelle gérante: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), présidente"
    m = match(pattern + r'(?:, avec signature individuelle)?')
    if source(pattern + r', avec signature individuelle', m):
        return [person('fr.persons.new_manager_president.v1', m['name'], place=m['place'], role='gérante présidente', signing='Einzelunterschrift', extra={'origin': m['origin'], 'action': 'appointed'})], ''

    m = match(rf'Signature collective à deux, sauf avec (?P<excluded>{NAME}), a été conférée à (?P<name>{NAME}), nommée sous-directrice; sa procuration est radiée')
    if m:
        return [person('fr.persons.deputy_director_restricted_signing.v1', m['name'], role='sous-directrice', signing='Kollektivunterschrift zu zweien', extra={'signing_restriction': 'not_with', 'excluded_partner': m['excluded'], 'procuration_removed': True})], ''

    pattern = rf"(?P<removed>{NAME}) n'est plus administrateur; sa signature est radiée\. Nouvel administrateur"
    tail = rf' avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME}): (?P<name>{NAME}), de et à (?P<place>{NAME})'
    m = match(pattern + r'(?: avec signature collective à deux)?' + tail)
    if source(pattern + r' avec signature collective à deux' + tail, m):
        rule = 'fr.persons.administrator_replaced_restricted_signing.v1'
        return [person(rule, m['removed'], kind='officer_removed', role='administrateur', extra={'signing_removed': True}), person(rule, m['name'], place=m['place'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'origin': m['place'], 'signing_restriction': 'only_with', 'authorized_partners': [m['partner1'], m['partner2']]})], ''

    pattern = rf"(?P<removed>{NAME}), dont la signature est radiée, reste membre du conseil de fondation\. Nouveau membre du conseil de fondation"
    tail = rf" toutefois avec le trésorier ou le secrétaire: (?P<name>[^,;]+), de (?P<origin>{NAME}), à (?P<place>[^.;]+)"
    m = match(pattern + r'(?: avec signature collective à deux,)?' + tail)
    if source(pattern + r' avec signature collective à deux,' + tail, m):
        rule = 'fr.persons.foundation_member_restricted_signing.v1'
        return [person(rule, m['removed'], role='membre du conseil de fondation', signing='ohne Zeichnungsberechtigung', extra={'signing_removed': True}), person(rule, m['name'], place=m['place'], role='membre du conseil de fondation', signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'], 'signing_restriction': 'only_with', 'authorized_partner_roles': ['trésorier', 'secrétaire']})], ''

    pattern = rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est directrice"
    tail = r' \(et non pas (?P<previous_name>[^()]+)\)'
    m = match(pattern + r'(?: avec signature collective à deux)?' + tail)
    if source(pattern + r' avec signature collective à deux' + tail, m):
        return [person('fr.persons.director_name_corrected.v1', m['name'], role='directrice', signing='Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'action': 'corrected'})], ''

    pattern = rf"L'administrateur (?P<name>{NAME}) est élu liquidateur"
    tail = rf" Les (?P<count>\d+) actions nominatives de CHF (?P<nominal>{MONEY}), formant l'entier du capital-actions, ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)"
    m = match(pattern + r'(?: avec signature individuelle\.)?' + tail)
    if source(pattern + r' avec signature individuelle\.' + tail, m) and int(m['count']) > 0:
        return [person('fr.persons.administrator_liquidator.v1', m['name'], role='liquidateur', signing='Einzelunterschrift', extra={'previous_role': 'administrateur'}), event('capital_changed', 'fr.text.share_transfer_restriction_removed.v1', shares_count=int(m['count']), shares_nominal=m['nominal'], currency='CHF', transfer_restricted=False, legal_basis='art. 685a, al. 3 CO')], ''

    pattern = rf"Conversion des (?P<converted>{COUNT}) actions privilégiées quant aux dividendes en actions ordinaires\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives"
    m = match(pattern + r'(?:, liées selon statuts)?')
    if source(pattern + r', liées selon statuts\. Nouveaux statuts du ' + DATE, m):
        number = lambda key: Decimal(m[key].replace("'", ''))
        if 0 < number('converted') <= number('count') and number('count') * number('nominal') == number('capital'):
            return [event('capital_changed', 'fr.text.preferred_shares_converted.v1', **m.groupdict(), currency='CHF', action='preferred_to_ordinary', transfer_restricted=True)], ''

    m = match(r'Eingetragene Person geändert: (?P<previous_name>[^()]+) \((?P<previous_uid>CH-[\d-]+)\), Revisionsorgan, firmiert neu: (?P<name>[^()]+) \((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\), Revisionsorgan')
    if m:
        return [person('de.persons.auditor_renamed.v1', m['name'], role='Revisionsorgan', extra={**m.groupdict(), 'action': 'renamed'})], ''

    m = match(rf",? ?Sede principale a: Sede principale: (?P<place>{NAME}) \((?P<country>[A-Z])\)\. Nuovo capitale sociale/responsabilità della sede principale: EUR (?P<capital>{MONEY})\.-- suddiviso in (?P<count>{COUNT}) azioni da EUR (?P<nominal>{MONEY})\.--, interamente liberato \[finora: Nuovo capitale sociale/responsabilità della sede principale: EUR (?P<previous_capital>{MONEY})\.-- suddiviso in (?P<previous_count>{COUNT}) azioni da EUR (?P<previous_nominal>{MONEY})\.--, interamente liberato\]")
    if m:
        number = lambda key: Decimal(m[key].replace("'", ''))
        if all(number(prefix + 'count') > 0 and number(prefix + 'nominal') > 0 and number(prefix + 'count') * number(prefix + 'nominal') == number(prefix + 'capital') for prefix in ['', 'previous_']):
            return [event('capital_changed', 'it.text.foreign_head_office_capital_changed.v1', **m.groupdict(), currency='EUR', kind='head_office_capital', fully_paid=True)], ''

    rights = r'mit Rechten auf Anteil am Bilanzgewinn und am Liquidationserlös sowie auf den Bezug neuer Aktien und Partizipationsscheine gemäss Statuten'
    pattern = rf'Die Generalversammlung hat mit Beschluss vom (?P<date>{DATE}) die mit Beschluss vom (?P<previous_date>{DATE}) eingeführte genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P=previous_date) eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in Art\. 3a der Statuten beschlossen\.\]\. '
    tail = rf'\[bisher: (?P<previous_count>{COUNT}) Genussscheine, {rights}\.\]'
    m = match(pattern + tail)
    s = source(pattern + rf'Genussscheine neu: (?P<count>{COUNT}) Genussscheine, {rights}\. ' + tail, m)
    if s and int(s['count'].replace("'", '')) > 0 and int(s['previous_count'].replace("'", '')) > 0:
        return [event('capital_changed', 'de.text.authorized_participation_capital_changed.v1', date=m['date'], previous_date=m['previous_date'], action='authorization_changed'), event('capital_changed', 'de.text.profit_participation_certificates_changed.v1', count=s['count'], previous_count=s['previous_count'], rights='profit_liquidation_and_subscription')], ''

    item = rf'(?P<count>{MONEY}) Ansprüche der Klasse (?P<class>[12]) an der Anlagegruppe "(?P<group>[^"\n]+)" mit einem Nettoinventarwert von CHF (?P<nav>{MONEY}) pro Anspruch'
    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\)\. Gegenleistung: (?P<consideration>.+), jeweils mit Wirkung per (?P<effective_date>{DATE})')
    if m:
        parts = re.split(r', | und ', m['consideration'])
        entries = [re.fullmatch(item, part) for part in parts]
        if len(entries) == 4 and all(e and Decimal(e['count'].replace("'", '')) > 0 and Decimal(e['nav'].replace("'", '')) > 0 for e in entries):
            return [event('assets_transferred', 'de.text.assets_transferred_investment_claims.v1', **m.groupdict(), currency='CHF', claims=[e.groupdict() for e in entries])], ''

    return [], leftover
