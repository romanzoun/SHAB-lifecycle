from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID

MONTHS = dict(zip(('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'), range(1, 13)))
WRITTEN_DATE = r'\d{1,2} (?:' + '|'.join(MONTHS) + r') \d{4}'


def extract_parser291_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed clauses and retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def date(value):
        if ' ' not in value:
            return datetime.strptime(value, '%d.%m.%Y')
        day, month, year = value.split()
        return datetime(int(year), MONTHS[month], int(day))

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for k, v in m.groupdict().items():
                    if k.endswith('date'):
                        date(v)
            except ValueError:
                return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est complétée dans ce sens: (?P<name>{NAME}), procuration collective à deux, selon art\. (?P<article>459 al\. 2 CO)")
    if m:
        return [person('fr.persons.procuration_article459_notice_completed.v1', m['name'], signing='Kollektivprokura zu zweien', extra={k: v for k, v in m.groupdict().items() if k != 'name'})], ''

    m = match(rf"L'assemblée générale a supprimé une clause statutaire relative à une augmentation autorisée du capital \(selon décision du (?P<previous_date>{WRITTEN_DATE})\), par décision du (?P<decision_date>{WRITTEN_DATE})\. Pour les détails, voir les statuts\. L'assemblée générale a introduit deux clauses statutaires relatives à une augmentation autorisée du capital par décision du (?P=decision_date)\. Pour les détails, voir les statuts")
    if m and date(m['previous_date']) <= date(m['decision_date']):
        return [event('fr.text.authorized_capital_clauses_replaced.v1', action='authorized_capital_clauses_replaced', removed_clauses=1, introduced_clauses=2, **m.groupdict())], ''

    m = match(rf'Bei der im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) wurde der "bisher"-Text nicht richtig publiziert\. Korrekt ist: " \[bisher: (?P<name>{NAME}) \((?P<register_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]", nicht: " \[bisher: (?P=name)\]"', 'de')
    if m:
        return [event('de.text.previous_auditor_register_id_corrected.v1', action='previous_text_corrected', **m.groupdict())], ''

    m = match(rf'\[gestrichen: Die (?P<company>{NAME}) betreibt folgende Geschäftsstellen:\]\. \[gestrichen: (?P=company), (?P<address>[^;\[\]]+)\]', 'de')
    if m:
        return [event('de.text.business_office_clause_deleted.v1', action='business_office_clause_deleted', **m.groupdict())], ''

    m = match(rf"Liquidateurs: (?P<name1>{NAME}), président, et (?P<name2>{NAME}), membres du conseil d'administration, lesquels continuent de signer collectivement à deux\. Les restrictions statutaires liées à la transmissibilité des actions sont levées de par la loi")
    if m:
        rule = 'fr.persons.board_liquidators_share_restrictions_lifted.v1'
        return [person(rule, m['name1'], role="président du conseil d'administration liquidateur", signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role="membre du conseil d'administration liquidateur", signing='Kollektivunterschrift zu zweien'), event(rule, action='share_transfer_restrictions_lifted')], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<company>{NAME}), in (?P<place>{NAME}) \((?P<uid>{UID}) \), gemäss Fusionsvertrag vom (?P<contract_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da dieselbe Aktionärin sämtliche Aktien der an der Fusion beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m and number(m['assets']) > 0 and number(m['liabilities']) >= 0 and date(m['balance_date']) <= date(m['contract_date']):
        return [event('de.text.merger_same_female_shareholder.v1', action='merger', currency='CHF', capital_increase=False, share_allocation=False, **m.groupdict())], ''

    m = match(rf"Par décision rendue le (?P<decision_date>{WRITTEN_DATE}), le président du (?P<court>[^.;]+?) a prolongé de trois mois le sursis concordataire accordé à la société, soit jusqu'au (?P<until_date>{WRITTEN_DATE})")
    if m and date(m['decision_date']) < date(m['until_date']):
        return [event('fr.text.moratorium_extended_three_months.v1', action='moratorium_extended', extension_months=3, **m.groupdict())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est membre de la direction générale adjoint \(et non membre de la direction générale\)")
    if m:
        return [person('fr.persons.deputy_general_management_corrected.v1', m['name'], role='membre de la direction générale adjoint', extra={'entry': m['entry'], 'entry_date': m['entry_date'], 'previous_role': 'membre de la direction générale'})], ''

    # Earlier extractors leave a partial notice date. Verify the complete source
    # reference before consuming that fragment; never infer a date from it.
    m = match(rf', (?P<fragment>\d{{2}}\.\d{{4}}), p\. (?P<reference>\d+/\d+)\)\. Raison sociale du siège principal: (?P<company>[^.;]+?) \((?P<uid>{UID})\)')
    if m:
        source = re.search(rf'\(FOSC du (?P<notice_date>{DATE}), p\. {re.escape(m["reference"])}\)\. Raison sociale du siège principal: {re.escape(m["company"])} \({re.escape(m["uid"])}\)\.', source_text)
        if source and source['notice_date'].endswith(m['fragment']):
            try:
                date(source['notice_date'])
            except ValueError:
                return [], leftover
            return [event('fr.text.branch_head_office_name_uid.v1', action='head_office_name_recorded', company=m['company'], uid=m['uid'], notice_date=source['notice_date'], reference=m['reference'])], ''

    m = match(rf'Nouvel administateur sans signature: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        return [person('fr.persons.unsigned_administrator_typo.v1', m['name'], role='administrateur', signing='ohne Zeichnungsberechtigung', place=m['place'], extra={'origin': m['origin']})], ''

    m = match(rf'Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) werden (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}) zur Beseitigung einer Unterbilanz vernichtet\. Gleichzeitig wird das Stammkapital wieder erhöht durch Verrechnung einer Forderung von CHF (?P<claim>{MONEY}), wofür (?P=count) Stammanteile zu je CHF (?P=nominal) ausgegeben werden', 'de')
    if m and number(m['count']) > 0 and number(m['nominal']) > 0 and number(m['count']) * number(m['nominal']) == number(m['claim']):
        return [event('de.text.capital_reduction_restoration_offset_claim.v1', action='capital_reduction_and_restoration', currency='CHF', **m.groupdict())], ''

    m = match(rf'(?P<dates>{DATE}(?:\. {DATE})*)\. Organisation neu: \[Organisation: (?P<organization>Generalversammlung, Vorstand von 1 bis 9 Mitgliedern, Qualitätskommission und Quästor)\.\]', 'de')
    if m:
        source = re.search(rf'Statutenänderung: (?P<first_date>{DATE})\. {re.escape(leftover.removesuffix("."))}\.?$', source_text)
        if source:
            dates = [source['first_date']] + m['dates'].split('. ')
            try:
                parsed = [date(value) for value in dates]
            except ValueError:
                return [], leftover
            if parsed == sorted(set(parsed)):
                return [event('de.text.association_statute_dates_organization.v1', action='statutes_and_organization_changed', statute_dates=dates, organization=m['organization'], board_min=1, board_max=9)], ''

    return [], leftover
