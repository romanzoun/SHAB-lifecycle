from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, COUNT, UID

PERSON = r'[^,;]+?'


def extract_parser368_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses after all previous parser versions."""
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
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'In der am (?P<entry_date>{DATE}) unter TR-Nr\. (?P<entry>\d+) vorgenommenen Eintragung wurde bei (?P<name>{PERSON}, {PERSON}) der Bisher-Text unvollständig wiedergegeben\. Richtig: \[bisher: in (?P<previous_place>{PERSON}), Gesellschafter, ohne Zeichnungsberechtigung, mit einem Stammanteil von CHF (?P<previous_nominal>{MONEY})\]', 'de')
    if m:
        return [person('associate_previous_details_corrected', m, m['name'], currency='CHF', previous_role='Gesellschafter', previous_signing='ohne Zeichnungsberechtigung', previous_count='1')], ''

    m = match(rf"Création d'un capital-participations de CHF (?P<capital>{MONEY}), fondée sur la décision de l'assemblée générale relative à une augmentation conditionnelle du capital-participations du (?P<decision_date>{DATE}), par l'émission de (?P<count>{COUNT}) bons de CHF (?P<nominal>{MONEY}), nominatifs\. Suppression de la clause statutaire relative à l'augmentation autorisée du capital-participation, fondée sur la décision d'autorisation du (?P<authorization_date>{DATE})")
    if m:
        return [event('participation_capital_created_authorization_deleted', m, currency='CHF', security_kind='bons nominatifs')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le vice-président porte le nom exact (?P<name>[^()]+?) \(et non pas (?P<previous_name>[^()]+)\)")
    if m:
        return [person('vice_president_name_corrected', m, m['name'], role='Vizepräsident')], ''

    m = match(rf'(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), sont gérants et signent collectivement à deux, avec un gérant')
    if m:
        return [person('two_managers_joint_signing_with_manager', m, m[f'name{i}'], m[f'place{i}'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', signing_restriction='avec un gérant') for i in (1, 2)], ''

    m = match(rf'Transfert de patrimoine: selon contrat des (?P<first_contract_day>\d{{2}})\.(?P<first_contract_month>\d{{2}}) et (?P<contract_date>{DATE}) et décision de l\'autorité de surveillance du (?P<decision_date>{DATE}), la fondation en liquidation a transféré une partie des actifs de CHF (?P<assets>{MONEY}) et une partie des passifs envers les tiers de CHF (?P<liabilities>{MONEY}) à la société "(?P<recipient>[^";]+)" à (?P<recipient_place>[^();]+) \((?P<recipient_uid>{UID})\)\. Contre-prestation: aucune')
    if m:
        # The first contract date has no year in the publication; do not infer it.
        try:
            datetime.strptime(m['first_contract_day'] + '.' + m['first_contract_month'] + '.2000', '%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('liquidating_foundation_partial_asset_transfer', m, currency='CHF', consideration='aucune')], ''

    m = match(rf'(?P<name>{PERSON}), associé, nommé gérant, exerce désormais la signature sociale, individuellement')
    if m:
        return [person('associate_appointed_manager_individual_signing', m, m['name'], role='Geschäftsführer', signing='Einzelunterschrift')], ''

    m = match(r'Prestations des associés: Obligations de fournir des prestations \(pour les détails, voir les statuts\)')
    if m:
        return [event('associate_ancillary_obligations_statutes', m, obligations='Obligations de fournir des prestations', details='statuts')], ''

    m = match(rf"(?P<name>{PERSON})\. Nouvelle raison sociale de l'associée et numéro d'identification des entreprises: (?P=name) \((?P<uid>{UID})\), laquelle a maintenant son siège à (?P<place>[^,;.]+)")
    if m:
        return [event('corporate_associate_name_uid_seat_changed', m)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>[^;]+?), in (?P<court_place>{PERSON}), über die Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, den Konkurs eröffnet\. Neue Firma: (?P<company_name>[^;]+? in Liquidation)')
    if m and int(m['time'][:2]) < 24 and int(m['time'][3:]) < 60:
        return [event('bankruptcy_opened_german_text_french_notice', m)], ''

    m = match(rf"(?P<seller1>{PERSON}) et (?P<seller2>[^;]+?) ne sont plus associés; leurs pouvoirs sont radiés; leurs parts, respectivement (?P<count1>{COUNT}) et (?P<count2>{COUNT}) de CHF (?P<nominal>{MONEY}), ont été cédées à la nouvelle associée (?P<recipient>{PERSON}), à (?P<recipient_place>{PERSON}), (?P<recipient_country>[^.;]+)\. (?P<seller3>{PERSON}), jusqu'ici associé, gérant, président, a cédé ses (?P<count3>{COUNT}) parts de CHF (?P=nominal) à la nouvelle associée (?P=recipient), à (?P=recipient_place), (?P=recipient_country)\. La nouvelle associée (?P=recipient), à (?P=recipient_place), (?P=recipient_country), détient (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal) et n'exerce pas la signature sociale\. (?P=seller3) est désormais gérant, président et est domicilié à (?P<manager_place>{PERSON}), (?P<manager_country>[^.;]+)")
    if m:
        return [event('three_associates_transfer_unsigned_corporate_recipient', m, currency='CHF', recipient_signing='ohne Zeichnungsberechtigung', manager_role='Präsident der Geschäftsführung')], ''

    m = match(rf'Administraiton: (?P<name1>{PERSON}), nommé président, (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), vice-président, (?P<name3>{PERSON}), de (?P<origin3>{PERSON}), à (?P<place3>{PERSON}), secrétaire, et (?P<name4>{PERSON}), maintenant domiciliée à (?P<place4>{PERSON}), lesquels signent collectivement à deux')
    if m:
        roles = ('Präsident des Verwaltungsrates', 'Vizepräsident des Verwaltungsrates', 'Sekretär', None)
        return [person('board_joint_signing_administration_typo', m, m[f'name{i}'], m.groupdict().get(f'place{i}'), roles[i-1], 'Kollektivunterschrift zu zweien') for i in range(1, 5)], ''

    m = match(rf'Die Befreiung von der Revisionsstellenpflicht wurde mit Verfügung der Aufsichtsbehörde vom (?P<decision_date>{DATE}) widerrufen', 'de')
    if m:
        return [event('audit_exemption_revoked_by_supervisor', m)], ''

    return [], leftover
