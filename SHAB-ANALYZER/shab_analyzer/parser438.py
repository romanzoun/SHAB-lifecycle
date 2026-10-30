from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, UID
from .parser409 import NAME
from . import parser55, parser60, parser107, parser252

_LEGACY = (parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser107._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY,
           parser252._DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_PRIOR_CLAUSE)


def extract_parser438_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, evidenced residual clauses outside historical rules."""
    leftover = text.strip()
    if any(p.search(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def people(m, count, action):
        return [_person_event(*context, 'officer_changed', f'fr.persons.{action}.v1',
                              m[f'name{i}'], place=m[f'place{i}'],
                              role='membre du conseil de fondation',
                              signing='ohne Zeichnungsberechtigung',
                              extra={'action': 'appointed', 'origin': m[f'origin{i}'],
                                     **({'country': m[f'country{i}']} if f'country{i}' in m.groupdict() else {})})
                for i in range(1, count + 1)]

    def member(i):
        return rf'(?P<name{i}>{NAME}), de (?P<origin{i}>{NAME}), à (?P<place{i}>{NAME}), (?P<country{i}>[A-Z]{{2,3}})'
    m = match(member(1) + ', ' + member(2) + ', et ' + member(3) + r', sont membres du conseil de fondation, tous trois sans signature')
    if m:
        return people(m, 3, 'three_foundation_members_foreign_countries_unsigned'), ''

    m = match(rf'Nouveaux membres du conseil de fondation: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), sans signature, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sans signature')
    if m:
        return people(m, 2, 'two_foundation_members_each_unsigned'), ''

    m = match(rf'Statuts originaires: (?P<corrected_date>{DATE}) \[et non (?P<previous_date>{DATE})\]')
    if m:
        return [event('original_statutes_date_corrected', m, 'publication_corrected', kind='original_statutes_date')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que la présidente porte le nom de (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [event('president_name_spelling_corrected', m, 'publication_corrected', kind='person_name')], ''

    m = match(r'La clause statutaire concernant la restriction de transmissibilité des actions est abrogée')
    if m:
        return [event('share_transfer_restriction_statutory_clause_repealed', m, restriction_repealed=True)], ''

    m = match(rf'\[bisher: (?P<previous_place1>[^\[\]\n]+)\]\. (?P<place>{NAME}) \((?P<uid>{UID})\) \[bisher: (?P<previous_place2>[^\[\]\n]+)\]\. \[Ergänzung CHE-Nr\. bei Zweigniederlassung aufgrund geänderter Eintragungsvorschriften\]', 'de')
    if m:
        return [event('branch_uid_supplement_registration_requirements', m, branch_uid=m['uid'])], ''

    def capital_clause(kind, suffix, spelling='Kapitalerhöhung'):
        return (rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date{suffix}>{DATE}) die mit Beschluss vom (?P<introduced_date{suffix}>{DATE}) eingeführte {kind} {spelling} abgeändert gemäss näherer Umschreibung in den Statuten')

    pattern = (capital_clause('genehmigte', '1') + r'\. \[bisher: ' + capital_clause('genehmigte', '2') + r'\.\]\. '
               + capital_clause('bedingte', '3', 'Kapialerhöhung') + r'\. \[bisher: ' + capital_clause('bedingte', '4') + r'\.\]')
    m = match(pattern, 'de')
    if m:
        return [event('authorized_and_conditional_capital_amendments_with_history_typo', m)], ''
    return [], text
