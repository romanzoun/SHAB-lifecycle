from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser341_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append complete, sample-backed clauses after all existing rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, **extra})

    m = match(rf"(?P<name1>{NAME}) et (?P<name2>{NAME}), tous deux de (?P<origin>{NAME}), à (?P<place>{NAME}), nommés gérants, n'exercent pas la signature sociale")
    if m:
        return [person('managers_appointed_unsigned', m, m[f'name{i}'], 'Geschäftsführer', 'ohne Zeichnungsberechtigung', m['place']) for i in (1, 2)], ''

    m = match(rf'Nuovi certificati di quota: Quote sociali da un minimo di CHF (?P<minimum>{MONEY})\.-- a un massimo di CHF (?P<maximum>{MONEY})\.--\. \[finora: Quote sociali da CHF (?P<previous_nominal>{MONEY})\.--\]\. \[radiati: Il raggio di attività comprende i Comuni di: (?P<previous_area1>[^\[\]]+)\.\]\. \[radiati: Il raggio di attività comprende: (?P<previous_area2>[^\[\]]+)\.\]\. Il raggio di attività comprende i Comuni di: (?P<activity_area>[^.\[\]]+?)', 'it')
    if m:
        return [event('cooperative_share_range_and_area', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"(?P<transferor>{NAME}), qui est maintenant de (?P<origin>{NAME}), à (?P<place>{NAME}), cède (?P<transferred>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), de (?P<recipient_origin>{NAME}), à (?P<recipient_place>{NAME}), nouvel associé-gérant président avec (?P<recipient_count>{COUNT}) parts de CHF (?P<recipient_nominal>{MONEY}); (?P<remaining_holder>{NAME}) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P<remaining_nominal>{MONEY})")
    if m:
        return [event('partial_share_transfer_manager_president', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"(?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), FRA, président et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), FRA, sont membres du conseil d'administration")
    if m:
        return [person('administrators_membership_confirmed', m, m[f'name{i}'], 'Präsident' if i == 1 else 'Verwaltungsrat', place=m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf"No IDE de l'établissement principal: (?P<principal_uid>{UID})")
    if m:
        return [event('principal_establishment_uid', m)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), jusqu'ici signent maintenant collectivement à deux")
    if m:
        original = leftover.replace("jusqu'ici signent", "jusqu'ici avec signature individuelle, signent")
        if original not in source_text:
            return [], leftover
        return [person('collective_signing_notice_completed', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', previous_signing='Einzelunterschrift') for i in (1, 2, 3)], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<contract_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: (?P<share_count>{COUNT}) azioni nominative da CHF (?P<nominal>{MONEY})', 'it')
    if m:
        return [event('asset_transfer_registered_share_consideration', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Conseil de fondation: (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président, (?P<name2>{NAME}), jusqu'ici trésorier, nommé secrétaire, (?P<name3>{NAME}), nommé trésorier, et (?P<name4>{NAME}), jusqu'ici présidente, lesquels signent collectivement à deux")
    if m:
        roles = ('Präsident', 'Sekretär', 'Kassier', 'Stiftungsrat')
        return [person('foundation_roles_collective_signing', m, m[f'name{i}'], roles[i-1], 'Kollektivunterschrift zu zweien') for i in range(1, 5)], ''

    m = match(rf"Rectification de l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\): La société ayant été radiée par erreur, elle est réinscrite")
    if m:
        return [event('erroneous_deletion_reinstated_reference', m)], ''

    m = match(r'Moritz \(CHE- (?P<branch_uid>\d{3}\.\d{3}\.\d{3})\)', 'it')
    if m and 'Nuova succursale: St. ' + leftover in source_text:
        return [event('new_branch_split_place', m, branch_place='St. Moritz', normalized_branch_uid='CHE-' + m['branch_uid'])], ''

    # Preserve the unusual amount spelling verbatim; no numeric correction is inferred.
    m = match(rf"Réduction du capital-actions de CHF (?P<previous_capital>{MONEY}) à CHF (?P<reduced_capital>{MONEY}) par destruction des (?P<cancelled_count>{COUNT}) actions nominatives de CHF (?P<cancelled_nominal>{MONEY}), , entièrement libérées pour supprimer un excédent passif constaté au bilan et simultanément augmentation ordinaire du capital de CHF (?P<increase_from>{MONEY}) à CHF (?P<capital>\d{{3}}\.\d{{3}}\.\d{{2}}) par compensation de créance de CHF (?P<claim>{MONEY}) contre remise en échange de (?P<issued_count>{COUNT}) actions nominatives de CHF (?P<issued_nominal>{MONEY}), liées selon statuts, entièrement libérées")
    if m:
        original = leftover.replace(', , entièrement', ', liées selon statuts, entièrement')
        if original not in source_text:
            return [], leftover
        return [event('capital_reduction_simultaneous_claim_increase', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Nouveau membre du conseil de fondation sans signature: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})\. Rectificatif: l\x27inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<corrected_name>{NAME}) signe collectivement à deux avec le président \(et non "pas avec (?P<previous_excluded_signatory>{NAME})", comme publié\)')
    if m:
        return [person('foundation_member_appointed_unsigned', m, m['name'], 'Stiftungsrat', 'ohne Zeichnungsberechtigung', m['place']), person('foundation_signing_restriction_corrected', m, m['corrected_name'], signing='Kollektivunterschrift zu zweien mit dem Präsidenten')], ''

    return [], leftover
