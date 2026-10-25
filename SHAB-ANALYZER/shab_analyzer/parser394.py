from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE
from . import parser66, parser87, parser164, parser247

NAME = r'[^,;.\[\]\n]+?'
# Reuse predecessor patterns: their supported clauses retain ownership.
_LEGACY = tuple(p for module in (parser66, parser87, parser164, parser247)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser394_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete bounded residual variants without changing predecessor events."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            source = re.search(source_pattern + r'\.(?:\s|$)', source_text)
            if not source or source.groupdict() != m.groupdict():
                return None
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
                             extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf'(?P<name>{NAME}) nommé administrateur, signe désormais individuellement')
    if m:
        return [person('administrator_appointed_individual_without_comma', m, m['name'], 'administrateur', 'Einzelunterschrift')], ''

    m = match(rf"En complément à l'inscription no\. (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\), dépôt d'un nouvel exemplaire des statuts")
    if m:
        return [event('statutes_copy_filed_complement_notice', m)], ''

    m = match(rf'Signature collective à deux a été conférée à (?P<name>{NAME})')
    if m:
        return [person('collective_signatory_without_residence', m, m['name'], signing='Kollektivunterschrift zu zweien')], ''

    pattern = rf"Les administrateurs (?P<name1>{NAME}), (?P<name2>{NAME}), et (?P<name3>{NAME}), sont nommés liquidateurs Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant l'entier du capital-actions, ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)"
    m = match(pattern, source_pattern=pattern.replace('liquidateurs Les', r'liquidateurs avec signature collective à deux\. Les'))
    if m:
        return [person('three_administrators_collective_liquidators', m, m[f'name{i}'], 'administrateur, liquidateur', 'Kollektivunterschrift zu zweien') for i in (1, 2, 3)] + [event('three_liquidators_share_restrictions_removed', m, 'capital_changed', currency='CHF', transfer_restricted=False)], ''

    # The XML labels this German publication as French.
    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der Präsident des (?P<court>{NAME}), in (?P<place>{NAME}), mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, über die Gesellschaft den Konkurs eröffnet\. Neue Firma: (?P<company>{NAME}) in Liquidation')
    if m:
        try:
            datetime.strptime(m['time'], '%H.%M')
        except ValueError:
            return [], text
        return [event('bankruptcy_opened_president_then_company_name', m, 'status_changed')], ''

    m = match(rf'Organisation neu: \[Organisation: Stiftungsrat von (?P<minimum>\d+) bis (?P<maximum>\d+) Mitgliedern und (?P<auditor>Kontrollstelle)\.\]', 'de')
    if m and 0 < int(m['minimum']) <= int(m['maximum']):
        return [event('foundation_organization_inner_period', m)], ''

    pattern = rf"L'associé-gérant et président (?P<seller1>{NAME}) cède (?P<count1>{COUNT}) de ses (?P<previous1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), nouvel associé-gérant Les associés-gérants (?P<seller2>{NAME}) et (?P<seller3>{NAME}) cèdent chacun (?P<count2>{COUNT}) de leurs (?P<previous2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé-gérant avec signature collective à deux, titulaire de (?P<received2>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1), (?P=seller2) et (?P=seller3), restent chacun titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)"
    m = match(pattern, source_pattern=pattern.replace('associé-gérant Les', r'associé-gérant avec signature collective à deux\. Les'))
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if n('previous1') - n('count1') != n('remaining') or n('previous2') - n('count2') != n('remaining') or 2 * n('count2') != n('received2'):
            return [], text
        return [event('president_and_two_managers_share_transfers', m, currency='CHF')] + [person('new_collective_manager_after_combined_transfers', m, m[f'buyer{i}'], 'associé-gérant', 'Kollektivunterschrift zu zweien', m[f'place{i}'], origin=m[f'origin{i}']) for i in (1, 2)], ''

    m = match(rf"La société est réinscrite à titre provisoire au registre du commerce conformément aux mesures provisionnelles ordonnées par le (?P<authority>président du Tribunal de l'arrondissement de la Broye et Nord vaudois) du (?P<decision_day>\d{{1,2}}) décembre (?P<decision_year>\d{{4}})")
    if m:
        try:
            datetime(int(m['decision_year']), 12, int(m['decision_day']))
        except ValueError:
            return [], text
        return [event('provisional_reinstatement_interim_measures', m, 'status_changed', provisional=True)], ''

    m = match(rf"\[biffé: Radiation par suite de cessation d'activité\]\. A la suite d'une erreur dans la réquisition, l'entreprise est réinscrite comme ci-devant \(FOSC No (?P<notice>{COUNT}) du (?P<notice_date>{DATE}), publ\. (?P<notice_ref>\d+)\)")
    if m:
        return [event('reinstatement_erroneous_requisition', m, 'status_changed', correction=True)], ''

    m = match(rf'(?P<vice>{NAME}) est nommée vice-présidente\. Nouveaux membres du conseil de fondation sans signature: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de et à (?P<place2>{NAME}), (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME})')
    if m:
        return [person('foundation_vice_president_appointed_unsigned_members', m, m['vice'], 'vice-présidente')] + [person('foundation_member_appointed_without_signing', m, m[f'name{i}'], 'membre du conseil de fondation', 'ohne Zeichnungsberechtigung', m[f'place{i}'], origin=m['place2'] if i == 2 else m[f'origin{i}']) for i in (1, 2, 3, 4)], ''

    m = match(rf"L'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que suite aux cessions opérées, l'associé (?P<name1>{NAME}) détient (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non: (?P<previous1>{COUNT}) parts de CHF (?P=nominal)\) et que l'associé (?P<name2>{NAME}) détient (?P<count2>{COUNT}) parts de CHF (?P=nominal) \(et non: (?P<previous2>{COUNT}) parts de CHF (?P=nominal)\)")
    if m:
        return [event('two_associate_holdings_corrected_after_transfers', m, currency='CHF', correction=True)], ''

    pattern = rf"L'associée (?P<name>{NAME}) est nommée gérante"
    # Parser 286 owns the identical residue when the source grants individual signing.
    m = match(pattern, source_pattern=pattern + r' avec signature collective à deux')
    if m and not re.search(pattern + r' avec signature individuelle\.', source_text):
        return [person('female_associate_manager_collective_signing', m, m['name'], 'associée-gérante', 'Kollektivunterschrift zu zweien')], ''
    return [], text
