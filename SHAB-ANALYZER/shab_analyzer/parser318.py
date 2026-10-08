from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser318_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume bounded sample-backed clauses, leaving unsupported input intact."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('_dash_date'):
                    datetime.strptime(v, '%d-%m-%Y')
                elif k.endswith('_date'):
                    datetime.strptime(v, '%d.%m.%Y')
                elif k == 'time':
                    datetime.strptime(v, '%H.%M')
        except ValueError:
            return None
        return m

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    def person(rule, m, key, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, rule, m[key], role=role, signing=signing, place=m[place] if place else None, extra={**m.groupdict(), **extra})

    m = match(rf'Liquidateurs: les gérants (?P<name1>{NAME}), maintenant domicilié à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}) et (?P<name2>{NAME}), maintenant domicilié à (?P<place2>{NAME}), lesquels continuent à signer individuellement', 'fr')
    if m:
        rule = 'fr.text.two_managers_liquidators_residence_changed.v1'
        return [person(rule, m, f'name{i}', 'Liquidator', 'Einzelunterschrift', f'place{i}') for i in (1, 2)], ''

    m = match(rf'Mit Verfügung des (?P<appeal_court>{NAME}) vom (?P<decision_date>{DATE}) ist der Beschwerde gegen die Verfügung des Einzelrichters des (?P<court>{NAME}) vom (?P<bankruptcy_date>{DATE}) aufschiebende Wirkung zuerkannt worden\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen \[bisher: Über den Inhaber dieses Einzelunternehmens ist mit Verfügung des Einzelrichters des (?P=court) vom (?P=bankruptcy_date) mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('de.text.sole_trader_bankruptcy_appeal_suspended.v1', m, 'status_changed', bankruptcy_entry_removed=True, suspensive_effect=True)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar vom (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('de.text.asset_transfer_inventory_assets_only.v1', m, currency='CHF')], ''

    m = match(r"Radiation de la mention selon laquelle la société n'est pas soumise à un contrôle ordinaire et a renoncé à un contrôle restreint", 'fr')
    if m:
        return [event('fr.text.audit_exemption_statement_removed.v1', m, audit_exemption_statement_removed=True)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) den Betriebsteil "(?P<business_unit>[^"\n]+)" mit Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('de.text.business_unit_asset_transfer.v1', m, currency='CHF')], ''

    tail = rf', in (?P<place>[^,]+?), hat mit Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) die Zweigniederlassung auf die neu gegründete (?P<recipient>[^()]+) \((?P<recipient_uid>{UID})\), in (?P<recipient_place>[^,]+?), übertragen\. Die Zweigniederlassung wird gemäss Art\. 112 Abs\. 2 HRegV als solche der (?P=recipient) \((?P=recipient_uid)\), in (?P=recipient_place), weitergeführt'
    m = match(r'Angaben zur ' + tail, 'de', rf'Angaben zur Zweigniederlassung neu: Die vormalige Hauptniederlassung (?P<previous_name>[^,]+), neu (?P<holding_name>[^()]+) \((?P<previous_uid>{UID})\)' + tail)
    if m:
        return [event('de.text.branch_transferred_new_head_office.v1', m)], ''

    m = match(rf'Nouveau membre du conseil de fondation avec signature collective à deux avec le président ou les vices-présidents: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})', 'fr')
    if m:
        return [person('fr.text.foundation_member_restricted_signing.v1', m, 'name', 'Mitglied des Stiftungsrates', 'Kollektivunterschrift zu zweien', 'place', signing_restriction='avec le président ou les vices-présidents')], ''

    m = match(rf'Abspaltung: Ein Teil der Aktiven geht gemäss Spaltungsplan vom (?P<plan_date>{DATE}) auf die neu gegründete (?P<recipient>{NAME}), in (?P<place>[^,()]+?) \((?P<recipient_uid>{UID})\), über', 'de')
    if m:
        return [event('de.text.demerger_assets_new_company.v1', m)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_dash_date>\d{{2}}-\d{{2}}-\d{{4}}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est originaire d'(?P<origin>[^()]+) \(et non de (?P<previous_origin>[^()]+)\) et domicilié à (?P<place>[^()]+) \(et non à (?P<previous_place>[^()]+)\)", 'fr')
    if m:
        return [person('fr.text.person_origin_residence_corrected.v1', m, 'name', place='place')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée par la radiation de la mention relative à la renonciation au contrôle restreint", 'fr')
    if m:
        return [event('fr.text.audit_waiver_deletion_entry_completed.v1', m, audit_waiver_statement_removed=True)], ''

    m = match(rf"(?P<name1>{NAME}), d' (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}) et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), sont membres du conseil d'administration, avec signature collective à deux, avec le président ou le secrétaire", 'fr')
    if m:
        rule = 'fr.text.three_board_members_restricted_signing.v1'
        return [person(rule, m, f'name{i}', 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', f'place{i}', signing_restriction='avec le président ou le secrétaire') for i in (1, 2, 3)], ''

    # The supplied historical notice is tagged German but contains Italian text.
    m = match(rf'Persone dimissionarie e firme cancellate: (?P<surname1>{NAME}), (?P<given1>{NAME}), da (?P<origin1>{NAME}), in (?P<place1>{NAME}), presidente della gerenza, con firma individuale\. Nuove persone iscritte o modifiche: (?P<surname2>{NAME}), (?P<given2>{NAME}), da (?P<origin2>{NAME}), in (?P<place2>{NAME}), presidente della gerenza, con firma individuale', 'de')
    if m:
        rule = 'it.text.management_chair_replaced_german_metadata.v1'
        return [_person_event(*context, kind, rule, m[f'surname{i}'] + ', ' + m[f'given{i}'], place=m[f'place{i}'], role='Vorsitzender der Geschäftsführung', signing='Einzelunterschrift', extra={**m.groupdict(), 'action': action}) for i, kind, action in ((1, 'officer_removed', 'removed'), (2, 'officer_changed', 'appointed'))], ''

    return [], leftover
