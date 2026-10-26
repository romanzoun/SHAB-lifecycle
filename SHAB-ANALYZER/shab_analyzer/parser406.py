from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event, _FR_MONTHS
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser52, parser78, parser100, parser101, parser113, parser132, parser162, parser227, parser243

NAME = r'[^,;.\[\]\n]+?'
# Complete earlier rules retain ownership, including in isolated calls.
_LEGACY = (
    parser52._FR_ASSOCIATION_DISSOLUTION,
    parser78._FR_ASSOCIATE_MANAGER_TRANSFER,
    parser100._DE_NEW_PERSON_MIXED_LANGUAGE,
    parser101._DE_NEW_PERSON_WITHOUT_SIGNATURE_MIXED_LANGUAGE,
    parser113._DE_REMOVED_BUSINESS_OFFICES_WITH_HEADING,
    parser132._FR_ORGANIZATION_SHARE_TRANSFER,
    parser162._DE_AUTHORIZED_CAPITAL_MODIFIED,
    parser227._DE_EARLY_DELETION_EXPERT_CONFIRMATION,
    parser243._FR_MANAGER_GIVEN_NAME_CORRECTED_APPOINTED_LIQUIDATOR,
)


def extract_parser406_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed residual variants; existing events and payloads stay intact."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='de', evidence=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if evidence:
            source = re.search(r'(?<!\S)' + evidence + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
        try:
            for date in re.findall(DATE, m[0]):
                datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, *, fields=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **(m.groupdict() if fields is None else fields), **extra, 'name': name, 'place': place})

    m = match(rf'(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}) \((?P<buyer_uid>{UID})\), désormais titulaire de (?P<received>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)', 'fr')
    if m:
        number = lambda k: int(m[k].replace("'", ''))
        if number('transferred') + number('remaining') == number('before') and number('received') >= number('transferred'):
            return [event('partial_shares_transfer_corporate_recipient', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Neu eingetragene Person: (?P<name>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Kollektivunterschrift zu zweien', 'fr')
    if m:
        return [person('mixed_language_person_joint_signing_no_role', m, m['name'], signing='Kollektivunterschrift zu zweien', place=m['place'])], ''

    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<liquidation_name>{NAME} in Liquidation)\. Eingetragene Person geändert: (?P<name>{NAME}), vorsitzender Geschäftsführer, Einzelunterschrift, neu vorsitzender Geschäftsführer, Liquidator, Einzelunterschrift, nun von (?P<origin>{NAME}) \(Gemeindefusion\)', 'fr')
    if m:
        return [event('mixed_language_dissolution_resolution', m, 'status_changed', dissolved=True), event('mixed_language_liquidation_name', m, 'company_name_changed'), person('presiding_manager_liquidator_origin_merger', m, m['name'], 'vorsitzender Geschäftsführer, Liquidator', 'Einzelunterschrift')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<count>{COUNT}) Ansprüche \(Fondsanteile\) am vertraglichen Immobilienanlagefonds (?P<fund>{NAME}) mit einem Nettoinventarwert von CHF (?P<nav>{MONEY}) pro Anspruch, zuzüglich CHF (?P<cash_adjustment>{MONEY}) als Spitzenausgleich durch Barabgeltung')
    if m:
        return [event('asset_transfer_fund_units_nav_cash', m, 'assets_transferred', currency='CHF')], ''

    pattern = rf"L'associé-gérant président (?P<seller1>{NAME}) a cédé une part de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), nouvel associé pour une part de CHF (?P=nominal)\. L'associé-gérant (?P<seller2>{NAME}) a cédé une part de CHF (?P=nominal) à (?P<buyer2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé pour une part de CHF (?P=nominal), et une part de CHF (?P=nominal) à (?P<buyer3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvel associé pour une part de CHF (?P=nominal)\. Les associés (?P=buyer2), (?P=buyer3) et (?P=buyer1) sont nommés gérants ; les pouvoirs de (?P=buyer1) sont modifiés en ce sens"
    m = match(pattern, 'fr', evidence=pattern.replace('sont nommés gérants ;', 'sont nommés gérants avec signature individuelle;'))
    if m:
        transfers = [event('single_share_transfer_three_new_managers', m, 'ownership_changed', seller=m['seller1' if i == 1 else 'seller2'], buyer=m[f'buyer{i}'], transferred='1', currency='CHF') for i in (1, 2, 3)]
        managers = [person('three_associates_appointed_individual_signing_managers', m, m[f'buyer{i}'], 'gérant', 'Einzelunterschrift', m.groupdict().get(f'place{i}')) for i in (2, 3, 1)]
        return transfers + managers, ''

    m = match(rf'\[gestrichen: Weitere Geschäftsstelle: (?P<office>{NAME}), (?P<street>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME})\]')
    if m:
        return [event('additional_business_office_deleted', m, 'address_changed', removed=True)], ''

    m = match(rf"(?P<previous_name>{NAME}), dont le prénom exact est (?P<name1>{NAME}), et (?P<name2>{NAME}) sont maintenant d'(?P<origin>{NAME})", 'fr')
    if m:
        return [person('given_name_corrected_pair_origin_changed', m, m['name1'], corrected=True), person('pair_origin_changed_after_name_correction', m, m['name2'], fields={'origin': m['origin']})], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) eine Änderung des genehmigten Aktienkapitals gemäss näherer Umschreibung in den Statuten beschlossen')
    if m:
        return [event('authorized_share_capital_clause_changed_general_meeting', m, 'capital_changed', kind='authorized_capital')], ''

    m = match(r"Selon décision de son assemblée générale du (?P<day>\d{1,2}) (?P<month>novembre) (?P<year>\d{4}), l'association a prononcé sa dissolution", 'fr')
    if m:
        try:
            datetime(int(m['year']), _FR_MONTHS[m['month']], int(m['day']))
        except ValueError:
            return [], text
        return [event('association_dissolved_written_november_date', m, 'status_changed', dissolved=True)], ''

    m = match(rf'Mit dem im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde der bisherige Text nicht vollständig publiziert\. Korrekt wäre: (?P<name>{NAME}) \((?P<uid>{UID})\), in (?P<place>{NAME}), Revisionsstelle \[bisher: (?P=name) \((?P<previous_registry_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\)\]')
    if m:
        return [event('auditor_incomplete_publication_corrected', m, 'publication_corrected', kind='auditor', corrected=True)], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) des (?P<court>{NAME}) wurde der Gesellschaft eine provisorische Nachlassstundung von (?P<duration>vier) Monaten gewährt\. Als provisorische Sachwalterin amtet die (?P<name>{NAME}) \((?P<administrator_uid>{UID})\), in (?P<place>{NAME}) \(verantwortliche Person: (?P<representative>{NAME})\)')
    if m:
        return [event('provisional_moratorium_four_months_representative', m, 'organization_changed', provisional=True), person('provisional_corporate_administrator_representative', m, m['name'], 'provisorische Sachwalterin', place=m['place'])], ''

    m = match(rf'Die Liquidation ist mit Bestätigung der zugelassenen Revisionsexpertin vom (?P<confirmation_date>{DATE}) vor Ablauf des Sperrjahres beendet')
    if m:
        return [event('liquidation_completed_early_expert_confirmation', m, 'status_changed', liquidation_completed=True, before_blocking_year=True)], ''
    return [], text
