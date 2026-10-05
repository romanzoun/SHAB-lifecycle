from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event

NAME = r'[^,.;]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
MONEY = r"[\d']+(?:\.\d+)?"
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'
REGISTER = r'CH-[\d.-]+'


def extract_parser262_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Match complete fixture-backed clauses and verify facts lost in preprocessing."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def source(pattern):
        return re.search(pattern + r'\.?$', source_text, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def date(raw):
        return datetime.strptime(raw, '%d.%m.%Y').date().isoformat()

    m = match(rf'Beim TR-Eintrag Nr\. (?P<entry>\d+) vom (?P<date>{DATE}) wurde bei der Revisionsstelle der Bisher-Text unvollständig wiedergegeben\. Richtig: \[bisher: (?P<name>[^\[\]]+?) \((?P<register>{REGISTER})\)\]')
    if m:
        try:
            entry_date = date(m['date'])
        except ValueError:
            return [], leftover
        return [event('auditor_changed', 'de.text.previous_auditor_reference_corrected.v1', dict(m.groupdict(), action='previous_reference_corrected', entry_date=entry_date))], ''

    m = match(r'\[Die weitere Adresse wird im Handelsregister gelöscht\] \[gestrichen: Weiteres Geschäftslokal: (?P<address>[^,.;]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+)\.\]')
    if m:
        return [event('address_changed', 'de.text.additional_business_address_deleted.v1', dict(m.groupdict(), action='removed'))], ''

    pattern = rf'Nouvel administrateur (?:avec signature collective à deux )?(?P<name>{NAME}), de et à (?P<place>{NAME})'
    m = match(pattern)
    s = source(rf'Nouvel administrateur avec signature collective à deux (?P<name>{NAME}), de et à (?P<place>{NAME})') if m else None
    if s and all(s[k].strip() == m[k].strip() for k in m.groupdict()):
        return [person('fr.persons.administrator_shared_origin_place.v1', m['name'], place=m['place'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'action': 'appointed', 'origin': m['place']})], ''

    m = match(rf"(?P<name>{NAME}) \((?P<register>{REGISTER})\), dont le numéro d'identification est \((?P<uid>{UID})\), est désormais à (?P<place>{NAME})")
    if m:
        return [event('organization_changed', 'fr.text.registered_entity_seat_uid_updated.v1', dict(m.groupdict(), action='seat_changed', entity_uid=m['uid']))], ''

    reference = rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que "
    m = match(reference + rf'(?P<a>{NAME}) est à (?P<place_a>{NAME}) \(et non à (?P<old_a>{NAME}) comme publié\) et (?P<b>{NAME}) à (?P<place_b>{NAME}) \(et non à (?P<old_b>{NAME}) comme publié\)')
    if m:
        return [person('fr.persons.two_residences_corrected.v1', m[k], place=m['place_'+k], extra={'action': 'residence_corrected', 'previous_place': m['old_'+k], **{f: m[f] for f in ('entry', 'entry_date', 'notice_date', 'notice_ref')}}) for k in 'ab'], ''

    m = match(reference + rf'le prénom exact est: (?P<name>{NAME}) \(et non (?P<previous>{NAME}) comme publié\)')
    if m:
        return [person('fr.persons.exact_given_name_corrected.v1', m['name'], extra={'action': 'given_name_corrected', 'previous_given_name': m['previous'], **{f: m[f] for f in ('entry', 'entry_date', 'notice_date', 'notice_ref')}})], ''

    m = match(rf'Administration: (?P<a>{NAME}), de (?P<origin_a>{NAME}), à (?P<place_a>{NAME}), président, et (?P<b>{NAME}), de (?P<origin_b>{NAME}), à (?P<place_b>{NAME}), lesquels signent individuellement')
    if m:
        return [person('fr.persons.two_administrators_individual_signing.v1', m[k], role='président' if k == 'a' else 'administrateur', place=m['place_'+k], signing='Einzelunterschrift', extra={'action': 'new_or_changed', 'origin': m['origin_'+k]}) for k in 'ab'], ''

    branch = rf'\[aufgehoben\] \[gestrichen: (?P<place>{NAME})(?: \((?P<register>{REGISTER})\))?\]'
    if match(r'Zweigniederlassung neu: ' + branch + r'(?:\. ' + branch.replace('?P<place>', '?:').replace('?P<register>', '?:') + r'){3}'):
        return [event('branch_changed', 'de.text.four_branches_removed.v1', dict(m.groupdict(), action='removed')) for m in re.finditer(branch, leftover)], ''

    pattern = rf'Mit Urteil vom (?P<date>{DATE}) hat die Nachlassrichterin des (?P<court>{NAME}) über die Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, den Konkurs eröffnet; demnach ist die Gesellschaft aufgelöst'
    m = match(pattern)
    s = source(pattern + rf'\. \[nicht: Mit Urteil vom (?P<old_date>{DATE}) hat die Konkursrichterin des (?P<old_court>{NAME}) über die Gesellschaft mit Wirkung ab dem (?P<old_effective_date>{DATE}), (?P<old_time>\d{{2}}\.\d{{2}}) Uhr, den Konkurs eröffnet; demnach ist die Gesellschaft aufgelöst\.\]') if m else None
    if s and all(m[k] == s[k] == s['old_'+k] for k in m.groupdict()):
        try:
            dates = {k: date(m[k]) for k in ('date', 'effective_date')}
            datetime.strptime(m['time'], '%H.%M')
        except ValueError:
            return [], leftover
        return [event('status_changed', 'de.text.bankruptcy_judge_corrected.v1', dict(m.groupdict() | dates, action='judge_corrected', judge='Nachlassrichterin', previous_judge='Konkursrichterin', dissolved=True))], ''

    pattern = rf"(?P<seller>{NAME}), associé-gérant, cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), gérant (?:avec signature individuelle, )?président\. (?P<seller_again>{NAME}) reste titulaire d'une part de CHF (?P<remaining_nominal>{MONEY}); continue de signer individuellement"
    m = match(pattern)
    original = pattern.replace('(?:avec signature individuelle, )?', 'avec signature individuelle, ').replace('; continue', '; il continue')
    s = source(original) if m else None
    if s and all(s[k].strip() == m[k].strip() for k in m.groupdict()) and m['seller'] == m['seller_again'] and m['seller'] != m['buyer'] and int(m['count']) > 0 and int(m['before']) == int(m['count']) + 1 and m['count'] == m['received'] and len({m[k] for k in ('nominal', 'buyer_nominal', 'remaining_nominal')}) == 1:
        rule = 'fr.persons.share_transfer_manager_president.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        return [person(rule, m['seller'], role='associé-gérant', signing='Einzelunterschrift', extra=dict(common, action='shares_transferred', shares_count=1, shares_transferred=int(m['count']))), person(rule, m['buyer'], role='associé-gérant président', signing='Einzelunterschrift', place=m['place'], extra=dict(common, action='appointed', origin=m['origin'], shares_count=int(m['received'])))], ''

    m = match(rf"La succursale d'(?P<place>{NAME}) est radiée \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)")
    if m:
        return [event('branch_changed', 'fr.text.branch_removed_notice_reference.v1', dict(m.groupdict(), action='removed'))], ''

    if match(r'Der Zweck der Zweigniederlassung ist zu löschen, da er genau dem Zweck des Hauptsitzes entspricht'):
        return [event('purpose_changed', 'de.text.branch_duplicate_purpose_deleted.v1', {'action': 'removed', 'scope': 'branch', 'reason': 'identical_to_head_office'})], ''

    return [], leftover
