from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser273_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract complete, fixture-backed clauses; retain unsupported facts."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover)

    def event(kind, rule, **payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"(?P<name>{NAME}), jusqu'ici sous-directeur, nommé directeur, continuent à signer collectivement à deux")
    if m:
        return [person('fr.persons.director_promotion_continued_signing.v1', m['name'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'sous-directeur', 'signing_continued': True})], ''

    m = match(rf"L'administrateur (?P<name>{NAME}), nommé vice-président, lequel continue à signer collectivement à deux")
    if m:
        return [person('fr.persons.administrator_vice_president_continued_signing.v1', m['name'], role='administrateur vice-président', signing='Kollektivunterschrift zu zweien', extra={'signing_continued': True})], ''

    m = match(rf"Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<name1>{NAME}) et (?P<name2>{NAME}) sont associés pour (?P<shares>{COUNT}) parts de CHF (?P=nominal) chacun")
    if m and 0 < number(m['transferred']) <= number(m['shares']) and number(m['nominal']) > 0:
        return [person('fr.persons.share_transfer_equal_holdings.v1', m['name'+str(i)], role='associé', extra={'shares': int(number(m['shares'])), 'share_nominal': m['nominal'], 'transfer_total': int(number(m['transferred']))}) for i in (1, 2)], ''

    m = match(r'Angaben zur Zweigniederlassung neu: Übergang dieser Zweigniederlassung infolge Spaltung gemäss Art\. (?P<article>112 HRegV)')
    if m:
        return [event('organization_changed', 'de.text.branch_transfer_by_split.v1', action='branch_transfer', reason='Spaltung', article=m['article'])], ''

    m = match(rf"(?P<name1>{NAME}), maintenant à (?P<place>{NAME}), (?P<name2>{NAME}), qui est nommé directeur général, et (?P<name3>{NAME}) signent désormais collectivement à deux")
    if m:
        rule = 'fr.persons.three_signers_director_relocation.v1'
        return [person(rule, m['name1'], place=m['place'], signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role='directeur général', signing='Kollektivunterschrift zu zweien'), person(rule, m['name3'], signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Signature collective à deux, toutefois pas entre eux, est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME})")
    if m:
        return [person('fr.persons.three_collective_signers_exclusion.v1', m['name'+str(i)], place=m['place'+str(i)], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'+str(i)], 'not_with_each_other': True}) for i in (1, 2, 3)], ''

    clause = rf"La commandite de l'associé commanditaire (?P<name{{i}}>{NAME}) a été réduite de CHF (?P<previous{{i}}>{MONEY}) à CHF (?P<amount{{i}}>{MONEY})"
    m = match(clause.replace('{i}', '1') + r'\. ' + clause.replace('{i}', '2'))
    if m and all(0 < number(m['amount'+str(i)]) < number(m['previous'+str(i)]) for i in (1, 2)):
        return [person('fr.persons.two_limited_partner_contributions_reduced.v1', m['name'+str(i)], role='associé commanditaire', extra={'previous_contribution': m['previous'+str(i)], 'contribution': m['amount'+str(i)], 'currency': 'CHF', 'action': 'reduced'}) for i in (1, 2)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement et (?P<name2>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), avec signature collective à deux")
    if m:
        rule = 'fr.persons.board_president_new_collective_member.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Einzelunterschrift', extra={'signing_continued': True}), person(rule, m['name2'], role='administrateur', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    m = match(rf"L'associé-gérant (?P<name1>{NAME}), jusqu'ici avec signature individuelle, désormais avec signature collective à deux, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant et président pour (?P=transferred) parts de CHF (?P=nominal) avec signature individuelle")
    if m and number(m['remaining']) > 0 and number(m['transferred']) > 0 and number(m['nominal']) > 0:
        rule = 'fr.persons.manager_share_transfer_signing_changed.v1'
        return [person(rule, m['name1'], role='associé-gérant', signing='Kollektivunterschrift zu zweien', extra={'previous_signing': 'Einzelunterschrift', 'shares': int(number(m['remaining'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé-gérant président', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"(?P<name1>{NAME}) est maintenant associé pour (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), suite à la cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à raison de (?P<received2>{COUNT}) parts à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé pour (?P=received2) parts de CHF (?P=nominal), et à raison de (?P<received3>{COUNT}) parts à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), (?P<country>{NAME}), nouvel associé pour (?P=received3) parts de CHF (?P=nominal)\. (?P=name2) est nommé gérant, président, avec signature individuelle; l'associé (?P=name3) n'exerce pas la signature sociale")
    if m and number(m['received2']) + number(m['received3']) == number(m['transferred']) and all(number(m[k]) > 0 for k in ('received2', 'received3', 'remaining', 'nominal')):
        rule = 'fr.persons.share_transfer_two_new_associates.v1'
        return [person(rule, m['name1'], role='associé', extra={'shares': int(number(m['remaining'])), 'transferred_shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé-gérant président', place=m['place2'], signing='Einzelunterschrift', extra={'shares': int(number(m['received2'])), 'share_nominal': m['nominal'], 'origin': m['origin2']}), person(rule, m['name3'], role='associé', place=m['place3'] + ', ' + m['country'], extra={'shares': int(number(m['received3'])), 'share_nominal': m['nominal'], 'origin': m['origin3'], 'without_signature': True})], ''

    m = match(rf"Augmentation conditionnelle du capital-participation, fondée sur la décision relative à l'octroi de droits du (?P<decision_date>{DATE}), porté de CHF (?P<previous>{MONEY}) à CHF (?P<capital>{MONEY}), par l'émission de (?P<issued>{COUNT}) bons de participation de CHF (?P<nominal>{MONEY}), nominatifs, liés selon statuts\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) bons de CHF (?P=nominal), nominatifs, liés selon statuts")
    if m:
        try:
            datetime.strptime(m['decision_date'], '%d.%m.%Y')
        except ValueError:
            return [], leftover
        if number(m['capital']) > number(m['previous']) > 0 and number(m['issued']) * number(m['nominal']) == number(m['capital']) - number(m['previous']) and number(m['count']) * number(m['nominal']) == number(m['capital']):
            return [event('capital_changed', 'fr.text.conditional_participation_capital_increase.v1', **m.groupdict(), conditional=True, fully_paid=True, registered=True, restricted_by_statutes=True)], ''

    m = match(rf"Les (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives, sont désormais liées selon statuts\. Division de (?P<split_count>{COUNT}) actions de CHF (?P=previous_nominal), nominatives, liées selon statuts, en (?P<preferred_count>{COUNT}) actions de CHF (?P<preferred_nominal>{MONEY}), désormais à droit de vote privilégié\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=preferred_count) actions de CHF (?P=preferred_nominal), à droit de vote privilégié, et (?P<ordinary_count>{COUNT}) actions ordinaires de CHF (?P=previous_nominal), toutes nominatives, liées selon statuts")
    if m:
        v = {k: number(value) for k, value in m.groupdict().items()}
        if all(value > 0 for value in v.values()) and v['previous_count'] == v['split_count'] + v['ordinary_count'] and v['split_count'] * v['previous_nominal'] == v['preferred_count'] * v['preferred_nominal'] and v['previous_count'] * v['previous_nominal'] == v['capital']:
            return [event('capital_changed', 'fr.text.share_split_preferred_voting_rights.v1', **m.groupdict(), fully_paid=True, registered=True, restricted_by_statutes=True, preferred_voting_rights=True)], ''

    return [], leftover
