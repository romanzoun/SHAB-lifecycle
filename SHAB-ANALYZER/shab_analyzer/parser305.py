from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser305_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, preserving unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(source_pattern, source_text)
            if not source or any(source[k] != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, m):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict()})

    def person(rule, m, key='name', **kwargs):
        return _person_event(*context, 'officer_changed', rule, m[key], extra=m.groupdict(), **kwargs)

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}) continuent à engager la société par leur signature collective à deux, désormais sans restriction', 'fr')
    if m:
        rule = 'fr.text.two_signing_restrictions_removed.v1'
        return [person(rule, m, key, signing='Kollektivunterschrift zu zweien') for key in ('name1', 'name2')], ''

    m = match(rf'Par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<name1>{NAME}) est maintenant associé pour (?P<count1>{COUNT}) parts de CHF (?P=nominal), (?P<name2>{NAME}) est maintenant associé pour (?P<count2>{COUNT}) parts de CHF (?P=nominal), (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), est nouvel associé pour (?P<count3>{COUNT}) parts de CHF (?P=nominal), et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), est nouvel associé pour (?P<count4>{COUNT}) parts de CHF (?P=nominal)\. Nouveaux gérants: les associés (?P=name3) et (?P=name4), tous deux avec signature collective à deux', 'fr')
    if m:
        rule = 'fr.text.share_transfer_two_new_managers.v1'
        return [event(rule, m)] + [person(rule, m, f'name{i}', place=m[f'place{i}'], role='associé gérant', signing='Kollektivunterschrift zu zweien') for i in (3, 4)], ''

    m = match(rf'Zweigniederlassung neu: \[aufgehoben\] \[gestrichen: (?P<place1>{NAME})\]\. \[aufgehoben\] \[gestrichen: (?P<place2>{NAME})\]', 'de')
    if m:
        return [event('de.text.two_branches_deleted.v1', m)], ''

    m = match(rf'Nouvelle succursale: (?P<place>{NAME}) \((?P<uid>{UID})\) \[non: (?P<previous_place>{NAME}) \((?P=uid)\)\]', 'fr')
    if m:
        return [event('fr.text.branch_place_corrected.v1', m)], ''

    m = match(rf"\((?P<german_name>{NAME}) in Liquidation\) \((?P<english_name>{NAME}) in liquidation\)\. L'administrateur (?P<name>{NAME}) est élu liquidateur avec signature individuelle", 'fr')
    if m:
        rule = 'fr.text.liquidation_translations_liquidator.v1'
        return [event(rule, m), person(rule, m, role='liquidateur', signing='Einzelunterschrift')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<resolution_date>{DATE}) eine Anpassung des bedingten Kapitals gemäss näherer Umschreibung in den Statuten beschlossen', 'de')
    if m:
        return [event('de.text.conditional_capital_adjusted.v1', m)], ''

    fragment = rf'eingetragenen Einzelfirma (?P<business>{NAME}), (?P<activity>{NAME}), in (?P<place>{NAME}), gemäss einer noch zu erstellenden Übernahmebilanz zum Preis von höchstens CHF (?P<maximum>{COUNT})\.-- zu übernehmen\.\]'
    source = rf'Qualifizierte Tatbestände neu: \[Die Bestimmung über die beabvsichtigte Sachübernahme bei der Gründung vom (?P<foundation_date>{DATE}) ist aus den Statuten gestrichen worden\.\] \[gestrichen: Beabsichtigte Sachübernahme: Die Gesellschaft beabsichtigt, nach der Gründung einen Teil der Aktiven und Passiven der im Handelsregister {fragment}\.'
    m = match(fragment, 'de', source)
    if m:
        return [event('de.text.intended_asset_acquisition_deleted.v1', m)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président et directeur, lequel continue à signer individuellement, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), et (?P<name4>{NAME}), de et à (?P<place4>{NAME}), lesquels signent collectivement à deux", 'fr')
    if m:
        rule = 'fr.text.administration_president_three_collective.v1'
        return [person(rule, m, 'name1', role='président et directeur', signing='Einzelunterschrift')] + [person(rule, m, f'name{i}', place=m[f'place{i}'], role='administration', signing='Kollektivunterschrift zu zweien') for i in (2, 3, 4)], ''

    m = match(rf'Anteilscheine neu: CHF (?P<nominal>{MONEY})\. Haftung/Nachschusspflicht neu: Persönliche Haftung der Genossenschafter gemäss näherer Umschreibung in den Statuten\. Nachschusspflicht der Genossenschafter gemäss näherer Umschreibung in den Statuten', 'de')
    if m:
        return [event('de.text.cooperative_shares_liability_additional_contributions.v1', m)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), présidente avec signature individuelle, (?P<name2>{NAME}), nommé délégué, et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), secrétaire, lesquels signent collectivement à deux; les pouvoirs (?P=name2) sont modifiés en ce sens', 'fr')
    if m:
        rule = 'fr.text.administration_president_delegate_secretary.v1'
        return [person(rule, m, 'name1', place=m['place1'], role='présidente', signing='Einzelunterschrift'), person(rule, m, 'name2', role='délégué', signing='Kollektivunterschrift zu zweien'), person(rule, m, 'name3', place=m['place3'], role='secrétaire', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Succursale: \[biffé: (?P<place>{NAME}) \((?P<uid>{UID})\)\]', 'fr')
    if m:
        return [event('fr.text.branch_deleted.v1', m)], ''

    m = match(rf'(?P<name>{NAME}), dont le prénom exact est (?P<given_names>{NAME}), est maintenant à (?P<place>{NAME})', 'fr')
    if m:
        # The clause explicitly supplies the corrected given names, retaining the surname.
        surname = m['name'].rsplit(' ', 1)[0]
        rule = 'fr.text.given_names_domicile_corrected.v1'
        return [_person_event(*context, 'officer_changed', rule, surname + ' ' + m['given_names'], place=m['place'], extra={**m.groupdict(), 'name': surname + ' ' + m['given_names'], 'previous_name': m['name']})], ''

    return [], leftover
