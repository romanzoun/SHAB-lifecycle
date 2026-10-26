from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser96, parser125, parser157, parser164, parser171, parser192, parser209, parser227, parser248

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser96, parser125, parser157, parser164, parser171, parser192, parser209, parser227, parser248)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser402_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded residual variants while preserving earlier rule ownership."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(r'(?<!\S)' + source_pattern + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Das korrekte Statutendatum lautet: (?P<date>{DATE}) nicht (?P<previous_date>{DATE})', 'de')
    if m:
        # Reuse the established date types and payload semantics.
        canonical = f"Das korrekte Statutendatum ist der {m['date']} und nicht der {m['previous_date']}"
        return parser192.extract_parser192_leftovers(canonical, language, publication_id, published_at, org_uid, plz, canton)

    m = match(rf"Transfert de patrimoine: selon contrat des (?P<agreement_date1>{DATE}) et (?P<agreement_date2>{DATE}) et selon décision de l'autorité de surveillance (?P<authority>{NAME}) du (?P<approval_date>{DATE}), la fondation transfère des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}) à la fondation (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation : aucune")
    if m and Decimal(m['assets'].replace("'", '')) - Decimal(m['liabilities'].replace("'", '')) == Decimal(m['net_assets'].replace("'", '')):
        return [event('foundation_asset_transfer_two_contract_dates_authority', m, 'assets_transferred', currency='CHF', consideration='aucune')], ''

    pattern = r'wurde Text Weitere Adresse nicht angezeigt'
    source = rf'Mit dem im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) ' + pattern
    m = match(pattern, 'de', source)
    if m:
        evidence = re.search(source, source_text)
        try:
            for date in re.findall(DATE, evidence[0]):
                datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            return [], text
        return [event('additional_address_publication_omission', evidence, omitted_field='Weitere Adresse')], ''

    pattern = rf"Les administrateurs (?P<name1>{NAME}), jusqu'ici président, délégué et (?P<name2>{NAME}), signent désormais collectivement à deux avec le président du conseil d'administration; leurs pouvoirs sont modifiés en ce sens\. (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), président et (?P<name4>{NAME}), du et au (?P<place4>{NAME}), sont membres du conseil d'administration, tous deux"
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [person('board_joint_signing_with_president', m, m[f'name{i}'], role='administrateur', signing='Kollektivunterschrift zu zweien', signing_restriction="avec le président du conseil d'administration", previous_role='président, délégué' if i == 1 else None) for i in (1, 2)] + [person('board_pair_appointed_individual', m, m[f'name{i}'], role="président du conseil d'administration" if i == 3 else "membre du conseil d'administration", signing='Einzelunterschrift', place=m[f'place{i}'], origin=m['origin3'] if i == 3 else m['place4']) for i in (3, 4)], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici administrateur, nommé directeur, signe désormais collectivement à deux")
    if m:
        return [person('administrator_becomes_director_joint_signing', m, m['name'], role='directeur', signing='Kollektivunterschrift zu zweien', previous_role='administrateur')], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), (?P<name4>{NAME}), inscrits sans signature, ne sont plus membres du conseil de fondation\. Nouveaux membres du conseil de fondation sans signature: (?P<name5>{NAME}), de (?P<origin5>{NAME}), à (?P<place5>{NAME}), (?P<name6>{NAME}), de et à (?P<place6>{NAME}), et (?P<name7>{NAME}), de (?P<origin7>{NAME}), à (?P<place7>{NAME})')
    if m:
        return [person('unsigned_foundation_members_removed', m, m[f'name{i}'], role='membre du conseil de fondation', signing='ohne Zeichnungsberechtigung', kind='officer_removed') for i in (1, 2, 3, 4)] + [person('unsigned_foundation_members_appointed', m, m[f'name{i}'], role='membre du conseil de fondation', signing='ohne Zeichnungsberechtigung', place=m[f'place{i}'], origin=m['place6'] if i == 6 else m[f'origin{i}']) for i in (5, 6, 7)], ''

    pattern = rf'Nouveau liquidateur : (?P<name>{NAME}), de et à (?P<place>{NAME})'
    m = match(pattern, source_pattern=pattern.replace(' : ', ' avec signature individuelle: '))
    if m:
        return [person('liquidator_same_origin_residence_individual', m, m['name'], role='Liquidator', signing='Einzelunterschrift', place=m['place'], origin=m['place'])], ''

    pattern = rf"L'associé (?P<name1>{NAME}) et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), sont nommés directeurs"
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [person('associate_and_new_director_individual', m, m['name1'], role='directeur', signing='Einzelunterschrift', origin=None, country=None), person('associate_and_new_director_individual', m, m['name2'], role='directeur', signing='Einzelunterschrift', place=m['place'])], ''

    pattern = rf'(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=count) parts de CHF (?P=nominal)'
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [event('shares_transferred_new_foreign_associate', m, 'ownership_changed', currency='CHF'), person('new_foreign_associate_individual', m, m['buyer'], role='associé', signing='Einzelunterschrift', place=m['place'])], ''

    m = match(rf'Mit dem im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisherige Text nicht vollständig publiziert\. Korrekt wäre: (?P<name>[^,;\n]+, [^,;\n]+), von (?P<origin>{NAME}), in (?P<place>{NAME}), Mitglied des Verwaltungsrates, mit Kollektivunterschrift zu zweien \[bisher: in (?P<previous_place>{NAME}), Mitglied des Verwaltungsrates, mit Einzelunterschrift\]', 'de')
    if m:
        return [person('incomplete_notice_board_member_signing_corrected', m, m['name'], role='Mitglied des Verwaltungsrates', signing='Kollektivunterschrift zu zweien', place=m['place'], previous_signing='Einzelunterschrift', corrected=True)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) der "(?P<issuer>{NAME})" \((?P<issuer_uid>{UID})\) im Wert von CHF (?P<value>{MONEY}) auf die "(?P<recipient>{NAME})" \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: keine', 'de')
    if m:
        return [event('company_asset_transfer_registered_shares', m, 'assets_transferred', currency='CHF', consideration='keine', share_kind='Namenaktien')], ''

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}})\. Signature individuelle a été conférée à l'associé (?P=buyer)\. Par conséquent, (?P=seller) est maintenant tituaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('shares_transferred_remaining_holding_typo', m, 'ownership_changed', currency='CHF'), person('new_associate_individual_explicit_grant', m, m['buyer'], role='associé', signing='Einzelunterschrift', place=m['place'])], ''
    return [], text
