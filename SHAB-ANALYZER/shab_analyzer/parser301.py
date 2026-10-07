from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID

MONTHS = {'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12}
WRITTEN_DATE = r'\d{1,2} (?:' + '|'.join(MONTHS) + r') \d{4}'


def extract_parser301_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses and preserve unsupported input."""
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
                    elif key.endswith('_written'):
                        day, month, year = value.split()
                        datetime(int(year), MONTHS[month], int(day))
            except ValueError:
                return None
        return m

    def event(rule, action, m):
        return _event(*context, 'organization_changed', rule, {'action': action, **m.groupdict()})

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    m = match(rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID}) \), secondo il contratto di fusione del (?P<contract_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le quote della società trasferente, per cui la fusione avviene senza aumento di capitale e senza attribuzione di azioni', 'it')
    if m:
        e = event('it.text.wholly_owned_merger_no_allocation.v1', 'merger', m)
        e.payload.update(capital_increase=False, share_allocation=False)
        return [e], ''

    m = match(rf'Nouveaux membres du conseil de fondation avec signature collective à deux: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), trésorier, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})', 'fr')
    if m:
        return [person('fr.persons.foundation_members_treasurer.v1', m[f'name{i}'], place=m[f'place{i}'], signing='Kollektivunterschrift zu zweien', role='membre du conseil de fondation' + (', trésorier' if i == 1 else ''), extra={'origin': m[f'origin{i}']}) for i in (1, 2)], ''

    m = match(rf'\[Fälschlicherweise wurde die mit Beschluss vom (?P<revocation_date>{DATE}) beschlossene Aufhebung der am (?P<introduction_date>{DATE}) beschlossenen genehmigten Kapitalerhöhung nicht publiziert\.\]', 'de')
    if m:
        return [event('de.text.authorized_capital_revocation_omission.v1', 'authorized_capital_revocation_corrected', m)], ''

    m = match(rf'Abspaltung: Die Gesellschaft übernimmt von der (?P<transferor>{NAME}), in (?P<place>{NAME}) \((?P<transferor_uid>{UID})\), einen Teil des Vermögens\. Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY})\. Da derselbe Aktionär alle Aktien der an der Spaltung beteiligen Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        e = event('de.text.demerger_common_shareholder_assets.v1', 'demerger', m)
        e.payload.update(capital_increase=False, share_allocation=False)
        return [e], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}) \((?P<register>HRB \d+)\), Gesellschafterin, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), firmiert neu (?P<name>{NAME}) \((?P=register)\)', 'de')
    if m:
        return [event('de.text.corporate_associate_renamed.v1', 'corporate_associate_renamed', m)], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), (?P<name4>{NAME}), (?P<name5>{NAME}) et (?P<name6>{NAME}) sont nommés liquidateurs avec signature collective à deux', 'fr')
    if m:
        return [person('fr.persons.six_liquidators_appointed.v1', m[f'name{i}'], role='liquidateur', signing='Kollektivunterschrift zu zweien') for i in range(1, 7)], ''

    m = match(rf'Mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde das Konkursbegehren abgewiesen\. Infolgedessen besteht die Gesellschaft entsprechend den früheren Eintragungen weiter', 'de')
    if m:
        return [event('de.text.bankruptcy_petition_rejected_continued.v1', 'bankruptcy_petition_rejected', m)], ''

    m = match(rf"Par décision du (?P<decision_written>{WRITTEN_DATE}), le président du (?P<court>[^;]+?) a prolongé jusqu'au (?P<deadline_written>{WRITTEN_DATE}) le sursis concordataire définitif accordé à la société", 'fr')
    if m:
        e = event('fr.text.definitive_moratorium_deadline_extended.v1', 'definitive_moratorium_extended', m)
        for key in ('decision', 'deadline'):
            day, month, year = m[key + '_written'].split()
            e.payload[key + '_date'] = datetime(int(year), MONTHS[month], int(day)).strftime('%d.%m.%Y')
        return [e], ''

    m = match(rf'La società è reiscritta nel registro di commercio conformemente alla decisione della (?P<court>{NAME}) del (?P<reinstatement_date>{DATE})\. Con decisione del (?P<reopening_date>{DATE}) è stata ordinata la riapertura della procedura fallimentare\. \[finora: Con decreto del (?P<closure_date>{DATE}), la (?P=court) ha deciso la chiusura della procedura fallimentare aperta in data (?P<opening_date>{DATE})\. \]', 'it')
    if m:
        return [event('it.text.reinstatement_bankruptcy_reopened.v1', 'organization_reinstated_bankruptcy_reopened', m)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom de la localité dans la domicile social est (?P<place>{NAME}) \(et non pas (?P<previous_place>{NAME})\)", 'fr')
    if m:
        return [event('fr.text.domicile_locality_spelling_corrected.v1', 'domicile_locality_corrected', m)], ''

    m = match(rf"L'associée-gérante (?P<name>{NAME}), désormais de (?P<origin>{NAME}), est nommée liquidatrice avec signature individuelle", 'fr')
    if m:
        return [person('fr.persons.associate_manager_liquidator_origin.v1', m['name'], role='associée-gérante, liquidatrice', signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici président avec signature collective à deux, est actuellement administrateur unique avec signature individuelle", 'fr')
    if m:
        return [person('fr.persons.president_now_sole_administrator.v1', m['name'], role='administrateur unique', signing='Einzelunterschrift', extra={'previous_role': 'président', 'previous_signing': 'Kollektivunterschrift zu zweien'})], ''

    return [], leftover
