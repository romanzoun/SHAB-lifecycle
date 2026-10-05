from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID
from .parser271 import LONG_DATE, MONTHS


def extract_parser272_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract bounded fixture-backed clauses, preserving unsupported facts."""
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

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"Par arrêt du (?P<decision_date>{LONG_DATE}), la (?P<court>{NAME}) a admis le recours et annulé d'office le jugement")
    if m:
        return [event('organization_changed', 'fr.text.appeal_judgment_annulled.v1', **m.groupdict(), action='judgment_annulled', appeal_allowed=True)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a annulé la faillite du titulaire de l'entreprise prononcée le (?P<bankruptcy_date>{DATE}); l'inscription est rétablie comme ci-devant \(FOSC du (?P<notice_date>{DATE}) p\. (?P<page>{COUNT})\)")
    if m:
        return [event('organization_changed', 'fr.text.sole_trader_bankruptcy_annulled.v1', **m.groupdict(), action='bankruptcy_annulled', registration_restored=True)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>{NAME}), jusqu'ici (?P<previous_role>vice-président et trésorier), reste (?P<role>membre de la direction), désormais sans signature sociale")
    if m:
        return [person('fr.persons.direction_role_unsigned_corrected.v1', m['name'], place=m['place'] + ', ' + m['country'], role=m['role'], extra={k: v for k, v in m.groupdict().items() if k not in ('name', 'place', 'role')} | {'without_signature': True, 'action': 'corrected'})], ''

    pattern = rf"Le gérant (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement\. (?P<name2>[^,;]+?), du (?P<origin>{NAME}), à (?P<place>{NAME}), est gérant"
    m = match(pattern + '(?: avec signature collective à deux)?', pattern + ' avec signature collective à deux')
    if m:
        rule = 'fr.persons.manager_president_new_collective_manager.v1'
        return [person(rule, m['name1'], role='gérant président', signing='Einzelunterschrift', extra={'signing_continued': True}), person(rule, m['name2'], role='gérant', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    m = match(rf"L'associée-gérante (?P<name1>{NAME}) a cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associée (?P<name2>{NAME})\. Associées: (?P=name1) pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal) et (?P=name2) pour (?P<received>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        transferred, remaining, received = (int(number(m[k])) for k in ('transferred', 'remaining', 'received'))
        if transferred <= 0 or received < transferred:
            return [], leftover
        rule = 'fr.persons.associate_share_transfer_holdings.v1'
        return [person(rule, m['name1'], role='associée-gérante', extra={'shares': remaining, 'transferred_shares': transferred, 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associée', extra={'shares': received, 'share_nominal': m['nominal']})], ''

    pattern = rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), (?P<origin>cittadina germanica), in (?P<place>{NAME}), (?P<role>presidente), con firma individuale'
    m = match(pattern, pattern + r' \[no: (?P<previous_name>[^\[\]]+)\]')
    if m:
        return [person('it.persons.president_name_corrected.v1', m['surname'] + ', ' + m['given_names'], role=m['role'], place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'previous_name': m['previous_name'], 'action': 'corrected'})], ''

    m = match(rf"Rectification de l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{NAME}), procuration collective à deux, limitée à la succursale \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('fr.persons.branch_procuration_name_corrected.v1', m['name'], signing='Kollektivprokura zu zweien', extra={k: v for k, v in m.groupdict().items() if k != 'name'} | {'limited_to_branch': True, 'action': 'corrected'})], ''

    pattern = rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}) sont nommés liquidateurs'
    m = match(pattern + '(?: avec signature collective à deux)?', pattern + ' avec signature collective à deux')
    if m:
        return [person('fr.persons.four_liquidators_collective_signing.v1', m['name'+str(i)], role='liquidateur', signing='Kollektivunterschrift zu zweien') for i in (1, 2, 3, 4)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital-actions de CHF (?P<capital>{MONEY}) est divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives \(et non pas en (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives\)")
    if m:
        if number(m['count']) * number(m['nominal']) != number(m['capital']) or number(m['count']) <= 0 or number(m['nominal']) <= 0:
            return [], leftover
        return [event('capital_changed', 'fr.text.registered_share_count_corrected.v1', **m.groupdict(), action='corrected', share_kind='nominatives')], ''

    m = match(rf"L'associée (?P<name1>[^;]+?) \((?P<uid>{UID})\) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé (?P<name2>{NAME}), désormais titulaire de (?P<received>{COUNT}) parts de CHF (?P=nominal); (?P=name1) \((?P=uid)\) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        values = {k: int(number(m[k])) for k in ('transferred', 'previous', 'received', 'remaining')}
        if values['transferred'] <= 0 or values['remaining'] + values['transferred'] != values['previous'] or values['received'] < values['transferred']:
            return [], leftover
        rule = 'fr.persons.corporate_associate_partial_share_transfer.v1'
        return [person(rule, m['name1'], role='associée', extra={'uid': m['uid'], 'shares': values['remaining'], 'previous_shares': values['previous'], 'transferred_shares': values['transferred'], 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé', extra={'shares': values['received'], 'share_nominal': m['nominal']})], ''

    m = match(rf"Procuration collective à deux, toutefois pas entre eux ni avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}), (?P<excluded3>{NAME}) ni (?P<excluded4>{NAME}), est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME})")
    if m:
        return [person('fr.persons.collective_procuration_exclusions.v1', m['name'+str(i)], place=m['place'+str(i)], signing='Kollektivprokura zu zweien', extra={'origin': m['origin'+str(i)], 'not_with_each_other': True, 'excluded_signers': [m['excluded'+str(j)] for j in (1, 2, 3, 4)]}) for i in (1, 2)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<reference>\d+/\d+)\) est rectifiée en ce sens que les nouveaux statuts sont datés du (?P<statutes_date>{DATE}) \(et non: (?P<previous_date>{DATE})\)")
    if m:
        return [event('statutes_changed', 'fr.text.statutes_date_corrected.v1', **m.groupdict(), action='corrected')], ''

    return [], leftover
