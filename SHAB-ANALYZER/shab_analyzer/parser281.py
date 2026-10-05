from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event, _FR_MONTHS
from .parser267 import NAME, DATE, COUNT, MONEY

FRENCH_DATE = r'\d{1,2} (?:' + '|'.join(_FR_MONTHS) + r') \d{4}'


def extract_parser281_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete fixture-backed clauses and preserve unsupported residue."""
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
                        if re.fullmatch(DATE, value):
                            datetime.strptime(value, '%d.%m.%Y')
                        else:
                            day, month, year = value.split()
                            datetime(int(year), _FR_MONTHS[month], int(day))
            except (ValueError, KeyError):
                return None
        return m

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Nouveaux associés: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        rule = 'fr.persons.two_new_associates_origins.v1'
        return [person(rule, m[f'name{i}'], role='associé', place=m[f'place{i}'], extra={'origin': m[f'origin{i}']}) for i in (1, 2)], ''

    m = match(rf"Les (?P<previous_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY}), formant l'entier du capital-actions, sont transformées en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), avec restrictions quant à la transmissibilité selon statuts\. L'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital par décision du (?P<decision_date>{FRENCH_DATE})\. Pour les détails, voir les statuts")
    if m and all(num(m[k]) > 0 for k in ('previous_count', 'previous_nominal', 'count', 'nominal')) and num(m['previous_count'])*num(m['previous_nominal']) == num(m['count'])*num(m['nominal']):
        return [event('fr.text.share_split_authorized_capital.v1', action='share_split_authorized_capital', transfer_restricted=True, **m.groupdict())], ''

    m = match(r"Le conseil de fondation se réserve expressément la possibilité de faire modifier le but par l'autorité de surveillance, en application de l'article (?P<article>86a CC) et des statuts")
    if m:
        return [event('fr.text.foundation_purpose_change_reserved.v1', action='purpose_change_reserved', **m.groupdict())], ''

    m = match(rf"(?P<name1>{NAME}), directrice, (?P<name2>{NAME}), (?P<name3>{NAME}), (?P<name4>{NAME}) et (?P<name5>{NAME}), tous nommés membres du conseil d'administration, continuent de signer collectivement à deux")
    if m:
        rule = 'fr.persons.five_board_members_signing_retained.v1'
        return [person(rule, m[f'name{i}'], role="directrice, membre du conseil d'administration" if i == 1 else "membre du conseil d'administration", signing='Kollektivunterschrift zu zweien') for i in range(1, 6)], ''

    m = match(rf'(?P<statutes_date>{DATE})\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<previous_date>{DATE}) \(für Stammaktien\) geändert\. \. Die Generalversammlung hat mit Beschluss vom (?P<preferred_date>{DATE}) eine bedingte Kapitalerhöhung \(für Vorzugsaktien\) gemäss näherer Umschreibung in den Statuten eingeführt', 'de')
    if m:
        return [event('de.text.conditional_capital_common_preferred.v1', action='conditional_capital_changed_and_introduced', **m.groupdict())], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{NAME}), nommé vice-président, (?P<name2>{NAME}), (?P<name3>{NAME}), (?P<name4>{NAME}), (?P<name5>{NAME}), (?P<name6>{NAME}), (?P<name7>{NAME}) et (?P<name8>{NAME}), signent désormais collectivement à deux, sans autre restriction; leurs pouvoirs sont modifiés en ce sens')
    if m:
        rule = 'fr.persons.foundation_board_unrestricted_collective.v1'
        return [person(rule, m[f'name{i}'], role='vice-président du conseil de fondation' if i == 1 else 'membre du conseil de fondation', signing='Kollektivunterschrift zu zweien', extra={'signing_restriction_removed': True}) for i in range(1, 9)], ''

    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company>{NAME}) in Liquidation\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, Geschäftsführer, Liquidator, Einzelunterschrift', 'de')
    if m and num(m['count']) > 0 and num(m['nominal']) > 0:
        rule = 'de.persons.dissolution_manager_liquidator.v1'
        return [event(rule, action='dissolution', decision_date=m['decision_date'], company=m['company'] + ' in Liquidation'), person(rule, m['name'], role='Gesellschafter, Geschäftsführer, Liquidator', signing='Einzelunterschrift', extra={'shares': int(num(m['count'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>F), président, (?P<name2>{NAME}), jusqu'ici président, (?P<name3>{NAME}), (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), (?P<country4>F), secrétaire, (?P<name5>{NAME}), de (?P<origin5>{NAME}), à (?P<place5>{NAME}), (?P<country5>F), et (?P<name6>{NAME}), de (?P<origin6>{NAME}), à (?P<place6>{NAME}), (?P<country6>F), sont membres du conseil d'administration\. Signature individuelle de (?P=name2) ou (?P=name3), ou collective à deux de (?P=name1), (?P=name4) ou (?P=name5); (?P=name6) n'exerce pas la signature sociale")
    if m:
        rule = 'fr.persons.board_mixed_signing.v1'
        events = []
        for i in range(1, 7):
            extra = {key: m[f'{key}{i}'] for key in ('origin', 'country') if f'{key}{i}' in m.groupdict()}
            if i == 2:
                extra['previous_role'] = 'président'
            events.append(person(rule, m[f'name{i}'], role="président du conseil d'administration" if i == 1 else "secrétaire du conseil d'administration" if i == 4 else "membre du conseil d'administration", place=m.groupdict().get(f'place{i}'), signing='Einzelunterschrift' if i in (2, 3) else 'ohne Zeichnungsberechtigung' if i == 6 else 'Kollektivunterschrift zu zweien', extra=extra))
        return events, ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'autre adresse est: (?P<address>[^,;]+), (?P<postal_code>\d{{4}}) (?P<place>{NAME}) \(et non pas (?P<previous_address>[^,;]+), (?P<previous_postal_code>\d{{4}}) (?P<previous_place>{NAME})\)")
    if m:
        return [event('fr.text.other_address_corrected.v1', action='other_address_corrected', correction=True, **m.groupdict())], ''

    m = match(rf'Der (?P<court>Kantonsgerichtspräsident des Kantonsgerichts Schwyz) hat mit Entscheid vom (?P<decision_date>{DATE}) der gegen die Konkurseröffnung erhobenen Beschwerde aufschiebende Wirkung zuerkannt', 'de')
    if m:
        return [event('de.text.bankruptcy_appeal_suspensive_effect.v1', action='bankruptcy_appeal_suspensive_effect', **m.groupdict())], ''

    m = match(rf"(?P<name1>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par (?P<count2>{COUNT}) parts à (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), et par (?P<count3>{COUNT}) parts à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouveaux associés sans signature, avec respectivement (?P=count2) et (?P=count3) parts de CHF (?P=nominal); (?P=name1) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(num(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'count2', 'count3', 'remaining')) and num(m['count2']) + num(m['count3']) == num(m['transferred']) and num(m['previous']) - num(m['transferred']) == num(m['remaining']):
        rule = 'fr.persons.transfer_two_unsigned_associates.v1'
        return [person(rule, m['name1'], role='associé', extra={'shares': int(num(m['remaining'])), 'transferred_shares': int(num(m['transferred'])), 'share_nominal': m['nominal']})] + [person(rule, m[f'name{i}'], role='associé', place=m[f'place{i}'], signing='ohne Zeichnungsberechtigung', extra={'origin': m[f'origin{i}'], 'shares': int(num(m[f'count{i}'])), 'share_nominal': m['nominal']}) for i in (2, 3)], ''

    m = match(rf"Le (?P<court>président du Tribunal de l'arrondissement de l'Est vaudois) a prononcé le (?P<decision_date>{FRENCH_DATE}) la révocation de la faillite et ordonné la réintégration du titulaire dans la libre disposition de ses biens")
    if m:
        return [event('fr.text.bankruptcy_revoked_owner_reinstated.v1', action='bankruptcy_revoked_owner_reinstated', **m.groupdict())], ''

    return [], leftover
