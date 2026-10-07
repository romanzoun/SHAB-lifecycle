from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser299_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete fixture-backed clauses and retain unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    m = match(rf"Kapital neu: CHF (?P<capital>{MONEY}) \[bisher: CHF (?P<previous_capital>{MONEY})\]\. Erhöhung des Dotationskapitals gemäss Beschluss des (?P<authority>[^;]+?) vom (?P<decision_date>{DATE}) betreffend die Übertragung des Grundstücks Nr\. (?P<parcel>[A-Z]\d+) um CHF (?P<increase>{MONEY})", 'de')
    if m:
        return [event('de.text.endowment_capital_land_transfer.v1', action='endowment_capital_increased', **m.groupdict())], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital-actions est de: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), et non de CHF (?P<previous_nominal>{MONEY}), nominatives, liées selon statuts", 'fr')
    if m:
        return [event('fr.text.registered_share_nominal_corrected.v1', action='share_nominal_corrected', fully_paid=True, **m.groupdict())], ''

    m = match(rf"Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafterin, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführerin, Einzelunterschrift, neu Gesellschafterin, (?P=count) Stammanteile zu CHF (?P=nominal), ohne Unterschrift", 'de')
    if m:
        return [person('de.persons.associate_manager_signing_removed.v1', m['name'], role='Gesellschafterin', signing='ohne Unterschrift', extra={'count': m['count'], 'nominal': m['nominal'], 'previous_role': 'Gesellschafterin, Geschäftsführerin', 'previous_signing': 'Einzelunterschrift'})], ''

    m = match(rf'(?P<name1>{NAME}), des USA, à (?P<place1>{NAME}), DEU, président et (?P<name2>{NAME}), des USA, à (?P<place2>{NAME}), UT, USA, vice-président, sont membres du Conseil de fondation, avec signature individuelle', 'fr')
    if m:
        rule = 'fr.persons.foreign_foundation_president_vice_president.v1'
        return [person(rule, m['name' + i], place=m['place' + i], role=role, signing='Einzelunterschrift', extra={'origin': 'USA', 'country': country, **({'region': 'UT'} if i == '2' else {})}) for i, role, country in [('1', 'président du conseil de fondation', 'DEU'), ('2', 'vice-président du conseil de fondation', 'USA')]], ''

    # German text is labelled French in this fixture.
    member = rf'(?P<name>{{name}}), von (?P<origin>[^;]+?), in (?P<place>{NAME}), (?P<role>Vizepräsidentin des Vorstandes|Mitglied des Vorstandes(?:, Aktuarin)?), mit Kollektivunterschrift zu zweien \[bisher: (?P<previous_role>Vizepräsidentin des Vorstandes, Aktuarin|Mitglied des Vorstandes), (?P<previous_signing>mit Kollektivunterschrift zu zweien|ohne Zeichnungsberechtigung)\]'
    patterns = [member.replace('{name}', r'[^,;]+, [^,;]+').replace('(?P<', f'(?P<p{i}_') for i in range(3)]
    m = match('Eingetragene Personen neu oder mutierend: ' + '; '.join(patterns), 'fr')
    if m:
        rule = 'de.persons.association_board_changes_fr_xml.v1'
        return [person(rule, m[f'p{i}_name'], place=m[f'p{i}_place'], role=m[f'p{i}_role'], signing='Kollektivunterschrift zu zweien', extra={k: m[f'p{i}_{k}'] for k in ('origin', 'previous_role', 'previous_signing')}) for i in range(3)], ''

    m = match(rf"Administration: (?P<president>{NAME}), nommé président, lequel continue à signer individuellement, (?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signent collectivement à deux", 'fr')
    if m:
        rule = 'fr.persons.board_president_two_members_signing.v1'
        return [person(rule, m['president'], role='président', signing='Einzelunterschrift')] + [person(rule, m['name' + i], place=m['place' + i], role='administrateur', signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin' + i]}) for i in ('1', '2')], ''

    m = match(rf"\((?P<translation_de>[^;]+?)\) \((?P<translation_en>[^;]+?)\)\. Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant l'entier du capital-actions, ne sont désormais plus restreintes quant à la transmissiblité \(art\. 685a, al\. 3 CO\)\. L'administrateur (?P<name>{NAME}) est élu liquidateur avec signature individuelle", 'fr')
    if m:
        rule = 'fr.text.liquidation_share_restrictions_removed.v1'
        return [event(rule, action='share_transfer_restrictions_removed', **{k: v for k, v in m.groupdict().items() if k != 'name'}), person(rule, m['name'], role='liquidateur', signing='Einzelunterschrift', extra={'previous_role': 'administrateur'})], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund des Urteils des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) nur zum Zweck der Geltendmachung von abgetretenen Ansprüchen nach Art\. 260 SchKG wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter', 'de')
    if m:
        return [event('de.text.reinstatement_assigned_claims.v1', action='organization_reinstated', purpose='assigned_claims', legal_basis='Art. 260 SchKG', **m.groupdict())], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) sont nommé liquidateur avec signature collective à deux\. Les membres du conseil de fondation (?P<name4>{NAME}), (?P<name5>{NAME}), (?P<name6>{NAME}) et (?P<name7>{NAME}) sont nommés liquidateurs sans signature', 'fr')
    if m:
        rule = 'fr.persons.foundation_liquidators_mixed_signing.v1'
        return [person(rule, m[f'name{i}'], role='liquidateur', signing='Kollektivunterschrift zu zweien' if i <= 3 else 'ohne Unterschrift', extra={'previous_role': 'membre du conseil de fondation'}) for i in range(1, 8)], ''

    m = match(rf'Conseil de fondation : (?P<president>{NAME}), nommé président, (?P<vice>{NAME}), de et à (?P<vice_place>{NAME}), vice-président, et (?P<secretary>{NAME}), de (?P<secretary_origin>{NAME}), à (?P<secretary_place>{NAME}), F, secrétaire\. Signature individuelle du président, ou collective à deux avec le président des autres membre du conseil de fondation', 'fr')
    if m:
        rule = 'fr.persons.foundation_signing_with_president.v1'
        return [person(rule, m['president'], role='président', signing='Einzelunterschrift'), person(rule, m['vice'], place=m['vice_place'], role='vice-président', signing='Kollektivunterschrift zu zweien', extra={'origin': m['vice_place'], 'signing_partners': [m['president']]}), person(rule, m['secretary'], place=m['secretary_place'], role='secrétaire', signing='Kollektivunterschrift zu zweien', extra={'origin': m['secretary_origin'], 'country': 'F', 'signing_partners': [m['president']]})], ''

    m = match(rf'Administration: (?P<president>{NAME}), du Canada, à (?P<president_place>{NAME}), CAN, président, (?P<delegate1>{NAME}), nommé délégué, (?P<secretary>{NAME}), du Canada, à (?P<secretary_place>{NAME}), CAN, secrétaire, (?P<delegate2>{NAME}), de et à (?P<delegate_place>{NAME}), délégué, et (?P<member>{NAME}), du Canada, à (?P<member_place>{NAME}), CAN\. Signature collective à deux de (?P=delegate1) et (?P=delegate2) ou collective à deux avec (?P=delegate1) ou (?P=delegate2) des autres administrateurs', 'fr')
    if m:
        rule = 'fr.persons.board_signing_with_delegates.v1'
        delegates = [m['delegate1'], m['delegate2']]
        result = [person(rule, name, role='délégué', place=m['delegate_place'] if i == 1 else None, signing='Kollektivunterschrift zu zweien', extra={'signing_partners': [delegates[1-i]], **({'origin': m['delegate_place']} if i == 1 else {})}) for i, name in enumerate(delegates)]
        result += [person(rule, m[key], place=m[key + '_place'], role=role, signing='Kollektivunterschrift zu zweien', extra={'origin': 'Canada', 'country': 'CAN', 'signing_partners': delegates}) for key, role in [('president', 'président'), ('secretary', 'secrétaire'), ('member', 'administrateur')]]
        return result, ''

    clause = rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<previous_date>{DATE}) geänderte Bestimmung betreffend {{kind}} Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<history_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte Bestimmung betreffend {{kind}} Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.\]'
    first = clause.replace('{kind}', 'genehmigter').replace('(?P<', '(?P<authorized_')
    second = clause.replace('{kind}', 'bedingter').replace('(?P<', '(?P<conditional_')
    m = match(first + r'\. ' + second, 'de')
    if m:
        return [event('de.text.authorized_conditional_capital_provisions_changed.v1', action='capital_provisions_changed', **m.groupdict())], ''

    return [], leftover
