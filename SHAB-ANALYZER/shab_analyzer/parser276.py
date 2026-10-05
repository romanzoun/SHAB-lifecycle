from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser276_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only complete, fixture-backed clauses; retain unsupported text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
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

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def number(raw):
        return Decimal(raw.replace("'", ''))

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>{COUNT})\) est rectifiée en ce sens que le nom de l'associé-gérant président est (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}) comme publié\)", 'fr')
    if m:
        return [person('fr.persons.manager_president_name_corrected_notice.v1', m['name'], role='associé-gérant président', extra={k: v for k, v in m.groupdict().items() if k != 'name'} | {'correction': True})], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'associé-gérant porte le nom de (?P<name>{NAME}), et non pas (?P<previous_name>{NAME})", 'fr')
    if m:
        return [person('fr.persons.associate_manager_name_corrected.v1', m['name'], role='associé-gérant', extra={k: v for k, v in m.groupdict().items() if k != 'name'} | {'correction': True})], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}), nommée présidente et (?P<name2>{NAME}), jusqu\x27ici président, continuent à signer collectivement à deux', 'fr')
    if m:
        rule = 'fr.persons.board_presidency_changed_signing_continued.v1'
        return [person(rule, m['name1'], role='administratrice présidente', signing='Kollektivunterschrift zu zweien', extra={'signing_continued': True}), person(rule, m['name2'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'président', 'signing_continued': True})], ''

    m = match(rf'Les membres du comité (?P<name1>{NAME}) et (?P<name2>{NAME}) sont nommés respectivement vice-présidente et secrétaire, et signent désormais collectivement à deux', 'fr')
    if m:
        rule = 'fr.persons.committee_vice_president_secretary_collective.v1'
        return [person(rule, m['name'+str(i)], role=role, signing='Kollektivunterschrift zu zweien') for i, role in ((1, 'membre du comité vice-présidente'), (2, 'membre du comité secrétaire'))], ''

    m = match(rf'Liquidateurs: les administrateurs (?P<name1>{NAME}), président et (?P<name2>{NAME}), secrétaire, lesquels continuent à signer individuellement', 'fr')
    if m:
        rule = 'fr.persons.two_board_liquidators_signing_continued.v1'
        return [person(rule, m['name'+str(i)], role='liquidateur', signing='Einzelunterschrift', extra={'board_role': role, 'signing_continued': True}) for i, role in ((1, 'président'), (2, 'secrétaire'))], ''

    m = match(rf'Gérants: les associés (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}) et (?P<name3>{NAME}), tous trois avec signature individuelle', 'fr')
    if m:
        rule = 'fr.persons.three_associate_managers_individual.v1'
        return [person(rule, m['name'+str(i)], role='associé-gérant président' if i == 1 else 'associé-gérant', signing='Einzelunterschrift') for i in (1, 2, 3)], ''

    m = match(rf'Eingetragene Person geändert: (?P<previous_name>{NAME}), Gesellschafterin, (?P<shares>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), vorsitzende Geschäftsführerin, Kollektivunterschrift zu zweien, neu mit dem Namen (?P<name>{NAME})', 'de')
    if m and number(m['shares']) > 0 and number(m['nominal']) > 0:
        return [person('de.persons.associate_chair_manager_name_changed.v1', m['name'], role='Gesellschafterin, vorsitzende Geschäftsführerin', signing='Kollektivunterschrift zu zweien', extra={'previous_name': m['previous_name'], 'shares': int(number(m['shares'])), 'share_nominal': m['nominal']})], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}), und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}), auf die (?P<recipient_name>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY}), unter Vorbehalt einer vertraglich vereinbarten Preisanpassungsklausel', 'de')
    if m and all(number(m[k]) >= 0 for k in ('assets', 'liabilities', 'consideration')):
        return [event('de.text.asset_transfer_price_adjustment_reserved.v1', action='asset_transfer', currency='CHF', price_adjustment_reserved=True, **m.groupdict())], ''

    m = match(rf'Par décision du (?P<decision_date>{DATE}) prononcée par le (?P<court>{NAME}), le recours contre la décision de faillite du (?P<bankruptcy_date>{DATE}) a été rejeté; la faillite est prononcée avec effet dès le (?P<effective_date>{DATE}) à (?P<hour>\d{{1,2}})h(?P<minute>\d{{1,2}})', 'fr')
    if m and int(m['hour']) < 24 and int(m['minute']) < 60:
        return [event('fr.text.bankruptcy_appeal_rejected_effective_time.v1', action='bankruptcy_appeal_rejected', effective_time=f"{int(m['hour']):02d}:{int(m['minute']):02d}", **m.groupdict())], ''

    m = match(rf'Les associés-gérants (?P<name1>{NAME}) et (?P<name2>{NAME}), tous deux maintenant à (?P<place>{NAME}), cèdent chacun (?P<transferred>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvelle associée avec (?P<received>{COUNT}) parts de CHF (?P=nominal), gérante avec signature collective à deux\. (?P=name1) et (?P=name2) restent titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacun', 'fr')
    if m and number(m['nominal']) > 0 and 0 < number(m['transferred']) < number(m['previous']) and number(m['received']) == 2 * number(m['transferred']) and number(m['remaining']) == number(m['previous']) - number(m['transferred']):
        rule = 'fr.persons.two_managers_equal_transfer_new_manager.v1'
        return [person(rule, m['name'+str(i)], role='associé-gérant', place=m['place'], extra={'shares': int(number(m['remaining'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associée-gérante', place=m['place3'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin3'], 'shares': int(number(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf'Les associés-gérants (?P<name1>{NAME}) et (?P<name2>{NAME}) cèdent respectivement (?P<transferred1>{COUNT}) et (?P<transferred2>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvel associé avec (?P<received>{COUNT}) parts de CHF (?P=nominal), gérant avec signature collective à trois\. (?P=name1) et (?P=name2), qui signent désormais collectivement à trois, restent respectivement titulaires de (?P<remaining1>{COUNT}) et (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)', 'fr')
    if m and number(m['nominal']) > 0 and all(0 < number(m['transferred'+str(i)]) < number(m['previous']) and number(m['remaining'+str(i)]) == number(m['previous']) - number(m['transferred'+str(i)]) for i in (1, 2)) and number(m['received']) == number(m['transferred1']) + number(m['transferred2']):
        rule = 'fr.persons.two_managers_transfer_collective_three.v1'
        return [person(rule, m['name'+str(i)], role='associé-gérant', signing='Kollektivunterschrift zu dreien', extra={'shares': int(number(m['remaining'+str(i)])), 'transferred_shares': int(number(m['transferred'+str(i)])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associé-gérant', place=m['place3'], signing='Kollektivunterschrift zu dreien', extra={'origin': m['origin3'], 'shares': int(number(m['received'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"(?P<name1>{NAME}), associé-gérant, cède (?P<transferred1>{COUNT}) de ses (?P<previous1>{COUNT}) parts de CHF (?P<nominal>{MONEY}), et (?P<name2>{NAME}), associé, cède (?P<transferred2>{COUNT}) de ses (?P<previous2>{COUNT}) parts de CHF (?P=nominal) à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvelle associée (?P<received>{COUNT}) parts de CHF (?P=nominal), sans signature\. (?P=name1) reste titulaire de (?P<remaining1>{COUNT}) parts de CHF (?P=nominal) et (?P=name2), de (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)", 'fr')
    if m and number(m['nominal']) > 0 and all(0 < number(m['transferred'+str(i)]) < number(m['previous'+str(i)]) and number(m['remaining'+str(i)]) == number(m['previous'+str(i)]) - number(m['transferred'+str(i)]) for i in (1, 2)) and number(m['received']) == number(m['transferred1']) + number(m['transferred2']):
        rule = 'fr.persons.two_associates_transfer_unsigned_new_associate.v1'
        return [person(rule, m['name'+str(i)], role='associé-gérant' if i == 1 else 'associé', extra={'shares': int(number(m['remaining'+str(i)])), 'transferred_shares': int(number(m['transferred'+str(i)])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associée', place=m['place3'], extra={'origin': m['origin3'], 'shares': int(number(m['received'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    return [], leftover
