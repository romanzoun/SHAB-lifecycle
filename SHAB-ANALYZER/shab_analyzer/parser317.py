from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser317_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; preserve unsupported input."""
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
                if k.endswith('_date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, m, kind='organization_changed', **extra):
        return _event(*context, kind, rule, {**m.groupdict(), 'action': rule.split('.')[2], **extra})

    def person(rule, m, key, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', rule, m[key], role=role, signing=signing, place=m[place] if place else None, extra={**m.groupdict(), **extra})

    def number(m, key):
        return Decimal(m[key].replace("'", ''))

    m = match(rf"Nouvel administarteur(?: avec signature individuelle:| :) (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME})", 'fr', rf"Nouvel administarteur avec signature individuelle: (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME})")
    if m:
        return [person('fr.text.administrator_appointed_typo.v1', m, 'name', 'Mitglied des Verwaltungsrates', 'Einzelunterschrift', place='place')], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID}) \), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Genossenschaft über\. Die Genossenschafter der übertragenden Genossenschaft erhalten pro Anteilschein zu CHF (?P<previous_nominal>{MONEY}) der übertragenden Genossenschaft (?P<count>{COUNT}) Anteilscheine zu CHF (?P<nominal>{MONEY}) der übernehmenden Genossenschaft und eine Ausgleichszahlung von CHF (?P<compensation>{MONEY})', 'de')
    if m:
        if number(m, 'previous_nominal') != number(m, 'count') * number(m, 'nominal') + number(m, 'compensation'):
            return [], leftover
        return [event('de.text.cooperative_merger_cash_compensation.v1', m, 'company_merged', currency='CHF')], ''

    m = match(rf'Mit Entscheid der Einzelrichterin des (?P<court>{NAME}), (?P<division>{NAME}), vom (?P<decision_date>{DATE}) wurde eine definitive Nachlassstundung von vier Monaten bis (?P<end_date>{DATE}) bewilligt\. Als Sachwalterin wird die (?P<administrator>[^()]+) \((?P<administrator_uid>{UID})\), Herr (?P<representative>{NAME}), (?P<street>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME}), ernannt', 'de')
    if m:
        if datetime.strptime(m['end_date'], '%d.%m.%Y') <= datetime.strptime(m['decision_date'], '%d.%m.%Y'):
            return [], leftover
        return [event('de.text.definitive_moratorium_administrator.v1', m, 'status_changed', duration_months=4)], ''

    m = match(rf'Kommanditsumme neu: CHF (?P<capital>{MONEY}) \[bisher: CHF (?P<previous_capital>{MONEY})\]\. Erhöhung Kommanditkapital durch Ausgabe neuer Kommanditen', 'de')
    if m:
        if number(m, 'capital') <= number(m, 'previous_capital'):
            return [], leftover
        return [event('de.text.limited_partnership_capital_increased.v1', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"\[finora: Inventario di beni \(mobili d'ufficio ed attrezzature\) per il valore di CHF (?P<valuation>{COUNT})\.-- accettati dalla società per CHF (?P<capital>{COUNT})\.-- interamente computati sul capitale azionario contro rimessa all'apportatore di (?P<count>{COUNT}) azioni al portatore da CHF (?P<nominal>{COUNT})\.--\. Contratto di apporto ed inventario: (?P<agreement_date>{DATE})\.\]", 'it')
    if m:
        if number(m, 'capital') != number(m, 'count') * number(m, 'nominal'):
            return [], leftover
        return [event('it.text.previous_contribution_in_kind.v1', m, historical=True, currency='CHF')], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given>{NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}), membro, con firma individuale', 'it')
    if m:
        rule = 'it.text.registered_person_corrected.v1'
        return [_person_event(*context, 'officer_changed', rule, m['surname'] + ', ' + m['given'], place=m['place'], role='Mitglied des Verwaltungsrates', signing='Einzelunterschrift', extra=m.groupdict())], ''

    m = match(rf'\]\. (?P<place>{NAME}) \((?P<branch_uid>{UID})\)\. \[gestrichen: (?P=place) \((?P<previous_uid>{UID})\)\]', 'de', rf'Zweigniederlassung neu: \[folgende Zweigniederlassung wird gelöscht\]\. \[gestrichen: (?P<removed_place>{NAME}) \((?P<removed_uid>{UID})\)\]\. (?P<place>{NAME}) \((?P<branch_uid>{UID})\)\. \[gestrichen: (?P=place) \((?P<previous_uid>{UID})\)\]')
    if m:
        return [event('de.text.branch_register_updated.v1', m)], ''

    m = match(rf'Signature collective à deux à été conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de et à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), tous directeurs\. (?P=name1) et (?P=name2) ne signent pas entre eux', 'fr')
    if m:
        rule = 'fr.text.three_directors_signing_pair_excluded.v1'
        return [person(rule, m, f'name{i}', 'Direktor', 'Kollektivunterschrift zu zweien', f'place{i}', excluded_signing_pair=[m['name1'], m['name2']]) for i in (1, 2, 3)], ''

    m = match(rf'La liquidation est opérée sous la raison de commerce (?P<legal_name>{NAME}) en liquidation, par (?P<liquidator>[^()]+) \((?P<liquidator_uid>{UID})\), à (?P<place>{NAME}), nommée liquidatrice', 'fr')
    if m:
        return [event('fr.text.corporate_liquidator_appointed.v1', m, legal_name=m['legal_name'] + ' en liquidation'), person('fr.text.corporate_liquidator_appointed.v1', m, 'liquidator', 'Liquidatorin', place='place')], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<resolution_date>{DATE}) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P<authorization_date>{DATE}) gemäss näherer Umschreibung in den Statuten angepasst\. \. Die Generalversammlung hat mit Beschluss vom (?P=resolution_date) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P=authorization_date) geändert\. \[bisher: Die Generalversammlung hat mit Beschluss vom (?P=authorization_date) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<previous_date>{DATE}) geändert\.\]', 'de')
    if m:
        return [event('de.text.authorized_conditional_capital_provisions_changed.v1', m, 'capital_changed')], ''

    pattern = rf"Les administratrices (?P<name1>{NAME}) et (?P<name2>{NAME}) sont nommées liquidatrices"
    shares = rf"Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant l'entier du capital-actions, ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)"
    m = match(pattern + r'(?: avec signature collective à deux\. )?' + r' ?' + shares, 'fr', pattern + r' avec signature collective à deux\. ' + shares)
    if m:
        rule = 'fr.text.two_liquidators_share_restrictions_removed.v1'
        return [person(rule, m, key, 'Liquidatorin', 'Kollektivunterschrift zu zweien') for key in ('name1', 'name2')] + [event(rule, m, 'capital_changed', transfer_restricted=False)], ''

    classes = rf"(?P<count1>{COUNT}) actions de CHF (?P<nominal1>{MONEY}), nominatives et liées, de Type A, privilégiées quant au droit de vote et (?P<count2>{COUNT}) actions de CHF (?P<nominal2>{MONEY}), nominatives, de Type B, ordinaires"
    old_classes = r"(?P=count1) actions de CHF (?P=nominal1), nominatives et liées, de Type A, privilégiées quant au droit de vote et (?P=count2) actions de CHF (?P<previous_nominal2>" + MONEY + r"), nominatives, de Type B, ordinaires"
    m = match(rf"Rectification de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): Capital-actions: CHF (?P<capital>{MONEY}), entèrement libéré, divisé en " + classes + r' \(et non pas divisé en ' + old_classes + r'\)', 'fr')
    if m:
        if number(m, 'capital') != number(m, 'count1') * number(m, 'nominal1') + number(m, 'count2') * number(m, 'nominal2'):
            return [], leftover
        return [event('fr.text.share_class_nominal_corrected_typo.v1', m, 'capital_changed', fully_paid=True, currency='CHF')], ''

    return [], leftover
