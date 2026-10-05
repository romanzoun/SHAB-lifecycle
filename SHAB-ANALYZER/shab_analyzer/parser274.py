from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser274_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete clauses evidenced by the parser-274 fixtures."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def event(rule, kind='organization_changed', **payload):
        return _event(*context, kind, rule, payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"Jusqu'ici titulaire de (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}), l'associé-gérant (?P<seller>{NAME}) détient (?P<remaining>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred>{COUNT}) parts à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal), lequel n'exerce pas la signature sociale")
    if m and all(number(m[k]) > 0 for k in ('remaining', 'transferred', 'nominal')) and number(m['remaining']) + number(m['transferred']) == number(m['previous']):
        rule = 'fr.persons.manager_transfer_unsigned_associate.v1'
        return [person(rule, m['seller'], role='associé-gérant', extra={'shares': int(number(m['remaining'])), 'previous_shares': int(number(m['previous'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé', place=m['place'], extra={'shares': int(number(m['transferred'])), 'share_nominal': m['nominal'], 'origin': m['origin'], 'without_signature': True})], ''

    m = match(rf"Par arrêt du (?P<order_date>{DATE}), le (?P<court>Tribunal cantonal de Fribourg) a accordé l'effet suspensif au recours interjeté le (?P<appeal_date>{DATE}) contre la décision du (?P<decision_date>{DATE})")
    if m:
        return [event('fr.text.appeal_suspensive_effect.v1', action='suspensive_effect_granted', **m.groupdict())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est recfifiée en ce sens que (?P<name>{NAME}) signe individuellement \(et non pas collectivement à deux\)")
    if m:
        return [person('fr.persons.signing_corrected_typo.v1', m['name'], signing='Einzelunterschrift', extra={'entry': m['entry'], 'entry_date': m['entry_date'], 'previous_signing': 'Kollektivunterschrift zu zweien', 'correction': True})], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici membre secrétaire générale du conseil de fondation, maintenant directrice, continue à signer collectivement à deux")
    if m:
        return [person('fr.persons.foundation_secretary_becomes_director.v1', m['name'], role='directrice', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'membre secrétaire générale du conseil de fondation', 'signing_continued': True})], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) parts de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant et président avec signature collective à deux\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('remaining', 'transferred', 'nominal')) and number(m['remaining']) + number(m['transferred']) == number(m['previous']):
        signing_clause = f"{m['buyer']}, du {m['origin']}, à {m['place']}, nouvel associé-gérant et président avec signature collective à deux."
        if signing_clause in source_text:
            rule = 'fr.persons.manager_transfer_collective_president.v1'
            return [person(rule, m['seller'], role='associé-gérant', extra={'shares': int(number(m['remaining'])), 'previous_shares': int(number(m['previous'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant président', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'shares': int(number(m['transferred'])), 'share_nominal': m['nominal'], 'origin': m['origin']})], ''

    m = match(rf'Die Eidgenössische Finanzmarktaufsicht FINMA hat mit provisorischer Verfügung vom (?P<order_date>{DATE}) die sich aus der superprovisorischen Verfügung vom (?P<previous_date>{DATE}) ergebenden Eintragungen \(TR-Eintrag (?P<entry>{COUNT}) vom (?P<entry_date>{DATE})\) bestätigt')
    if m:
        return [event('de.text.finma_provisional_confirmation.v1', authority='FINMA', action='entries_confirmed', **m.groupdict())], ''

    m = match(r'\{1\. Anmeldung 2\. Unterschriftenmuster 3\. Protokoll der Generalversammlung\]')
    if m:
        return [event('de.text.registration_supporting_documents.v1', documents=['Anmeldung', 'Unterschriftenmuster', 'Protokoll der Generalversammlung'])], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito alla (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. Nessuna controprestazione')
    if m and number(m['assets']) > 0 and number(m['liabilities']) >= 0:
        return [event('it.text.asset_transfer_without_consideration.v1', action='asset_transfer', currency='CHF', consideration='none', **m.groupdict())], ''

    m = match(rf"L'administrateur (?P<name1>{NAME}), nommé président, signe désormais collectivement à deux\. (?P<name2>{NAME}) et (?P<name3>{NAME}), directeurs, sont nommés membres du conseil d'administration et continuent à signer collectivement à deux")
    if m:
        rule = 'fr.persons.president_and_directors_board_appointments.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Kollektivunterschrift zu zweien')] + [person(rule, m['name'+str(i)], role="membre du conseil d'administration", signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'directeur', 'signing_continued': True}) for i in (2, 3)], ''

    m = match(rf'(?P<name1>{NAME}), administrateur, est élu président; continue de signer individuellement\. Nouvelles administratrices avec signature collective à deux: (?P<name2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), à (?P<place3>{NAME}), toutes deux de (?P<origin>{NAME})')
    if m and f"Nouvelles administratrices avec signature collective à deux: {m['name2']}, à {m['place2']}, et {m['name3']}, à {m['place3']}, toutes deux de {m['origin']}." in source_text:
        rule = 'fr.persons.president_two_new_administratrices.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Einzelunterschrift', extra={'signing_continued': True})] + [person(rule, m['name'+str(i)], role='administratrice', place=m['place'+str(i)], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']}) for i in (2, 3)], ''

    m = match(rf"L'inscription no (?P<entry1>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que par suite de changement d'état civil, (?P<old_name>{NAME}) porte désormais le nom de (?P<name1>[^();]+?) \(et non pas procuration collective à deux a été conférée à (?P=name1)\)\. L'inscription no (?P<entry2>{COUNT}) du (?P<second_date>{DATE}) est rectifiée en ce sens qu'une signature collective à deux a été conférée à (?P<name2>{NAME}) \(et non pas (?P<wrong_name>{NAME})\)")
    if m:
        rule = 'fr.persons.civil_status_name_and_signer_corrected.v1'
        return [person(rule, m['name1'], extra={'previous_name': m['old_name'], 'correction': True, 'entry': m['entry1'], 'entry_date': m['entry_date'], 'erroneous_procuration_removed': True}), person(rule, m['name2'], signing='Kollektivunterschrift zu zweien', extra={'previous_name': m['wrong_name'], 'correction': True, 'entry': m['entry2'], 'entry_date': m['second_date']})], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom de la gérante présidente est (?P<name>{NAME}) \(et non: (?P<previous_name>{NAME})\)")
    if m:
        return [person('fr.persons.manager_president_surname_corrected.v1', m['name'], role='gérante présidente', extra={k: v for k, v in m.groupdict().items() if k != 'name'} | {'correction': True, 'name_scope': 'surname'})], ''

    return [], leftover
