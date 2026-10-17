from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser334_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded sample-backed residues after the existing parser chain."""
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), Vorsitzender der Geschäftsleitung \(CEO\), Kollektivunterschrift zu zweien, neu von (?P<origin>{NAME})', 'de')
    if m:
        return [person('ceo_origin_changed', m, m['name'], 'Vorsitzender der Geschäftsleitung (CEO)', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf"Par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<holder1>{NAME}) est désormais titulaire de (?P<count1>{COUNT}) parts de CHF (?P=nominal), et (?P<holder2>{NAME}) est désormais titulaire d'une part de CHF (?P=nominal)", 'fr')
    if m:
        return [event('share_holdings_after_transfer', m, 'ownership_changed', currency='CHF', count2='1')], ''

    # This publication is tagged French but contains German register sections.
    # Require the complete six-person structure, including previous entries.
    m = match(r'Ausgeschiedene Personen und erloschene Unterschriften: (?P<departed>[^;]+? ohne Zeichnungsberechtigung)\. Eingetragene Personen neu oder mutierend: (?P<officers>[^;]+? \[bisher: [^\[\]]+\]; [^;]+? \[bisher: [^\[\]]+\]; [^;]+? \[bisher: [^\[\]]+\]; [^;]+? ohne Zeichnungsberechtigung; [^;]+? ohne Zeichnungsberechtigung)', 'fr')
    if m:
        chunks = [m['departed'], *m['officers'].split('; ')]
        events = []
        pattern = (r'(?P<name>[^,]+, (?:Dr\. )?[^,]+), '
                   r'(?:(?:genannt (?P<known_as>[^,]+)), )?von (?P<origin>.+?), in (?P<place>.+?), '
                   r'(?P<role>Präsident des Stiftungsrates|Mitglied des Stiftungsrates(?:, Aktuar|, Kassier)?), '
                   r'(?P<signing>ohne Zeichnungsberechtigung|mit Kollektivunterschrift zu zweien)'
                   r'(?:, mit Kollektivunterschrift zu zweien)?(?: \[bisher: (?P<previous>[^\[\]]+)\])?')
        for index, chunk in enumerate(chunks):
            item = re.fullmatch(pattern, chunk)
            if not item:
                return [], leftover
            data = item.groupdict()
            events.append(_person_event(
                *context, 'officer_removed' if index == 0 else 'officer_changed',
                'fr.text.german_foundation_officers.v1', data['name'],
                role=data['role'], place=data['place'],
                signing=data['signing'].removeprefix('mit '),
                extra={k: v for k, v in data.items() if k not in ('name', 'place') and v is not None},
            ))
        return events, ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss dem öffentlich beurkundeten Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar vom (?P<inventory_date>{DATE}) Aktiven \(inklusive der darin enthaltenen Liegenschaften (?P<properties>[^()]+)\) von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine', 'de')
    if m:
        return [event('notarized_asset_transfer_no_consideration', m, 'ownership_changed', currency='CHF', no_consideration=True)], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine weitere bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen', 'de')
    if m:
        return [event('further_conditional_capital_increase', m, 'capital_changed')], ''

    m = match(rf'Statutenänderung: Statut vom (?P<statute_date>{DATE})', 'de')
    if m:
        return [event('statute_date_recorded', m)], ''

    m = match(rf"L'inscription n°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'administrateur (?P<name>{NAME}) est directeur et cette dernière fonction a été radiée par erreur", 'fr')
    if m:
        return [person('director_role_reinstated_correction', m, m['name'], 'Verwaltungsrat und Direktor')], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}), Verwaltungsratsmitglied, Kollektivunterschrift, neu mit dem Namen (?P<name>{NAME})', 'fr')
    if m:
        return [person('board_member_name_changed', m, m['name'], 'Verwaltungsratsmitglied', 'Kollektivunterschrift')], ''

    french_date = r'\d{1,2} juin \d{4}'
    m = match(rf"Suppression de la clause statutaire relative à l'augmentation autorisée du capital \(fondée sur la décision d'autorisation du (?P<previous_authorization>{french_date})\), par décision du (?P<removal_decision>{french_date}) \. L'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital par décision du (?P<authorization_decision>{french_date})\. Pour les détails, voir les statuts", 'fr')
    if m:
        try:
            for value in m.groupdict().values():
                datetime.strptime(value.replace('juin', '06'), '%d %m %Y')
        except ValueError:
            return [], leftover
        return [event('authorized_capital_clause_replaced', m, 'capital_changed')], ''

    m = match(rf"Radiation de la restriction statutaire de transmissibilité des (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives", 'fr')
    if m:
        return [event('registered_share_transfer_restriction_removed', m, 'capital_changed', currency='CHF', fully_paid=True)], ''

    m = match(rf"Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant la totalité du capital-actions, ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)\. L'administratrice (?P<name>{NAME}), désormais à (?P<place>{NAME}), est nommée liquidatrice", 'fr')
    if m:
        return [event('all_registered_shares_transfer_restriction_removed', m, 'capital_changed', currency='CHF'), person('board_member_appointed_liquidator', m, m['name'], 'Verwaltungsrat und Liquidator', place=m['place'])], ''

    m = match(rf'Diritto di firma corretto: (?P<surname>{NAME}), (?P<given_name>{NAME}), cittadino italiano, in (?P<place>{NAME}), con procura collettiva a due', 'it')
    if m:
        return [person('collective_procuration_corrected', m, f"{m['surname']}, {m['given_name']}", signing='Kollektivprokura zu zweien', place=m['place'])], ''

    return [], leftover
