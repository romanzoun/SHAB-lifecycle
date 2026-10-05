from __future__ import annotations

import re

from .keys import person_key
from .parser253 import _event, _iso_date, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'
MONEY = r"[\d']+(?:\.\d+)?"


def extract_parser259_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete families evidenced by the twelve parser259 fixtures."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf"Inscription d'office par suite de la fusion des communes de (?P<a>{NAME}) et (?P<b>{NAME}) entrée en vigueur le (?P<date>{DATE})\. Nouvelle dénomination du siège: (?P<seat>{NAME})")
    if m:
        return [event('seat_changed', 'fr.text.seat_renamed_municipal_merger.v1', {'kind': 'municipal_merger', 'municipalities': [m['a'], m['b']], 'effective_date': _iso_date(m['date']), 'seat': m['seat'], 'action': 'renamed_ex_officio'})], ''

    m = match(r'Vollständige Adresse: (?P<address>[^,]+), (?P<postal_code>\d{4}) (?P<place>[^.]+)\. Neue andere Adresse: (?P<other_address>[^,]+), (?P<other_postal_code>\d{4}) (?P<other_place>[^.]+)')
    if m:
        rule = 'de.text.complete_and_other_address.v1'
        return [event('address_changed', rule, {'kind': 'complete_address', 'address': m['address'], 'postal_code': m['postal_code'], 'place': m['place']}), event('address_changed', rule, {'kind': 'other_address', 'action': 'new', 'address': m['other_address'], 'postal_code': m['other_postal_code'], 'place': m['other_place']})], ''

    m = match(r"L'associazione dev' essere cancellata a seguito della procedura di cui all'art\. (?P<article>155 ORC)\. La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali federali e cantonali")
    if m:
        return [event('status_changed', 'it.text.association_deletion_pending_tax_consent.v1', {'kind': 'deletion', 'action': 'pending', 'legal_basis': m['article'], 'reason': 'missing_federal_and_cantonal_tax_authorities_consent', 'deleted': False})], ''

    m = match(rf'Unter TR-Nr \. (?P<entry>\d+) vom (?P<date>{DATE}) wurde die weitere Staatsangehörigkeit von (?P<surname>{NAME}), (?P<given>{NAME}) \((?P<nationality>{NAME}) Staatsangehörige\) nicht publiziert')
    if m:
        return [person('de.persons.additional_nationality_notice_supplement.v1', f"{m['surname']}, {m['given']}", extra={'action': 'additional_nationality_published', 'nationality': m['nationality'], 'entry': m['entry'], 'entry_date': _iso_date(m['date'])})], ''

    m = match(rf'Der Eintrag Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt berichtigt: (?P<name>{NAME}), Direktor, Kollektivunterschrift zu zweien, in (?P<place>{NAME}) \(und nicht in (?P<previous_place>{NAME})\)')
    if m:
        return [person('de.persons.director_residence_corrected.v1', m['name'], role='Direktor', signing='Kollektivunterschrift zu zweien', place=m['place'], extra={'action': 'domicile_corrected', 'previous_place': m['previous_place'], 'entry': m['entry'], 'entry_date': _iso_date(m['entry_date']), 'notice_date': _iso_date(m['notice_date']), 'notice_id': m['notice_id']})], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<date>{DATE}) est complétée en ce sens que (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), a été nommée gérante(?: avec signature individuelle)?")
    if m and f"{m['name']}, de {m['origin']}, à {m['place']}, a été nommée gérante avec signature individuelle." in source_text:
        return [person('fr.persons.manager_appointment_notice_supplement.v1', m['name'], role='gérante', signing='Einzelunterschrift', place=m['place'], extra={'action': 'appointment_supplemented', 'origin': m['origin'], 'entry': m['entry'], 'entry_date': _iso_date(m['date'])})], ''

    m = match(rf"(?P<old>[^()]+) \((?P<old_uid>{UID})\) n'est plus organe de révision\. Nouvel organe de révision: (?P<new>[^()]+) \((?P<new_uid>{UID})\), à (?P<place>{NAME})")
    if m:
        rule = 'fr.persons.auditor_replaced_branch.v1'
        events = []
        for key, action in [('old', 'departed'), ('new', 'appointed')]:
            auditor = _person_event(*context, 'auditor_changed', rule, m[key], role='organe de révision', place=m['place'] if key == 'new' else None, extra={'action': action, 'uid': m[key+'_uid']})
            auditor.person_key = person_key(name=m[key].strip(), uid=m[key+'_uid'])
            events.append(auditor)
        return events, ''

    m = match(rf'Administration : (?P<a>{NAME}), maintenant domicilié à (?P<place_a>{NAME}), (?P<country_a>[A-Z]{{3}}), nommé président et (?P<b>{NAME}), de (?P<origin_b>{NAME}), à (?P<place_b>{NAME}), lesquels signent individuellement')
    typo = False
    if not m:
        m = match(rf"Administrsation: (?P<a>{NAME}), nommé président, et (?P<b>{NAME}), d'(?P<origin_b>{NAME}), à (?P<place_b>{NAME}), (?P<country_b>[A-Z]), vice-président, lesquels signent individuellement")
        typo = True
    if m:
        rule = 'fr.persons.board_president_vice_president_signing_typo.v1' if typo else 'fr.persons.board_president_residence_and_member_signing.v1'
        a = person(rule, m['a'], role='président', signing='Einzelunterschrift', place=None if typo else m['place_a'], extra={'action': 'appointed_president' if typo else 'role_and_domicile_changed', **({} if typo else {'country': m['country_a']})})
        b = person(rule, m['b'], role='vice-président' if typo else 'administrateur', signing='Einzelunterschrift', place=m['place_b'], extra={'action': 'new_or_changed', 'origin': m['origin_b'], **({'country': m['country_b']} if typo else {})})
        return [a, b], ''

    m = match(rf'(?P<seller>{NAME}), maintenant à (?P<seller_place>{NAME}), cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée sans signature\. (?P<again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})')
    family = 'new_associate'
    if not m:
        m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à l'associée (?P<buyer>[^()]+) \((?P<uid>{UID})\), désormais titulaire de (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY})\. (?P<again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
        family = 'existing_company'
    if not m:
        m = match(rf'(?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), directeur, nouvel associé avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), gérant, lequel continue de signer collectivement à deux\. (?P<again>{NAME}), qui est élu président, reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY}); continue de signer individuellement')
        family = 'director_manager'
    if m:
        count, before, remaining = (int(m[key]) for key in ('count', 'before', 'remaining'))
        if m['seller'] != m['again'] or count <= 0 or before - count != remaining or remaining < 0 or m['nominal'] != m['remaining_nominal']:
            return [], leftover
        if family != 'new_associate' and (m['nominal'] != m['buyer_nominal'] or int(m['received']) < count or (family == 'director_manager' and int(m['received']) != count)):
            return [], leftover
        if family == 'director_manager' and (f"gérant, lequel continue de signer collectivement à deux." not in source_text or f"{m['seller']}, qui est élu président, reste titulaire de {m['remaining']} parts de CHF {m['remaining_nominal']}; il continue de signer individuellement." not in source_text):
            return [], leftover
        rule_family = 'new_associate_without_signing' if family == 'new_associate' else family
        rule = 'fr.persons.partial_share_transfer_' + rule_family + '.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        seller = person(rule, m['seller'], role='gérant président' if family == 'director_manager' else ('associé-gérant' if family == 'existing_company' else None), place=m['seller_place'] if family == 'new_associate' else None, signing='Einzelunterschrift' if family == 'director_manager' else None, extra=dict(common, action='shares_transferred_and_president_elected' if family == 'director_manager' else 'shares_transferred', shares_before=before, shares_transferred=count, shares_count=remaining))
        buyer_extra = dict(common, action='shares_received' if family == 'existing_company' else 'appointed_and_shares_received', shares_received=count, shares_count=count if family == 'new_associate' else int(m['received']))
        if family == 'new_associate':
            buyer_extra['origin'] = m['origin']
        if family == 'existing_company':
            buyer_extra.update(uid=m['uid'], shares_before=int(m['received']) - count)
        if family == 'director_manager':
            buyer_extra['previous_role'] = 'directeur'
        buyer = person(rule, m['buyer'], role='associé-gérant' if family == 'director_manager' else 'associée', place=m['place'] if family == 'new_associate' else None, signing='Kollektivunterschrift zu zweien' if family == 'director_manager' else ('ohne Unterschrift' if family == 'new_associate' else None), extra=buyer_extra)
        if family == 'existing_company':
            buyer.person_key = person_key(name=m['buyer'].strip(), uid=m['uid'])
        return [seller, buyer], ''

    return [], leftover
