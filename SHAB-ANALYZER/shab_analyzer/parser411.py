from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser376 import MONTHS
from .parser234 import _FR_PRESIDENCY_CHANGED_NEW_FIRST
from .parser150 import _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED
from .parser159 import _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY
from .text_extras import _DE_MUNICIPALITY_SEAT_CHANGE

_LEGACY = (_FR_PRESIDENCY_CHANGED_NEW_FIRST,
           _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED,
           _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_WITH_HISTORY,
           _DE_MUNICIPALITY_SEAT_CHANGE)
WRITTEN_DATE = r'(?:1er|\d{1,2}) (?:' + '|'.join(MONTHS) + r') \d{4}'


def extract_parser411_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete bounded residual clauses; retain unsupported input unchanged."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_suffix=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_suffix and not re.search(re.escape(leftover.rstrip('.')) + source_suffix + r'\.?$', source_text):
            return None
        try:
            for value in re.findall(DATE, m[0]):
                datetime.strptime(value, '%d.%m.%Y')
            for value in re.findall(WRITTEN_DATE, m[0]):
                day, month, year = value.split()
                datetime(int(year), MONTHS.index(month) + 1, int(day.replace('er', '')))
        except ValueError:
            return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"Les administrateurs (?P<name1>{NAME}), nommé président et (?P<name2>{NAME}), jusqu'ici président, lesquels continuent à signer collectivement à deux")
    if m:
        return [person('presidency_changed_continued_joint_signing', m, m[f'name{i}'], 'Präsident des Verwaltungsrates' if i == 1 else 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Signature collective à deux, pas entre eux ni avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}) et (?P<excluded3>{NAME}), est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('two_signers_three_excluded_partners', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', place=m[f'place{i}'], signing_restriction='pas entre eux ni avec ' + ', '.join([m['excluded1'], m['excluded2']]) + ' et ' + m['excluded3'], excluded_signing_partners=[m[f'name{3-i}']] + [m[f'excluded{j}'] for j in (1, 2, 3)]) for i in (1, 2)], ''

    m = match(rf'\[Die Bestimmung über die Sacheinlage/Sachübernahme bei der Gründung vom (?P<foundation_date>{DATE}) ist aus den Statuten gestrichen worden\.\]', 'de')
    if m:
        return [event('contribution_acquisition_foundation_clause_removed', m)], ''

    m = match(rf"L'assemblée générale a modifié une clause statutaire relative à une augmentation conditionnelle du capital \(selon décision du (?P<clause_date>{WRITTEN_DATE})\) par décision du (?P<decision_date>{WRITTEN_DATE})\. Pour les détails, voir les statuts")
    if m:
        return [event('conditional_capital_clause_changed_written_dates', m, 'capital_changed')], ''

    m = match(rf"L'administrateur (?P<previous_president>{NAME}), jusqu'ici président, lequel continue à signer collectivement à deux\. (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}) et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), sont membres du conseil d'administration", source_suffix=r', avec signature collective à deux')
    if m:
        return [person('former_president_remains_member_joint_signing', m, m['previous_president'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien')] + [person('three_board_members_new_president', m, m[f'name{i}'], 'Präsident des Verwaltungsrates' if i == 1 else 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2, 3)], ''

    m = match(rf'Sitz neu: (?P<to>{NAME})\. \[(?P<reason>Anpassung des Sitzes und der Personenangaben infolge Namensänderung der Gemeinde)\]', 'de')
    if m:
        return [event('municipality_seat_and_person_details_change', m, 'seat_changed', reason='municipality_name_change', raw_reason=m['reason'], official_change=False, person_details_adapted=True)], ''

    m = match(rf"(?P<seller>[^\n()]+) \((?P<seller_uid>{UID})\) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associée (?P<buyer>[^\n()]+) \((?P<buyer_uid>{UID})\), désormais titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        n = lambda k: int(m[k].replace("'", ''))
        if n('before') != n('count') + n('remaining') or n('buyer_count') < n('count'):
            return [], text
        return [event('corporate_associate_partial_transfer', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Kapital neu: CHF (?P<capital>{MONEY}) \[bisher: CHF (?P<previous_capital>{MONEY})\]', 'de')
    if m:
        return [event('capital_amount_changed_without_share_details', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) a cédé (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), nouvel associé pour (?P=count1) parts de CHF (?P=nominal), et (?P<count2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), de et à (?P<place2>{NAME}), pour (?P=count2) parts de CHF (?P=nominal)\. Gérants: les associés (?P=seller), président, (?P=buyer1), vice-président, et (?P=buyer2), tous les trois", source_suffix=r' avec signature individuelle')
    if m:
        return [event('two_share_transfers_three_managers', m, 'ownership_changed', currency='CHF')] + [person('three_associate_managers_individual_signing', m, m[key], role, 'Einzelunterschrift', m[place] if place else None) for key, role, place in [('seller', 'Gesellschafter und Vorsitzender der Geschäftsführung', None), ('buyer1', 'Gesellschafter und stellvertretender Vorsitzender der Geschäftsführung', 'place1'), ('buyer2', 'Gesellschafter und Geschäftsführer', 'place2')]], ''

    m = match(rf"(?P<removed1>[^,;]+), (?P<removed2>[^;]+?) et (?P<removed3>[^;]+?) ne sont plus administrateurs; leurs pouvoirs sont radiés\. Les administrateurs (?P<name1>{NAME}), jusqu'ici vice-présidente, nommée présidente et (?P<name2>{NAME}), nommé vice-président, continuent à signer collectivement à deux")
    if m:
        return [person('three_administrators_removed_powers_revoked', m, m[f'removed{i}'], kind='officer_removed', powers_revoked=True) for i in (1, 2, 3)] + [person('president_vice_president_joint_signing', m, m[f'name{i}'], 'Präsidentin des Verwaltungsrates' if i == 1 else 'Vizepräsident des Verwaltungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<liquidation_name>[^\n]+? in Liquidation)\. Eingetragene Person geändert: (?P<previous_name>{NAME}), korrekterweise (?P<name>{NAME}), Gesellschafter, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Gesellschafter, (?P=count) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Liquidator, Einzelunterschrift', 'de')
    if m:
        return [event('dissolved_meeting_corrected_liquidator_name', m, 'status_changed', dissolved=True), person('associate_manager_liquidator_name_corrected', m, m['name'], 'Gesellschafter, Geschäftsführer, Liquidator', 'Einzelunterschrift', corrected=True)], ''

    # The source publication is French-tagged but contains German register prose.
    m = match(rf'Gelöschte Person: (?P<removed>[^\n()]+) \((?P<removed_uid>{UID})\), Gesellschafterin, (?P<removed_count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY})\. Eingetragene Personen geändert: (?P<name1>{NAME}), Gesellschafter, (?P<count1>{COUNT}) Stammanteile zu CHF (?P=nominal), vorsitzender Geschäftsführer, Einzelunterschrift, nun in (?P<place1>{NAME}); (?P<name2>{NAME}), Gesellschafter, (?P<previous_count2>{COUNT}) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Kollektivunterschrift zu zweien, neu Gesellschafter (?P<count2>{COUNT}) Stammanteile zu CHF (?P=nominal), Geschäftsführer, Kollektivunterschrift zu zweien\. Neu eingetragene Person: (?P<name3>{NAME}), von (?P<origin3>{NAME}), in (?P<place3>{NAME}), Gesellschafter, (?P<count3>{COUNT}) Stammanteile zu CHF (?P=nominal), ohne Unterschrift')
    if m:
        n = lambda k: int(m[k].replace("'", ''))
        if n('removed_count') + n('previous_count2') != n('count2') + n('count3'):
            return [], text
        return [event('corporate_associate_removed_holdings_redistributed', m, 'ownership_changed', currency='CHF'), person('associate_presiding_manager_residence_changed', m, m['name1'], 'Gesellschafter und Vorsitzender der Geschäftsführung', 'Einzelunterschrift', m['place1']), person('associate_manager_holding_changed', m, m['name2'], 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien'), person('new_unsigned_associate', m, m['name3'], 'Gesellschafter', 'ohne Unterschrift', m['place3'])], ''
    return [], text
