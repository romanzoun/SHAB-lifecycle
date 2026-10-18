from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY

PERSON = r'[^,;.]+?'


def extract_parser360_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual clauses without replacing earlier events."""
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

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"(?P<name1>{PERSON}), d'(?P<origin1>{PERSON}), à (?P<place1>{PERSON}), (?P<country1>[A-Z]{{3}}), et (?P<name2>{PERSON}), des (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>[A-Z]{{3}}), sont membres du conseil de fondation, tous deux sans signature")
    if m:
        return [person('foundation_members_without_signing', m, m[f'name{i}'], 'Mitglied des Stiftungsrates', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat die Einzelrichterin im summarischen Verfahren des Bezirksgerichts (?P<court_place>{PERSON}) die gewährte definitive Nachlassstundung um (?P<extension>drei) Monate bis (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('definitive_composition_moratorium_extended', m)], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que les administrateurs se nomment (?P<name1>[^()]+?) \(et non (?P<previous_name1>[^()]+)\) et (?P<name2>[^()]+?) \(et non (?P<previous_name2>[^()]+)\)")
    if m:
        return [person('board_member_name_corrected', m, m[f'name{i}'], 'Mitglied des Verwaltungsrates', previous_name=m[f'previous_name{i}']) for i in (1, 2)], ''

    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}) et avenants du (?P<amendment1_date>{DATE}) et du (?P<amendment2_date>{DATE}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}), à (?P<recipient>[^()]+?) \((?P<recipient_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), à (?P<place>{PERSON})\. Contre-prestation: une créance de CHF (?P<consideration>{MONEY})')
    if m:
        return [event('asset_transfer_with_two_amendments', m, currency='CHF')], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{PERSON}), Kollektivunterschrift zu zweien, neu Verwaltungsratmitglied, Delegierter, Kollektivunterschrift zu zweien', 'de')
    if m:
        return [person('board_delegate_role_changed', m, m['name'], 'Mitglied des Verwaltungsrates, Delegierter', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf"L'association est dissoute par décision de l'assemblée générale du (?P<decision_date>{DATE})\. Liquidateurs: les membres du comité de direction (?P<name1>{PERSON}), président et (?P<name2>{PERSON}), nommé secrétaire, tous deux ; les pouvoirs de (?P=name2) sont modifiés en ce sens")
    if m and ('Liquidateurs: ' + leftover.split('Liquidateurs: ', 1)[1]).replace('tous deux ;', 'tous deux avec signature collective à deux;') in source_text:
        return [event('association_dissolved_by_general_meeting', m)] + [person('association_liquidators_collective_signing', m, m[f'name{i}'], 'Liquidator', 'Kollektivunterschrift zu zweien', committee_role='président' if i == 1 else 'secrétaire') for i in (1, 2)], ''

    m = match(rf"L'associé-gérant (?P<transferor>{PERSON}) cède (?P<transferred>\d+) de ses (?P<previous_count>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), du (?P<origin>{PERSON}), à (?P<place>{PERSON}), nouvelle associé avec (?P=transferred) parts de CHF (?P=nominal), président des gérants (?P=transferor) reste titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m and leftover.replace('président des gérants ', 'président des gérants avec signature individuelle. ') in source_text:
        return [event('share_transfer_new_presiding_manager', m, currency='CHF'), person('new_presiding_manager_individual_signing', m, m['recipient'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}), le montant de l'augmentation ayant été atteint \. \. \. \[biffé: La clause statutaire relative à une augmentation autorisée du capital-actions par décision du (?P<previous_authorization_date>{DATE}) a été modifiée par décision du (?P<amendment_date>{DATE})\. Pour les détails, voir les statuts\]")
    if m:
        return [event('authorized_capital_clause_removed_amount_reached', m)], ''

    m = match(r'\[gestrichen: Geschäftsstelle: (?P<previous_address>[^\n]+?)\.\]\. Weitere Adresse: (?P<address>[^.\n]+?)', 'de')
    if m:
        return [event('office_deleted_additional_address_added', m)], ''

    m = match(rf'Bisher betrug das Aktienkapital CHF (?P<previous_capital>{MONEY})', 'de')
    if m:
        return [event('previous_share_capital_stated', m, currency='CHF')], ''

    m = match(rf"Modification formelle des statuts pour l'indication du siège à (?P<place>{PERSON})")
    if m:
        return [event('formal_statutes_registered_seat_indication', m)], ''

    m = match(rf"Rectificatif: l'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>[\d/]+)\) est rectifiée en ce sens que le nom exact de (?P<previous_name>{PERSON}) est: (?P<name>{PERSON})")
    if m:
        return [person('person_name_corrected_notice_reference', m, m['name'], None)], ''

    return [], leftover
