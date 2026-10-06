from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser288_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete fixture-backed clauses, retaining unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
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

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom du directeur (?P<previous_name>{NAME}) s'orthographie en réalité (?P<name>{NAME})")
    if m:
        return [person('fr.persons.director_name_spelling_corrected.v1', m['name'], role='directeur', extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que les nouveaux statuts sont datés du (?P<statutes_date>{DATE}) \(et non du: (?P<previous_statutes_date>{DATE})\)")
    if m:
        return [event('fr.text.statutes_date_corrected_colon.v1', action='statutes_corrected', correction=True, **m.groupdict())], ''

    m = match(rf'Nuova succursale: (?P<place>{NAME}) \(CHE (?P<uid_digits>\d{{3}}\.\d{{3}}\.\d{{3}})\)', 'it')
    if m:
        return [event('it.text.branch_added_uid_space.v1', action='branch_added', place=m['place'], branch_uid='CHE-' + m['uid_digits'])], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FSOC du (?P<notice_date>{DATE}) p\.(?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est originaire de (?P<origin>{NAME}) \(et non pas de de (?P<previous_origin>{NAME})\)")
    if m:
        return [person('fr.persons.origin_corrected_notice_typos.v1', m['name'], extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf'Nouveaux gérants: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>[^,;]+?), de (?P<origin2>{NAME}), à (?P<place2>{NAME})(?:, avec signature collective à deux)?')
    if m and leftover.removesuffix(', avec signature collective à deux') + ', avec signature collective à deux.' in source_text:
        rule = 'fr.persons.two_new_managers_collective_signing.v1'
        return [person(rule, m['name' + i], role='gérant', place=m['place' + i], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin' + i]}) for i in ('1', '2')], ''

    m = match(rf"Capital-actions réduit de CHF (?P<capital>{MONEY}) à CHF 0 par destruction des (?P<destroyed>{COUNT}) actions de CHF (?P<nominal>{MONEY}), et reporté simultanément de CHF 0 à CHF (?P=capital) par l'émission de (?P<issued>{COUNT}) actions de CHF (?P=nominal)\. Montant libéré par compensation de créance: CHF (?P<offset>{MONEY}) en échange de (?P<offset_shares>{COUNT}) actions de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('capital', 'destroyed', 'nominal', 'issued', 'offset', 'offset_shares')) and number(m['destroyed']) * number(m['nominal']) == number(m['capital']) == number(m['issued']) * number(m['nominal']) and number(m['offset_shares']) * number(m['nominal']) == number(m['offset']) <= number(m['capital']):
        return [event('fr.text.capital_reset_claim_offset.v1', action='capital_reset', currency='CHF', reduced_capital='0', **m.groupdict())], ''

    m = match(rf"L'associé (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par (?P<count1>{COUNT}) parts de CHF (?P=nominal) à l'associé-gérant (?P<buyer1>{NAME}), désormais titulaire de (?P<total1>{COUNT}) parts de CHF (?P=nominal), et par (?P<count2>{COUNT}) parts de CHF (?P=nominal) à l'associée (?P<buyer2>{NAME}) \((?P<buyer_registration>ATU\d+)\), désormais titulaire de (?P<total2>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'count1', 'count2', 'total1', 'total2', 'remaining')) and number(m['count1']) + number(m['count2']) == number(m['transferred']) and number(m['remaining']) + number(m['transferred']) == number(m['previous']) and all(number(m['total' + i]) >= number(m['count' + i]) for i in ('1', '2')):
        rule = 'fr.persons.share_transfer_two_recipients.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['seller'], role='associé', extra={'shares': int(number(m['remaining'])), 'share_nominal': m['nominal']}), person(rule, m['buyer1'], role='associé-gérant', extra={'shares': int(number(m['total1'])), 'share_nominal': m['nominal']}), person(rule, m['buyer2'], role='associée', extra={'shares': int(number(m['total2'])), 'share_nominal': m['nominal'], 'registration': m['buyer_registration']})], ''

    m = match(rf'Administration : (?P<name1>{NAME}), nommé président et (?P<name2>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>FRA), lesquels signent individuellement')
    if m:
        rule = 'fr.persons.board_president_two_individual_signatures.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Einzelunterschrift'), person(rule, m['name2'], role='administrateur', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'country': m['country']})], ''

    m = match(rf'Grenzüberschreitende Fusion nach den Vorschriften des Art\. (?P<article>163a IPRG): Übernahme der Aktiven und Passiven der (?P<transferor>[^;\n]+?), in (?P<place>[^;\n]+?) \(Company No\.: (?P<registration>\d+)\), gemäss Fusionsvertrag vom (?P<contract_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft einzige Gesellschafterin der übertragenden Gesellschaft ist, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt', 'de')
    if m and number(m['assets']) > 0 and number(m['liabilities']) >= 0:
        return [event('de.text.cross_border_merger_sole_shareholder.v1', action='merger', cross_border=True, capital_increase=False, shares_allocated=False, currency='CHF', **m.groupdict())], ''

    m = match(rf'Le nom exacte de (?P<previous_name>{NAME}) est (?P<name>{NAME})')
    if m:
        return [person('fr.persons.name_corrected_exacte_typo.v1', m['name'], extra={'previous_name': m['previous_name'], 'correction': True})], ''

    m = match(rf'(?P<name>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>KEN), est membre du comité, sans signature sociale')
    if m:
        return [person('fr.persons.committee_member_no_social_signature.v1', m['name'], role='membre du comité', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'country': m['country']})], ''

    m = match(rf'Les gérants (?P<name1>{NAME}), maintenant domicilié à (?P<place>{NAME}), et (?P<name2>{NAME}), sont nommés liquidateurs, lesquels continuent de signer collectivement à deux')
    if m:
        rule = 'fr.persons.managers_liquidators_continue_collective_signing.v1'
        return [person(rule, m['name1'], role='gérant liquidateur', place=m['place'], signing='Kollektivunterschrift zu zweien'), person(rule, m['name2'], role='gérant liquidateur', signing='Kollektivunterschrift zu zweien')], ''

    return [], leftover
