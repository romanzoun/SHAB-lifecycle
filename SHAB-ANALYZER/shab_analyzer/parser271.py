from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID

MONTHS = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
LONG_DATE = r'\d{1,2} (?:' + '|'.join(MONTHS) + r') \d{4}'


def extract_parser271_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume bounded fixture-backed clauses; retain unsupported or invalid facts."""
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
                    if re.fullmatch(DATE, value):
                        datetime.strptime(value, '%d.%m.%Y')
                    else:
                        day, month, year = value.split()
                        datetime(int(year), MONTHS.index(month) + 1, int(day))
        except ValueError:
            return None
        return m

    def event(kind, rule, **payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, *, kind='officer_changed', **kwargs):
        return _person_event(*context, kind, rule, name, **kwargs)

    m = match(rf"Par décision du (?P<decision_date>{LONG_DATE}), le président du (?P<court>{NAME}) a prolongé le sursis concordataire définitif accordé à la société jusqu'au (?P<until_date>{LONG_DATE})")
    if m:
        return [event('organization_changed', 'fr.text.definitive_moratorium_extended_long_dates.v1', **m.groupdict(), action='moratorium_extended', definitive=True)], ''

    for existing in (False, True):
        giver = rf'(?P<name1>{NAME})' + (r', (?P<role1>associé-gérant),' if existing else '')
        receiver = (r'(?P<role2>associée-gérante présidente), laquelle est désormais' if existing else rf'de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature,')
        pattern = giver + rf' cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), ' + receiver + rf' titulaire de (?P<received>{COUNT}) parts de CHF (?P=nominal)\. (?P=name1) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
        m = match(pattern)
        if m:
            values = {k: int(m[k].replace("'", '')) for k in ('transferred', 'previous', 'received', 'remaining')}
            if values['transferred'] <= 0 or values['remaining'] + values['transferred'] != values['previous'] or values['received'] < values['transferred'] or (not existing and values['received'] != values['transferred']):
                return [], leftover
            rule = 'fr.persons.partial_share_transfer_existing_manager.v1' if existing else 'fr.persons.partial_share_transfer_new_unsigned_associate.v1'
            return [person(rule, m['name1'], role=m.groupdict().get('role1'), extra={'shares': values['remaining'], 'previous_shares': values['previous'], 'transferred_shares': values['transferred'], 'share_nominal': m['nominal']}), person(rule, m['name2'], place=m.groupdict().get('place'), role=m['role2'] if existing else 'associé', extra={'shares': values['received'], 'share_nominal': m['nominal'], **({'origin': m['origin'], 'without_signature': True} if not existing else {})})], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>{NAME}), secrétaire\. Signature individuelle du président; le secrétaire n'exerce pas la signature sociale")
    if m:
        rule = 'fr.persons.board_president_unsigned_secretary.v1'
        return [person(rule, m['name1'], role='président', signing='Einzelunterschrift'), person(rule, m['name2'], place=m['place'] + ', ' + m['country'], role='secrétaire', extra={'origin': m['origin'], 'without_signature': True})], ''

    m = match(rf"L'administrateur président (?P<name1>{NAME}), nommé délégué et (?P<name2>{NAME}), nommée directrice générale, continuent à signer collectivement à deux")
    if m:
        rule = 'fr.persons.delegate_general_director_continued_signing.v1'
        return [person(rule, m['name1'], role='administrateur président, délégué', signing='Kollektivunterschrift zu zweien', extra={'signing_continued': True}), person(rule, m['name2'], role='directrice générale', signing='Kollektivunterschrift zu zweien', extra={'signing_continued': True})], ''

    m = match(rf"Complément: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\) est complétée en ce sens que le nouveau no d'identification des entreprises de l'organe de révision (?P<name>.+?), à (?P<place>{NAME}), est \((?P<uid>{UID})\)")
    if m:
        return [event('auditor_changed', 'fr.text.auditor_uid_supplemented.v1', **m.groupdict(), action='uid_supplemented')], ''

    m = match(rf"(?P<old1>{NAME}), (?P<old2>{NAME}), (?P<old3>{NAME}) ne sont plus administrateurs\. (?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), sont membres du conseil d'administration, ils n'exercent pas la signature sociale")
    if m:
        rule = 'fr.persons.three_board_members_replaced_unsigned.v1'
        return [person(rule, m['old'+str(i)], kind='officer_removed', role='administrateur') for i in (1, 2, 3)] + [person(rule, m['name'+str(i)], role="membre du conseil d'administration", place=m['place'+str(i)], extra={'origin': m['origin'+str(i)], 'without_signature': True}) for i in (1, 2, 3)], ''

    pattern = rf"(?P<name1>{NAME}), nommé président,? et (?P<name2>{NAME}), jusqu'ici président, continuent à signer collectivement à deux\. (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), et (?P<name4>{NAME}), de et à (?P<place4>{NAME}), sont membres du conseil d'administration"
    m = match(pattern + '(?: avec signature collective à deux)?', pattern + ' avec signature collective à deux')
    if m:
        rule = 'fr.persons.board_president_changed_two_members.v1'
        return [person(rule, m['name'+str(i)], role='président' if i == 1 else "membre du conseil d'administration", signing='Kollektivunterschrift zu zweien', place=m.groupdict().get('place'+str(i)), extra=({'signing_continued': True} if i < 3 else {'origin': m['origin3'] if i == 3 else m['place4']}) | ({'previous_role': 'président'} if i == 2 else {})) for i in (1, 2, 3, 4)], ''

    m = match(rf'par (?P<name>.+?) \((?P<uid>{UID})\), à (?P<place>{NAME}), nommée liquidatrice')
    if m:
        return [person('fr.persons.corporate_liquidator_appointed.v1', m['name'], role='liquidatrice', place=m['place'], extra={'uid': m['uid']})], ''

    m = match(rf"Nouveaux faits qualifiés: \[La disposition statutaire sur la reprise de biens lors de la fondation du (?P<foundation_date>{DATE}) est abrogée\] \[biffé: Reprise de biens: selon contrat du (?P<contract_date>{DATE}), (?P<previous_assets>[^\[\]]+?) pour le prix de CHF (?P<price>{MONEY})\.\]")
    if m:
        return [event('statutes_changed', 'fr.text.asset_takeover_clause_abrogated.v1', **m.groupdict(), action='asset_takeover_clause_deleted')], ''

    m = match(rf"Signature collective ä deux de (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME})")
    if m:
        return [person('fr.persons.collective_signing_umlaut_typo.v1', m['name'], place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    return [], leftover
