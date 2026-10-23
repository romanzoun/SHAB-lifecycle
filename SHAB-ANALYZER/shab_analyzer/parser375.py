from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser145 import _FR_ASSOCIATE_ORGANIZATION_SEAT_CHANGED
from .parser174 import _DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_CHANGED

PERSON = r'[^,;.]+?'


def extract_parser375_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed variants; earlier rule ownership and source context are preserved."""
    leftover = text.strip()
    legacy = {'fr': (_FR_ASSOCIATE_ORGANIZATION_SEAT_CHANGED,),
              'de': (_DE_CONDITIONAL_AND_AUTHORIZED_CAPITAL_CHANGED,)}
    if any(p.fullmatch(leftover) for p in legacy.get(language, ())):
        return [], leftover
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(r'(?:^|\. )' + source_pattern + r'\.$', source_text)
            if not source or any(source[k] != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for k, v in m.groupdict().items():
                    if k.endswith('date'):
                        datetime.strptime(v, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    def num(v):
        return Decimal(v.replace("'", ''))

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que les associés (?P<name1>{PERSON}) et (?P<name2>{PERSON}) sont respectivement titulaires de (?P<count1>{COUNT}) et (?P<count2>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non de CHF (?P<previous_nominal>{MONEY}), comme publié\)", 'fr')
    if m:
        return [event('two_associates_share_nominal_corrected', m, currency='CHF')], ''

    transfer = rf"L'associé-gérant (?P<seller>{PERSON}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}), nouvelle associée avec (?P=transferred) parts de CHF (?P=nominal), gérante"
    ending = rf' (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)'
    m = match(transfer + ending, 'fr', transfer + r' avec signature collective à deux\.' + ending)
    if m and num(m['before']) == num(m['transferred']) + num(m['remaining']):
        return [event('share_transfer_new_female_collective_manager', m, currency='CHF'), person('share_transfer_new_female_collective_manager', m, m['buyer'], m['place'], 'associée-gérante', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Infolge Systemfehler wurde beim bisher Text der bisherige Wohnort \[bisher: (?P<previous_place>{PERSON})\] nicht aufgeführt\. Korrekt wäre: \[bisher: in (?P=previous_place), ohne eingetragene Funktion, mit Kollektivunterschrift zu zweien\]', 'de')
    if m:
        return [event('previous_residence_system_error_corrected', m, previous_role='ohne eingetragene Funktion', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Spaltung: Die mit dem Betrieb des (?P<business>{PERSON}) verbundenen Aktiven und Passiven gehen gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE}) auf die (?P<recipient>{PERSON}), in (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\), über', 'de')
    if m:
        return [event('business_assets_liabilities_split_transferred', m, 'assets_transferred')], ''

    corrected = rf'Persona iscritta corretta: (?P<surname>{PERSON}), (?P<given>{PERSON}), cittadino italiano, in (?P<place>{PERSON}) \((?P<country>[A-Z]{{2}})\), socio, senza diritto di firma, con (?P<count>{COUNT}) quote da CHF (?P<nominal>{MONEY})'
    m = match(corrected, 'it', corrected + rf' \[no: (?P=surname), (?P<previous_given>{PERSON})\]')
    if m and m['given'] != m['previous_given']:
        return [person('associate_given_name_corrected_unsigned', m, m['surname']+' '+m['given'], m['place'], 'socio', 'ohne Zeichnungsberechtigung', previous_name=m['surname']+' '+m['previous_given'], currency='CHF')], ''

    m = match(r'Organe de publication: FOSC\. Communication aux membres: communication personnelle aux associées', 'fr')
    if m:
        return [event('cooperative_publication_personal_member_communications', m, publication_medium='FOSC', member_communications='communication personnelle aux associées')], ''

    m = match(rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{PERSON}), in (?P<absorbed_place>{PERSON}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}) , che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le quote della società trasferente, per cui la fusione avviene senza aumento di capitale e senza attribuzione di quote', 'it')
    if m:
        return [event('wholly_owned_merger_without_quota_allocation', m, 'company_merged', currency='CHF', wholly_owned=True, capital_increase=False, share_allocation=False)], ''

    m = match(rf'L\'associée "(?P<name>[^"\n]+)" \((?P<uid>{UID})\) a maintenant son siège à (?P<place>[^,;.]+)', 'fr')
    if m:
        return [event('corporate_associate_swiss_seat_changed', m)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF CHF (?P<assets>{MONEY}) auf die (?P<recipient>{PERSON}), in (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_duplicated_currency', m, 'assets_transferred', currency='CHF')], ''

    capital = rf'(?P<statutes_date>{DATE})\. Die Gesellschaft hat mit Beschluss vom (?P<conditional_date>{DATE}) eine Erhöhung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\. Die Generalversammlung hat mit Beschluss vom (?P<authorized_date>{DATE}) eine Anpassung des genehmigten Aktienkapitals gemäss näherer Umschreibung in den Statuten beschlossen'
    m = match(capital, 'de', rf'Statutenänderung: (?P<first_statutes_date>{DATE})\. ' + capital)
    if m:
        return [event('conditional_increase_authorized_capital_adjusted', m, 'capital_changed')], ''

    m = match(rf'Les liquidateurs (?P<name1>{PERSON}) et (?P<name2>{PERSON}) signent individuellement', 'fr')
    if m:
        return [person('two_liquidators_individual_signing', m, m[f'name{i}'], role='Liquidator', signing='Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Änderung des mit Beschluss vom (?P<previous_date>{DATE}) eingeführten genehmigten Aktienkapitals gemäss näherer Umschreibung in den Statuten beschlossen', 'de')
    if m:
        return [event('previously_introduced_authorized_capital_changed', m, 'capital_changed')], ''
    return [], leftover
