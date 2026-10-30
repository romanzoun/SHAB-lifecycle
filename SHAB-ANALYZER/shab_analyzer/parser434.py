from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from . import parser55, parser60

# These search rules own partial formulations too, even in isolated tests.
_LEGACY = (parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_BOARD_MEMBERS_SEPARATE_ORIGINS)


def extract_parser434_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses without changing historical payloads."""
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             m['name'], role=role, signing=signing,
                             place=m.groupdict().get('place'),
                             extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Gemäss Erklärung der Verwaltung vom (?P<declaration_date>{DATE}) untersteht die Genossenschaft keiner ordentlichen Revision und verzichtet auf eine eingeschränkte Revision', 'de')
    if m:
        return [event('cooperative_board_declaration_audit_waiver', m, 'audit_requirement_changed', ordinary_audit=False, limited_audit_waived=True)], ''

    # The three-digit year is retained verbatim; no date is inferred or repaired.
    m = match(rf"L'inscription No (?P<entry>{COUNT}) du (?P<entry_date_text>\d{{2}}\.\d{{2}}\.\d{{3}}) est rectifiée en ce sens que le capital-actions est de CHF (?P<capital>{MONEY}), entièrement libéré \(et non de CHF (?P<previous_capital>{MONEY})\)")
    if m:
        return [event('capital_corrected_incomplete_entry_year', m, 'capital_changed', corrected=True, fully_paid=True, currency='CHF')], ''

    m = match(rf'La société a été dissoute au siège principal par suite de faillite prononcée le (?P<decision_date>{DATE}), avec effet à partir du (?P<effective_date>{DATE}), à (?P<effective_time>(?:[01]\d|2[0-3])h[0-5]\d)\. Nouvelle raison de commerce de la succursale: (?P<branch_name>{NAME} en liquidation succursale de {NAME})')
    if m:
        return [event('head_office_bankruptcy_branch_liquidation_name', m, 'status_changed', bankrupt=True, scope='head_office')], ''

    m = match(rf'Diese infolge Konkurses im Sinne von (?P<legal_basis>Art\. 159 Abs\. 5 aHRegV) am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen, nachdem der Konkursrichter mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) die Wiedereröffnung eines summarischen Verfahrens angeordnet hat\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('bankrupt_company_reinstated_court_order_old_law', m, 'status_changed', reinstated=True, bankruptcy_reopened=True, procedure='summarisch')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_reference>\d+/\d+)\) est complétée en ce sens que le directeur de la succursale (?P<name>{NAME}) est originaire de (?P<origin>{NAME}), et est rectifiée en ce sens qu'(?:il)? dispose de la signature individuelle \(et non: signature collective à deux\)")
    if m:
        return [person('branch_director_origin_signing_corrected', m, 'directeur de la succursale', 'Einzelunterschrift', corrected=True, previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Rectification de l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{NAME}), signautre collective à 2, à (?P<place>{NAME}) \(et non pas à (?P<previous_place>{NAME})\)", 'de')
    if m:
        return [person('officer_domicile_corrected_signing_typo', m, signing='Kollektivunterschrift zu zweien', corrected=True)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est annulée en ce sens que la société n'est pas radiée d'office, une personne ayant fait valoir son intérêt au maintient de l'inscription")
    if m:
        return [event('official_deletion_cancelled_interest_typo', m, 'status_changed', deletion_cancelled=True)], ''

    m = match(rf'(?P<previous_name>{NAME}) se somme désormais (?P<name>{NAME})')
    if m:
        return [person('officer_name_changed_typo_somme', m, corrected=True)], ''

    return [], text
