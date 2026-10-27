from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser50, parser84, parser131, parser163, parser183, parser233, parser252

NAME = r'[^,;.\[\]\n]+?'
# Reuse existing patterns: legacy clauses must also pass through in isolation.
_LEGACY = (
    parser50._FR_ADMINISTRATION_PAIR,
    parser50._FR_OFFICIAL_DELETION_NO_OPPOSITION,
    parser84._FR_FOUNDATION_GIVEN_NAMES_CORRECTED,
    parser131._DE_DEFINITIVE_MORATORIUM_EXTENDED,
    parser163._DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY,
    parser183._DE_STATUTES_DATE_CAPITAL_CORRECTED,
    parser233._FR_RESTRICTION_REMOVED_THEN_LIQUIDATOR,
    parser252._FR_LIQUIDATOR_AND_SHARE_RESTRICTION,
)


def extract_parser407_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete residual variants evidenced by the release fixtures."""
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

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf'Administration: (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), lesquels signent collectivement à deux')
    if m:
        return [person('three_administrators_president_joint_signing', m, m[f'name{i}'], 'Präsident des Verwaltungsrates' if i == 1 else 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', m.groupdict().get(f'place{i}')) for i in (1, 2, 3)], ''

    m = match(rf"L'administrateur (?P<previous_name>{NAME}) porte les prénoms de (?P<given_names>{NAME})")
    if m:
        return [event('administrator_given_names_specified', m, 'publication_corrected', kind='person', corrected=True)], ''

    m = match(rf'\((?P<german_name>[^()]+ in Liquidation)\) \((?P<italian_name>[^()]+ in liquidazione)\) \((?P<english_name>[^()]+ in liquidation)\)\. Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) ne sont plus restreintes quant à la transmissibilité selon l\'(?P<legal_basis>article 685a, al\. 3 CO)')
    if m:
        return [event('liquidation_name_translations_three_languages', m, 'company_name_changed', translations={lang: m[key] for lang, key in (('de', 'german_name'), ('it', 'italian_name'), ('en', 'english_name'))}), event('registered_shares_transfer_restrictions_removed_article', m, 'capital_changed', transfer_restricted=False)], ''

    m = match(r"La ditta è cancellata per cessazione dell'attività aziendale", 'it')
    if m:
        return [event('sole_proprietorship_deleted_activity_ceased', m, 'status_changed', deleted=True)], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<previous_name>{NAME}), dont le nom de famille exact est (?P<name>{NAME}), est désormais de (?P<origin>{NAME}), toujours à (?P<place>{NAME})")
    if m:
        return [person('family_name_corrected_origin_changed', m, m['name'], place=m['place'], corrected=True)], ''

    m = match(r"Aucune opposition motivée n'ayant été présentée ou l'entreprise individuelle ayant cessé ses activités, elle est radiée d'office, conformément à l'(?P<legal_basis>art\. 159, al\. 5, let\. a aORC)")
    if m:
        return [event('sole_proprietorship_official_deletion_alternative_grounds', m, 'status_changed', deleted=True, official=True)], ''

    m = match(rf'In der am (?P<entry_date>{DATE}) unter TR-Nr\. (?P<entry>{COUNT}) vorgenommenen Eintragung wurde irrtümlich das Statutendatum mit (?P<previous_date>{DATE}) statt mit (?P<date>{DATE}) wiedergegeben', 'de')
    if m:
        return [event('statutes_date_entry_corrected', m, 'publication_corrected', kind='statutes_date', corrected=True)], ''

    # The previous parser360 variant explicitly owns "drei"; only "vier" is new.
    m = match(rf'Mit Urteil vom (?P<decision_date>{DATE}) hat die Einzelrichterin im summarischen Verfahren des Bezirksgerichts (?P<court_place>{NAME}) die gewährte definitive Nachlassstundung um (?P<extension>vier) Monate bis (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('definitive_moratorium_extended_four_months_judgment', m, definitive=True, extended=True)], ''

    m = match(rf'Les (?P<voting_count>{COUNT}) actions nominatives de CHF (?P<voting_nominal>{MONEY}) sont désormais privilégiées quant au droit de vote et les (?P<previous_count>{COUNT}) actions nomnatives de CHF (?P<previous_nominal>{MONEY}) sont transformées en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY})')
    if m:
        number = lambda key: Decimal(m[key].replace("'", ''))
        if number('previous_count') * number('previous_nominal') == number('count') * number('nominal'):
            return [event('voting_preference_and_registered_share_split_typo', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Fusion: Übernahme der Aktiven von CHF (?P<assets>{MONEY}) und des Fremdkapitals von CHF (?P<liabilities>{MONEY}) der (?P<absorbed_name>[^,;\[\]\n]+?) \((?P<absorbed_uid>{UID})\), in (?P<absorbed_place>{NAME}), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Da dieselbe Gesellschafterin alle Stammanteile der übertragenden und der übernehmenden Gesellschaft hält, findet weder eine Kapitalerhöhung, noch eine Zuteilung von Stammanteilen statt', 'de')
    if m:
        return [event('merger_assets_liabilities_common_sole_associate', m, 'company_merged', currency='CHF', capital_increase=False, shares_allocated=False)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) dem Rekurs vom (?P<appeal_date>{DATE}) gegen das Konkurseröffnungsurteil vom (?P<bankruptcy_date>{DATE}) die aufschiebende Wirkung erteilt \((?P<legal_basis>Art\. 159 HRegV)\)')
    if m:
        return [event('mixed_language_bankruptcy_appeal_suspensive_effect', m, 'status_changed', suspensive_effect=True)], ''

    m = match(rf'Die Zweigniederlassung von (?P<place>{NAME}) ist gelöscht \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)')
    if m:
        return [event('mixed_language_branch_deleted_notice_reference', m, 'branch_changed', removed=True)], ''
    return [], text
