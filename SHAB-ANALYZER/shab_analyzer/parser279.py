from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser279_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded sample-backed clauses without consuming unknown residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def person(rule, name, **kw):
        return _person_event(*context, kw.pop('event_type', 'officer_changed'), rule, name, **kw)

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def num(v):
        return Decimal(v.replace("'", ''))

    p = rf"Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) formant l'entier du capital-actions ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)\. Les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}), dont la signature est radiée, sont nommés liquidateurs"
    m = match(p + ' avec signature collective à deux')
    if m and num(m['count']) > 0 and num(m['nominal']) > 0:
        rule = 'fr.persons.two_administrators_liquidators_restrictions_removed.v1'
        return [event(rule, action='share_transfer_restrictions_removed', count=m['count'], nominal=m['nominal'])] + [person(rule, m['name'+str(i)], role='administrateur liquidateur', signing='Kollektivunterschrift zu zweien', extra={'previous_signing_removed': True}) for i in (1, 2)], ''

    p = rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) n'est pas administrateur, mais directeur"
    m = match(p + ', avec signature collective à deux')
    if m:
        return [person('fr.persons.administrator_corrected_director.v1', m['name'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'correction': True, 'previous_role': 'administrateur', 'entry': m['entry'], 'entry_date': m['entry_date']})], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce cens que (?P<name>{NAME}) est gérante")
    if m:
        return [person('fr.persons.manager_supplement_cens_typo.v1', m['name'], role='gérante', extra={'supplement': True, 'entry': m['entry'], 'entry_date': m['entry_date']})], ''

    p = rf"par (?P<name>{NAME}), de et à (?P<place>{NAME}), liquidatrice"
    m = match(p + rf" avec signature individuelle\. Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) ne sont plus restreintes quant à la transmissibilité selon l'art\. 685a, al\. 3 CO")
    if m and num(m['count']) > 0 and num(m['nominal']) > 0:
        return [event('fr.persons.liquidatrice_shared_origin.v1', action='share_transfer_restrictions_removed', count=m['count'], nominal=m['nominal']), person('fr.persons.liquidatrice_shared_origin.v1', m['name'], role='liquidatrice', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['place']})], ''

    p = rf"\((?P<translation>[^()]+ in liquidation)\)\. L'associée-gérante (?P<name>{NAME}), est nommée liquidatrice"
    m = match(p + ' avec signature individuelle')
    if m:
        rule = 'fr.persons.associate_liquidatrice_translated_name.v1'
        return [event(rule, action='liquidation_name_translation', translated_name=m['translation']), person(rule, m['name'], role='associée-gérante liquidatrice', signing='Einzelunterschrift')], ''

    m = match(rf"Anteilscheine neu: Anteilscheine zu CHF (?P<nominal>{MONEY}) \[bisher: Anteilscheine zu CHF (?P<previous_nominal>{MONEY})\]", 'de')
    if m and num(m['nominal']) > 0 and num(m['previous_nominal']) > 0:
        return [event('de.text.cooperative_share_nominal_changed.v1', action='cooperative_share_nominal_changed', **m.groupdict())], ''

    m = match(rf"Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag und Inventar vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: Keine", 'de')
    if m and num(m['assets']) >= 0 and num(m['liabilities']) >= 0:
        return [event('de.text.asset_transfer_no_consideration.v1', action='asset_transfer', consideration='Keine', **m.groupdict())], ''

    m = match(rf"L'associé (?P<name1>{NAME}) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<name2>{NAME}), de et à (?P<place>{NAME}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal) sans signature sociale")
    if m and all(num(m[k]) > 0 for k in ('remaining', 'transferred', 'nominal')):
        rule = 'fr.persons.associate_transfer_unsigned_shared_origin.v1'
        return [person(rule, m['name1'], role='associé', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['name2'], role='associé', place=m['place'], extra={'origin': m['place'], 'shares': int(num(m['transferred'])), 'share_nominal': m['nominal'], 'without_signature': True})], ''

    m = match(rf"(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), lesquels ne sont plus associés et dont la signature est radiée, cèdent (?P<count1>{COUNT}), respectivement (?P<count2>{COUNT}), respectivement (?P<count3>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<recipient>{NAME}), désormais titulaire de (?P<total>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(num(m[k]) > 0 for k in ('count1', 'count2', 'count3', 'nominal')) and num(m['total']) >= sum(num(m['count'+str(i)]) for i in (1, 2, 3)):
        rule = 'fr.persons.three_associates_transfer_removed.v1'
        return [person(rule, m['name'+str(i)], event_type='officer_removed', role='associé', extra={'signing_removed': True, 'transferred_shares': int(num(m['count'+str(i)])), 'share_nominal': m['nominal']}) for i in (1, 2, 3)] + [person(rule, m['recipient'], role='associé-gérant', extra={'shares': int(num(m['total'])), 'share_nominal': m['nominal']})], ''

    p1 = rf"(?P<name1>{NAME}) cède (?P<first>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), désormais titulaire de (?P<intermediate>{COUNT}) parts de CHF (?P=nominal)\. (?P=name1) et (?P=name2) cèdent chacun (?P<each>{COUNT}) de leurs (?P=intermediate) parts de CHF (?P=nominal) à (?P<name3>{NAME}), dont la procuration est éteinte, nouvel associé-gérant"
    p2 = rf", avec (?P<received>{COUNT}) parts de CHF (?P=nominal)\. (?P=name1) et (?P=name2) restent titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacun"
    m = match(p1 + ' avec signature individuelle' + p2)
    if m and num(m['nominal']) > 0 and num(m['first']) > 0 and num(m['each']) > 0 and num(m['previous'])-num(m['first']) == num(m['intermediate']) and num(m['intermediate'])-num(m['each']) == num(m['remaining']) > 0 and num(m['received']) == 2*num(m['each']):
        rule = 'fr.persons.sequential_transfers_manager_procuration_ended.v1'
        return [person(rule, m['name'+str(i)], role='associé', extra={'shares': int(num(m['remaining'])), 'share_nominal': m['nominal']}) for i in (1, 2)] + [person(rule, m['name3'], role='associé-gérant', signing='Einzelunterschrift', extra={'shares': int(num(m['received'])), 'share_nominal': m['nominal'], 'procuration_ended': True})], ''

    m = match(rf"Radiation de la mention relative à l'exploitation d'autres établissements à (?P<place1>{NAME}), (?P<address1>[^;]+?) et à (?P<place2>{NAME}), (?P<address2>[^;]+?)\. Nouveau numéro d'identification des succursales à (?P<branch1>{NAME}) \((?P<uid1>{UID})\), (?P<branch2>{NAME}) \((?P<uid2>{UID})\), et (?P<branch3>{NAME}) \((?P<uid3>{UID})\)")
    if m:
        return [event('fr.text.establishments_removed_branch_uids.v1', action='branch_identifiers_updated', removed_establishments=[{'place': m['place'+str(i)], 'address': m['address'+str(i)]} for i in (1, 2)], branches=[{'place': m['branch'+str(i)], 'uid': m['uid'+str(i)]} for i in (1, 2, 3)])], ''

    p = rf"Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>{NAME}) eine definitive Nachlassstundung für sechs Monate bewilligt\. Als Sachwalter wurde (?P<name>{NAME}), lic\. iur\., Advokat, LL\.M\., (?P<address>[^;]+?), Postfach (?P<box>\d+), (?P<postal_code>\d{{4}}) (?P<place>{NAME}) ernannt\. \[gestrichen: Mit Entscheid vom (?P<previous_date>{DATE}) hat der (?P=court) eine provisorische Nachlassstundung von vier Monaten, d\.h\. bis (?P<previous_end_date>{DATE}), bewilligt\. Als provisorischer Sachwalter wurde (?P=name), lic\. iur\., Advokat LL\.M\., (?P=address), Postfach (?P=box), (?P=postal_code) (?P=place) eingesetzt\. Dieser hat die Geschäftstätigkeiten während der provisorischen Nachlassstundung zu beaufsichtigen\.\]"
    m = match(p, 'de')
    if m:
        rule = 'de.text.definitive_moratorium_replaces_provisional.v1'
        return [event(rule, action='definitive_debt_moratorium', duration_months=6, previous_duration_months=4, **m.groupdict()), person(rule, m['name'], role='Sachwalter', place=m['place'], extra={'address': m['address'], 'postal_code': m['postal_code'], 'post_office_box': m['box']})], ''

    return [], leftover
