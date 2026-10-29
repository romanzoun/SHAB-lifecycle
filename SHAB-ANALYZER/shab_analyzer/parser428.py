from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser63, parser88, parser105, parser125, parser142, parser153, parser213

# Reuse historical patterns: these clauses remain owned by their original rules.
_LEGACY = tuple(p for module in (parser63, parser88, parser105, parser125,
                                 parser142, parser153, parser213)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser428_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>Einzelrichter am Kantonsgericht) die provisorische Nachlassstundung bis (?P<until_date>{DATE})verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_missing_space', m, 'status_changed', provisional=True, extended=True)], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}) \((?P<country>{NAME})\), nouvelle associée (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_new_associate_missing_separator', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), lequel n'exerce pas la signature sociale\. Associés: (?P=seller) pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal) et (?P=buyer) pour (?P=count) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_associates_recap_no_signing', m, 'ownership_changed', currency='CHF', buyer_signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf'Administration: (?P<name1>{NAME}), maintenant domicilié à (?P<place1>{NAME}), nommé vice-président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), président, lesquels signent individuellement')
    if m:
        return [person('two_administrators_individual_signing_residence', m, m[f'name{i}'], role, 'Einzelunterschrift', m[f'place{i}']) for i, role in ((1, 'vice-président'), (2, 'président'))], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante présidente avec (?P=count) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_new_female_manager_president', m, 'ownership_changed', currency='CHF'), person('new_female_manager_president', m, m['buyer'], 'associée-gérante présidente', place=m['place'])], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P=count) parts de CHF (?P=nominal), gérant (?P=seller), qui reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal), est nommé président')
    if m:
        return [event('share_transfer_new_male_manager_president', m, 'ownership_changed', currency='CHF'), person('seller_appointed_president_after_transfer', m, m['seller'], 'président'), person('buyer_appointed_manager_after_transfer', m, m['buyer'], 'gérant', place=m['place'])], ''

    m = match(rf'Die mit Entscheid vom (?P<decision_date>{DATE}) gewährte Nachlassstundung wird mit Wirkung ab dem (?P<effective_date>{DATE}) um weitere (?P<months>drei) Monate bis zum (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('moratorium_extended_effective_date', m, 'status_changed', extended=True)], ''

    # German register wording also occurs in French publications.
    m = match(rf'Gelöschte Person: (?P<removed>{NAME}), Gesellschafterin, (?P<removed_count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY})\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<before>{COUNT}) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Einzelunterschrift')
    if m:
        return [event('associate_removed_remaining_holding_increased', m, 'ownership_changed', currency='CHF'), person('remaining_associate_manager_individual_signing', m, m['name'], 'Gesellschafter, Geschäftsführer', 'Einzelunterschrift')], ''

    m = match(rf'Mit Entscheid des (?P<court>Präsidenten des Bezirksgerichts {NAME}) vom (?P<decision_day>\d{{2}})\. (?P<decision_month>Juli) (?P<decision_year>\d{{4}}) wurde die Auflösung der Gesellschaft gemäss Entscheid des (?P=court) vom (?P<previous_date>{DATE}) widerrufen', 'de')
    if m:
        try:
            datetime(int(m['decision_year']), 7, int(m['decision_day']))
        except ValueError:
            return [], text
        return [event('court_dissolution_revoked_written_month', m, 'status_changed', dissolution_revoked=True)], ''

    m = match(rf'\[bisher: (?P<surname>{NAME}), (?P<given_names>{NAME}), von (?P<origin1>{NAME}) und (?P<origin2>{NAME}), in (?P<place>{NAME}), Mitglied des Stiftungsrates, ohne Zeichnungsberechtigung\]', 'de')
    if m and leftover in source_text and re.search(r'Nachtrag des im SHAB Nr\. \d+ vom ' + DATE, source_text):
        return [event('foundation_historical_officer_supplement', m, historical=True, previous_role='Mitglied des Stiftungsrates', previous_signing='ohne Zeichnungsberechtigung')], ''

    m = match(rf"Rectification de l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): Apport en nature et reprise de biens: Selon contrat du (?P<contract_date>{DATE}), est fait apport de (?P<count>{COUNT}) actions nominatives et liées de CHF (?P<nominal>{MONEY}) de (?P<contributed_company>{NAME}) \((?P<contributed_uid>{UID})\), à (?P<place>{NAME}), pour le prix de CHF (?P<price>{MONEY})\. En contrepartie, est remis à l'apporteur (?P=count) actions de CHF (?P=nominal), nominatives et \. Le solde de CHF (?P<balance>{MONEY}) constitue des autres réserves issues du capital \(agio\) \(et non pas une réserve issue d'apport en capital\)")
    if m and re.search(r"il est remis à l'apporteur " + re.escape(m['count']) + r' actions de CHF ' + re.escape(m['nominal']) + r', nominatives et liées selon statuts\.', source_text):
        return [event('contribution_capital_reserve_classification_corrected', m, 'capital_changed', corrected=True, reserve_type='autres réserves issues du capital (agio)', previous_reserve_type="réserve issue d'apport en capital", share_restriction='liées selon statuts')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) \(kein Fremdkapital\) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_no_liabilities_contract_inventory', m, 'assets_transferred', currency='CHF', no_liabilities=True)], ''
    return [], text
