from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event

NAME = r'[^,.;]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
MONEY = r"[\d']+(?:\.\d+)?"
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser263_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; recover removed facts only from source."""
    del language
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def source(pattern):
        return re.search(pattern + r'\.?$', source_text, re.I | re.UNICODE)

    def event(event_type, rule, **payload):
        return _event(*context, event_type, rule, payload)

    def person(rule, name, *, kind='officer_changed', **kwargs):
        return _person_event(*context, kind, rule, name, **kwargs)

    def valid_dates(m):
        try:
            for key, value in m.groupdict().items():
                if 'date' in key:
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return False
        return True

    m = match(rf'Gelöschte Person: (?P<name>{NAME}), (?P<role>Verwaltungsratsmitglied), ohne Unterschrift')
    if m:
        return [person('de.persons.deleted_board_member_unsigned.v1', m['name'], kind='officer_removed', role=m['role'], signing='ohne Unterschrift', extra={'action': 'removed'})], ''

    m = match(rf'(?P<name>{NAME}), associé, exerce désormais la signature sociale, individuellement')
    if m:
        return [person('fr.persons.associate_social_signing_individual.v1', m['name'], role='associé', signing='Einzelunterschrift', extra={'action': 'signing_changed'})], ''

    m = match(rf"Complément: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC\. du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que la société était précédemment à (?P<previous_place>{NAME})")
    if m and valid_dates(m):
        return [event('seat_changed', 'fr.text.previous_seat_supplemented.v1', **m.groupdict(), action='previous_seat_supplemented')], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que le but social a été modifié")
    s = source(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que le but social a été modifié sur un point non soumis à publication") if m else None
    if s and m.groupdict() == s.groupdict() and valid_dates(m):
        return [event('purpose_changed', 'fr.text.unpublished_purpose_change_supplemented.v1', **m.groupdict(), action='supplemented', detail='not_subject_to_publication')], ''

    m = match(rf"L'Office des faillites du canton de (?P<canton_name>{NAME}) a refusé d'exécuter le jugement de faillite du (?P<court>{NAME}) du (?P<date>{DATE}) en constatant sa nullité\. De ce fait, la raison sociale redevient: (?P<name>{NAME})")
    if m and valid_dates(m):
        return [event('status_changed', 'fr.text.bankruptcy_judgment_void_name_restored.v1', **m.groupdict(), action='bankruptcy_void')], ''

    m = match(rf"Selon décision de l'(?P<authority>{NAME}) du (?P<date>{DATE}), la fondation est dissoute\. Liquidateurs: les membres du conseil (?P<a>{NAME}), (?P<b>{NAME}) et (?P<c>{NAME})")
    if m and valid_dates(m):
        rule = 'fr.text.foundation_dissolved_council_liquidators.v1'
        return [event('status_changed', rule, authority=m['authority'], date=m['date'], action='dissolved')] + [person(rule, m[k], role='liquidateur', extra={'action': 'appointed', 'previous_role': 'membre du conseil'}) for k in 'abc'], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<a>{NAME}), (?P<b>{NAME}), (?P<c>{NAME}), et (?P<d>{NAME}), lequel est à (?P<place>{NAME}) \(et non à (?P<old_place>{NAME}) comme publié\), sont tous de (?P<origin>{NAME}) \(et non de (?P<old_origin>{NAME}) comme publié\)")
    if m and valid_dates(m):
        return [person('fr.persons.four_origins_one_residence_corrected.v1', m[k], place=m['place'] if k == 'd' else None, extra={'action': 'corrected', 'origin': m['origin'], 'previous_origin': m['old_origin'], **({'previous_place': m['old_place']} if k == 'd' else {}), **{f: m[f] for f in ('entry', 'entry_date', 'notice_date', 'notice_ref')}}) for k in 'abcd'], ''

    m = match(rf'\]\. (?P<place_a>{NAME}) \((?P<uid_a>{UID})\)\. (?P<place_b>{NAME}) \((?P<uid_b>{UID})\)')
    s = source(rf'Zweigniederlassung neu: \[gestrichen: (?P<old_a>{NAME}) \((?P<uid_a>{UID})\) (?P<old_b>{NAME}) \((?P<uid_b>{UID})\)\]\. (?P<place_a>{NAME}) \((?P<new_uid_a>{UID})\)\. (?P<place_b>{NAME}) \((?P<new_uid_b>{UID})\)') if m else None
    if s and all(m[k] == s[k] for k in m.groupdict()) and s['uid_a'] == s['new_uid_a'] and s['uid_b'] == s['new_uid_b']:
        return [event('branch_changed', 'de.text.branch_places_replaced_uid.v1', action='updated', place=s['place_'+k], previous_place=s['old_'+k], entity_uid=s['uid_'+k]) for k in 'ab'], ''

    m = match(rf"\[Con decisione della (?P<court>{NAME}) del (?P<date>{DATE}) è mantenuta l'iscrizione della società a registro di commercio\.\] \[radiati: \]")
    s = source(rf"\[Con decisione della (?P<court>{NAME}) del (?P<date>{DATE}) è mantenuta l'iscrizione della società a registro di commercio\.\] \[radiati: La società deve essere cancellata a seguito della procedura di cui all'art\. 155 ORC\. La cancellazione non può tuttavia essere effettuata mancando il consenso delle autorità fiscali federali e cantonali\.\]") if m else None
    if s and s.groupdict() == m.groupdict() and valid_dates(m):
        return [event('status_changed', 'it.text.registration_maintained_deletion_clause_removed.v1', **m.groupdict(), action='registration_maintained', removed_article='155 ORC')], ''

    pattern = rf"Transfert de patrimoine: selon contrat du (?P<date>{DATE}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), à (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<uid>{UID})\)\. Contre-prestation: (?P<count>\d+) actions de CHF (?P<nominal>{MONEY}), nominatives, liées selon statuts, et une créance de CHF (?P<claim>{MONEY})"
    m = match(pattern)
    s = source(pattern) if m else None
    if s and s.groupdict() == m.groupdict() and valid_dates(m):
        return [event('organization_changed', 'fr.text.asset_transfer_shares_and_claim.v1', **m.groupdict(), action='transferred', kind='asset_transfer', currency='CHF', shares_count=int(m['count']), share_restriction='liées selon statuts')], ''

    pattern = rf"L'associé-gérant (?P<seller>{NAME}), qui est nommé président, cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), gérant avec signature individuelle\. (?P<seller_again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})\. Nouvelles formes des La clause statutaire relative à l'apport en nature et reprise de biens est abrogée conformément à l'article 628 al\. 4 CO"
    m = match(pattern)
    original = pattern.replace('Nouvelles formes des La clause', 'Nouvelles formes des communications aux associés: (?P<communications>par écrit ou par courriel)\\. La clause')
    s = source(original) if m else None
    if s and all(m[k] == s[k] for k in m.groupdict()) and m['seller'] == m['seller_again'] and int(m['count']) > 0 and int(m['before']) == int(m['count']) + int(m['remaining']) and m['count'] == m['received'] and len({m[k] for k in ('nominal', 'buyer_nominal', 'remaining_nominal')}) == 1:
        rule = 'fr.persons.partial_share_transfer_president_communications.v1'
        return [person(rule, m['seller'], role='associé-gérant président', extra={'action': 'shares_transferred', 'shares_count': int(m['remaining']), 'shares_transferred': int(m['count']), 'shares_nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant', signing='Einzelunterschrift', place=m['place'], extra={'action': 'appointed', 'origin': m['origin'], 'shares_count': int(m['received']), 'shares_nominal': m['nominal']}), event('organization_changed', rule, action='communications_changed', method=s['communications']), event('organization_changed', rule, action='contribution_clause_removed', article='628 al. 4 CO')], ''

    m = match(rf"(?P<seller>{NAME}), associé-gérant, cède ses (?P<count_a>\d+) parts de CHF (?P<nominal_a>{MONEY}) à (?P<a>{NAME}), de (?P<origin_a>{NAME}), à (?P<place_a>{NAME}), nouvel associé avec (?P<received_a>\d+) parts de CHF (?P<received_nominal_a>{MONEY}), sans signature, et ses (?P<count_bc>\d+) parts de CHF (?P<nominal_bc>{MONEY}), par (?P<split>\d+) parts de CHF (?P<split_nominal>{MONEY}), chacun, à (?P<b>{NAME}), à (?P<place_b>{NAME}), et (?P<c>{NAME}), à (?P<place_c>{NAME}), tous deux de (?P<origin_bc>{NAME}), nouveaux associés, chacun avec (?P<received_bc>\d+) parts de CHF (?P<received_nominal_bc>{MONEY}), sans signature\. (?P<seller_again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
    if m and m['seller'] == m['seller_again'] and int(m['count_a']) > 0 and m['count_a'] == m['received_a'] and m['nominal_a'] == m['received_nominal_a'] and int(m['split']) > 0 and int(m['count_bc']) == 2 * int(m['split']) and m['split'] == m['received_bc'] and len({m[k] for k in ('nominal_bc', 'split_nominal', 'received_nominal_bc')}) == 1:
        rule = 'fr.persons.multiclass_shares_three_recipients.v1'
        return [person(rule, m['seller'], role='associé-gérant', extra={'action': 'shares_transferred', 'shares_count': int(m['remaining']), 'shares_nominal': m['remaining_nominal'], 'transferred_classes': [{'count': int(m['count_a']), 'nominal': m['nominal_a']}, {'count': int(m['count_bc']), 'nominal': m['nominal_bc']}]})] + [person(rule, m[k], role='associé', signing='ohne Unterschrift', place=m['place_'+k], extra={'action': 'appointed', 'origin': m['origin_a' if k == 'a' else 'origin_bc'], 'shares_count': int(m['received_a' if k == 'a' else 'received_bc']), 'shares_nominal': m['nominal_a' if k == 'a' else 'nominal_bc']}) for k in 'abc'], ''

    return [], leftover
