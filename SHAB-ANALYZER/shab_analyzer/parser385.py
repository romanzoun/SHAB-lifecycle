from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser101 import _DE_BUSINESS_OFFICE_REMOVED
from .parser242 import _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser385_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded variants attested by the local version 385 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_DE_BUSINESS_OFFICE_REMOVED, _FR_CONDITIONAL_PARTICIPATION_CAPITAL_INCREASE)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, leftover):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=extra.get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"(?P<seller>{NAME}), maintenant présidente détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=transferred) parts de CHF (?P=nominal) avec signature collective à deux")
    if m:
        original = leftover.replace('maintenant présidente détient', 'maintenant présidente avec signature collective à deux, détient')
        if not source_text.endswith(original.rstrip('.') + '.'):
            return [], text
        return [event('president_share_transfer_new_collective_manager', m, currency='CHF', seller_signing='Kollektivunterschrift zu zweien', buyer_signing='Kollektivunterschrift zu zweien')], ''

    m = match(r'Moritz\. \[gestrichen: Weiteres Geschäftslokal: (?P<deleted_address>\d{4} [^\[\]\n]+)\]', 'de')
    if m:
        address = re.search(r'\[Neue\] Weitere Adresse: (?P<address>[^\[\]\n]+?, \d{4} St\. Moritz)\. \[gestrichen: Weiteres Geschäftslokal: ' + re.escape(m['deleted_address']) + r'\]\.$', source_text)
        if not address:
            return [], text
        return [event('additional_address_fragment_and_office_deleted', m, additional_address=address['address'])], ''

    m = match(rf"La société est dissoute\. (?P<name>{NAME}) \((?P<register>CH-\d{{3}}-\d{{7}}-\d)\), dont le numéro d'identification des entreprises \(IDE/UID\) de l'associée indéfiniment responsable est le \((?P<uid>{UID})\), est nommée liquidatrice")
    if m:
        return [event('dissolution_corporate_general_partner_liquidator', m, 'status_changed', dissolved=True, role='liquidatrice')], ''

    m = match(rf'Mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) ist über diese Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3]):[0-5]\d) Uhr, der Konkurs eröffnet worden', 'de')
    if m:
        return [event('bankruptcy_opened_order_colon_time', m, 'status_changed')], ''

    m = match(rf'(?P<name>{NAME}) continue de signer par procuration, mais désormais individuellement')
    if m:
        return [person('procuration_now_individual', m, m['name'], None, 'Einzelprokura')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss dem öffentlich beurkundeten Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar vom (?P<inventory1_date>{DATE}) und (?P<inventory2_date>{DATE}) Aktiven \(inklusive der darin enthaltenen Liegenschaften (?P<properties>[^()]+)\) von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_two_inventories_cash', m, currency='CHF')], ''

    m = match(rf"Statuts modifiés le (?P<statutes_date_text>1er décembre \d{{4}})\. Les (?P<count>{COUNT}) actions au porteur de CHF (?P<nominal>{MONEY}), formant la totalité du capital-actions, sont converties en (?P=count) actions nominatives de CHF (?P=nominal)")
    if m:
        return [event('bearer_shares_converted_total_capital', m, currency='CHF', previous_kind='au porteur', share_kind='nominatives')], ''

    m = match(rf"L'administrateur (?P<name1>{NAME}), nommé président, signe désormais individuellement\. (?P<name2>{NAME}), jusqu'ici président, n'exerce plus la signature sociale")
    if m:
        return [person('administrator_president_signing_changed', m, m['name1'], 'administrateur président', 'Einzelunterschrift'), person('previous_president_signing_revoked', m, m['name2'], None, None, signing_revoked=True)], ''

    m = match(rf'L\'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la raison sociale de l\'associée avec (?P<count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) est "(?P<name>[^"\n]+)" \(File number (?P<registry_id>\d+)\) \(et non pas "(?P<previous_name>[^"\n]+)"\)')
    if m:
        return [event('corporate_associate_name_corrected_file_number', m, 'publication_corrected')], ''

    pair = lambda a, b: rf'(?P<name{a}>{NAME}), de (?P<origin{a}>{NAME}), à (?P<place{a}>{NAME}), et (?P<name{b}>{NAME}), de (?P<origin{b}>{NAME}), à (?P<place{b}>{NAME}), sont membres du comité cantonal'
    m = match(pair(1, 2) + ' ' + pair(3, 4) + ', sans signature sociale')
    if m:
        original = leftover.replace('comité cantonal ', 'comité cantonal avec signature collective à deux. ', 1)
        if not source_text.endswith(original.rstrip('.') + '.'):
            return [], text
        return [person('cantonal_committee_members_signing', m, m[f'name{i}'], 'membre du comité cantonal', 'Kollektivunterschrift zu zweien' if i < 3 else None, origin=m[f'origin{i}'], place=m[f'place{i}'], signing_authorized=i < 3) for i in range(1, 5)], ''

    transfer = rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), la titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}), à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation: une créance de CHF (?P<consideration>{MONEY})'
    if language == 'fr':
        parts = leftover.rstrip('.').split('. Transfert de patrimoine: ')
        if len(parts) == 2:
            matches = [re.fullmatch(transfer, parts[0]), re.fullmatch(transfer, 'Transfert de patrimoine: ' + parts[1])]
            if all(matches):
                try:
                    for item in matches:
                        datetime.strptime(item['agreement_date'], '%d.%m.%Y')
                        money = lambda key: Decimal(item[key].replace("'", ''))
                        if money('assets') - money('liabilities') != money('net_assets') or money('net_assets') != money('consideration'):
                            return [], text
                except ValueError:
                    return [], text
                return [event('female_proprietor_asset_transfer_claim', item, currency='CHF') for item in matches], ''

    m = match(rf"Augmentation conditionnelle du capital-participation, fondée sur la décision relative à l'octroi de droits du (?P<decision_date>{DATE}), porté de CHF (?P<previous>{MONEY}) à CHF (?P<capital>{MONEY}), par l'émission de (?P<issued>{COUNT}) bons de CHF (?P<nominal>{MONEY}), nominatifs, liés selon statuts\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) bons de participation de CHF (?P=nominal), nominatifs, liés selon statuts")
    if m:
        number = lambda key: Decimal(m[key].replace("'", ''))
        if number('previous') + number('issued') * number('nominal') != number('capital') or number('count') * number('nominal') != number('capital'):
            return [], text
        return [event('conditional_participation_capital_short_issued_bonds', m, currency='CHF', fully_paid=True)], ''
    return [], text
