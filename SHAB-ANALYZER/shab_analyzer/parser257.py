from __future__ import annotations

import re

from .keys import person_key
from .parser253 import _event, _iso_date, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'
MONEY = r"[\d']+(?:\.\d+)?"


def extract_parser257_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse only complete families observed in the twelve parser257 fixtures."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<date>{DATE}) eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in (?P<article>Art\. \d+[a-z]?) der Statuten beschlossen')
    if m:
        return [event('capital_changed', 'de.text.authorized_participation_capital_increase.v1', {'kind': 'authorized_participation_capital_increase', 'date': _iso_date(m['date']), 'statutes_article': m['article']})], ''

    m = match(r"(?P<court>Le président de la Cour des poursuites et faillites du Tribunal cantonal) a admis la requête d'effet suspensif de la procédure de faillite le (?P<day>\d{1,2}) janvier (?P<year>\d{4})")
    if m:
        return [event('status_changed', 'fr.text.bankruptcy_suspensive_effect_january.v1', {'kind': 'bankruptcy', 'action': 'suspensive_effect_granted', 'court': m['court'], 'decision_date': _iso_date(f"{int(m['day']):02d}.01.{m['year']}")})], ''

    m = match(rf"(?P<a>{NAME}), jusqu'ici directeur adjoint, nommé directeur et (?P<b>{NAME}), maintenant domiciliée à (?P<place>{NAME}), jusqu'ici sous-directrice, nommée directrice, continuent à signer collectivement à deux")
    if m:
        rule = 'fr.persons.two_directors_promoted_collective_signing.v1'
        return [person(rule, m['a'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'action': 'role_changed', 'previous_role': 'directeur adjoint'}), person(rule, m['b'], role='directrice', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'action': 'role_and_domicile_changed', 'previous_role': 'sous-directrice'})], ''

    m = match(rf'Les associés-gérants (?P<a>{NAME}) et (?P<b>{NAME}) cèdent chacun (?P<count>\d+) de leurs (?P<before_a>\d+) et (?P<before_b>\d+) parts de CHF (?P<nominal>{MONEY}) respectives à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), gérant avec signature collective à deux\. (?P<again_a>{NAME}) et (?P<again_b>{NAME}) restent titulaires respectivement de (?P<remaining_a>\d+) et (?P<remaining_b>\d+) parts de CHF (?P<remaining_nominal>{MONEY})')
    if m and m['a'] == m['again_a'] and m['b'] == m['again_b'] and m['nominal'] == m['buyer_nominal'] == m['remaining_nominal'] and int(m['count']) > 0 and 2 * int(m['count']) == int(m['received']) and all(int(m['before_'+g]) - int(m['count']) == int(m['remaining_'+g]) >= 0 for g in ('a', 'b')):
        # Require the same signing clause in the original publication text.
        clause = f"nouvel associé avec {m['received']} parts de CHF {m['buyer_nominal']}, gérant avec signature collective à deux."
        if clause in source_text:
            rule = 'fr.persons.two_partial_share_transfers_new_manager.v1'
            common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
            events = [person(rule, m[g], extra=dict(common, action='shares_transferred', shares_before=int(m['before_'+g]), shares_transferred=int(m['count']), shares_count=int(m['remaining_'+g]))) for g in ('a', 'b')]
            events.append(person(rule, m['buyer'], role='associé-gérant', place=m['place'], signing='Kollektivunterschrift zu zweien', extra=dict(common, action='appointed_and_shares_received', origin=m['origin'], shares_received=int(m['received']), shares_count=int(m['received']))))
            return events, ''

    m = match(rf"Transfert de patrimoine: Selon contrat du (?P<date>{DATE}) et (?P<second_date>{DATE}), approuvé par décision de l'autorité de surveillance du (?P<approval_date>{DATE}), la fondation a transféré des actifs de CHF (?P<assets>{MONEY}), dont l'immeuble n° (?P<property_number>\d+) du RF de (?P<property_place>{NAME}), à (?P<recipient>[^()]+) \((?P<uid>{UID})\) à (?P<place>{NAME})\. Contre-prestation: CHF (?P<consideration>{MONEY})")
    if m:
        payload = m.groupdict()
        for key in ('date', 'second_date', 'approval_date'):
            payload[key] = _iso_date(payload[key])
        return [event('organization_changed', 'fr.text.foundation_asset_transfer_two_contract_dates.v1', dict(payload, kind='asset_transfer', currency='CHF'))], ''

    m = match(rf'Eingetragene Personen neu oder mutierend: (?P<surname>{NAME}), (?P<given>{NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), Mitglied der Geschäftsleitung, mit Kollektivunterschrift zu zweien')
    if m:
        return [person('de.persons.executive_member_new_or_changed.v1', f"{m['surname']}, {m['given']}", role='Mitglied der Geschäftsleitung', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'action': 'new_or_changed', 'nationality': m['nationality']})], ''

    for pattern, rule in [
        (rf'Die Zweigniederlassung in (?P<place>[^()]+) \((?P<uid>{UID})\) ist gelöscht', 'de.text.branch_deleted.v1'),
        (rf'Zweigniederlassung neu: \[Folgende Zweigniederlassungen sind aufgehoben worden:\] \[gestrichen: (?P<place>[^()]+) \((?P<uid>{UID})\) \(HRA (?P<registry_canton>[A-Z]{{2}})\)\]', 'de.text.branch_struck_from_new_listing.v1'),
    ]:
        m = match(pattern)
        if m:
            return [event('organization_changed', rule, dict(m.groupdict(), kind='branch', action='deleted'))], ''

    m = match(rf'Mit Verfügung vom (?P<date>{DATE}) hat das (?P<court>{NAME}) im summarischen Verfahren eine Nachlassstundung von (?P<months>\d+) Monaten bewilligt')
    if m:
        return [event('status_changed', 'de.text.composition_moratorium_months_granted.v1', {'kind': 'composition_moratorium', 'action': 'granted', 'decision_date': _iso_date(m['date']), 'court': m['court'], 'duration_months': int(m['months']), 'procedure': 'summarisch'})], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce cens que (?P<name>{NAME}) est à (?P<place>{NAME}) \(et non à (?P<previous_place>{NAME}) comme publié\)")
    if m:
        payload = m.groupdict()
        for key in ('entry_date', 'notice_date'):
            payload[key] = _iso_date(payload[key])
        return [person('fr.persons.residence_corrected_notice_typo.v1', payload.pop('name'), place=payload.pop('place'), extra=dict(payload, action='domicile_corrected', source_typo='en ce cens'))], ''

    m = match(rf'(?P<name>{NAME}), administrateur président, est nommé liquidateur avec signature individuelle\. Les (?P<count>[\d\']+) actions nominatives de CHF (?P<nominal>{MONEY}) ne sont plus restreintes quant à leur transmissibilité \(art\. 685a, al\. 3 CO\)')
    if m and f"{m['name']}, administrateur président, est nommé liquidateur avec signature individuelle." in source_text:
        rule = 'fr.persons.board_president_appointed_liquidator.v1'
        return [person(rule, m['name'], role='liquidateur', signing='Einzelunterschrift', extra={'action': 'appointed', 'previous_role': 'administrateur président'}), event('capital_changed', rule, {'kind': 'share_transfer_restriction', 'transfer_restricted': False, 'share_count': int(m['count'].replace("'", '')), 'nominal': m['nominal'], 'currency': 'CHF', 'legal_basis': 'art. 685a, al. 3 CO'})], ''

    m = match(rf'Liquidateurs: Le gérant (?P<name>{NAME}), lequel continue de signer individuellement, et (?P<company>[^()]+) \((?P<uid>{UID})\), à (?P<place>{NAME})')
    if m:
        rule = 'fr.persons.manager_and_corporate_liquidators.v1'
        corporate = person(rule, m['company'], role='liquidateur', place=m['place'], extra={'action': 'appointed', 'uid': m['uid']})
        corporate.person_key = person_key(name=m['company'], uid=m['uid'])
        return [person(rule, m['name'], role='liquidateur', signing='Einzelunterschrift', extra={'action': 'appointed', 'previous_role': 'gérant'}), corporate], ''

    return [], leftover
