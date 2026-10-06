from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser297_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, retaining unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + (re.escape(suffix) if suffix else '') + r'\.?', leftover)
        if not m:
            return None
        if suffix and not source_text.endswith(leftover.rstrip('.') + '.'):
            return None
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

    m = match(rf'\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<decision_date>{DATE}) eingeführte genehmigte Erhöhung des Partizipationskapitals infolge Zeitablaufs\.\] \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P=decision_date) eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        return [event('de.text.authorized_participation_capital_expired.v1', action='authorized_capital_expired', **m.groupdict())], ''

    m = match(r'Die Inhaberaktien sind gemäss Art\. 622 OR zulässig, weil die Gesellschaft Beteiligungspapiere an einer Börse kotiert hat', 'de')
    if m:
        return [event('de.text.bearer_shares_listed_securities.v1', action='bearer_shares_permitted', legal_basis='Art. 622 OR', reason='listed_securities')], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que l'organe de publication est la Feuille officielle suisse du commerce et les communications aux associés s'effectuent par courrier écrit, courriel ou téléfax", 'fr')
    if m:
        return [event('fr.text.publication_communications_completed.v1', action='publication_communications_completed', publication_medium='Feuille officielle suisse du commerce', communication_methods=['courrier écrit', 'courriel', 'téléfax'], **m.groupdict())], ''

    m = match(r'Unter Ziffer\.8\.2 Genussscheine wurde irrtümlich das Wort SHAB eingetragen\. Das Wort SHAB ist unter der Rubrik Genussscheine zu streichen', 'de')
    if m:
        return [event('de.text.profit_certificates_word_corrected.v1', action='profit_certificates_corrected', removed_word='SHAB', section='8.2')], ''

    m = match(rf'(?P<name>{NAME}), dont le prénom exact est (?P<given_names>{NAME}), est maintenant de (?P<origin>{NAME}), à (?P<place>{NAME})', 'fr')
    if m:
        return [person('fr.persons.given_name_origin_residence_corrected.v1', m['name'], place=m['place'], extra={'action': 'person_details_corrected', 'given_names': m['given_names'], 'origin': m['origin']})], ''

    # The French clause is labelled German in the supplied XML.
    m = match(rf"(?P<name1>{NAME}) est nommé président; (?P<name2>{NAME}), qui n'est plus président, reste administrateur; tous deux continuent à signer collectivement à deux", 'de')
    if m:
        rule = 'fr.persons.board_roles_de_xml.v1'
        return [person(rule, m['name1'], role='président', signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'président'})], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf das Einzelunternehmen (?P<recipient>[^,;]+), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('de.text.assets_transfer_sole_proprietorship.v1', action='asset_transfer', **m.groupdict())], ''

    m = match(rf'(?P<name>{NAME}), maintenant de (?P<origin>{NAME}), est nommée liquidatrice', 'fr', ' avec signature individuelle')
    if m:
        return [person('fr.persons.liquidator_origin_changed.v1', m['name'], role='liquidatrice', signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(rf"Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<name1>{NAME}) est maintenant associé pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal), et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est nouvelle associée pour (?P=transferred) parts de CHF (?P=nominal)\. Gérants: les associés (?P=name1), nommé président, et (?P=name2), tous deux", 'fr', ' avec signature individuelle')
    if m:
        rule = 'fr.persons.share_transfer_two_managers.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['name1'], role='associé, gérant président', signing='Einzelunterschrift', extra={'shares': m['remaining'], 'nominal': m['nominal']}), person(rule, m['name2'], role='associée, gérante', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': m['transferred'], 'nominal': m['nominal']})], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice>{COUNT})\) est rectifiée en ce sens que le membre du conseil (?P<name>{NAME}) signe collectivement à deux \(et non pas sans signature\)", 'fr')
    if m and datetime.strptime(m['entry_date'], '%d.%m.%Y') <= datetime.strptime(m['notice_date'], '%d.%m.%Y'):
        return [person('fr.persons.board_signing_corrected.v1', m['name'], role='membre du conseil', signing='Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'previous_signing': 'sans signature'})], ''

    m = match(rf"(?P<removed>{NAME}) n'est plus gérante; ses pouvoirs sont radiés\. Gérant: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})", 'de', ' avec signature individuelle')
    if m:
        rule = 'fr.persons.manager_replaced_de_xml.v1'
        return [person(rule, m['removed'], 'officer_removed', role='gérante'), person(rule, m['name'], role='gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(rf'Nouvelles actions: (?P<count1>{COUNT}) actions nominatives de CHF (?P<nominal1>{MONEY}) et (?P<count2>{COUNT}) actions nominatives de CHF (?P<nominal2>{MONEY}) \(privilégiées quant au droit de vote\) \[non: (?P=count1) actions nominatives de CHF (?P=nominal1) et (?P=count2) actions nominatives de CHF (?P=nominal2)\]', 'fr')
    if m:
        return [event('fr.text.share_voting_privilege_corrected.v1', action='share_rights_corrected', privileged_class=2, **m.groupdict())], ''

    return [], leftover
