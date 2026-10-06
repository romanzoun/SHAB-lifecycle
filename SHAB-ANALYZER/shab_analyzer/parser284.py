from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser284_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract fixture-backed complete clauses, retaining unsupported text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', evidence=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m or (evidence and not re.search(evidence, source_text)):
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, event_type='officer_changed', **kw):
        return _person_event(*context, event_type, rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Nouvel associé: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), lequel signe individuellement')
    if m:
        return [person('fr.persons.new_associate_individual.v1', m['name'], role='associé', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(r'Weitere Adresse gestrichen: (?P<street>[^,]+), (?P<postal_code>\d{4}) (?P<place>(?:St\. )?[^.;]+)', 'de')
    if m:
        return [event('de.text.additional_address_removed.v1', action='additional_address_removed', **m.groupdict())], ''

    m = match(rf'Procuration individuelle est conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), à (?P<place2>{NAME}), tous deux du (?P<origin>{NAME})')
    if m:
        return [person('fr.persons.two_individual_procurations_shared_origin.v1', m[f'name{i}'], place=m[f'place{i}'], signing='Einzelprokura', extra={'origin': m['origin']}) for i in (1, 2)], ''

    m = match(rf'Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<resolution_date>{DATE}) aufgelöst\. Die Liquidation wird unter der Firma: (?P<company>[^;]+?) durchgeführt\. Eingetragene Person geändert: (?P<previous_name>{NAME}), korrekterweise (?P<name>{NAME}), Verwaltungsratsmitglied, Vizepräsidentin, Einzelunterschrift, neu Verwaltungsratsmitglied, Vizepräsidentin, Liquidatorin, Einzelunterschrift', 'de')
    if m:
        rule = 'de.text.dissolution_corrected_name_liquidator.v1'
        return [event(rule, action='dissolution', resolution_date=m['resolution_date'], liquidation_name=m['company']), person(rule, m['name'], role='Verwaltungsratsmitglied, Vizepräsidentin, Liquidatorin', signing='Einzelunterschrift', extra={'previous_name': m['previous_name'], 'correction': True})], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>[^,.;]+? ép\. [^,.;]+?) sont maintenant domiciliés à (?P<place>{NAME})')
    if m:
        return [person('fr.persons.two_domiciles_changed.v1', m[f'name{i}'], place=m['place']) for i in (1, 2)], ''

    m = match(rf'Le gérant (?P<name1>{NAME}), nommé président, signe désormais collectivement à deux\. Nouveaux gérants: (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}) et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), avec signature collective à deux')
    if m:
        rule = 'fr.persons.manager_president_two_new_managers.v1'
        return [person(rule, m[f'name{i}'], role='gérant président' if i == 1 else 'gérant', signing='Kollektivunterschrift zu zweien', place=m.groupdict().get(f'place{i}'), extra={'origin': m[f'origin{i}']} if i != 1 else {}) for i in (1, 2, 3)], ''

    m = match(rf"Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<seller>{NAME}), maintenant domiciliée à (?P<seller_place>{NAME}), (?P<country>{NAME}), est désormais associée pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal), et (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est nouvel associé pour (?P=transferred) parts de CHF (?P=nominal)\. Gérants: les associés (?P=seller), présidente, et (?P=buyer), tous deux avec signature individuelle\. Signature individuelle conférée (?P<director>{NAME}), de et à (?P<director_place>{NAME}), directrice")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'nominal', 'remaining')):
        restored = leftover
        if re.search(re.escape(restored) + r'\.?$', source_text):
            rule = 'fr.persons.transfer_managers_director_individual.v1'
            return [person(rule, m['seller'], role='associée-gérante présidente', place=m['seller_place'], signing='Einzelunterschrift', extra={'country': m['country'], 'shares': int(number(m['remaining'])), 'share_nominal': m['nominal'], 'transferred_shares': int(number(m['transferred']))}), person(rule, m['buyer'], role='associé-gérant', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['director'], role='directrice', place=m['director_place'], signing='Einzelunterschrift', extra={'origin': m['director_place']})], ''

    m = match(r"Radiation de la mention relative à l'exploitation (?P<establishment>[^.;]+)")
    if m:
        return [event('fr.text.establishment_mention_removed.v1', action='establishment_mention_removed', **m.groupdict())], ''

    m = match(rf"Complément: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<page>\d+)/(?P<notice_id>\d+)\) est complétée en ce sens que le prénom exact de l'administrateur délégué est (?P<name>{NAME})")
    if m:
        return [person('fr.persons.delegate_given_name_corrected.v1', m['name'], role='administrateur délégué', extra={'correction': True, **{k: v for k, v in m.groupdict().items() if k != 'name'}})], ''

    m = match(rf"Les (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives sont maintenant liées selon statuts\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives, liées selon statuts")
    if m and all(number(m[k]) > 0 for k in ('count', 'nominal', 'capital')) and number(m['capital']) == number(m['count']) * number(m['nominal']):
        restored = leftover
        if re.search(re.escape(restored) + r'\.', source_text):
            return [event('fr.text.registered_shares_restricted.v1', action='share_transfer_restrictions_changed', fully_paid=True, restricted_by_statutes=True, **m.groupdict())], ''

    m = match(rf'Signature collective à deux a été conférée à (?P<name1>{NAME}) et (?P<name2>{NAME}), nommés directeurs; leur procuration est radiée')
    if m:
        return [person('fr.persons.two_directors_procurations_revoked.v1', m[f'name{i}'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'procuration_revoked': True}) for i in (1, 2)], ''

    # This German clause is published with French XML language metadata.
    m = match(rf'Ausgeschiedene Personen und erloschene Unterschriften: (?P<name1>[^,]+, [^,]+), von (?P<origin1>{NAME}), in (?P<place1>{NAME}), Gesellschafterin, ohne Zeichnungsberechtigung, mit (?P<count1>{COUNT}) Stammanteilen zu je CHF (?P<nominal>{MONEY})\. Eingetragene Personen neu oder mutierend: (?P<name2>[^,]+, [^,]+), von (?P<origin2>{NAME}), in (?P<place2>{NAME}), Gesellschafter, ohne Zeichnungsberechtigung, mit (?P<count2>{COUNT}) Stammanteilen zu je CHF (?P=nominal) \[bisher: mit (?P<previous_count>{COUNT}) Stammanteilen zu je CHF (?P=nominal)\]; (?P<name3>[^,]+, [^,]+), von (?P<origin3>{NAME}), in (?P<place3>{NAME}), Gesellschafter, ohne Zeichnungsberechtigung, mit (?P<count3>{COUNT}) Stammanteilen zu je CHF (?P=nominal)', 'fr')
    if m and all(number(m[k]) > 0 for k in ('count1', 'count2', 'count3', 'previous_count', 'nominal')):
        rule = 'de.persons.associate_exit_two_holdings.v1'
        return [person(rule, m[f'name{i}'], event_type='officer_removed' if i == 1 else 'officer_changed', role='Gesellschafterin' if i == 1 else 'Gesellschafter', place=m[f'place{i}'], signing='ohne Zeichnungsberechtigung', extra={'origin': m[f'origin{i}'], 'shares': int(number(m[f'count{i}'])), 'share_nominal': m['nominal'], **({'previous_shares': int(number(m['previous_count']))} if i == 2 else {})}) for i in (1, 2, 3)], ''

    return [], leftover
