from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser280_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses; preserve unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
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

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def num(value):
        return Decimal(value.replace("'", ''))

    reference = rf"l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\)"
    m = match(rf"Rectificatif: {reference} est rectifiée en ce sens que l'administratrice présidente se nomme (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}), comme publié\)")
    if m:
        return [person('fr.persons.president_name_corrected_notice.v1', m['name'], role='administratrice présidente', extra={**m.groupdict(), 'correction': True})], ''

    m = match(rf"Complément: {reference} est complétée en ce sens que l'administratrice (?P<name>{NAME}) est présidente")
    if m:
        return [person('fr.persons.president_supplement_notice.v1', m['name'], role='administratrice présidente', extra={**m.groupdict(), 'supplement': True})], ''

    m = match(rf"La commandite de l'associée (?P<name>{NAME}) \((?P<associate_uid>{UID})\) a été réduite de CHF (?P<previous>{MONEY}) à CHF (?P<amount>{MONEY})")
    if m and num(m['previous']) > num(m['amount']) > 0:
        return [person('fr.persons.commandite_reduced.v1', m['name'], role='associée commanditaire', extra=m.groupdict())], ''

    m = match(rf"\[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) ein genehmigtes Kapital gemäss näherer Umschreibung in den Statuten eingeführt\.\]", 'de')
    if m:
        return [event('de.text.authorized_capital_clause_removed.v1', action='authorized_capital_clause_removed', **m.groupdict())], ''

    m = match(rf"L'associé-gérant (?P<name1>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P=transferred) parts de CHF (?P=nominal), gérant avec signature individuelle\. (?P=name1), qui est élu président des gérants et continue à signer individuellement, reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and num(m['previous']) - num(m['transferred']) == num(m['remaining']) > 0 and num(m['transferred']) > 0 and num(m['nominal']) > 0:
        rule = 'fr.persons.transfer_manager_president.v1'
        return [person(rule, m['name1'], role='associé-gérant président', signing='Einzelunterschrift', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé-gérant', signing='Einzelunterschrift', place=m['place'], extra={'origin': m['origin'], 'shares': int(num(m['transferred'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Nouvel associé commanditaire: (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>E), avec une commandite de CHF (?P<amount>{MONEY}), lequel signe collectivement à deux")
    if m and num(m['amount']) > 0:
        return [person('fr.persons.new_commanditaire_collective.v1', m['name'], role='associé commanditaire', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'], 'country': m['country'], 'amount': m['amount']})], ''

    m = match(rf"Transfert de patrimoine: Selon contrat du (?P<contract_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), à (?P<recipient>{NAME}), à (?P<place>{NAME})\. Contre-prestation: CHF (?P<consideration>{MONEY})")
    if m and all(num(m[k]) >= 0 for k in ('assets', 'liabilities', 'consideration')):
        return [event('fr.text.asset_transfer_third_party_liabilities.v1', action='asset_transfer', **m.groupdict())], ''

    m = match(rf"Les associés (?P<name1>{NAME}) et (?P<name2>{NAME}) ont chacun cédé (?P<each>{COUNT}) de leurs (?P<previous>{COUNT}) parts sociales respectives de CHF (?P<nominal>{MONEY}) à (?P<name3>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>{COUNT}) parts sociales de CHF (?P=nominal)\. Gérants: (?P=name1), président, (?P=name2) et (?P=name3), lesquels signent individuellement")
    if m and num(m['previous']) > num(m['each']) > 0 and num(m['received']) == 2*num(m['each']) and num(m['nominal']) > 0:
        rule = 'fr.persons.two_transfers_three_managers.v1'
        return [person(rule, m['name'+str(i)], role='associé-gérant président' if i == 1 else 'associé-gérant', signing='Einzelunterschrift', extra={'shares': int(num(m['previous'])-num(m['each'])), 'transferred_shares': int(num(m['each'])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associé-gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(num(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nouveau membre du conseil d'administration porte le nom de famille (?P<surname>{NAME}) et les prénoms (?P<given_names>[^,.;()]+)\)")
    if m:
        return [person('fr.persons.board_name_corrected_unmatched_parenthesis.v1', m['surname'] + ' ' + m['given_names'], role="membre du conseil d'administration", extra={**m.groupdict(), 'correction': True})], ''

    m = match(rf"(?P<previous_name>{NAME}) porte désormais le prénom (?P<given_name>{NAME}), est maintenant domicilié à (?P<place>{NAME})")
    if m:
        surname, separator, _ = m['previous_name'].partition(' ')
        if separator:
            return [person('fr.persons.given_name_residence_changed.v1', surname + ' ' + m['given_name'], place=m['place'], extra=m.groupdict())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que le gérant (?P<name>{NAME}) est aussi associé pour (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY})")
    if m and num(m['count']) > 0 and num(m['nominal']) > 0:
        return [person('fr.persons.manager_associate_supplement.v1', m['name'], role='associé-gérant', extra={'supplement': True, 'entry': m['entry'], 'entry_date': m['entry_date'], 'shares': int(num(m['count'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Angaben zur Zweigniederlassung neu: Mit Verfügung des (?P<court>Obergerichts des Kantons Aargau) vom (?P<decision_date>{DATE}) wurde das Konkursbegehren am Hauptsitz abgewiesen\. Infolgedessen besteht die Gesellschaft entsprechend den früheren Eintragungen weiter\. \[bisher: Mit Verfügung des Obergerichtes des Kantons Aargau vom (?P<previous_date>{DATE}) ist der Beschwerde gegen die Verfügung des (?P<previous_court>Konkursrichters des Bezirksgerichts Aarau) vom (?P<opening_date>{DATE}) betreffend Konkurseröffnung am Hauptsitz aufschiebende Wirkung zuerkannt worden\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\.\]", 'de')
    if m:
        return [event('de.text.branch_headquarters_bankruptcy_request_rejected.v1', action='headquarters_bankruptcy_request_rejected', **m.groupdict())], ''

    return [], leftover
