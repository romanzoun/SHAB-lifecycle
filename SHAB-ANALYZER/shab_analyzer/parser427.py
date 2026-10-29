from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser57, parser87, parser107, parser116, parser124, parser137, parser158, parser189, parser308, parser412

# Historical rules retain ownership, even when tested outside the parser chain.
_LEGACY = tuple(p for module in (parser57, parser87, parser107, parser116, parser124,
                                 parser137, parser158, parser189, parser308, parser412)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser427_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'\[Aufhebung der Statutenbestimmung über die mit Gewährungsbeschluss vom (?P<introduced_date>{DATE}) eingeführte genehmigte Kapitalerhöhung\.\]', 'de')
    if m:
        return [event('authorized_capital_clause_repealed_bracketed', m, 'capital_changed', repealed=True)], ''

    m = match(rf'(?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) chacune à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) et (?P=seller2) restent titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacune')
    if m and re.search(re.escape(m['buyer']) + r', de ' + re.escape(m['origin']) + r', à ' + re.escape(m['place']) + r', nouvel associé avec signature individuelle, titulaire de ' + re.escape(m['buyer_count']) + r' parts de CHF ' + re.escape(m['nominal']), source_text):
        return [event('two_associates_transfer_equal_shares', m, 'ownership_changed', currency='CHF', count_per_seller=m['count'])], ''

    m = match(rf'Procuration collective à deux, sauf entre eux a été conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('two_procurists_except_between_no_comma', m, m[f'name{i}'], signing='Kollektivprokura zu zweien', place=m[f'place{i}'], signing_restriction='sauf entre eux', excluded_signing_partners=[m[f'name{3-i}']]) for i in (1, 2)], ''

    # A prior rule consumed the corrected auditor clause; only resolve this marker
    # when its complete, explicit historical correction is present in the source.
    if language == 'de' and leftover == '[nicht:':
        m = re.search(rf'\[nicht: Ausgeschiedene Personen und erloschene Unterschriften: (?P<auditor>{NAME}) \((?P<auditor_uid>{UID})\) in (?P<place>{NAME}), da diese schon mit dem TR (?P<previous_entry>{COUNT}) v\. (?P<previous_date>{DATE}) ausgeschieden ist\.\]$', source_text)
        if m:
            try:
                datetime.strptime(m['previous_date'], '%d.%m.%Y')
            except ValueError:
                return [], text
            return [event('auditor_repeated_departure_notice_corrected', m, corrected=True, already_departed=True)], ''

    # Seven separately identified officers, with shared exclusions and explicit roles.
    head = rf'Signature collective à deux, sauf entre eux et sauf avec (?P<excluded>{NAME}(?:, {NAME}){{4}} et {NAME}) a été conférée à '
    roles = ['directeur adjoint', 'directeur adjoint', 'directeur adjoint', 'directrice adjointe', 'sous-directeur', 'sous-directrice', 'sous-directeur']
    parts = []
    for i, role in enumerate(roles, 1):
        origin = rf'de (?P<origin{i}>{NAME}), à ' if i != 2 else rf'de et à '
        country = rf', (?P<country{i}>[A-Z]{{3}})' if i == 7 else ''
        parts.append(rf'(?P<name{i}>{NAME}), ' + origin + rf'(?P<place{i}>{NAME})' + country + ', ' + role)
    m = match(head + ', '.join(parts[:6]) + ' et ' + parts[6])
    if m:
        excluded = re.split(r', | et ', m['excluded'])
        return [person('seven_officers_with_shared_exclusions', m, m[f'name{i}'], roles[i-1], 'Kollektivunterschrift zu zweien', m[f'place{i}'], signing_restriction='sauf entre eux et sauf avec ' + m['excluded'], excluded_signing_partners=excluded + [m[f'name{j}'] for j in range(1, 8) if j != i]) for i in range(1, 8)], ''

    m = match(rf"Par arrêt du (?P<decision_date>{DATE}), le (?P<court>{NAME}) a rejeté le recours et fixé l'ouverture de la faillite de la société au (?P<effective_date>{DATE}), à (?P<time>(?:[01]\d|2[0-3])h[0-5]\d)\. Par conséquent sa raison sociale devient: (?P<company_name>[^;\n]+?) en liquidation")
    if m:
        return [event('bankruptcy_appeal_rejected_opening_fixed', m, 'status_changed', appeal_rejected=True, in_liquidation=True)], ''

    parts = [rf'(?P<name{i}>{NAME}), ' + (rf'de (?P<origin{i}>{NAME})' if i != 4 else rf"d'(?P<origin{i}>{NAME})") + rf', à (?P<place{i}>{NAME})' for i in range(1, 5)]
    m = match('Procuration collective à deux, sauf entre eux et avec un administrateur a été conférée à ' + ', '.join(parts[:3]) + ', et ' + parts[3])
    if m:
        return [person('four_procurists_with_administrator', m, m[f'name{i}'], signing='Kollektivprokura zu zweien', place=m[f'place{i}'], signing_restriction='sauf entre eux et avec un administrateur', required_signing_partner_role='administrateur', excluded_signing_partners=[m[f'name{j}'] for j in range(1, 5) if j != i]) for i in range(1, 5)], ''

    m = match(rf'Die Umschreibung der mit Beschluss der Generalversammlung vom (?P<introduced_date>{DATE}) eingeführten Bestimmung über das genehmigte Partizipationskapital wurde mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P=introduced_date) eine genehmigte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        return [event('authorized_participation_capital_description_changed', m, 'capital_changed')], ''

    m = match(r"Nuova organizzazione: \[L'indicazione relativa all'organizzazione è cancellata a seguito dell'abrogazione dell'art\. (?P<article>95 cpv\. 1 lett\. h ORC)\.\]", 'it')
    if m:
        return [event('organization_mention_removed_article_95', m, mention_removed=True)], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici directeur adjoint, nommé directeur, signe désormais collectivement à deux, sans autre restriction\. (?P<name2>{NAME}), jusqu'ici sous-directrice, nommée directrice adjointe, et (?P<name3>{NAME}), jusqu'ici sous-directrice, nommée directrice adjointe, continuent à signer collectivement à deux, avec un administrateur ou un directeur")
    if m:
        return [person('director_promoted_restrictions_removed', m, m['name1'], 'directeur', 'Kollektivunterschrift zu zweien', previous_role='directeur adjoint', signing_restriction='sans autre restriction')] + [person('female_deputy_director_promoted_restricted', m, m[f'name{i}'], 'directrice adjointe', 'Kollektivunterschrift zu zweien', previous_role='sous-directrice', signing_restriction='avec un administrateur ou un directeur') for i in (2, 3)], ''

    m = match(rf"Radiation de la mention de l'existence d'une succursale à (?P<place1>{NAME}) \((?P<branch_registry_id>CH-\d{{3}}\.\d{{4}}\.\d{{3}}-\d)\), et (?P<place2>{NAME})")
    if m:
        return [event('two_branch_mentions_removed_one_registry_id', m, mention_removed=True)], ''

    m = match(rf'Die Zweigniederlassung von (?P<previous_place>{NAME}) \((?P<previous_registry_id>CH-\d{{3}}-\d{{7}}-\d)\) hat ihren Sitz nach (?P<place>{NAME}) \((?P<branch_uid>{UID})\) verlegt', 'de')
    if m:
        return [event('branch_seat_relocated_with_historical_registry_id', m, 'address_changed')], ''
    return [], text
