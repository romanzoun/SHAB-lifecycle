from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser345_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events, leaving unsupported clauses intact."""
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}, **extra})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>[^()]+) \((?P<buyer_uid>{UID})\), à (?P<buyer_place>{NAME}), nouvelle associée pour (?P=count) parts de CHF (?P=nominal); par conséquent (?P=seller) est maintenant associée pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('shares_transferred_remaining_holding', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est nommé gérant et président \(et non pas gérante et présidente\)")
    if m:
        return [person('manager_president_gender_corrected', m, m['name'], 'Geschäftsführer', additional_role='Präsident')], ''

    m = match(r'\[bisher: (?P<previous_place>[^\[\]]+)\]', 'de')
    if m:
        source = re.search(rf'Zweigniederlassung neu: \[Sitz neu:\] (?P<place>{NAME}) \((?P<branch_uid>{UID})\) \[bisher: (?P<previous_place>[^\[\]]+)\]\.?$', source_text)
        if source and source['previous_place'] == m['previous_place']:
            return [event('branch_seat_previous_place', source)], ''

    m = match(r"Par décision du président du Tribunal de l'arrondissement de (?P<court_place>[^,.;]+) du (?P<day>\d{1,2}) juillet (?P<year>\d{4}), la société a été déclarée dissoute conformément à l'article 154 ORC; sa liquidation a été ordonnée selon les dispositions applicables à la faillite")
    if m:
        try:
            date = datetime(int(m['year']), 7, int(m['day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('judicial_dissolution_bankruptcy_liquidation', m, decision_date=date, legal_basis='article 154 ORC')], ''

    # This publication is labelled French but contains a complete German clause.
    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<new_name>{NAME})\. Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<shares>{COUNT} Stammanteil zu CHF {MONEY}, {COUNT} Stammanteil zu CHF {MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P=shares), Geschäftsführer, Liquidator, Einzelunterschrift\. Liquidationsadresse: (?P<address>[^.;]+)')
    if m:
        return [event('shareholder_resolution_dissolution', m), event('liquidation_name_changed', m), person('manager_liquidator_appointed', m, m['name'], 'Geschäftsführer', 'Einzelunterschrift', additional_role='Liquidator'), event('liquidation_address_set', m)], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par (?P<count1>{COUNT}) parts à (?P<name1>{NAME}), à (?P<place1>{NAME}), et par (?P<count2>{COUNT}) parts à (?P<name2>{NAME}), à (?P<place2>{NAME}), tous deux de (?P<origin>{NAME}), nouveaux associés sans signature, avec respectivement (?P=count1) et (?P=count2) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m and number(m['count1']) + number(m['count2']) == number(m['count']) and number(m['count']) + number(m['remaining']) == number(m['previous_count']):
        return [event('shares_transferred_two_associates', m, 'ownership_changed', currency='CHF')] + [person('associate_appointed_after_transfer', m, m[f'name{i}'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (1, 2)], ''

    pattern = rf'Administration: (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})'
    m = match(pattern)
    if m and re.search(re.escape(leftover) + r', avec signature collective à deux\.?$', source_text):
        return [person('board_president_appointed_continued_signing', m, m['name1'], 'Präsident', 'Einzelunterschrift'), person('board_member_appointed_collective_signing', m, m['name2'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m['place'])], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la raison de commerce de l'associée unique est (?P<name>[^()]+) \(et non (?P<previous_name>[^()]+)\)")
    if m:
        return [event('sole_associate_name_corrected', m, 'ownership_changed')], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das Gerichtspräsidium (?P<court_place>{NAME}) im summarischen Verfahren eine definitive Nachlassstundung von (?P<months>\d+) Monaten gewährt', 'de')
    if m:
        return [event('definitive_composition_moratorium_granted', m)], ''

    m = match(rf"L'ordonnance sur mesures superprovisionnelles du Tribunal de première instance du (?P<original_date>{DATE}), concernant l'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}), a été confirmée par ordonnance sur mesures provisionnelles du (?P<confirmation_date>{DATE})")
    if m:
        return [event('interim_order_confirmed', m)], ''

    m = match(rf"Réunion des (?P<old_count1>{COUNT}) parts de CHF (?P<old_nominal1>{MONEY}) de l'associé-gérant (?P<name1>{NAME}) en (?P<count1>{COUNT}) parts de CHF (?P<nominal1>{MONEY}) et des (?P<old_count2>{COUNT}) parts de CHF (?P<old_nominal2>{MONEY}) de l'associé (?P<name2>{NAME}) en (?P<count2>{COUNT}) parts de CHF (?P<nominal2>{MONEY})")
    if m and all(number(m[f'old_count{i}']) * number(m[f'old_nominal{i}']) == number(m[f'count{i}']) * number(m[f'nominal{i}']) for i in (1, 2)):
        return [event('shares_consolidated_by_holder', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Nouvel administrateur toutefois pas avec (?P<excluded_partners>[^:]+): (?P<name>{NAME}), de et à (?P<place>{NAME})')
    if m and f"Nouvel administrateur avec signature collective à deux, toutefois pas avec {m['excluded_partners']}: {m['name']}, de et à {m['place']}" in source_text:
        return [person('board_member_appointed_excluded_partners', m, m['name'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m['place'], signing_restriction='not_with')], ''

    return [], leftover
