from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event

NAME = r'[^,.;]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
COUNT = r"\d+(?:'\d{3})*"
MONEY = COUNT + r'(?:\.\d+)?'
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser267_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete sample-backed clauses, preserving unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, source_pattern=None):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k].strip() != v.strip() for k, v in m.groupdict().items() if v is not None):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(event_type, rule, **payload):
        return _event(*context, event_type, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def number(value):
        return Decimal(value.replace("'", ''))

    def shares(rule, **payload):
        return event('capital_changed', rule, currency='CHF', **payload)

    pattern = rf"In der am (?P<entry_date>{DATE}) unter TR-Nr\. (?P<entry>\d+) vorgenommenen Eintragung wurde bei der Revisionsstelle der Bisher-Text unvollständig wiedergegeben\. Richtig: \[bisher: (?P<previous_name>[^()]+) \((?P<previous_uid>CH-[\d.-]+)\)\]"
    m = match(pattern)
    if m:
        return [event('organization_changed', 'de.text.previous_auditor_corrected.v1', **m.groupdict(), action='previous_auditor_corrected')], ''

    m = match(rf"\[gestrichen: Der Geschäftsbetrieb hat aufgehört\. Das Einzelunternehmen wird gemäss Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]\. Das unter der TR Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) gelöschte Einzelunternehmen wird auf Antrag des Inhabers gemäss Art\. 116 Abs\. 3 lit\. b HRegV wieder in das Handelsregister eingetragen")
    if m:
        return [event('status_changed', 'de.text.sole_proprietorship_reinstated.v1', **m.groupdict(), action='reinstated', legal_basis='Art. 116 Abs. 3 lit. b HRegV', previous_deletion_revoked=True)], ''

    m = match(rf"Nouveau membre du conseil de fondation sans signature: (?P<name>{NAME}), d'(?P<origin>{NAME}), au (?P<place>{NAME})")
    if m:
        return [person('fr.persons.foundation_member_unsigned.v1', m['name'], place=m['place'], role='membre du conseil de fondation', signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'action': 'appointed'})], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) continuent à signer collectivement à deux, désormais avec un directeur ou le directeur général')
    if m:
        return [person('fr.persons.continued_signing_director_restriction.v1', m[k], signing='Kollektivunterschrift zu zweien', extra={'signing_restriction': 'only_with', 'authorized_partner_roles': ['directeur', 'directeur général']}) for k in ['name1', 'name2', 'name3']], ''

    m = match(rf'Administration: (?P<name1>{NAME}), maintenant domicilié à (?P<place1>{NAME}), nommé président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signet collectivement à deux; les pouvoirs de (?P=name1) sont modifiés en ce sens')
    if m:
        rule = 'fr.persons.administration_collective_signing_typo.v1'
        return [person(rule, m['name1'], place=m['place1'], role='président', signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], place=m['place2'], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin2']})], ''

    pattern = rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que le capital-actions se divise comme suit: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count1>{COUNT}) actions de CHF (?P<nominal1>{MONEY}), et (?P<count2>{COUNT}) actions de CHF (?P<nominal2>{MONEY}), privilégiées quant au droit de vote, et (?P<count3>{COUNT}) actions ordinaires de CHF (?P<nominal3>{MONEY}), toutes nominatives"
    m = match(pattern + r'(?:, liées selon statuts)?', pattern + r', liées selon statuts')
    if m and all(number(m['count'+str(i)]) > 0 and number(m['nominal'+str(i)]) > 0 for i in range(1, 4)) and sum(number(m['count'+str(i)]) * number(m['nominal'+str(i)]) for i in range(1, 4)) == number(m['capital']):
        return [shares('fr.text.share_classes_completed.v1', **m.groupdict(), fully_paid=True, transfer_restricted=True, share_classes=[{'count': m['count'+str(i)], 'nominal': m['nominal'+str(i)], 'kind': 'registered', 'voting_preferred': i == 2, 'ordinary': i == 3} for i in range(1, 4)])], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>[^()]+) \((?P<absorbed_uid>{UID})\), in (?P<absorbed_place>{NAME}), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF\s*(?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento di capitale e senza attribuzione di azioni")
    if m:
        return [event('company_merged', 'it.text.wholly_owned_merger_compact_currency.v1', **m.groupdict(), currency='CHF', kind='merger', capital_increase=False, share_allocation=False, wholly_owned=True)], ''

    pattern = rf'(?P<name1>{NAME}) et (?P<name2>{NAME}) ont cédé leurs (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>[^()]+) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée pour (?P=count) parts de CHF (?P=nominal)\. Gérants: (?P=name1), présidente, et (?P=name2), tous deux'
    m = match(pattern + r'(?: avec signature individuelle)?', pattern + r' avec signature individuelle')
    if m and number(m['count']) > 0 and number(m['nominal']) > 0:
        rule = 'fr.persons.joint_share_transfer_managers.v1'
        return [person(rule, m['recipient'], place=m['place'], role='associée', extra={**m.groupdict(), 'action': 'shares_received', 'shares_count': int(number(m['count'])), 'shares_nominal': m['nominal'], 'new_associate': True, 'transferors': [m['name1'], m['name2']]}), person(rule, m['name1'], role='gérante présidente', signing='Einzelunterschrift', extra={'associate_removed': True}), person(rule, m['name2'], role='gérant', signing='Einzelunterschrift', extra={'associate_removed': True})], ''

    m = match(rf'(?P<transferor>{NAME}), associé, a cédé (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), de et à (?P<place>{NAME}), nouvel associé\. Gérants: (?P=transferor), nommé président, et (?P=recipient), lesquels signent individuellement')
    if m and 0 < number(m['count']) <= number(m['previous_count']) and number(m['nominal']) > 0:
        rule = 'fr.persons.partial_share_transfer_managers.v1'
        return [person(rule, m['transferor'], role='associé', extra={**m.groupdict(), 'action': 'shares_transferred', 'shares_count': int(number(m['previous_count'])-number(m['count'])), 'remaining_count': str(int(number(m['previous_count'])-number(m['count'])))}), person(rule, m['transferor'], role='gérant président', signing='Einzelunterschrift'), person(rule, m['recipient'], place=m['place'], role='associé gérant', signing='Einzelunterschrift', extra={'origin': m['place']})], ''

    m = match(rf"La gérante (?P<transferor>{NAME}), qui n'est plus associée et signe désormais collectivement à deux, cède sa part de CHF (?P<nominal>{MONEY}) à (?P<recipient>[^()]+) \((?P<recipient_uid>{UID})\), à (?P<recipient_place>{NAME}), nouvelle associée\. Signature collective à deux est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})\. Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que les statuts ne prévoient pas l'obligation de fournir des prestations accessoires, droits de préférence, de préemption ou d'emption")
    if m and number(m['nominal']) > 0:
        rule = 'fr.persons.share_transfer_collective_managers.v1'
        return [person(rule, m['recipient'], place=m['recipient_place'], role='associée', extra={'transferor': m['transferor'], 'recipient_uid': m['recipient_uid'], 'nominal': m['nominal'], 'count': 1, 'shares_count': 1, 'new_associate': True, 'action': 'shares_received'}), person(rule, m['transferor'], role='gérante', signing='Kollektivunterschrift zu zweien', extra={'associate_removed': True}), *[person(rule, m['name'+str(i)], place=m['place'+str(i)], role='président' if i == 1 else None, signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'+str(i)]}) for i in [1, 2]], event('organization_changed', 'fr.text.ancillary_obligations_corrected.v1', entry=m['entry'], entry_date=m['entry_date'], notice_date=m['notice_date'], notice_ref=m['notice_ref'], ancillary_obligations=False, preference_rights=False, preemption_rights=False, purchase_option_rights=False)], ''

    pattern = rf"Gérants : (?P<transferor>{NAME}), maintenant domicilié à (?P<place1>{NAME}), (?P<country1>[A-Z]), nommé président, et (?P<manager>{NAME}), de (?P<origin>{NAME}), à (?P<place2>[^,;]+), tous deux"
    division = rf" Division des deux parts de CHF (?P<old_nominal1>{MONEY}) et CHF (?P<old_nominal2>{MONEY}) en (?P<divided_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}); par conséquent (?P=transferor) est maintenant associé pour (?P=divided_count) parts de CHF (?P=nominal)\. "
    transfer = rf"(?P=transferor) a cédé (?P<count1>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient1>{NAME}), de (?P<origin1>{NAME}), à (?P<recipient_place1>{NAME}), (?P<country2>[A-Z]), nouvel associé pour (?P=count1) parts de CHF (?P=nominal), (?P<count2>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient2>{NAME}), de (?P<origin2>{NAME}), à (?P<recipient_place2>{NAME}), (?P<country3>[A-Z]), nouvel associé pour (?P=count2) parts de CHF (?P=nominal), et (?P<count3>{COUNT}) part de CHF (?P=nominal) à (?P=manager), nouvel associé pour (?P=count3) part de CHF (?P=nominal); par conséquent (?P=transferor) est maintenant associé pour (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)"
    m = match(pattern + r'(?: avec signature individuelle\.)?' + division + transfer, pattern + r' avec signature individuelle\.' + division + rf'Nouveaux statuts du (?P<statutes_date>{DATE})\. ' + transfer)
    if m and all(number(m[k]) > 0 for k in ['old_nominal1', 'old_nominal2', 'divided_count', 'nominal', 'count1', 'count2', 'count3', 'remaining_count']) and number(m['old_nominal1'])+number(m['old_nominal2']) == number(m['divided_count'])*number(m['nominal']) and sum(number(m[k]) for k in ['count1', 'count2', 'count3', 'remaining_count']) == number(m['divided_count']):
        rule = 'fr.persons.share_division_multiple_transfers.v1'
        return [shares(rule, **m.groupdict(), action='share_division_and_transfer', transfers=[{'recipient': m['recipient1'], 'count': m['count1']}, {'recipient': m['recipient2'], 'count': m['count2']}, {'recipient': m['manager'], 'count': m['count3']}]), person(rule, m['transferor'], place=m['place1'], role='associé gérant président', signing='Einzelunterschrift', extra={'country': m['country1'], 'shares_count': m['remaining_count']}), person(rule, m['manager'], place=m['place2'], role='associé gérant', signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares_count': m['count3']})], ''

    m = match(rf"Administration: (?P<name1>{NAME}), président, (?P<name2>{NAME}), vice-président, (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), secrétaire et également directeur, (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), et (?P<name5>{NAME}), de (?P<origin5>{NAME}), à (?P<place5>{NAME})\. Signature individuelle de (?P=name4) ou collective à deux des autres membres du conseil d'administration; (?P=name1) et (?P=name2) ne signent pas entre eux; leurs pouvoirs sont modifiés en ce sens")
    if m:
        rule = 'fr.persons.board_mixed_signing_restrictions.v1'
        roles = ['président', 'vice-président', 'secrétaire et directeur', 'administrateur', 'administrateur']
        return [person(rule, m['name'+str(i)], place=m.groupdict().get('place'+str(i)), role=roles[i-1], signing='Einzelunterschrift' if i == 4 else 'Kollektivunterschrift zu zweien', extra={**({'origin': m['origin'+str(i)]} if i >= 3 else {}), **({'signing_restriction': 'not_with', 'excluded_partner': m['name'+str(3-i)]} if i <= 2 else {})}) for i in range(1, 6)], ''

    return [], leftover
