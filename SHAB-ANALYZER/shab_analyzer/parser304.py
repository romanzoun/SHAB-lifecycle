from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser304_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; retain unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, m):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict()})

    def person(rule, m, **kwargs):
        return _person_event(*context, 'officer_changed', rule, m['name'], extra=m.groupdict(), **kwargs)

    m = match(rf'(?P<name>{NAME}), maintenant domiciliée à (?P<place>{NAME}), signe désormais par procuration individuelle', 'fr')
    if m:
        return [person('fr.text.procuration_individual_new_domicile.v1', m, place=m['place'], signing='Einzelprokura')], ''

    m = match(r'Die Gesellschaft ist nun ohne eingetragene Revisionsstelle', 'de')
    if m:
        return [event('de.text.no_registered_auditor.v1', m)], ''

    m = match(rf"Complément: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\) est complétée en ce sens que la mention relative à la renonciation à l'organe de révision est radiée", 'fr')
    if m:
        return [event('fr.text.audit_waiver_deleted_completion.v1', m)], ''

    m = match(rf'Mit der Berichtigung des im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde irrtümlich das Jahr (?P<year>\d{{4}}) nicht korrekt ausgeschrieben, richtig wäre: Berichtigung des im SHAB Nr\. (?P=notice_number) vom (?P=notice_date) publizierten TR-Eintrags Nr\. (?P=entry) vom (?P=entry_date)', 'de')
    if m:
        return [event('de.text.register_reference_year_corrected.v1', m)], ''

    m = match(rf"Par décisions des (?P<first_date>{DATE}) et (?P<second_date>{DATE}) prononcées par le (?P<court>{NAME}), la société est réinscrite d'office et la liquidation de la faillite en la forme sommaire a été autorisée", 'fr')
    if m:
        return [event('fr.text.reinstatement_summary_bankruptcy.v1', m)], ''

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>{COUNT}), TR (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) und Publikation im SHAB Nr\. (?P<notice_number>{COUNT}) vom (?P<notice_date>{DATE}) wurde als letztes SHAB-Zitat irrtümlich SHAB Nr\. (?P<previous_number>{COUNT}) vom (?P<previous_date>{DATE}) genannt statt korrekt SHAB Nr\. (?P<correct_number>{COUNT}) vom (?P<correct_date>{DATE})', 'de')
    if m:
        return [event('de.text.previous_notice_reference_corrected.v1', m)], ''

    m = match(rf'(?P<name>{NAME}) continue de signer collectivement à deux, désormais sans restriction', 'fr')
    if m:
        return [person('fr.text.collective_signing_restriction_removed.v1', m, signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"L'assemblea generale ha introdotto una disposizione statutaria relativa all'aumento del capitale autorizzato mediante decisione del (?P<authorized_date>{DATE})\. Per i dettagli si rinvia allo statuto\. \[radiati: L'assemblea generale ha introdotto una disposizione statutaria relativa all'aumento di capitale autorizzato mediante decisione del (?P<previous_first_date>{DATE})\. Per i dettagli vedi statuti\. \]\. \[radiati: L'assemblea generale ha introdotto una disposizione statutaria relativa all'aumento del capitale autorizzato mediante decisione del (?P<previous_second_date>{DATE})\. Per i dettagli si rinvia allo statuto\.\]\. L'assemblea generale ha introdotto una disposizione statutaria relativa all'aumento condizionale del capitale mediante decisione del (?P<conditional_date>{DATE})\. Per i dettagli vedi statuti", 'it')
    if m:
        return [event('it.text.authorized_conditional_capital_clauses.v1', m)], ''

    m = match(rf'(?P<name>{NAME}), membre de la direction, est élue administratrice; elle continue de signer collectivement à deux', 'fr')
    if m:
        return [person('fr.text.management_member_elected_administrator.v1', m, role='administratrice', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<reference>\d+/\d+)\) est rectifiée en ce sens que le liquidateur se nomme (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\) et que l'adresse de liquidation exacte est (?P<address>[^;]+?), c/o (?P<care_of>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME})", 'fr')
    if m:
        rule = 'fr.text.liquidator_name_address_corrected.v1'
        return [event(rule, m), person(rule, m, role='liquidateur')], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) n'exercent plus la signature", 'fr')
    if m:
        rule = 'fr.text.three_administrators_signing_removed.v1'
        return [_person_event(*context, 'officer_changed', rule, m[key], role='administrateur', signing='ohne Zeichnungsberechtigung', extra={'signing_removed': True}) for key in ('name1', 'name2', 'name3')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die "(?P<recipient>{NAME})" \((?P<uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: keine', 'de')
    if m:
        return [event('de.text.assets_transfer_no_consideration.v1', m)], ''

    return [], leftover
