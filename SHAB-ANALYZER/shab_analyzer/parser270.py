from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT


def extract_parser270_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete fixture-backed clauses and validate recovered source facts."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, source_pattern=None, *, at_end=True):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + (r'\.?$' if at_end else r'\.'), source_text)
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

    start = rf"(?P<name1>{NAME}), associé-gérant,"
    end = rf" et l'associée (?P<name2>{NAME}), qui continue de signer individuellement, sont désormais à (?P<place>{NAME})"
    m = match(start + r'(?: lequel est nommé liquidateur avec signature individuelle,)?' + end, start + ' lequel est nommé liquidateur avec signature individuelle,' + end)
    if m:
        rule = 'fr.persons.liquidator_shared_relocation.v1'
        return [person(rule, m['name1'], place=m['place'], role='associé-gérant, liquidateur', signing='Einzelunterschrift'), person(rule, m['name2'], place=m['place'], role='associée', signing='Einzelunterschrift', extra={'signing_continued': True})], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Anpassung der genehmigten Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<previous_date>{DATE}) ein genehmigtes Partizipationskapital gemäss näherer Umschreibung in den Statuten beschlossen\.\]\. Die Gesellschaft hat mit Beschluss vom (?P=decision_date) eine bedingte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen')
    if m:
        return [event('capital_changed', 'de.text.authorized_conditional_participation_capital.v1', **m.groupdict(), capital_kind='participation', authorized_increase_amended=True, conditional_increase=True)], ''

    m = match(rf"Les membres du comité (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), jusqu'ici président, nommé trésorier, continuent à signer collectivement à deux")
    if m:
        rule = 'fr.persons.committee_president_treasurer_changed.v1'
        return [person(rule, m['name1'], role='président du comité', signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role='trésorier du comité', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'président'})], ''

    pattern = rf"Das (?P<court>{NAME}) hat mit Entscheid vom (?P<decision_date>{DATE}) festgestellt, dass die Beschlüsse der ausserordentlichen Generalversammlung vom (?P<assembly_date>{DATE}) betreffend die Statutenänderung sowie den Verzicht auf die Wahl einer Revisionsstelle nichtig sind\. Demzufolge werden das Statutendatum sowie der Verzicht auf die eingeschränkte Revision von Amtes wegen gestrichen und gemäss dem Zustand vor dem im SHAB-Nr\. (?P<issue>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wiederhergestellt"
    m = match(pattern, pattern + rf'\. \[nicht: Gemäss Erklärung vom (?P=assembly_date) wurde auf die eingeschränkte Revision verzichtet\.\]')
    if m:
        return [event('organization_changed', 'de.text.void_statutes_audit_restored.v1', **m.groupdict(), statutes_restored=True, audit_waiver_revoked=True, action='previous_register_state_restored')], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, nun mit dem Namen (?P<name>{NAME}), neu in (?P<place>{NAME})')
    if m:
        return [person('de.persons.board_member_name_place_changed.v1', m['name'], place=m['place'], role='Verwaltungsratsmitglied', signing='Einzelunterschrift', extra={'previous_name': m['previous_name']})], ''

    m = match(rf'(?P<previous_name>{NAME}), dont le nom exacte est (?P<name>{NAME}), est maintenant de (?P<origin>{NAME})')
    if m:
        return [person('fr.persons.name_origin_corrected_typo.v1', m['name'], extra={'previous_name': m['previous_name'], 'origin': m['origin']})], ''

    m = match(r'Organisation neu: \[Löschung des Eintrags betreffend die Organisation aufgrund geänderter Eintragungsvorschriften\]')
    if m:
        return [event('organization_changed', 'de.text.organization_entry_deleted_regulations.v1', action='organization_entry_deleted', reason='registration_regulations_changed')], ''

    m = match(rf"L'inscription (?:No )?(?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<previous_name>{NAME}) porte en réalité le nom (?!de )(?P<name>{NAME})")
    if m:
        return [person('fr.persons.registered_name_rectified.v1', m['name'], extra=m.groupdict())], ''

    m = match(r"Suppression de la clause statutaire relative à la reprise de biens envisagée à la constitution conformément à l'article 628 al\. 4 CO")
    if m:
        return [event('statutes_changed', 'fr.text.intended_asset_takeover_clause_deleted.v1', action='intended_asset_takeover_clause_deleted', legal_basis='article 628 al. 4 CO')], ''

    m = match(rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du comité; ils n'exercent pas la signature sociale")
    if m:
        return [person('fr.persons.two_committee_members_unsigned.v1', m['name'+str(i)], place=m['place'+str(i)], role='membre du comité', extra={'origin': m['origin'+str(i)], 'without_signature': True}) for i in [1, 2]], ''

    pattern = rf'(?P<name>{NAME}), directeur, est nommé administrateur; '
    end = 'continue de signer collectivement à deux'
    m = match(pattern + end, pattern + 'il ' + end)
    if m:
        return [person('fr.persons.director_appointed_administrator.v1', m['name'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'directeur', 'signing_continued': True})], ''

    return [], leftover
