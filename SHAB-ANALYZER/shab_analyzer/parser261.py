from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _iso_date, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
MONEY = r"[\d']+(?:\.\d+)?"
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser261_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed families; require source for stripped facts."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def source(pattern):
        return re.search(pattern + r'\.$', source_text, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(r'Das Statutenänderungsdatum wird berichtigt \(nicht (?P<previous>\d{1,2}\.\d{1,2}\.\d{4}) sondern (?P<date>\d{1,2}\.\d{1,2}\.\d{4})\)')
    if m:
        try:
            dates = {k: datetime.strptime(m[k], '%d.%m.%Y').date().isoformat() for k in ('previous', 'date')}
        except ValueError:
            return [], leftover
        return [event('statutes_changed', 'de.text.statutes_date_corrected.v1', {'kind': 'statutes', 'action': 'date_corrected', 'date': dates['date'], 'previous_date': dates['previous']})], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt die Geschäftseinheit "(?P<unit>[^"\n]+)" gemäss Vertrag vom (?P<date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}) \(Fremdkapital\) auf die (?P<recipient>{NAME}), in (?P<place>[^.;]+?) \((?P<uid>{UID})\)\. Gegenleistung CHF (?P<consideration>{MONEY})')
    if m:
        return [event('organization_changed', 'de.text.business_unit_asset_transfer.v1', dict(m.groupdict(), kind='asset_transfer', currency='CHF', date=_iso_date(m['date'])))], ''

    m = match(rf'Mit Entscheid des Einzelrichters des (?P<court>{NAME}) vom (?P<date>{DATE}) ist das Konkursverfahren geschlossen worden\. Der Inhaber führt das Einzelunternehmen weiter')
    if m:
        return [event('status_changed', 'de.text.bankruptcy_closed_business_continued.v1', {'kind': 'bankruptcy', 'action': 'closed', 'date': _iso_date(m['date']), 'court': m['court'], 'business_continues': True})], ''

    m = match(r'\[radiati: Altri uffici: (?P<address>[^,.;]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+)\. \]')
    if m:
        return [event('address_changed', 'it.text.other_office_deleted.v1', dict(m.groupdict(), action='removed'))], ''

    m = match(rf'Par suite de cession de (?P<count>\d+) parts de CHF (?P<nominal>{MONEY}), (?P<seller>{NAME}) est maintenant associé pour (?P<remaining>\d+) parts de CHF (?P<seller_nominal>{MONEY}), et (?P<buyer>{NAME}) est maintenant associé pour (?P<received_total>\d+) parts de CHF (?P<buyer_nominal>{MONEY})')
    if m:
        count, remaining, total = (int(m[k]) for k in ('count', 'remaining', 'received_total'))
        if count <= 0 or total < count or m['seller'] == m['buyer'] or len({m[k] for k in ('nominal', 'seller_nominal', 'buyer_nominal')}) != 1:
            return [], leftover
        rule = 'fr.persons.share_transfer_existing_associates.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        return [person(rule, m['seller'], role='associé', extra=dict(common, action='shares_transferred', shares_count=remaining, shares_transferred=count)), person(rule, m['buyer'], role='associé', extra=dict(common, action='shares_received', shares_count=total, shares_received=count))], ''

    m = match(rf'Gelöschte Person: (?P<old>{NAME}), Direktor, Kollektivunterschrift zu zweien\. Neu eingetragene Person: (?P<name>{NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), Direktor, Kollektivunterschrift zu zweien')
    if m:
        rule = 'de.persons.director_replaced.v1'
        return [person(rule, m['old'], role='Direktor', signing='Kollektivunterschrift zu zweien', extra={'action': 'removed'}), person(rule, m['name'], role='Direktor', signing='Kollektivunterschrift zu zweien', place=m['place'], extra={'action': 'appointed', 'nationality': m['nationality']})], ''

    pattern = rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given>{NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}), presidente, con firma individuale'
    m = match(pattern)
    s = source(pattern + rf' \[no: (?P<previous>{NAME}), (?P<previous_given>{NAME})\]') if m else None
    if s and all(m[k] == s[k] for k in m.groupdict()):
        return [person('it.persons.president_name_corrected.v1', f"{m['surname']}, {m['given']}", role='presidente', signing='Einzelunterschrift', place=m['place'], extra={'action': 'name_corrected', 'origin': m['origin'], 'previous_name': f"{s['previous']}, {s['previous_given']}"})], ''

    pattern = rf'(?P<name>{NAME}), administrateur président, est nommé liquidateur'
    m = match(pattern)
    s = source(pattern + r' avec signature individuelle') if m else None
    if s and m['name'].strip() == s['name'].strip():
        return [person('fr.persons.administrator_president_liquidator.v1', m['name'], role='liquidateur', signing='Einzelunterschrift', extra={'action': 'appointed', 'previous_role': 'administrateur président'})], ''

    pattern = rf'Administrateurs: (?P<a>{NAME}), nommée présidente, (?P<b>{NAME}), du (?P<origin_b>{NAME}), à (?P<place_b>{NAME}), et (?P<c>{NAME}), de et à (?P<place_c>{NAME}), tous trois'
    m = match(pattern)
    s = source(pattern + r' avec signature individuelle') if m else None
    if s and m.groupdict() == s.groupdict():
        rule = 'fr.persons.three_administrators_president.v1'
        return [person(rule, m['a'], role='présidente', signing='Einzelunterschrift', extra={'action': 'appointed'}), person(rule, m['b'], role='administrateur', signing='Einzelunterschrift', place=m['place_b'], extra={'action': 'new_or_changed', 'origin': m['origin_b']}), person(rule, m['c'], role='administrateur', signing='Einzelunterschrift', place=m['place_c'], extra={'action': 'new_or_changed', 'origin': m['place_c']})], ''

    members = rf'(?P<a>{NAME}), de (?P<origin_a>{NAME}), au (?P<place_a>{NAME}), (?P<b>{NAME}), de (?P<origin_b>{NAME}), à (?P<place_b>{NAME}), (?P<c>{NAME}), de (?P<origin_c>{NAME}), à (?P<place_c>{NAME}), et (?P<d>{NAME}), du (?P<origin_d>{NAME}), à (?P<place_d>{NAME})'
    m = match(r'Nouveaux membres du conseil de fondation : ' + members)
    s = source(r'Nouveaux membres du conseil de fondation avec signature collective à deux: ' + members) if m else None
    if s and m.groupdict() == s.groupdict():
        return [person('fr.persons.four_foundation_members.v1', m[k], role='membre du conseil de fondation', signing='Kollektivunterschrift zu zweien', place=m['place_'+k], extra={'action': 'appointed', 'origin': m['origin_'+k]}) for k in 'abcd'], ''

    pattern = rf"L'associée (?P<old>{NAME}) \(no (?P<register>[\d ]+ R\.C\.S {NAME})\) a pour nouvelle raison sociale (?P<new>{NAME}) \(no (?P<register_again>[\d ]+ R\.C\.S {NAME})\) et à maintenant son siège à (?P<seat>{NAME}), (?P<country>[A-Z])\. L'associée (?P<a>{NAME}), et (?P<b>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<person_country>[A-Z]) sont gérantes"
    m = match(pattern)
    s = source(pattern + r' avec signature individuelle') if m else None
    if s and m.groupdict() == s.groupdict() and m['register'] == m['register_again']:
        rule = 'fr.persons.corporate_associate_renamed_two_managers.v1'
        events = [person(rule, m['new'], role='associée', place=m['seat'], extra={'action': 'name_and_seat_changed', 'previous_name': m['old'], 'register': m['register'], 'country': m['country']})]
        events.extend(person(rule, m[k], role='gérante', signing='Einzelunterschrift', place=m['place'], extra={'action': 'appointed', 'origin': m['origin'], 'country': m['person_country']}) for k in 'ab')
        return events, ''

    pattern = rf'\]\. (?P<new_place>[^.;]+) \((?P<new_uid>{UID})\)\. (?P<place>[^.;]+) \((?P<uid>{UID})\)\. \[gestrichen: (?P<old_place>[^.;]+) \((?P<old_uid>{UID})\)\]'
    m = match(pattern)
    s = source(rf'Zweigniederlassung neu: \[folgende Zweigniederlassung wird gelöscht\]\. \[gestrichen: (?P<removed_place>[^.;]+) \((?P<removed_uid>{UID})\)' + pattern) if m else None
    if s and all(m[k] == s[k] for k in m.groupdict()) and m['uid'] == m['old_uid']:
        rule = 'de.text.branches_deleted_added_corrected.v1'
        return [event('branch_changed', rule, {'action': 'removed', 'place': s['removed_place'], 'branch_uid': s['removed_uid']}), event('branch_changed', rule, {'action': 'added', 'place': m['new_place'], 'branch_uid': m['new_uid']}), event('branch_changed', rule, {'action': 'place_corrected', 'place': m['place'], 'previous_place': m['old_place'], 'branch_uid': m['uid']})], ''

    return [], leftover
