from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser349_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Accept complete supported residue without replacing earlier events."""
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
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(r'(?P<name1>[^,;]+?) et (?P<name2>[^,;]+?) ne sont plus administrateurs; leur signature est radiée')
    if m:
        return [person('board_members_departed_signatures_revoked', m, m[f'name{i}'], signing='gelöscht', previous_role='Verwaltungsrat') for i in (1, 2)], ''

    m = match(rf'La succursale à (?P<previous_place>{NAME}) \((?P<uid>{UID})\) a transféré son siège à (?P<place>{NAME}) \((?P=uid)\)')
    if m:
        return [event('branch_seat_transferred', m)], ''

    m = match(rf'Kapital neu: CHF (?P<capital>{MONEY})\. Schaffung bzw\. Erhöhung des Dotationskapitals gemäss Beschluss der Kantonsrates Kanton St\.Gallen vom (?P<decision_date>{DATE}) um CHF (?P<amount>{MONEY}) betreffend die Übertragung der Spitalimmobilien', 'de')
    if m and Decimal(m['capital'].replace("'", '')) > 0 and Decimal(m['amount'].replace("'", '')) > 0:
        return [event('endowment_capital_created_or_increased', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'eingetragenen Einzelunternehmens (?P<business_name>{NAME}), in (?P<place>{NAME}), gemäss Vertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}), wofür (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}) zugeteilt und CHF (?P<credit>{MONEY}) als Forderung gutgeschrieben werden', 'de')
    if m:
        # Earlier rules remove the heading. Require its original context before
        # interpreting this fragment as a contribution in kind / acquisition.
        heading = 'Sacheinlage/Sachübernahme: Die Gesellschaft übernimmt bei der Gründung das Geschäft des im Handelsregister '
        if heading + m[0].rstrip('.') in source_text:
            number = lambda key: Decimal(m[key].replace("'", ''))
            if number('count') > 0 and number('nominal') > 0 and number('assets') - number('liabilities') == number('count') * number('nominal') + number('credit'):
                return [event('incorporation_contribution_acquisition_details', m, currency='CHF')], ''

    m = match(rf"(?P<transferor>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé pour (?P=count) parts de CHF (?P=nominal); lequel associé est nommé gérant L'associé-gérant (?P=transferor), nommé président, est maintenant titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal) et continue de signer individuellement")
    if m:
        return [event('shares_transferred_new_associate_manager', m), person('associate_appointed_manager', m, m['recipient'], 'Geschäftsführer', place=m['place']), person('associate_manager_president_continued_signing', m, m['transferor'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift')], ''

    m = match(rf'Les associés (?P<name1>{NAME}), désormais à (?P<place>{NAME}), et (?P<name2>{NAME}) signent désormais collectivement à deux')
    if m:
        return [person('associates_collective_signing', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', place=m['place'] if i == 1 else None) for i in (1, 2)], ''

    m = match(rf'Les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}) sont co-présidents et continuent à signer individuellement')
    if m:
        return [person('board_co_presidents_continued_signing', m, m[f'name{i}'], 'Co-Präsident', 'Einzelunterschrift') for i in (1, 2)], ''

    m = match(r'Liquidation ist entgegen früherem Eintrag noch nicht beendet', 'de')
    if m:
        return [event('liquidation_not_completed_correction', m)], ''

    m = match(rf"(?P<name1>{NAME}), jusqu'ici gérant, nommé directeur général, et (?P<name2>{NAME}), jusqu'ici directeur, nommé directeur général adjoint, continuent à signer collectivement à deux")
    if m:
        return [person('general_director_and_deputy_appointed', m, m[f'name{i}'], 'Generaldirektor' if i == 1 else 'Stellvertretender Generaldirektor', 'Kollektivunterschrift zu zweien', previous_role='gérant' if i == 1 else 'directeur') for i in (1, 2)], ''

    m = match(rf'\[gestrichen: (?P<previous_place1>{NAME})\]\. (?P<place1>{NAME}) \((?P<uid1>{UID})\)\. \[gestrichen: (?P<previous_place2>{NAME})\]\. (?P<place2>{NAME}) \((?P<uid2>{UID})\)\. (?P<place3>{NAME}) \((?P<uid3>{UID})\)', 'de')
    if m:
        return [event('branch_entries_updated', m)], ''

    m = match(rf'Con decreto del Pretore del Distretto di (?P<court_place>{NAME}) del (?P<decision_date>{DATE}), alla società è stata concessa una moratoria COVID-19 di (?P<months>\d+) mesi a far tempo dal (?P<start_date>{DATE})', 'it')
    if m and int(m['months']) > 0:
        return [event('covid_moratorium_granted', m)], ''

    m = match(rf'(?P<name>{NAME}), dont la signature est radiée, engage désormais la société par sa procuration individuelle')
    if m:
        return [person('signature_revoked_individual_procuration_granted', m, m['name'], signing='Einzelprokura', previous_signature_revoked=True)], ''

    return [], leftover
