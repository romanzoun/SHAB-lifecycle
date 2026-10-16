from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser332_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residue without replacing prior events."""
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
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(r'Gegen die Löschung gemäss Art\. 159 Abs\. 5 lit\. a HRegV wurde begründeter Einspruch erhoben', 'de')
    if m:
        return [event('official_deletion_objected', m, 'status_changed', legal_basis='Art. 159 Abs. 5 lit. a HRegV')], ''

    m = match(rf"Augmentation ordinaire du capital-actions porté de CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}) par l'émission de (?P<issued>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives, \. Capital-actions: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P=nominal), nominatives, liées selon statuts")
    if m:
        number = lambda k: Decimal(m[k].replace("'", ''))
        if number('capital') - number('previous_capital') != number('issued') * number('nominal') or number('capital') != number('count') * number('nominal'):
            return [], leftover
        # Transfer restrictions in the first sentence were consumed by older rules.
        return [event('ordinary_registered_capital_increase', m, 'capital_changed', currency='CHF', fully_paid=True)], ''

    m = match(r"La clause statutaire relative à l'apport en nature est abrogée conformément à l'art\. 628 al\. 4 CO")
    if m:
        return [event('contribution_in_kind_clause_repealed', m, legal_basis='art. 628 al. 4 CO')], ''

    m = match(rf"Unter TR-Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) wurde zudem der Bisher-Text unvollständig widergegeben: \[bisher: (?P<surname>{NAME}), (?P<given_names>{NAME}), von (?P<origin>{NAME}), in (?P<place>{NAME}), Gesellschafter und Geschäftsführer, mit Kollektivunterschrift zu zweien, mit (?P<count>{COUNT}) Stammanteilen zu je CHF (?P<nominal>{MONEY})\]", 'de')
    if m:
        # Historical text is a correction record, not a current appointment.
        return [event('previous_manager_text_corrected', m, corrected=True, historical=True, previous_role='Gesellschafter und Geschäftsführer', previous_signing='Kollektivunterschrift zu zweien', currency='CHF')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>{NAME}) wurde eine COVID-19-Stundung für drei Monate bis am (?P<end_date>{DATE}) bewilligt', 'de')
    if m:
        return [event('covid19_stay_granted', m, 'status_changed', duration_months=3)], ''

    pattern = rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), sont membres du conseil d'administration, avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME})"
    m = match(pattern)
    if m:
        # Signing text is removed upstream; require the original explicit evidence.
        source_clause = leftover.removesuffix('.').replace(", sont membres du conseil d'administration, avec ", ", sont membres du conseil d'administration, avec signature collective à deux avec ", 1)
        source = re.search(r'(?<!\S)' + re.escape(source_clause) + r'\.?$', source_text)
        if source:
            return [person('board_members_restricted_signing', m, m[f'name{i}'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}'], signing_restriction='only_with', authorized_partners=[m['partner1'], m['partner2']]) for i in (1, 2)], ''
        return [], leftover

    m = match(r'Zweigniederlassung neu: \[gestrichen: (?P<place>[^()\[\]]+) \(HR (?P<registry>[^()\[\]]+)\)\]', 'de')
    if m:
        return [event('branch_register_entry_removed', m)], ''

    m = match(rf"L'Autorité de surveillance LPP et des fondations de Suisse occidentale a prononcé la dissolution de la fondation par décision du (?P<decision_day>\d{{1,2}}) juillet (?P<decision_year>\d{{4}})\. Les signatures de (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), qui restent membres du conseil de fondation, sont radiées\. (?P<liquidator>{NAME}) \((?P<liquidator_uid>{UID})\) est nommée liquidatrice")
    if m:
        try:
            datetime(int(m['decision_year']), 7, int(m['decision_day']))
        except ValueError:
            return [], leftover
        return [event('foundation_dissolution_authority', m, 'status_changed'), *[person('foundation_member_signing_removed', m, m[f'name{i}'], 'Stiftungsrat', 'ohne Zeichnungsberechtigung') for i in (1, 2, 3)], person('foundation_liquidator_appointed', m, m['liquidator'], 'Liquidator')], ''

    m = match(rf'(?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME})\. Par conséquent, (?P=seller) et (?P=buyer) sont désormais titulaires de respectivement (?P<seller_remaining>{COUNT}) et (?P<buyer_remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_existing_holders', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_first_day>\d{{2}})\./(?P<agreement_date>{DATE}) und Verfügung der Aufsichtsbehörde vom (?P<decision_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine', 'de')
    if m:
        try:
            datetime.strptime(m['agreement_first_day'] + m['agreement_date'][2:], '%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('foundation_asset_transfer_no_consideration', m, 'ownership_changed', currency='CHF', no_consideration=True)], ''

    m = match(rf"La membre du conseil (?P<name1>{NAME}), nommée vice-présidente, signe désormais collectivement à deux\. (?P<name2>{NAME}), jusqu'ici vice-président, n'exerce plus la signature")
    if m:
        return [person('board_vice_presidency_changed', m, m['name1'], 'Vorstand, Vizepräsident', 'Kollektivunterschrift zu zweien'), person('former_vice_president_signing_removed', m, m['name2'], signing='ohne Zeichnungsberechtigung', previous_role='Vizepräsident')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens qu'une procuration a été conférée à (?P<name>{NAME}) \(et non pas (?P<previous_name>{NAME})\)")
    if m:
        return [person('procuration_name_corrected', m, m['name'], 'Prokurist', corrected=True)], ''

    return [], leftover
