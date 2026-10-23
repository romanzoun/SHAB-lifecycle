from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser109 import _FR_NEW_ADMINISTRATOR

NAME = r'[^,;.()]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser378_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle bounded additional variants without taking ownership of earlier rules."""
    leftover = text.strip()
    if _FR_NEW_ADMINISTRATOR.fullmatch(leftover):
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
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"L'associé-gérant (?P<seller>{NAME}), maintenant domicilié à (?P<seller_place>{NAME}), a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante et présidente pour (?P=count) parts de CHF (?P=nominal)")
    if m:
        return [event('shares_transferred_new_manager_president', m), person('new_associate_manager_president', m, m['buyer'], m['place'], 'associée-gérante et présidente')], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est domiciliée à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}) \(et non pas (?P<previous_place>{NAME}), (?P=country)\)")
    if m:
        return [person('notice_person_domicile_corrected', m, m['name'], m['place'])], ''

    m = match(rf"(?P<seller>{NAME}) jusqu'ici associé pour une part de CHF (?P<nominal>{MONEY}) est maintenant gérant et continue de signer individuellement; sa part de CHF (?P=nominal) a été cédée à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant, pour une part de CHF (?P=nominal)")
    if m:
        return [event('single_share_transferred_manager_retained', m), person('former_associate_manager_retained', m, m['seller'], role='gérant', signing='Einzelunterschrift'), person('new_associate_manager', m, m['buyer'], m['place'], 'associé-gérant')], ''

    m = match(rf'Die Gesellschaft wird gemäss Urteil des (?P<court>[^;]+?) vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen, die am (?P<suspension_date>{DATE}) angeordnete Einstellung des Konkursverfahrens aufgehoben und die Wiederaufnahme des Konkursverfahrens angeordnet\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung der Gesellschaft erhoben wurde, wird diese im Sinne von (?P<legal_basis>Art\. 159 Abs\. 5 lit\. a HRegV) von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('company_reinstated_bankruptcy_suspension_revoked', m, 'status_changed', bankruptcy_reopened=True)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\), handelnd als Fondsleitung und für Rechnung des Anlagefonds (?P<fund>{NAME})\. Gegenleistung: (?P<count>{COUNT}) Ansprüche \(Fondsanteile\) am Immobilienanlagefonds (?P=fund) mit einem Nettoinventarwert von CHF (?P<nav>{MONEY}) pro Anspruch, zuzüglich CHF (?P<cash_adjustment>{MONEY}) als Spitzenausgleich durch Barabgeltung', 'de')
    if m:
        return [event('assets_transferred_for_fund_units_cash_adjustment', m, currency='CHF')], ''

    m = match(rf"L'associé-gérant président (?P<seller>{NAME}), maintenant domicilié à (?P<seller_place>{NAME}), (?P<seller_country>[A-Z]{{3}}), a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=count) parts de CHF (?P=nominal)\. Gérant: l'associé (?P=buyer)")
    if m:
        return [event('president_shares_transferred_new_manager', m), person('new_associate_appointed_manager', m, m['buyer'], m['place'], 'associé-gérant')], ''

    m = match(rf'Nouvelle administratrice : (?P<name>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME})')
    if m:
        return [person('new_administrator_au_domicile', m, m['name'], m['place'], 'administratrice')], ''

    m = match(rf"(?P<seller1>{NAME}), qui est maintenant à (?P<seller_place>{NAME}), et (?P<seller2>{NAME}) \((?P<seller_uid>{UID})\) cèdent respectivement (?P<transferred1>{COUNT}) de ses (?P<before1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et (?P<transferred2>{COUNT}) de ses (?P<before2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante avec (?P<received>{COUNT}) parts de CHF (?P=nominal); (?P=seller1) et (?P=seller2) \((?P=seller_uid)\) restent titulaires respectivement de (?P<remaining1>{COUNT}) et (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('individual_company_partial_shares_transferred', m), person('new_associate_manager_partial_transfer', m, m['buyer'], m['place'], 'associée-gérante')], ''

    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company>{NAME}) in Liquidation\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafterin, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführerin, Einzelunterschrift, neu Gesellschafterin, (?P=count) Stammanteile zu CHF (?P=nominal), Geschäftsführerin, Liquidatorin, Einzelunterschrift', 'de')
    if m:
        return [event('company_dissolved_female_manager_liquidator', m, 'status_changed', liquidation=True), person('female_associate_manager_liquidator', m, m['name'], role='Gesellschafterin, Geschäftsführerin, Liquidatorin', signing='Einzelunterschrift')], ''

    m = match(rf'Gemäss Verfügung des Bezirksgerichts (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) wird dem Gesellschafter untersagt, seine Stammanteile an der Gesellschaft zu verkaufen\. \[bisher: Gemäss Verfügung des Bezirksgerichts (?P=court_place) vom (?P<previous_decision_date>{DATE}) wird dem Gesellschafter untersagt, seine Stammanteile an der Gesellschaft zu verkaufen\.\]', 'de')
    if m:
        return [event('share_sale_prohibition_order_updated', m)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) reste membre du conseil d'administration")
    if m:
        return [person('notice_board_membership_retained', m, m['name'], role="membre du conseil d'administration")], ''

    if language == 'de':
        m = re.search(r'Uebersetzungen der Firma neu: \((?P<translation_fr>[^()]+ \(Suisse\) SA)\) \((?P<translation_en>[^()]+ \(Switzerland\) Ltd)\)\.?$', source_text)
        if m and leftover == 'SA) (' + m['translation_en'] + ')':
            return [event('company_translations_corrected_nested_parentheses', m)], ''
    return [], text
