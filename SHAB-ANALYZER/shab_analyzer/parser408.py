from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event, _FR_MONTHS
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser63, parser71, parser162, parser165

MONTH = '(?:' + '|'.join(_FR_MONTHS) + ')'
WRITTEN_DATE = rf'\d{{1,2}} {MONTH} \d{{4}}'
NAME = r'[^,;.\[\]\n]+?'
_LEGACY = (
    parser63._DE_MIXED_PERSON_CHANGES,
    parser71._DE_PREVIOUS_DOMICILE_ADDRESS,
    parser162._DE_PARTIAL_ASSET_TRANSFER_SHARES_AND_CREDIT,
    parser165._DE_DISSOLUTION_PERSON_AND_ADDRESS,
)


def extract_parser408_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual forms supported by the release fixtures."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in _LEGACY):
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

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'\[gestrichen: Geschäftsdomizil: (?P<address>c/o [^\[\]\n]+, (?P<postal_code>\d{{4}}) (?P<place>{NAME}))\.\]', 'de')
    if m:
        return [event('business_domicile_deleted_bracket', m, 'address_changed', removed=True)], ''

    m = match(rf'Transfert de patrimoine: selon contrat du (?P<agreement_date>{DATE}), la société a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation CHF (?P<consideration>{MONEY})')
    if m:
        return [event('asset_transfer_past_tense_cash', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf"L'associé-gérant président (?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associe-gérant (?P<buyer>{NAME}) qui possède désormais (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_president_manager_typo', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'et (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), lequel signe collectivement à deux, avec le président')
    if m:
        # The residual conjunction alone does not establish an office.
        return [person('additional_person_joint_signing_president', m, m['name'], None, 'Kollektivunterschrift zu zweien', m['place'], signing_restriction='avec le président')], ''

    m = match(rf"(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), jusqu'ici directeur, maintenant nouvel associé, gérant, président, pour (?P=count) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_director_becomes_associate_president', m, 'ownership_changed', currency='CHF'), person('director_becomes_associate_manager_president', m, m['buyer'], 'Gesellschafter, Geschäftsführer, Präsident', previous_role='directeur')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: Gutschrift einer Forderung von CHF (?P<credit>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_credit_only', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf"Administration : (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), jusqu'ici présidente, (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country3>[A-Z]{{3}}), vice-présidente, et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), (?P<country4>[A-Z]{{3}}), lesquels signent individuellement")
    if m:
        roles = ['Präsident des Verwaltungsrates', 'Mitglied des Verwaltungsrates', 'Vizepräsidentin des Verwaltungsrates', 'Mitglied des Verwaltungsrates']
        return [person('four_administrators_individual_signing', m, m[f'name{i}'], roles[i-1], 'Einzelunterschrift', m.groupdict().get(f'place{i}')) for i in range(1, 5)], ''

    m = match(rf"Transfert de patrimoine: selon contrat du (?P<agreement_dates>(?P<day1>\d{{1,2}}), (?P<day2>\d{{1,2}}) et (?P<day3>\d{{1,2}}) (?P<month>{MONTH}) (?P<year>\d{{4}})) et selon décision de l'autorité de surveillance du (?P<approval_date>{WRITTEN_DATE}), la fondation a transféré des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}) à (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: aucune")
    if m:
        try:
            for key in ('day1', 'day2', 'day3'):
                datetime(int(m['year']), _FR_MONTHS[m['month']], int(m[key]))
            day, month, year = m['approval_date'].split()
            datetime(int(year), _FR_MONTHS[month], int(day))
        except ValueError:
            return [], text
        return [event('foundation_asset_transfer_multiple_written_dates', m, 'assets_transferred', currency='CHF', consideration_none=True)], ''

    m = match(rf'Gelöschte Person: (?P<removed>{NAME}), Geschäftsführer, Einzelunterschrift\. Neu eingetragene Person: (?P<name>{NAME}), von und in (?P<place>{NAME}), Geschäftsführer, Kollektivunterschrift zu zweien')
    if m:
        return [person('manager_removed_individual_signing', m, m['removed'], 'Geschäftsführer', 'Einzelunterschrift', removed=True), person('manager_added_joint_signing', m, m['name'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', m['place'])], ''

    m = match(rf"(?P<name1>{NAME}), de et à (?P<place1>{NAME}), et (?P<name2>{NAME}), de et à (?P<place2>{NAME}), sont membres du conseil d'administration et signent collectivement à deux, avec le président ou le vice-président")
    if m:
        return [person('two_administrators_restricted_joint_signing', m, m[f'name{i}'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', m[f'place{i}'], signing_restriction='avec le président ou le vice-président') for i in (1, 2)], ''

    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. \. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, Geschäftsführer, Einzelunterschrift, neu Gesellschafter, Geschäftsführer, Liquidator, Einzelunterschrift')
    if m:
        return [event('dissolution_residual_double_period', m, 'status_changed', dissolved=True), person('associate_manager_becomes_liquidator', m, m['name'], 'Gesellschafter, Geschäftsführer, Liquidator', 'Einzelunterschrift')], ''

    m = match(rf"(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<intermediary>{NAME}) \((?P<intermediary_uid>{UID})\), à (?P<place>{NAME}), qui les a cédées à, (?P<buyer>{NAME}), désormais associé-gérante pour (?P=count) parts de CHF (?P=nominal)")
    if m:
        return [event('successive_share_transfers_manager_typo', m, 'ownership_changed', currency='CHF'), person('successive_transfer_buyer_becomes_manager', m, m['buyer'], 'Gesellschafterin, Geschäftsführerin')], ''
    return [], text
