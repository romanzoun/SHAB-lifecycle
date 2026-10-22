from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser132 import _DE_LIQUIDATION_ADDRESS
from .parser159 import _FR_BRANCH_REGISTERED_AT

PERSON = r'[^,;.]+?'


def extract_parser372_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events without changing earlier parsers' results."""
    leftover = text.strip()
    # Keep ownership even in isolation tests which disable earlier extractors.
    if ((language == 'de' and _DE_LIQUIDATION_ADDRESS.fullmatch(leftover))
            or (language == 'fr' and _FR_BRANCH_REGISTERED_AT.fullmatch(leftover))):
        return [], leftover
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            # Fragmentary leftovers alone do not establish the original clause.
            source_match = re.search(r'(?:^|\. )' + source_pattern + r'\.$', source_text)
            if not source_match or any(source_match.groupdict().get(key) != value for key, value in m.groupdict().items()):
                return None
            m = source_match
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(r'Liquidationsdomizil: (?P<care_of>c/o [^,\[\]]+), (?P<street>[^,\[\]]+), (?P<postal_code>\d{4}) (?P<locality>[^.\[\]]+?) \[bisher: Liquidationsdomizil: (?P<previous_address>[^\[\]]+?)\.\]', 'de')
    if m:
        return [event('liquidation_address_changed_with_previous', m)], ''

    foundation = rf'(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), tous deux à (?P<shared_place>{PERSON}), et (?P<name3>{PERSON}), de (?P<origin3>{PERSON}), à (?P<place3>{PERSON}), sont membres du conseil de fondation'
    m = match(foundation, source_pattern=foundation + r', avec signature collective à deux')
    if m:
        return [person('three_foundation_members_shared_place', m, m[f'name{i}'], m['shared_place'] if i < 3 else m['place3'], 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2, 3)], ''

    transfer = rf"L'associé-gérant (?P<seller>{PERSON}), qui est nommé président, cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{PERSON}), de et à (?P<place>{PERSON}), nouvel associé-gérant"
    ending = rf" titulaire de (?P=transferred) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)"
    m = match(transfer + ending, source_pattern=transfer + ' avec signature collective à deux,' + ending)
    if m and int(m['before'].replace("'", '')) == int(m['transferred'].replace("'", '')) + int(m['remaining'].replace("'", '')):
        return [event('presiding_manager_share_transfer_new_joint_manager', m, currency='CHF'), person('presiding_manager_share_transfer_new_joint_manager', m, m['seller'], role='Präsident der Geschäftsführung'), person('presiding_manager_share_transfer_new_joint_manager', m, m['buyer'], m['place'], 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien')], ''

    committee = rf'(?P<name1>{PERSON}), du (?P<origin1>{PERSON}), à (?P<place1>[^,;()]+) \((?P<country1>[^()]+)\), et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>[^,;()]+) \((?P<country2>[^()]+)\)'
    m = match(r'Nouveaux membres du comité : ' + committee, source_pattern=r'Nouveaux membres du comité avec signature collective à deux: ' + committee)
    if m:
        return [person('two_new_committee_members_foreign_places', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Vorstandes', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    # A married-name abbreviation contains a dot; earlier comma-free name rules
    # intentionally do not accept it. Do not broaden this to their NAME grammar.
    m = match(r"Signature collective à deux a été conférée à l'associée (?P<name>[^,;.]+ ép\. [^,;.]+)")
    if m:
        return [person('female_associate_joint_signing_married_name', m, m['name'], role='Gesellschafterin', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Das Statutendatum datiert vom (?P<statutes_date>{DATE}), nicht vom (?P<incorrect_statutes_date>{DATE})', 'de')
    if m:
        return [event('statutes_date_corrected_without_richtig', m)], ''

    m = match(rf'Neue Identifikationsnummer Hauptsitz: (?P<head_office_id>HRB \d+ [A-Z])\. Bemerkungen zum Hauptsitz neu: \[Die Statuten des Hauptsitzes wurden am (?P<statutes_date>{DATE}) geändert; die publikationspflichtigen Tatsachen haben keine Änderungen erfahren\.\]', 'de')
    if m:
        return [event('head_office_identifier_non_publishable_statutes', m)], ''

    m = match(rf"Complément de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{PERSON}), associé, (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), gérant, signature collective à deux, maintenant à (?P<place>{PERSON})")
    if m:
        return [person('associate_manager_residence_supplemented', m, m['name'], m['place'], 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien')], ''

    conversion = rf"Transformation des (?P<previous_count>{COUNT}) actions jusqu'ici de CHF (?P<previous_nominal>{MONEY}), en (?P<count1>{COUNT}) actions de CHF (?P<nominal1>{MONEY}) et (?P<count2>{COUNT}) actions de CHF (?P<nominal2>{MONEY}) privilégiées quant au dividende, toutes nominatives et "
    capital = rf'\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count1) actions de CHF (?P=nominal1) et (?P=count2) actions de CHF (?P=nominal2) privilégiées quant au dividende, toutes nominatives et liées selon statuts'
    m = match(conversion + capital, source_pattern=conversion + 'liées selon statuts' + capital + rf'\. Statuts modifiés le (?P<statutes_date>{DATE}), ainsi que sur des points non soumis à publication')
    if m:
        def number(value):
            return Decimal(value.replace("'", ''))
        if number(m['previous_count']) * number(m['previous_nominal']) == number(m['capital']) == sum(number(m[f'count{i}']) * number(m[f'nominal{i}']) for i in (1, 2)):
            return [_event(*context, 'capital_changed', 'fr.text.registered_share_split_dividend_preference.v1', {'action': 'registered_share_split_dividend_preference', **m.groupdict(), 'currency': 'CHF', 'fully_paid': True, 'transfer_restricted': True, 'share_classes': [{'count': m[f'count{i}'], 'nominal': m[f'nominal{i}'], 'kind': 'registered', 'dividend_preferred': i == 2} for i in (1, 2)]})], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'adresse exacte de la société est: (?P<address>[^();]+) \(et non (?P<previous_address>[^();]+), comme publié\)")
    if m:
        return [event('company_address_corrected_exact_notice', m)], ''

    m = match(rf'(?P<seller1>{PERSON}) détient désormais (?P<remaining1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count1>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer1>{PERSON}), et de (?P<count2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer2>{PERSON})\. (?P<seller2>{PERSON}) détient désormais (?P<remaining2>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<count3>{COUNT}) parts de CHF (?P=nominal) à (?P=buyer2)\. (?P=buyer2) détient désormais (?P<total2>{COUNT}) parts de CHF (?P=nominal)\. (?P=buyer1) détient désormais (?P<total1>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('two_sellers_two_recipients_share_balances', m, currency='CHF')], ''

    m = match(rf'Inscription de la succursale de (?P<branch_name>[^,;()]+), succursale de (?P<place>[^,;()]+) \((?P<branch_uid>{UID})\), au registre du commerce du canton de (?P<register>[^,;()]+) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)')
    if m:
        return [event('named_branch_registered_notice_comma', m)], ''

    return [], leftover
