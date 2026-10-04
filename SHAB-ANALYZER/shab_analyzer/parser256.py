from __future__ import annotations

import re

from .keys import person_key
from .parser253 import _event, _iso_date, _person_event

DATE = r"\d{2}\.\d{2}\.\d{4}"
MONEY = r"[\d']+(?:\.\d+)?"
NAME = r"[^,.;]+?"
UID = r"CHE-\d{3}\.\d{3}\.\d{3}"


def extract_parser256_leftovers(text, language, publication_id, published_at, org_uid, plz, canton):
    """Complete, bounded families observed in the parser256 fixtures."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r"\.?", leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf"Der Eintrag Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_ref>\d+)\) wird wie folgt ergänzt: Gelöschte andere Adresse: (?P<street>[^,]+), (?P<postal_code>\d{{4}}) (?P<place>{NAME})")
    if m:
        payload = m.groupdict()
        for key in ('entry_date', 'notice_date'):
            payload[key] = _iso_date(payload[key])
        return [event('address_changed', 'de.text.other_address_deleted_supplement.v1', dict(payload, action='deleted', kind='other_address'))], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante avec signature collective à deux\. (?P<again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
    if m and m['seller'] == m['again'] and 0 < int(m['count']) <= int(m['before']) and int(m['before']) - int(m['count']) == int(m['remaining']) and m['nominal'] == m['remaining_nominal']:
        rule = 'fr.persons.partial_share_transfer_new_collective_manager.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        return [person(rule, m['seller'], extra=dict(common, action='shares_transferred', shares_before=int(m['before']), shares_transferred=int(m['count']), shares_count=int(m['remaining']))),
                person(rule, m['buyer'], role='associée-gérante', place=m['place'], signing='Kollektivunterschrift zu zweien', extra=dict(common, action='appointed_and_shares_received', origin=m['origin'], shares_received=int(m['count']), shares_count=int(m['count'])))], ''

    m = match(rf"Eingetragne Person geändert: (?P<name>{NAME}), Verwaltungsratsmitglied, Geschäftsführer, Kollektivunterschrift zu zweien, nun in (?P<place>{NAME})")
    if m:
        return [person('de.persons.board_manager_residence_typo.v1', m['name'], role='Verwaltungsratsmitglied, Geschäftsführer', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'action': 'domicile_changed', 'source_typo': 'Eingetragne'})], ''

    m = match(rf"Neu eingetragene Person: (?P<name>[^()]+) \((?P<uid>{UID})\), in (?P<place>{NAME}), Revisionsstelle\. Der Eintrag betreffend die Erklärung vom (?P<date>{DATE}) über den Verzicht auf die eingeschränkte Revision ist gelöscht worden")
    if m:
        rule = 'de.text.auditor_appointed_waiver_deleted.v1'
        auditor = _person_event(*context, 'auditor_changed', rule, m['name'], role='Revisionsstelle', place=m['place'], extra={'action': 'appointed', 'uid': m['uid']})
        auditor.person_key = person_key(name=m['name'], uid=m['uid'])
        return [auditor, event('auditor_changed', rule, {'kind': 'audit_waiver', 'action': 'deleted', 'declaration_date': _iso_date(m['date'])})], ''

    m = match(rf"Vollständige Adresse: (?P<street>[^,]+), (?P<postal_code>\d{{4}}) (?P<place>{NAME})\. Gelöschte Person: (?P<old>{NAME}), Kollektivprokura zu zweien\. Neu eingetragene Person: (?P<new>{NAME}), von (?P<origin>{NAME}), in (?P<residence>{NAME}), Kollektivprokura zu zweien")
    if m:
        rule = 'de.text.full_address_collective_proxy_replacement.v1'
        return [event('address_changed', rule, {'street': m['street'], 'postal_code': m['postal_code'], 'place': m['place'], 'kind': 'full_address'}),
                person(rule, m['old'], extra={'action': 'removed', 'previous_signing': 'Kollektivprokura zu zweien', 'signing_revoked': True}),
                person(rule, m['new'], place=m['residence'], signing='Kollektivprokura zu zweien', extra={'action': 'appointed', 'origin': m['origin']})], ''

    m = match(rf"\[gestrichen: Mit Entscheid vom (?P<previous_date>{DATE}) hat der (?P<court>{NAME}) eine provisorische Nachlassstundung bis (?P<previous_until>{DATE}) gewährt\.\]\. Mit Entscheid vom (?P<date>{DATE}) hat der (?P<again>{NAME}) die mit Verfügung vom (?P<grant_date>{DATE}) gewährte provisorische Nachlassstundung bis (?P<until>{DATE}) verlängert")
    if m and m['court'] == m['again'] and m['previous_date'] == m['grant_date']:
        return [event('status_changed', 'de.text.provisional_moratorium_extended_struck_clause.v1', {'kind': 'composition_moratorium', 'action': 'extended', 'definitive': False, 'court': m['court'], 'decision_date': _iso_date(m['date']), 'grant_date': _iso_date(m['grant_date']), 'until': _iso_date(m['until']), 'previous_until': _iso_date(m['previous_until'])})], ''

    m = match(rf"(?P<a>{NAME}), maintenant de (?P<origin>{NAME}), et (?P<b>{NAME}) sont désormais à (?P<place>{NAME})")
    if m:
        rule = 'fr.persons.two_residences_one_origin_changed.v1'
        return [person(rule, m['a'], place=m['place'], extra={'action': 'origin_and_domicile_changed', 'origin': m['origin']}), person(rule, m['b'], place=m['place'], extra={'action': 'domicile_changed'})], ''

    m = match(rf"Administration: (?P<a>{NAME}) et (?P<b>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), président, lesquels signe collectivement à deux; les pouvoirs de (?P<again>{NAME}) sont modifiés en ce sens")
    if m and m['a'] == m['again']:
        rule = 'fr.persons.board_president_collective_signing_grammar.v1'
        return [person(rule, m['a'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'action': 'signing_changed'}), person(rule, m['b'], role='administrateur président', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    m = match(rf"La commandite de (?P<a>{NAME}) a été portée de CHF (?P<old_a>{MONEY}) à CHF (?P<new_a>{MONEY})\. La commandite de (?P<b>{NAME}) a été portée de CHF (?P<old_b>{MONEY}) à CHF (?P<new_b>{MONEY})\. (?P<c>{NAME}) jusqu'ici associé indéfiniment responsable a été nommé associé commanditaire, avec une commandite de CHF (?P<new_c>{MONEY}); ses pouvoirs sont radiés")
    if m:
        rule = 'fr.persons.limited_partnership_amounts_role_changed.v1'
        events = [person(rule, m[g], extra={'action': 'limited_partnership_amount_changed', 'currency': 'CHF', 'previous_amount': m['old_'+g], 'amount': m['new_'+g]}) for g in ('a', 'b')]
        events.append(person(rule, m['c'], role='associé commanditaire', extra={'action': 'role_changed', 'previous_role': 'associé indéfiniment responsable', 'amount': m['new_c'], 'currency': 'CHF', 'signing_revoked': True}))
        return events, ''

    m = match(rf"Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>[^()]+) \((?P<uid>{UID})\)\. Gegenleistung: (?P<claims>{MONEY}) Ansprüche an der Gruppe (?P<group>[^.;]+?) der (?P<again>[^.;]+?) in der Höhe von je (?P<value>{MONEY}) aufgrund des per (?P<nav_date>{DATE}) festgelegten Net Asset Values des Anlagevermögens der Anlagegruppe (?P<again_group>[^.;]+)")
    if m and m['recipient'] == m['again'] and m['group'] == m['again_group']:
        payload = m.groupdict()
        del payload['again'], payload['again_group']
        payload.update(kind='asset_transfer', currency='CHF', date=_iso_date(m['date']), nav_date=_iso_date(m['nav_date']))
        return [event('organization_changed', 'de.text.foundation_asset_transfer_investment_claims.v1', payload)], ''

    bond = rf"Die öffentliche Urkunde der Versammlung der Gläubigergemeinschaft vom (?P<date>{DATE}) der (?P<rate>\d+\.\d+)% Covered Bonds von CHF (?P<amount>{MONEY}) \(Valor (?P<valor>\d+) / ISIN (?P<isin>CH\d{{10}})\), fällig am (?P<maturity>{DATE}), ist am (?P<filed>{DATE}) beim Handelsregisteramt des Kantons (?P<canton>{NAME}) eingereicht worden und wird gemäss Art\. 151 HRegV bei den Handelsregisterakten der Schuldnerin aufbewahrt"
    # Consume all repeated clauses atomically, including their punctuation.
    clauses = list(re.finditer(bond + r"(?:\. |\.$|$)", leftover, re.I))
    if clauses and ''.join(m[0] for m in clauses) == leftover:
        events = []
        for m in clauses:
            payload = m.groupdict()
            for key in ('date', 'maturity', 'filed'):
                payload[key] = _iso_date(payload[key])
            events.append(event('organization_changed', 'de.text.covered_bond_creditor_deed_filed.v1', dict(payload, currency='CHF', legal_basis='Art. 151 HRegV')))
        return events, ''

    m = match(rf"(?P<a>{NAME}), (?P<b>{NAME}), (?P<c>{NAME}) ne sont plus membres du conseil; leurs pouvoirs sont radiés\. Les membres du conseil (?P<vice>{NAME}), nommée vice-présidente, et (?P<former>{NAME}), jusqu'ici vice-président, lesquels continuent à signer collcetivement à deux\. (?P<president>{NAME}), de et à (?P<president_place>{NAME}), président, (?P<member>{NAME}), de et à (?P<member_place>{NAME}), et (?P<last>{NAME}), de (?P<origin>{NAME}), à (?P<last_place>{NAME}), sont membres du conseil signature collective à deux")
    if m:
        rule = 'fr.persons.council_replacement_vice_president_typo.v1'
        events = [person(rule, m[g], extra={'action': 'removed', 'previous_role': 'membre du conseil', 'signing_revoked': True}) for g in ('a', 'b', 'c')]
        for g, role, extra in [('vice', 'vice-présidente du conseil', {'action': 'role_changed'}), ('former', 'membre du conseil', {'action': 'role_changed', 'previous_role': 'vice-président'}), ('president', 'président du conseil', {'action': 'appointed', 'origin': m['president_place']}), ('member', 'membre du conseil', {'action': 'appointed', 'origin': m['member_place']}), ('last', 'membre du conseil', {'action': 'appointed', 'origin': m['origin']})]:
            place = m[g+'_place'] if g in ('president', 'member', 'last') else None
            events.append(person(rule, m[g], role=role, place=place, signing='Kollektivunterschrift zu zweien', extra=extra))
        return events, ''
    return [], leftover
