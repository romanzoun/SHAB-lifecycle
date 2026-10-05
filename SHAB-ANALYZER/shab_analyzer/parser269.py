from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser269_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract complete, sample-backed clauses; validate consumed source facts."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, source_pattern=None):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k].strip() != v.strip() for k, v in m.groupdict().items() if v is not None):
                return None
            m = s
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(kind, rule, **payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"Contrat de société modifié le (?P<day>\d{{1,2}}) décembre (?P<year>\d{{4}})\. Le montant de la commandite est augmenté de CHF (?P<before>{MONEY}) à CHF (?P<after>{MONEY})")
    if m and num(m['after']) > num(m['before']) >= 0:
        try:
            date = datetime(int(m['year']), 12, int(m['day'])).date().isoformat()
        except ValueError:
            return [], leftover
        return [event('statutes_changed', 'fr.text.partnership_contract_amended.v1', date=date), event('capital_changed', 'fr.text.limited_partnership_capital_increased.v1', **m.groupdict(), currency='CHF', date=date)], ''

    head = rf"L'inscription N°(?P<entry>\d+) du (?P<entry_date>{DATE}) a été rectifiée comme suit : "
    method = "par n'importe quel moyen de transmission écrit ou imprimable (par ex. courrier écrit, télécopie, courrier électronique)"
    m = match(head + re.escape('courrier écrit, télécopie, courrier électronique)'), head + 'Communication aux actionnaires: ' + re.escape(method))
    if m:
        return [event('organization_changed', 'fr.text.shareholder_communications_corrected.v1', **m.groupdict(), recipients='actionnaires', method=method)], ''

    m = match(rf'Nouvelles personnes inscrtes: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), procuration collective à deux; (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), procuration collective à deux')
    if m:
        return [person('fr.persons.new_collective_procurists_typo.v1', m['name'+str(i)], place=m['place'+str(i)], signing='Kollektivprokura zu zweien', extra={'origin': m['origin'+str(i)], 'action': 'appointed'}) for i in [1, 2]], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici présidente, et (?P<name2>{NAME}), nommé président, tous deux membres du conseil de fondation, continuent de ne pas exercer la signature sociale")
    if m:
        rule = 'fr.persons.foundation_president_changed_unsigned.v1'
        return [person(rule, m['name1'], role='membre du conseil de fondation', extra={'previous_role': 'présidente', 'without_signature': True}), person(rule, m['name2'], role='président du conseil de fondation', extra={'without_signature': True})], ''

    m = match(r'Angaben zur Zweigniederlassung neu: Übergang dieser Zweigniederlassung infolge Spaltung gemäss Art\. 112 Abs\. 2 HRegV')
    if m:
        return [event('organization_changed', 'de.text.branch_transferred_by_division.v1', action='branch_transferred', reason='division', article='112 Abs. 2 HRegV')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est président du conseil d'administration \(et non (?P<previous_name>[^()]+)\)")
    if m:
        return [person('fr.persons.board_president_corrected.v1', m['name'], role="président du conseil d'administration", extra=m.groupdict())], ''

    m = match(rf"L'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la gérante-présidente porte le nom de (?P<name>{NAME}), et non pas (?P<previous_name>{NAME})")
    if m:
        return [person('fr.persons.president_manager_name_corrected.v1', m['name'], role='gérante-présidente', extra=m.groupdict())], ''

    m = match(rf'Selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et aucun passif à la société "(?P<recipient>[^"\n]+)" \((?P<recipient_uid>{UID})\) à (?P<recipient_place>{NAME})\. Contre-prestation: aucune')
    if m and num(m['assets']) > 0:
        return [event('organization_changed', 'fr.text.assets_transferred_no_liabilities_consideration.v1', **m.groupdict(), currency='CHF', liabilities='0', consideration='0', action='assets_transferred')], ''

    m = match(rf'Procuration collective à deux a été conférée à (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}); leur signature est radiée')
    if m:
        return [person('fr.persons.three_signatures_replaced_by_procuration.v1', m['name'+str(i)], signing='Kollektivprokura zu zweien', extra={'previous_signing_revoked': True}) for i in [1, 2, 3]], ''

    start = rf'Les associés-gérants (?P<name1>{NAME}) et (?P<name2>{NAME}) cédent chacun (?P<transferred>{COUNT}) de leurs (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) respectivement à (?P<recipient1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<recipient2>{NAME}), de et à (?P<place2>{NAME}), toutes deux nouvelles associées avec (?P<received>{COUNT}) parts de CHF (?P=nominal), gérantes'
    end = rf' (?P=name1) et (?P=name2) restent chacun titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
    m = match(start + r'(?: avec signature individuelle\.)?' + end, start + r' avec signature individuelle\.' + end)
    if m and num(m['transferred']) == num(m['received']) > 0 and num(m['before'])-num(m['transferred']) == num(m['remaining']) >= 0 and num(m['nominal']) > 0:
        rule = 'fr.persons.paired_partial_share_transfers.v1'
        return [*[person(rule, m['name'+str(i)], role='associé-gérant', extra={'shares_before': int(num(m['before'])), 'shares_count': int(num(m['remaining'])), 'shares_transferred': int(num(m['transferred'])), 'shares_nominal': m['nominal'], 'recipient': m['recipient'+str(i)]}) for i in [1, 2]], *[person(rule, m['recipient'+str(i)], place=m['place'+str(i)], role='associée-gérante', signing='Einzelunterschrift', extra={'origin': m['origin1'] if i == 1 else m['place2'], 'shares_count': int(num(m['received'])), 'shares_nominal': m['nominal']}) for i in [1, 2]]], ''

    pattern = rf'(?P<name>{NAME}) \(et non: (?P<previous_given_name>{NAME})\), maintenant originaire de (?P<origin>{NAME}), président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient>{NAME}), de et à (?P<place>{NAME}), nouvelle associée-gérante pour (?P<received>{COUNT}) parts de CHF (?P=nominal)'
    m = match(pattern + r'(?: avec signature individuelle)?', pattern + ' avec signature individuelle')
    if m and num(m['transferred']) == num(m['received']) > 0 and num(m['remaining']) >= 0 and num(m['nominal']) > 0:
        rule = 'fr.persons.corrected_president_partial_share_transfer.v1'
        return [person(rule, m['name'], role='président', extra={'origin': m['origin'], 'previous_given_name': m['previous_given_name'], 'shares_count': int(num(m['remaining'])), 'shares_transferred': int(num(m['transferred'])), 'shares_nominal': m['nominal'], 'recipient': m['recipient']}), person(rule, m['recipient'], place=m['place'], role='associée-gérante', signing='Einzelunterschrift', extra={'origin': m['place'], 'shares_count': int(num(m['received'])), 'shares_nominal': m['nominal']})], ''

    pattern = rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), cittadino (?P<nationality>{NAME}), in (?P<place>[^()]+) \((?P<country>[A-Z]{{2}})\), membro, direttore, con firma individuale'
    m = match(pattern, pattern + r' \[no: membro, con firma individuale\]')
    if m:
        return [person('it.persons.member_director_corrected.v1', m['surname'] + ' ' + m['given_names'], place=m['place'], role='membro, direttore', signing='Einzelunterschrift', extra={'nationality': m['nationality'], 'country': m['country'], 'previous_role': 'membro'})], ''

    return [], leftover
