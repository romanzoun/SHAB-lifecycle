from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser285_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract complete fixture-backed clauses; preserve unsupported or invalid text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    reference = rf"L'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que "

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'administrateur président (?P<name>{NAME}) signe individuellement \(et non pas collectivement à deux\)")
    if m:
        return [person('fr.persons.president_signing_corrected.v1', m['name'], role='administrateur président', signing='Einzelunterschrift', extra={'correction': True, 'previous_signing': 'Kollektivunterschrift zu zweien', 'entry': m['entry'], 'entry_date': m['entry_date']})], ''

    m = match(r'Nouvelle succursale: (?P<place1>[^.;]+?) \((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\) \[précédemment: (?P<previous_place1>[^\]]+)\]\. (?P<place2>[^.;]+?) \((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\) \[précédemment: (?P<previous_place2>[^\]]+)\]')
    if m:
        return [event('fr.text.two_branch_identifiers.v1', action='branch_changed', place=m[f'place{i}'], branch_uid=m[f'uid{i}'], previous_place=m[f'previous_place{i}']) for i in (1, 2)], ''

    m = match(reference + rf"le nom de famille de l'associé-gérant président est (?P<name>{NAME}) \(et non: (?P<previous_name>{NAME})\)")
    if m:
        return [person('fr.persons.associate_manager_name_corrected.v1', m['name'], role='associé-gérant président', extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que selon décision de son assemblée générale du (?P<day>\d{{1,2}}) (?P<month>novembre) (?P<year>\d{{4}}) \(et non du (?P<previous_day>\d{{1,2}}) (?P<previous_month>décembre) (?P<previous_year>\d{{4}}) comme publié\)")
    if m:
        try:
            corrected = datetime(int(m['year']), 11, int(m['day'])).strftime('%d.%m.%Y')
            previous = datetime(int(m['previous_year']), 12, int(m['previous_day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        restored = leftover.replace('en ce sens que selon', 'en ce sens que la société a prononcé sa dissolution selon')
        if restored in source_text:
            return [event('fr.text.dissolution_resolution_date_corrected.v1', action='dissolution_date_corrected', correction=True, resolution_date=corrected, previous_resolution_date=previous, entry=m['entry'], entry_date=m['entry_date'], notice_date=m['notice_date'], notice_id=m['notice_id'], page=m['page'])], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund des Entscheids des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation im Sinne von Art\. 164 Abs\. 1 lit\. d HRegV wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[gestrichen: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('de.text.court_reinstatement_for_liquidation.v1', action='reinstatement', purpose='liquidation', legal_basis='Art. 164 Abs. 1 lit. d HRegV', previous_deletion_basis='Art. 159 Abs. 5 lit. a HRegV', **m.groupdict())], ''

    m = match(reference + rf"l'administrateur (?P<name>{NAME}) dispose de la signature collective à deux \(et non: signature individuelle\)")
    if m:
        return [person('fr.persons.administrator_signing_corrected.v1', m['name'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'correction': True, 'previous_signing': 'Einzelunterschrift', **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf"Procuration collective à deux a été conférée à (?P<name>{NAME}), jusqu'ici directeur; ses pouvoirs sont modifiés en ce sens")
    if m:
        return [person('fr.persons.director_to_collective_procuration.v1', m['name'], signing='Kollektivprokura zu zweien', extra={'previous_role': 'directeur'})], ''

    m = match(rf"(?P<name1>{NAME}) et (?P<name2>{NAME}), jusqu'ici avec procuration individuelle, signent désormais par procuration collective à deux, avec un administrateur")
    if m:
        return [person('fr.persons.two_procurations_with_administrator.v1', m[f'name{i}'], signing='Kollektivprokura zu zweien', extra={'previous_signing': 'Einzelprokura', 'signing_restriction': 'avec un administrateur'}) for i in (1, 2)], ''

    m = match(rf"(?P<seller1>{NAME}) cède sa part de CHF (?P<nominal1>{MONEY}) et (?P<seller2>{NAME}) cède sa part de CHF (?P<nominal2>{MONEY}) à (?P<buyer>{NAME}), nouvel associé, titulaire d'une part de CHF (?P=nominal1) et d'une part de CHF (?P=nominal2), qui reste seul gérant et continue à signer individuellement")
    if m and all(number(m[f'nominal{i}']) > 0 for i in (1, 2)):
        rule = 'fr.persons.two_single_shares_transferred.v1'
        return [event(rule, action='share_transfer', seller=m[f'seller{i}'], buyer=m['buyer'], shares=1, share_nominal=m[f'nominal{i}']) for i in (1, 2)] + [person(rule, m['buyer'], role='associé-gérant', signing='Einzelunterschrift', extra={'sole_manager': True, 'share_classes': [{'shares': 1, 'share_nominal': m[f'nominal{i}']} for i in (1, 2)]})], ''

    m = match(rf"Nouvelle division du capital-actions: (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives\. Capital-actions actuel: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives \(jusqu'ici: (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives et liées selon statuts\)\. La clause statutaire concernant la restriction de transmissibilité des actions est radiée")
    if m and all(number(m[k]) > 0 for k in ('count', 'nominal', 'capital', 'previous_count', 'previous_nominal')) and number(m['capital']) == number(m['count']) * number(m['nominal']) == number(m['previous_count']) * number(m['previous_nominal']):
        if leftover in source_text:
            return [event('fr.text.share_split_restrictions_removed.v1', action='share_division_changed', fully_paid=True, restricted_by_statutes=False, previous_restricted_by_statutes=True, **m.groupdict())], ''

    m = match(rf"Les associés-gérants (?P<name1>{NAME}) et (?P<name2>{NAME}) cèdent chacun (?P<transferred>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvelle associée avec (?P<received>{COUNT}) parts de CHF (?P=nominal), gérante avec signature individuelle\. (?P=name1) et (?P=name2) restent tous deux titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'received', 'remaining')) and number(m['received']) == 2 * number(m['transferred']) and number(m['previous']) == number(m['remaining']) + number(m['transferred']):
        restored = leftover
        if restored in source_text:
            rule = 'fr.persons.two_managers_transfer_new_manager.v1'
            return [person(rule, m[f'name{i}'], role='associé-gérant', extra={'shares': int(number(m['remaining'])), 'previous_shares': int(number(m['previous'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['buyer'], role='associée-gérante', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['place'], 'shares': int(number(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf'Gemäss Verfügung des Bezirksgerichts (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) wird dem Gesellschafter untersagt, seine Stammanteile an der Gesellschaft zu verkaufen', 'de')
    if m:
        return [event('de.text.court_share_sale_prohibited.v1', action='share_sale_prohibited', court='Bezirksgericht ' + m['court_place'], decision_date=m['decision_date'])], ''

    return [], leftover
