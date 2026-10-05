from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser275_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete clauses evidenced by the parser-275 fixtures."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, suffix=None):
        m = re.fullmatch(pattern + (r'(?:' + re.escape(suffix) + r')?' if suffix else '') + r'\.?', leftover)
        if not m:
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        if suffix:
            clause = leftover.rstrip('.')
            if not clause.endswith(suffix):
                clause += suffix
            if clause + '.' not in source_text:
                return None
        return m

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, (?P<name2>{NAME}), nommé secrétaire et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country3>[A-Z]{{3}}), tous', ' avec signature individuelle')
    if m:
        rule = 'fr.persons.board_president_secretary_member_individual.v1'
        return [person(rule, m['name1'], role='président', place=m['place1'], signing='Einzelunterschrift', extra={'origin': m['origin1']}), person(rule, m['name2'], role='secrétaire', signing='Einzelunterschrift'), person(rule, m['name3'], role="membre du conseil d'administration", place=m['place3'], signing='Einzelunterschrift', extra={'origin': m['origin3'], 'country': m['country3']})], ''

    m = match(r'\[Die Angabe der Rechtsgrundlagen ist im Rahmen der Umwandlung in eine privatrechtliche Stiftung zu streichen\.\]')
    if m:
        return [event('de.text.foundation_legal_basis_removed.v1', action='legal_basis_removed', reason='conversion_to_private_law_foundation')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est domicilié à (?P<place>{NAME}) \(et non (?P<previous_place>{NAME})\)")
    if m:
        return [person('fr.persons.domicile_corrected_entry.v1', m['name'], place=m['place'], extra={k: v for k, v in m.groupdict().items() if k not in ('name', 'place')} | {'correction': True})], ''

    m = match(rf"Le nom exact d'un membre du conseil est (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('fr.persons.board_member_name_corrected.v1', m['name'], role='membre du conseil', extra={'previous_name': m['previous_name'], 'correction': True})], ''

    m = match(rf'Nouveau gérant: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), sans signature sociale')
    if m:
        return [person('fr.persons.new_manager_without_signature.v1', m['name'], role='gérant', place=m['place'], extra={'origin': m['origin'], 'without_signature': True})], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont nommés liquidateurs', ' avec signature collective à deux')
    if m:
        return [person('fr.persons.three_liquidators_collective.v1', m['name'+str(i)], role='liquidateur', signing='Kollektivunterschrift zu zweien') for i in (1, 2, 3)], ''

    m = match(rf'Signature collective à deux, sauf avec un fondé de pouvoir ou un sous-directeur, a été conférée à (?P<name>{NAME}), nommé sous-directeur; sa procuration est radiée')
    if m:
        return [person('fr.persons.subdirector_restricted_signature_procuration_removed.v1', m['name'], role='sous-directeur', signing='Kollektivunterschrift zu zweien', extra={'signing_restriction': 'sauf avec un fondé de pouvoir ou un sous-directeur', 'procuration_removed': True})], ''

    m = match(rf"L'administrateur (?P<name1>{NAME}), nommé président continue à signer individuellement\. (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de et à (?P<place3>{NAME}), sont membres du conseil d'administration", ' avec signature individuelle')
    if m:
        rule = 'fr.persons.president_two_board_members_individual.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Einzelunterschrift', extra={'signing_continued': True}), person(rule, m['name2'], role="membre du conseil d'administration", place=m['place2'], signing='Einzelunterschrift', extra={'origin': m['origin2']}), person(rule, m['name3'], role="membre du conseil d'administration", place=m['place3'], signing='Einzelunterschrift', extra={'origin': m['place3']})], ''

    m = match(rf"Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<name1>{NAME}) est maintenant associé pour (?P<shares1>{COUNT}) parts de CHF (?P=nominal), (?P<name2>{NAME}) est maintenant associé pour (?P<shares2>{COUNT}) parts de CHF (?P=nominal), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country3>[A-Z]+), est nouvel associé pour (?P=transferred) parts de CHF (?P=nominal)\. L'associé (?P=name3) n'exerce pas la signature sociale")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'nominal', 'shares1', 'shares2')):
        rule = 'fr.persons.share_transfer_two_existing_one_unsigned.v1'
        return [person(rule, m['name'+str(i)], role='associé', extra={'shares': int(number(m['shares'+str(i)])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associé', place=m['place3'], extra={'shares': int(number(m['transferred'])), 'share_nominal': m['nominal'], 'origin': m['origin3'], 'country': m['country3'], 'without_signature': True})], ''

    m = match(rf"L'inscription N°(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée comme suit: les (?P<shares>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives, ne sont plus", ' liées selon statuts')
    if m and number(m['shares']) > 0 and number(m['nominal']) > 0:
        return [event('fr.text.registered_share_restriction_removed_supplement.v1', action='share_transfer_restriction_removed', share_kind='nominatives', **m.groupdict())], ''

    m = match(rf'Nouveaux gérants: (?P<name1>{NAME}), des (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), des (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]+), tous deux', ' avec signature individuelle')
    if m:
        rule = 'fr.persons.two_new_managers_individual.v1'
        return [person(rule, m['name'+str(i)], role='gérant', place=m['place'+str(i)], signing='Einzelunterschrift', extra={'origin': m['origin'+str(i)]} | ({'country': m['country2']} if i == 2 else {})) for i in (1, 2)], ''

    m = match(rf"Le gérant-président (?P<seller>{NAME}) a cédé ses (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<buyer>{NAME}) qui possède désormais (?P<shares>{COUNT}) parts de CHF (?P=nominal)")
    if m and number(m['nominal']) > 0 and 0 < number(m['transferred']) <= number(m['shares']):
        rule = 'fr.persons.manager_president_transfers_all_shares.v1'
        return [person(rule, m['seller'], role='gérant-président', extra={'shares': 0, 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant', extra={'shares': int(number(m['shares'])), 'share_nominal': m['nominal']})], ''

    return [], leftover
