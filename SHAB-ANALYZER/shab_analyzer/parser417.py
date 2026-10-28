from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser90 import (_DE_STATUTES_DATE_ENTERED_INCORRECTLY,
                       _DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT, extract_parser90_leftovers)
from .parser104 import _FR_SIGNING_GRANTED_DEPUTY_DIRECTOR

_LEGACY = (_DE_STATUTES_DATE_ENTERED_INCORRECTLY, _FR_SIGNING_GRANTED_DEPUTY_DIRECTOR,
           _DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT)


def extract_parser417_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete sample-backed residual clauses, without claiming legacy variants."""
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

    def number(m, key):
        return int(m[key].replace("'", ''))

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée sans signature\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        if number(m, 'before') != number(m, 'count') + number(m, 'remaining'):
            return [], text
        return [event('manager_partial_transfer_new_unsigned_female_associate', m, 'ownership_changed', currency='CHF'),
                person('new_unsigned_female_associate_partial_transfer', m, m['buyer'], 'associée', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Mit Entscheid des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) wurde über die Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}) das Konkursverfahren wieder eröffnet', 'de')
    if m:
        return [event('bankruptcy_reopened_by_single_judge', m, 'status_changed')], ''

    m = match(rf'Sitz neu: (?P<place>{NAME})\. \[(?P<reason>Angaben des Sitzes infolge Namensänderung der Gemeinde)\]', 'de')
    if m:
        return [event('registered_office_municipality_renamed', m)], ''

    m = match(rf'''L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que la nouvelle raison sociale de l'organe de révision "(?P<previous_name>[^"\n]+)" \((?P<auditor_uid>{UID})\) est "(?P<name>[^"\n]+)"''')
    if m:
        return [event('auditor_company_name_correction', m, corrected=True)], ''

    m = match(r'\[bisher: Identifikationsnummer Hauptsitz: (?P<previous_head_office_id>CH-\d{3}\.\d\.\d{3}-\d{3}-\d)\]', 'de')
    if m:
        return [event('previous_head_office_identifier_annotation', m, historical_annotation=True)], ''

    m = match(r'\[(?P<reason>Anpassung des Sitzes infolge Namensänderung der Gemeinde)\]', 'de')
    if m:
        return [event('registered_office_municipality_name_annotation', m)], ''

    m = match(rf'Als Statutendatum wurde (?P<entered_date>{DATE}) anstelle von (?P<correct_date>{DATE}) eingetragen', 'de')
    if m:
        return [event('statutes_date_entry_corrected_without_irrtuemlich', m, corrected=True)], ''

    m = match(rf"(?P<seller>{NAME}), associé, a cédé (?P<count1>{COUNT}) de ses (?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<count2>{COUNT}) autres à (?P<buyer2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouveaux associés ; ils n'exercent pas la signature sociale\. (?P=seller) est désormais titulaire de (?P<remaining>{COUNT}) parts sociales de CHF (?P=nominal)")
    if m:
        if number(m, 'before') != sum(number(m, key) for key in ('count1', 'count2', 'remaining')):
            return [], text
        return [event('partial_transfer_two_new_unsigned_associates', m, 'ownership_changed', currency='CHF'),
                *[person('new_unsigned_associate_split_transfer', m, m[f'buyer{i}'], 'associé', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (1, 2)]], ''

    m = match(rf'Nouveaux membres du conseil de fondation toutefois pas avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}), (?P<excluded3>{NAME}) et (?P<excluded4>{NAME}), ni entre eux: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), du (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        # The residual has lost the signing phrase to earlier parsing; require it in the source.
        source_clause = leftover.replace('Nouveaux membres du conseil de fondation toutefois',
                                         'Nouveaux membres du conseil de fondation avec signature collective à deux, toutefois', 1)
        if source_clause not in source_text:
            return [], text
        return [person('two_foundation_members_four_exclusions', m, m[f'name{i}'], 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien', m[f'place{i}'], excluded_partners=[m[f'excluded{j}'] for j in range(1, 5)], excluded_between_appointees=True) for i in (1, 2)], ''

    m = match(rf'Abspaltung: Ein Teil der Aktiven und Passiven geht gemäss Spaltungsvertrag vom (?P<agreement_date>{DATE}) auf die (?P<counterparty>{NAME}), in (?P<place>{NAME}) \((?P<counterparty_uid>{UID})\), über\. Abspaltung: Die Gesellschaft übernimmt von der (?P=counterparty), in (?P=place) \((?P=counterparty_uid)\), einen Teil des Vermögens\. Die Gesellschaft übernimmt dabei gemäss Spaltungsvertrag vom (?P=agreement_date) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY})\. Da dieselbe Gesellschafterin sämtliche Stammanteile der an der Abspaltung beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt', 'de')
    if m:
        clause = leftover.split('. Abspaltung: ', 1)[0] + '.'
        if not _DE_OUTGOING_SPIN_OFF_SINGLE_RECIPIENT.fullmatch(clause):
            return [], text
        old, rest = extract_parser90_leftovers(clause, language, *context)
        if rest.strip(' .'):
            return [], text
        return [*old, event('demerger_incoming_assets_common_shareholder', m, 'assets_transferred', direction='incoming', currency='CHF', capital_increase=False, shares_allocated=False)], ''

    m = match(rf'Signature collective à deux à été conférée à (?P<name>{NAME}), nommé sous-directeur; sa procuration est radiée')
    if m:
        return [person('deputy_director_collective_signing_typo_proxy_revoked', m, m['name'], 'sous-directeur', 'Kollektivunterschrift zu zweien', procuration_revoked=True)], ''

    m = match(rf'Procuration collective à deux est conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), à (?P<place2>{NAME}), les deux de (?P<origin>{NAME})')
    if m:
        return [person('two_proxies_shared_origin_distinct_residences', m, m[f'name{i}'], signing='Kollektivprokura zu zweien', place=m[f'place{i}']) for i in (1, 2)], ''
    return [], text
