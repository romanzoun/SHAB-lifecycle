from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, UID
from .parser409 import NAME
from .parser69 import _FR_FOUNDATION_MEMBER_WITHOUT_SIGNING
from .parser71 import _FR_FOUNDATION_MEMBER_SAME_ORIGIN_AND_PLACE
from .parser144 import _FR_COLLECTIVE_SIGNING_NOW

# Keep related legacy formulations with their original rules.
_LEGACY = (_FR_FOUNDATION_MEMBER_WITHOUT_SIGNING,
           _FR_FOUNDATION_MEMBER_SAME_ORIGIN_AND_PLACE, _FR_COLLECTIVE_SIGNING_NOW)


def extract_parser421_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed complete residual clauses, preserving previous events."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
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
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Par suite de fusion de communes, la commune du siège de la succursale à (?P<previous_place>{NAME}) \((?P<branch_uid>{UID})\) devient (?P<place>{NAME})')
    if m:
        return [event('branch_seat_municipality_merged', m)], ''

    m = match(rf'Succursales: (?P<place1>{NAME}) \((?P<branch_uid1>{UID})\) \[précédemment: (?P<previous_place1>{NAME})\]\. (?P<place2>{NAME}) \((?P<branch_uid2>{UID})\) \[précédemment: (?P<previous_place2>{NAME})\]')
    if m:
        return [event('two_branches_previous_localities', m)], ''

    m = match(rf"(?P<name>{NAME}) n'est associé indéfiniment responsable ni administrateur et ses pouvoirs sont radiés")
    if m:
        # As in parser414, the missing "plus" does not prove a departure.
        return [person('unlimited_associate_administrator_powers_revoked_typo', m, m['name'], signing='ohne Unterschrift', mentioned_roles=['associé indéfiniment responsable', 'administrateur'], powers_revoked=True)], ''

    m = match(rf"Radiation de la mention relative à la renonciation à l'organe de révision\. Nouvel organe de révision: (?P<auditor>{NAME}) \((?P<auditor_uid>{UID}) \), à (?P<place>{NAME})")
    if m:
        return [event('audit_waiver_removed_new_auditor_spaced_uid', m, audit_waiver=False, audit_waiver_removed=True)], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) genehmigtes Aktienkapital gemäss näherer Umschreibung in den Statuten geschaffen', 'de')
    if m:
        return [event('authorized_share_capital_created_statutes', m, 'capital_changed')], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>Bezirksgericht {NAME}) die gewährte definitive Nachlassstundung um (?P<duration>sechs) Monate bis (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('definitive_moratorium_extended_order_until', m, 'status_changed')], ''

    m = match(rf'(?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), signe individuellement')
    if m:
        return [person('individual_signing_country_code_origin', m, m['name'], signing='Einzelunterschrift', place=m['place'])], ''

    m = match(rf'Nouveau membre du conseil de fondation sans signature: (?P<name>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME})')
    if m:
        return [person('foundation_member_unsigned_au_de_origin', m, m['name'], 'membre du conseil de fondation', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), délégué, jusqu'ici vice-président, nommé président, et (?P<name2>{NAME}), jusqu'ici président, continuent à signer collectivement à deux")
    if m:
        return [person('board_delegate_president_pair_signing', m, m['name1'], 'président', 'Kollektivunterschrift zu zweien', additional_role='délégué', previous_role='vice-président'),
                person('board_delegate_president_pair_signing', m, m['name2'], 'administrateur', 'Kollektivunterschrift zu zweien', previous_role='président')], ''

    m = match(rf'Nouvelle gérante: (?P<name>{NAME}), de et à (?P<place>{NAME}), secrétaire')
    if m and re.search(re.escape(leftover.rstrip('.') + ', avec signature collective à deux') + r'\.?\s*$', source_text):
        return [person('new_manager_secretary_same_origin_place', m, m['name'], 'gérante', 'Kollektivunterschrift zu zweien', m['place'], additional_role='secrétaire', origin=m['place'])], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom exact du nouvel associé et gérant est (?P<name>{NAME})")
    if m:
        return [person('associate_manager_exact_name_corrected', m, m['name'], 'associé et gérant', corrected=True)], ''

    m = match(rf'(?P<name>{NAME}) engage désormais la société par sa signature individuelle')
    if m:
        return [person('individual_signing_now_engages_company', m, m['name'], signing='Einzelunterschrift')], ''
    return [], text
