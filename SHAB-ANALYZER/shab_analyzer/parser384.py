from __future__ import annotations

import re
from decimal import Decimal
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser133 import _FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER
from .parser236 import _FR_TWO_APPOINTED_DIRECTORS_PROXY_REVOKED
from .parser81 import _DE_REMOVED_ADDITIONAL_ADDRESSES

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser384_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Add only bounded, sample-attested variants after the existing parsers."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (_FR_ONE_SHARE_TRANSFER_UNSIGNED_BUYER, _FR_TWO_APPOINTED_DIRECTORS_PROXY_REVOKED, _DE_REMOVED_ADDITIONAL_ADDRESSES)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value.replace('-', '.'), '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=m.groupdict().get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{NAME}), associée, (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), gérante, présidente, signature individuelle, domiciliée à (?P<place>{NAME}) \(et non pas (?P<previous_place>{NAME})\)")
    if m:
        return [person('associate_manager_president_domicile_corrected', m, m['name'], 'associée, gérante, présidente', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>\d{{2}}-\d{{2}}-\d{{4}}) est rectifiée en ce sens que l'associée (?P<name>[^;\n]+?) \(n° (?P<registry_id>\d+)\) est domiciliée à (?P<place>[^;\n]+?) \(et non aux (?P<previous_country>[A-Z]{{3}})\)")
    if m:
        return [event('corporate_associate_domicile_corrected', m, 'publication_corrected')], ''

    m = match(rf"Secondo dichiarazione dell'(?P<declaration_date>{DATE}) la società non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata", 'it')
    if m:
        return [event('audit_waiver_dell_declaration', m, ordinary_audit_exempt=True, limited_audit_waived=True)], ''

    m = match(rf"(?P<seller>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession d'une part de CHF (?P=nominal) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour une part de CHF (?P=nominal)")
    if m:
        # Signing was consumed upstream; require the attested source, and keep that event.
        if not source_text.endswith(leftover.rstrip('.') + ' avec signature collective à deux.'):
            return [], text
        return [event('single_share_transfer_new_collective_associate', m, transferred_count='1', currency='CHF', buyer_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), nommées directrices, signent désormais collectivement à deux; leur procuration est radiée')
    if m:
        return [person('directresses_appointed_proxies_revoked', m, m[k], 'directrice', 'Kollektivunterschrift zu zweien', proxy_revoked=True) for k in ('name1', 'name2')], ''

    m = match(rf"Les (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) du gérant (?P<seller>{NAME}), jusqu'ici associé, ont fait l'objet d'une vente de gré à gré à l'associé-gérant (?P<buyer>{NAME}), maintenant domicilié à (?P<place>{NAME}), qui détient désormais (?P<total>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        if not 0 < Decimal(m['transferred'].replace("'", '')) <= Decimal(m['total'].replace("'", '')):
            return [], text
        return [event('private_sale_manager_shareholding_transferred', m, currency='CHF', seller_remains_manager=True)], ''

    m = match(rf'Aktiengesellschaft\. Mit Entscheid vom (?P<decision_date>{DATE}) wird der Gesellschaft die definitive Nachlassstundung um (?P<months>sechs) Monate bis (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('definitive_moratorium_extended_company_decision', m, 'status_changed')], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Verfügung der Aufsichtsbehörde vom (?P<decision_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: keine', 'de')
    if m:
        return [event('foundation_asset_transfer_recipient_uid_before_place', m, currency='CHF', consideration='keine')], ''

    m = match(rf'Die Gesellschaft wird gemäss Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\. \[Die in Bezug auf den Liquidator und das Liquidationsdomizil bisher eingetragenen Tatsachen gelten weiterhin\.\]', 'de')
    if m:
        return [event('company_reinstated_liquidator_facts_retained', m, 'status_changed', liquidator_facts_retained=True)], ''

    m = match(rf'Bei der nachfolgenden Mutation wurde der bisherige Wohnort nicht publiziert\. Deshalb erfolgt folgender Nachtrag: (?P<name>{NAME}, {NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Mitglied des Verwaltungsrates, mit Einzelunterschrift \[bisher: in (?P<previous_place>{NAME}), ohne eingetragene Funktion, mit Einzelunterschrift\]', 'de')
    if m:
        return [person('board_member_previous_domicile_supplemented', m, m['name'], 'Mitglied des Verwaltungsrates', 'Einzelunterschrift', corrected=True)], ''

    m = match(rf'(?P<name1>{NAME}), désormais présidente et (?P<name2>{NAME}), sont nommées administratrices et continuent à signer individuellement')
    if m:
        return [person('administratrices_appointed_signing_retained', m, m[k], role, 'Einzelunterschrift') for k, role in [('name1', 'administratrice présidente'), ('name2', 'administratrice')]], ''

    address = r'[^\[\]\n]+?, \d{4} [^\[\]\n]+?'
    m = match(rf'(?P<labelled>(?:\[gestrichen: Weitere Adresse: {address}\.\]\. )+)\[gestrichen: (?P<unlabelled>{address})\]', 'de')
    if m:
        addresses = re.findall(r'\[gestrichen: Weitere Adresse: (.+?)\.\]', m['labelled'])
        return [event('additional_addresses_deleted_mixed_labels', m, addresses=addresses + [m['unlabelled']])], ''
    return [], text
