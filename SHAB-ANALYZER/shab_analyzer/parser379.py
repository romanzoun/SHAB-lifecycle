from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser120 import _FR_TWO_FOUNDATION_MEMBERS
from .parser122 import _FR_FOUNDATION_MEMBER_PAIR_AFTER_SIGNING

NAME = r'[^,;.()]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser379_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Additional bounded variants; context-dependent residues require their source."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_FR_TWO_FOUNDATION_MEMBERS, _FR_FOUNDATION_MEMBER_PAIR_AFTER_SIGNING)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(source_pattern + r'\.', source_text)
            if not source or {k: v.strip() for k, v in source.groupdict().items()} != m.groupdict():
                return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Abspaltung: Die Gesellschaft übernimmt die mit dem Betrieb des (?P<business>{NAME}) verbundenen Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}) der (?P<transferor>{NAME}), in (?P<place>{NAME}) \((?P<transferor_uid>{UID})\), gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE})\. Da dieselbe Gesellschafterin sämtliche Stammanteile der an der Abspaltung beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt', 'de')
    if m:
        return [event('business_demerger_common_sole_associate', m, currency='CHF', capital_increased=False, shares_allocated=False)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der Einzelrichter am Kantonsgericht die provisorische Nachlassstundung bis (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_cantonal_single_judge', m, 'status_changed', provisional=True)], ''

    capital = rf"Rectificatif: l'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le capital action est exactement composé de (?P<count1>{COUNT}) actions nominatives de CHF (?P<nominal1>{MONEY}), et (?P<count2>{COUNT}) actions nominatives de CHF (?P<nominal2>{MONEY}) de type (?P<share_class>A), privilégiées quant au produit de liquidation, toutes"
    m = match(capital, source_pattern=capital + r' avec restrictions quant à la transmissibilité selon statuts')
    if m:
        return [event('two_registered_share_classes_corrected', m, 'capital_changed', corrected=True, currency='CHF', preferred_rights='produit de liquidation', transfer_restricted=True)], ''

    officers = rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), {{signing}}sauf avec (?P<excluded1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), avec signature collective à deux, sauf avec (?P=name1), sont membres du conseil d'administration"
    m = match(officers.format(signing=''), source_pattern=officers.format(signing='avec signature collective à deux, '))
    if m:
        return [person('board_members_mutual_signing_exclusion', m, m[f'name{i}'], m[f'place{i}'], "membre du conseil d'administration", 'Kollektivunterschrift zu zweien', not_with=[m['excluded1'] if i == 1 else m['name1']]) for i in (1, 2)], ''

    m = match(rf'La liquidation est opérée sous la raison de commerce: (?P<company>[^()]+? in liquidation) \((?P<translation>[^()]+? en liquidation)\) par (?P<liquidator>{NAME}) \((?P<liquidator_uid>{UID})\), à (?P<place>{NAME}), nommée liquidatrice')
    if m:
        return [event('liquidation_name_translation_corporate_liquidator', m, 'status_changed', liquidation=True), person('corporate_liquidator_with_translated_name', m, m['liquidator'], m['place'], 'liquidatrice', liquidator_uid=m['liquidator_uid'])], ''

    board = rf'Administration: (?P<name1>{NAME}), nommé président, {{signing}}et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), secrétaire, avec signature collective à deux'
    m = match(board.format(signing=''), source_pattern=board.format(signing='avec signature individuelle, '))
    if m:
        return [person('three_board_members_mixed_signing', m, m[f'name{i}'], m.groupdict().get(f'place{i}'), ['président', "membre du conseil d'administration", 'secrétaire'][i-1], 'Einzelunterschrift' if i == 1 else 'Kollektivunterschrift zu zweien') for i in (1, 2, 3)], ''

    m = match(rf'Aufgrund des mit Urteil vom (?P<decision_date>{DATE}) eröffneten Konkursverfahrens erfolgte die Löschung der Gesellschaft in Anwendung von Art\. 155 HRegV irrtümlich und wird in allen Teilen widerrufen\. Die Gesellschaft besteht gemäss den früheren Eintragungen weiter\. \[bisher: Die Gesellschaft wird in Anwendung von Art\. 155 HRegV von Amtes wegen gelöscht, weil die Gesellschaft keine Geschäftstätigkeit mehr aufweist und keine verwertbaren Aktiven mehr hat und kein Interesse an der Aufrechterhaltung der Eintragung innert angesetzter Frist geltend gemacht wurde\.\]', 'de')
    if m:
        return [event('erroneous_art155_deletion_revoked_bankruptcy', m, 'status_changed', deletion_revoked=True)], ''

    m = match(rf'(?P<name>{NAME}), administratrice, est nommée vice-présidente; elle continue de signer individuellement')
    if m:
        return [person('female_board_member_appointed_vice_president', m, m['name'], role='administratrice, vice-présidente', signing='Einzelunterschrift')], ''

    foundation = rf'Nouveaux membres du conseil de fondation{{signing}}: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de et à (?P<place2>{NAME})'
    m = match(foundation.format(signing=' '), source_pattern=foundation.format(signing=' avec signature collective à deux'))
    if m:
        return [person('foundation_pair_shared_origin_domicile', m, m[f'name{i}'], m[f'place{i}'], 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien', origin=m['origin1'] if i == 1 else m['place2']) for i in (1, 2)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) reste également membre de la direction")
    if m:
        return [person('notice_management_membership_retained', m, m['name'], role='membre de la direction', corrected=True)], ''

    pair = rf'(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})'
    m = match(pair, source_pattern=pair + rf', {NAME}, de {NAME}, à {NAME}, et {NAME}, de {NAME}, à {NAME}, sont membres du conseil sans signature')
    if m:
        return [person('unsigned_board_members_residue', m, m[f'name{i}'], m[f'place{i}'], 'membre du conseil', 'ohne Zeichnungsberechtigung', without_signing=True) for i in (1, 2)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), vice-président, (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), secrétaire, et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME})\. Signature collective à deux sauf entre eux de (?P=name1) et (?P=name3), ou signature collective à deux sauf entre eux de (?P=name2) et (?P=name4)')
    if m:
        return [person('four_board_members_two_excluded_pairs', m, m[f'name{i}'], m.groupdict().get(f'place{i}'), ['président', 'vice-président', 'secrétaire', "membre du conseil d'administration"][i-1], 'Kollektivunterschrift zu zweien', not_with=[m[f'name{ {1:3, 2:4, 3:1, 4:2}[i]}']]) for i in (1, 2, 3, 4)], ''
    return [], text
