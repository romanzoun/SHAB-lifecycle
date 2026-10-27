from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser150 import _FR_INDIVIDUAL_PROXY_MODIFIED, _DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE, _DE_FOUNDATION_ASSET_TRANSFER_BY_ORDER
from .parser158 import _DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY_TYPO
from .parser87 import _DE_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED
from .parser137 import _FR_BRANCH_MENTION_REMOVED
from .parser240 import _FR_ADMINISTRATOR_REMOVED_POWERS_REVOKED

_LEGACY = (_DE_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED, _FR_BRANCH_MENTION_REMOVED, _FR_INDIVIDUAL_PROXY_MODIFIED, _DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE,
           _DE_FOUNDATION_ASSET_TRANSFER_BY_ORDER,
           _DE_AUTHORIZED_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY_TYPO,
           _FR_ADMINISTRATOR_REMOVED_POWERS_REVOKED)
REGISTRY_ID = r'CH-\d{3}\.\d{4}\.\d{3}-\d'


def extract_parser414_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only the residual variants covered by release 414 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
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
                             extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf'Procuration individuelle a été conféreé à (?P<name>{NAME}); ses pouvoirs sont modifiés en ce sens', 'fr')
    if m:
        return [person('individual_proxy_modified_typo', m, m['name'], signing='Einzelprokura')], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar sowie Verfügung der Aufsichtsbehörde vom (?P<order_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('foundation_asset_transfer_inventory_authority_order', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf"Radiation de la mention de l'existence d'une succursale à (?P<place>{NAME}) \((?P<branch_registry_id>{REGISTRY_ID})\)", 'fr')
    if m:
        return [event('branch_mention_removed_legacy_registry_id', m, 'branch_changed', mention_removed=True)], ''

    m = match(rf'Zweigniederlassung neu: (?P<place>{NAME}) \((?P<branch_canton>[A-Z]{{2}})\) \(eingetragen seit (?P<registration_date>{DATE})\)', 'de')
    if m:
        return [event('branch_listing_with_registration_date', m, 'branch_changed')], ''

    item = lambda i: rf'(?P<surname{i}>{NAME})\s*, (?P<given_names{i}>{NAME}), da (?P<origin{i}>{NAME}), in (?P<place{i}>{NAME}), (?P<role{i}>presidente|membro), con firma individuale'
    m = match('Funzioni corrette: ' + item(1) + r' ; ' + item(2), 'it')
    if m:
        # Earlier rules remove bracketed history. Only recover it from the
        # complete, matching original clause; never guess the former roles.
        source_pattern = 'Funzioni corrette: ' + item(1) + r' \[no: (?P<previous_role1>membro|presidente), con firma individuale\]; ' + item(2) + r' \[no: (?P<previous_role2>membro|presidente), con firma individuale\]'
        s = re.search(source_pattern + r'\.?$', source_text)
        if not s or any(s[k].strip() != v.strip() for k, v in m.groupdict().items()):
            return [], text
        return [person('two_board_roles_corrected', m, f"{m[f'surname{i}'].strip()}, {m[f'given_names{i}']}", m[f'role{i}'], 'Einzelunterschrift', m[f'place{i}'], corrected=True, previous_role=s[f'previous_role{i}']) for i in (1, 2)], ''

    m = match(rf"Les associés (?P<seller1>{NAME}), (?P<seller2>{NAME}), (?P<seller3>{NAME}) et (?P<seller4>{NAME}) ont cédé chacun (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal), sans signature sociale\. (?P=seller1) et (?P=seller2) détiennent maintenant (?P<remaining1>{COUNT}) parts de CHF (?P=nominal) chacun, (?P=seller3) et (?P=seller4) détiennent maintenant (?P<remaining2>{COUNT}) parts de CHF (?P=nominal) chacun", 'fr')
    if m:
        if Decimal(m['transferred'].replace("'", '')) * 4 != Decimal(m['buyer_count'].replace("'", '')):
            return [], text
        return [event('four_associates_transfer_with_remaining_holdings', m, 'ownership_changed', currency='CHF'), person('new_unsigned_associate_four_sellers', m, m['buyer'], 'Gesellschafter', 'ohne Unterschrift', m['place'])], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduced_date>{DATE}) eingeführte Bestimmung betreffend genehmigter Kapitalerhöhung des Aktienkapitals gemäss näherer Umschreibung in den Statuten geändert', 'de')
    if m:
        return [event('authorized_share_capital_clause_amended', m, 'capital_changed')], ''

    notice = rf'Mit dem im SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisherige Text nicht richtig publiziert\. Korrekt sind: '
    corrected = lambda i: rf'(?P<name{i}>{NAME}, {NAME}), (?P<nationality{i}>{NAME}) Staatsangehöriger, in (?P<place{i}>{NAME}(?: \([A-Z]{{2}}\))?), (?P<role{i}>Gesellschafter und Geschäftsführer|Gesellschafter), mit Einzelunterschrift \[bisher: (?P<previous_nationality{i}>{NAME}) Staatsangehöriger, in (?P<previous_place{i}>{NAME})\]'
    m = match(notice + corrected(1) + ' und ' + corrected(2), 'de')
    if m:
        return [person('two_associates_nationality_domicile_corrected', m, m[f'name{i}'], m[f'role{i}'], 'Einzelunterschrift', m[f'place{i}'], corrected=True) for i in (1, 2)], ''

    m = match(rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt berichtigt: (?P<name>{NAME}), Verwaltungsratsmitglied, Präsident, Einzelunterschrift \(und nicht (?P<previous_name>{NAME})\)', 'de')
    if m:
        return [person('board_president_full_name_corrected', m, m['name'], 'Verwaltungsratsmitglied, Präsident', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf"(?P<name>{NAME}) n'est associé indéfiniment responsable; ses pouvoirs sont radiés", 'fr')
    if m:
        # The source omits "plus". Its explicit revocation is unambiguous;
        # do not infer a departure or an ownership transfer from the typo.
        return [person('unlimited_partner_powers_revoked_typo', m, m['name'], signing='ohne Unterschrift', powers_revoked=True)], ''

    m = match(rf'Bei folgender juristischen Person wurde der "bisher"-Text nicht richtig aufgeführt: (?P<name>{NAME}) \((?P<auditor_uid>{UID})\), in (?P<place>{NAME}), Revisionsstelle \[bisher: (?P=name) \((?P<previous_registry_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]', 'de')
    if m:
        return [event('auditor_previous_registry_reference_corrected', m, corrected=True)], ''

    m = match(rf'Im SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrag (?P<entry>\d+/\d{{4}}) wurde irrtümlich bei (?P<surname>{NAME}), (?P<given_names>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Inhaber, mit Einzelunterschrift \[bisher: unbekannte Staatsangehörigkeit\] publiziert\. Richtig ist: (?P=surname), (?P=given_names) von (?P=origin), in (?P=place), Inhaber, mit Einzelunterschrift \[bisher: von (?P<previous_origin>{NAME}), Gesellschafter, mit Einzelunterschrift\]', 'de')
    if m:
        return [person('owner_previous_origin_role_corrected', m, f"{m['surname']}, {m['given_names']}", 'Inhaber', 'Einzelunterschrift', m['place'], corrected=True, previous_role='Gesellschafter')], ''
    return [], text
