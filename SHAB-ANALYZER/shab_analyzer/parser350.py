from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser350_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events only for fully supported remaining clauses."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, *, rule_language=None, **extra):
        return _event(*context, 'organization_changed', f'{rule_language or language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf"Administration: (?P<name1>{NAME}), président, (?P<name2>{NAME}), vice-président, (?P<name3>{NAME}), et (?P<name4>{NAME}), jusqu'ici directeur, lesquels signent collectivement à deux\. Les pouvoirs de (?P=name1), (?P=name2) et (?P=name3) sont modifiés en ce sens")
    if m:
        roles = ['Präsident', 'Vizepräsident', 'Verwaltungsrat', 'Verwaltungsrat']
        return [person('board_composition_collective_signing', m, m[f'name{i}'], roles[i-1], 'Kollektivunterschrift zu zweien', **({'previous_role': 'directeur'} if i == 4 else {})) for i in range(1, 5)], ''

    m = match(rf'\((?P<german_name>[^()]+ in Liquidation)\) \((?P<italian_name>[^()]+ in liquidazione)\) \((?P<english_name>[^()]+ in liquidation)\)\. Les associés-gérants (?P<name1>{NAME}), maintenant à (?P<place>{NAME}), et (?P<name2>{NAME}), sont nommés liquidateurs')
    if m:
        return [event('liquidation_translations', m)] + [person('associate_managers_appointed_liquidators', m, m[f'name{i}'], 'Liquidator', place=m['place'] if i == 1 else None, previous_role='associé-gérant') for i in (1, 2)], ''

    m = match(rf"Selon jugement du Tribunal de première instance du (?P<decision_date>{DATE}), octroi d'un sursis concordataire définitif jusqu'au (?P<end_date>{DATE})\. (?P<name>{NAME}), de et à (?P<place>{NAME}) est nommé commissaire au sursis")
    if m:
        return [event('definitive_composition_moratorium_granted', m), person('composition_commissioner_appointed', m, m['name'], 'Sachwalter', place=m['place'], origin=m['place'])], ''

    # This sample has French XML metadata but a German clause. Accept both
    # metadata languages for this complete clause, retaining its German rule ID.
    # Corporate names contain full stops, unlike the ordinary NAME token.
    company = r'[^();]+?'
    m = match(rf'Eingetragene Person geändert: (?P<name1>{company}) \((?P<register1>\d+)\), Gesellschafterin, (?P<previous_count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), neu Gesellschafterin, (?P<count1>{COUNT}) Stammanteile zu CHF (?P=nominal)\. Neu eingetragene Person: (?P<name2>{company}) \((?P<register2>\d+)\), in (?P<place>{NAME}) \((?P<country>[A-Z]{{2}})\), Gesellschafterin, (?P<count2>{COUNT}) Stammanteile zu CHF (?P=nominal)', language if language in ('de', 'fr') else 'de')
    if m:
        number = lambda key: Decimal(m[key].replace("'", ''))
        if all(number(k) > 0 for k in ('previous_count', 'count1', 'count2', 'nominal')) and number('previous_count') == number('count1') + number('count2'):
            return [event('corporate_shareholdings_changed', m, rule_language='de', currency='CHF')], ''

    m = match(rf'Die Eintragungsnummer (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) ist wie folgt ergänzt: Die Statutenbestimmung über die Beschränkung der Übertragbarkeit der Namenaktien ist gelöscht', 'de')
    if m:
        return [event('registered_share_transfer_restriction_deleted_correction', m)], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}) sont élus liquidateur')
    if m:
        return [person('board_members_elected_liquidators', m, m[f'name{i}'], 'Liquidator', previous_role='administrateur') for i in (1, 2)], ''

    m = match(rf"(?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), gérants, exercent désormais la signature sociale, collectivement à deux\. (?P<name3>{NAME}), jusqu'ici président, et (?P<name4>{NAME}), gérants, signent désormais collectivement à deux")
    if m:
        return [person('managers_presidency_collective_signing', m, m[f'name{i}'], 'Vorsitzender der Geschäftsführung' if i == 1 else 'Geschäftsführer', 'Kollektivunterschrift zu zweien', **({'previous_role': 'président'} if i == 3 else {})) for i in range(1, 5)], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. 159 Abs\. 5 HRegV am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen, nachdem der Einzelrichter mit Verfügung vom (?P<decision_date>{DATE}) die Wiedereröffnung des Konkursverfahrens angeordnet hat\. \[gestrichen: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('bankruptcy_reopened_company_reinstated', m)], ''

    m = match(rf'Liquidateurs: (?P<name1>{NAME}), président, et (?P<name2>{NAME}), tous deux gérants, lesquels continuent de signer individuellement')
    if m:
        return [person('managers_liquidators_continued_individual_signing', m, m[f'name{i}'], 'Liquidator', 'Einzelunterschrift', liquidation_president=i == 1, previous_role='gérant') for i in (1, 2)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est administratrice et non avec signature collective à deux")
    if m:
        return [person('board_member_role_signing_correction', m, m['name'], 'Verwaltungsrat', corrected_description='avec signature collective à deux')], ''

    m = match(rf"Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company_name>{NAME}), in Liquidation\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P=count) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Liquidator, Einzelunterschrift", 'de')
    if m and all(Decimal(m[k].replace("'", '')) > 0 for k in ('count', 'nominal')):
        return [event('company_dissolved_liquidation_name', m, liquidation_name=m['company_name'] + ', in Liquidation'), person('associate_manager_appointed_liquidator', m, m['name'], 'Liquidator', 'Einzelunterschrift', previous_role='Geschäftsführer')], ''

    m = match(rf'Die rechtliche Zuordnung der (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}) des verstorbenen Gesellschafters (?P<name>{NAME}) ist noch nicht geregelt', 'de')
    if m and all(Decimal(m[k].replace("'", '')) > 0 for k in ('count', 'nominal')):
        return [event('deceased_associate_share_allocation_unresolved', m, currency='CHF')], ''

    return [], leftover
