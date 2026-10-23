from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID

from .parser111 import _FR_SOLE_PROPRIETOR_MORATORIUM_EXTENDED
from .parser120 import _FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR
from .parser134 import _FR_ADDRESS_CORRECTED
from .parser159 import _FR_ADMINISTRATION_PRESIDENT_RELOCATED_AND_SECRETARY_APPOINTED
from .parser166 import _DE_ASSOCIATION_ASSET_TRANSFER_FOR_SHARES
from .parser197 import _DE_ASSOCIATION_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION

# Preserve older rules' ownership, including when an extractor is disabled.
_LEGACY_PATTERNS = {
    'fr': (_FR_SOLE_PROPRIETOR_MORATORIUM_EXTENDED,
           _FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR, _FR_ADDRESS_CORRECTED,
           _FR_ADMINISTRATION_PRESIDENT_RELOCATED_AND_SECRETARY_APPOINTED),
    'de': (_DE_ASSOCIATION_ASSET_TRANSFER_FOR_SHARES,
           _DE_ASSOCIATION_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION),
}

PERSON = r'[^,;.]+?'


def extract_parser373_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events without changing earlier parsers' results."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in _LEGACY_PATTERNS.get(language, ())):
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
                    if key in ('until', 'decision_date_text'):
                        day, month, year = value.split()
                        datetime(int(year), {'septembre': 9, 'octobre': 10, 'ottobre': 10}[month], int(day))
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"(?P<seller>{PERSON}) jusqu'ici associé, gérant, pour (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}), détient maintenant (?P<remaining>{COUNT}) parts de CHF (?P=nominal), par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à l'associée (?P<buyer>[^()]+) \((?P<buyer_uid>{UID})\), laquelle détient maintenant (?P<total>{COUNT}) parts de CHF (?P<buyer_nominal>{MONEY})")
    if m and Decimal(m['nominal'].replace("'", '')) == Decimal(m['buyer_nominal'].replace("'", '')) and int(m['before'].replace("'", '')) == int(m['remaining'].replace("'", '')) + int(m['transferred'].replace("'", '')):
        return [event('manager_share_transfer_company_associate_balance', m, currency='CHF')], ''

    m = match(r'(?P<surname>[^,;.]+), (?P<given_name>[^,;.]+), von (?P<origin>[^,;.]+), in (?P<place>[^,;.]+) wurde bei der Neueintragung irrtümlich ohne Zeichnungsart eingetragen anstelle von Einzelunterschrift', 'de')
    if m:
        return [person('initial_registration_missing_signing_corrected', m, m['surname'] + ', ' + m['given_name'], m['place'], signing='Einzelunterschrift')], ''

    m = match(rf"Administration: (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), président, (?P<name2>{PERSON}), jusqu'ici présidente, nommée secrétaire, et (?P<name3>{PERSON}), jusqu'ici secrétaire, lesquels signent collectivement à deux")
    if m:
        return [person('three_administrators_presidency_secretary_changed', m, m[f'name{i}'], m['place1'] if i == 1 else None, ['Präsident des Verwaltungsrates', 'Sekretär des Verwaltungsrates', 'Mitglied des Verwaltungsrates'][i-1], 'Kollektivunterschrift zu zweien', **({'previous_role': 'Präsident des Verwaltungsrates' if i == 2 else 'Sekretär des Verwaltungsrates'} if i > 1 else {})) for i in (1, 2, 3)], ''

    liquidator = rf"L'administratrice (?P<name>{PERSON}) est élue liquidatrice"
    m = match(liquidator, source_pattern=liquidator + ' avec signature individuelle')
    if m:
        return [person('female_administrator_elected_liquidator', m, m['name'], role='Liquidatorin', signing='Einzelunterschrift')], ''

    m = match(rf'Administration: (?P<name1>{PERSON}), nommé président, et (?P<name2>{PERSON}), de et à (?P<place2>{PERSON}), secrétaire, lesquels signent collectivement à deux')
    if m:
        return [person('president_and_local_secretary_joint_signing', m, m[f'name{i}'], m['place2'] if i == 2 else None, 'Präsident des Verwaltungsrates' if i == 1 else 'Sekretär des Verwaltungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Les associés-gérants (?P<seller1>{PERSON}) et (?P<seller2>{PERSON}) ont cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au gérant (?P<buyer>{PERSON}), lequel devient associé pour (?P=transferred) parts de CHF (?P=nominal)\. Par conséquent, (?P=seller1) et (?P=seller2) sont désormais associés chacun pour (?P<remaining_each>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('two_managers_transfer_to_existing_manager', m, currency='CHF')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom de famille de la gérante est (?P<surname>{PERSON}) \(et non: (?P<previous_surname>{PERSON})\)")
    if m:
        return [event('female_manager_surname_corrected_notice', m)], ''

    m = match(rf"Con decisione del (?P<decision_date>{DATE}), il (?P<court>[^;]+?) ha prolungato la durata dell'incarico del commissario avv\. (?P<commissioner>{PERSON}) fino al (?P<until>\d{{1,2}} ottobre \d{{4}})", 'it')
    if m:
        return [event('commissioner_mandate_extended', m)], ''

    m = match(rf'Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{PERSON}), in (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('association_assets_transferred_cash_consideration', m, currency='CHF')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifié en ce sens que l'adresse exacte est: (?P<address>[^.;]+)")
    if m:
        return [event('exact_address_corrected_notice_masculine', m)], ''

    m = match(r"Par décision du (?P<decision_date_text>\d{1,2} septembre \d{4}), le (?P<court>[^;]+?) a prolongé une ultime fois le sursis concordataire définitif accordé au titulaire jusqu'au (?P<until>\d{1,2} octobre \d{4})")
    if m:
        return [event('sole_proprietor_definitive_moratorium_final_extension', m)], ''

    m = match(rf"L'association est dissoute par décision de l'assemblée générale du (?P<decision_date>{DATE})\. Liquidateurs: (?P<name1>{PERSON}), président, et (?P<name2>{PERSON}), trésorier, lesquels continuent à signer collectivement à deux")
    if m:
        return [event('association_dissolved_two_continuing_liquidators', m), *[person('association_dissolved_two_continuing_liquidators', m, m[f'name{i}'], role='Liquidator', signing='Kollektivunterschrift zu zweien', organization_role='président' if i == 1 else 'trésorier') for i in (1, 2)]], ''

    return [], leftover
