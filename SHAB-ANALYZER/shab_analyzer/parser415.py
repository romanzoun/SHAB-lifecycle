from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY
from .parser409 import NAME
from .parser170 import _FR_ROLE_CORRECTED_TO_SUBDIRECTOR
from .parser100 import _FR_TWO_CONDITIONAL_CAPITAL_CLAUSES
from .parser116 import _FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE
from .parser144 import _DE_ADDITIONAL_CONDITIONAL_CAPITAL_INTRODUCED, extract_parser144_leftovers

_LEGACY = (_FR_ROLE_CORRECTED_TO_SUBDIRECTOR, _FR_TWO_CONDITIONAL_CAPITAL_CLAUSES,
           _FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE,
           _DE_ADDITIONAL_CONDITIONAL_CAPITAL_INTRODUCED)
WRITTEN_DATE = r'\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}'


def extract_parser415_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual clauses; existing rules keep their original inputs."""
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
                             extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est (?P<role>sous-directrice) \(et non pas directrice\)")
    if m:
        return [person('female_subdirector_role_corrected', m, m['name'], 'sous-directrice', corrected=True, previous_role='directrice')], ''

    m = match(rf'Nouveaux gérants: (?P<name1>{NAME}), de et à (?P<place1>{NAME}) et (?P<name2>{NAME}), du (?P<origin2>{NAME}), à (?P<place2>{NAME}) avec signature collective à deux')
    if m:
        return [person('two_managers_shared_collective_signing', m, m[f'name{i}'], 'gérant', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf"Augmentation conditionnelle du capital-participation fondée sur la décision relative à l'octroi de droits du (?P<rights_date>{WRITTEN_DATE}), modifiée en dernier lieu le (?P<amended_date>{WRITTEN_DATE})\. Nouveau capital-participation: CHF (?P<capital>{MONEY}), divisé en (?P<count>{COUNT}) bons nominatifs de CHF (?P<nominal>{MONEY})\. Le conseil d'administration a modifié une clause statutaire relative à une augmentation conditionnelle du capital-participation \(selon décision relative à l'octroi de droits de l'assemblée général du (?P=rights_date)\), par décision du (?P<decision_date>{WRITTEN_DATE}), pour le détail cf\. statuts")
    if m:
        number = lambda s: Decimal(s.replace("'", ''))
        if number(m['capital']) != number(m['count']) * number(m['nominal']):
            return [], text
        return [event('conditional_participation_capital_written_dates_amended', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'(?P<seller1>[^,;\[\]\n]+?) détient désormais (?P<remaining1>{COUNT}) parts de CHF (?P<nominal>{MONEY}), (?P<seller2>{NAME}) détient désormais (?P<remaining2>{COUNT}) parts de CHF (?P=nominal), et (?P<seller3>{NAME}) détient désormais (?P<remaining3>{COUNT}) parts de CHF (?P=nominal), par suite de cession de parts, respectivement de (?P<transferred1>{COUNT}), (?P<transferred2>{COUNT}) et (?P<transferred3>{COUNT}) parts de CHF (?P=nominal), à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal), sans signature sociale')
    if m:
        if sum(int(m[f'transferred{i}'].replace("'", '')) for i in (1, 2, 3)) != int(m['buyer_count'].replace("'", '')):
            return [], text
        return [event('three_associates_respective_share_transfers', m, 'ownership_changed', currency='CHF'), person('new_unsigned_associate_three_transfers', m, m['buyer'], 'Gesellschafterin', 'ohne Unterschrift', m['place'])], ''

    m = match(rf"Par arrêt du (?P<decision_date>{DATE}), le (?P<court>Tribunal cantonal) a rejeté le recours et a fixé l'ouverture de la faillite de la société au (?P<effective_date>{DATE}) à (?P<effective_time>(?:[01]\d|2[0-3])h[0-5]\d)\. Par conséquent sa raison sociale devient: (?P<company_name>{NAME} en liquidation)")
    if m:
        return [event('bankruptcy_appeal_rejected_opening_fixed', m, 'status_changed')], ''

    m = match(rf'Der korrekte Bishertext der Revisionsstelle wäre: \[bisher: (?P<name>{NAME}) \((?P<previous_registry_id>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d)\), in (?P<place>{NAME}), Revisionsstelle\]', 'de')
    if m:
        return [event('auditor_previous_text_supplemented', m, corrected=True)], ''

    m = match(rf'Emission de bons de jouissance: (?P<count>{COUNT}) bons de jouissance donnant droit aux mêmes dividendes et droits aux parts de liquidation de la société que les parts sociales')
    if m:
        return [event('profit_sharing_certificates_equal_distribution_rights', m, 'capital_changed', rights='mêmes dividendes et droits aux parts de liquidation de la société que les parts sociales')], ''

    m = match(rf"L'assemblée générale a introduit deux clauses statutaires relatives à une augmentation conditionnelle du capital par décision du (?P<decision_date>{DATE})\. Pour les détails, voir les statuts")
    if m:
        return [event('two_clauses_single_conditional_capital_increase', m, 'capital_changed', clause_count=2)], ''

    m = match(rf'(?P<name1>{NAME}), dont le prénom exact est (?P<given_names>{NAME}), (?P<name2>{NAME}), et (?P<name3>{NAME}), maintenant de (?P<origin3>{NAME}), sont nommés liquidateurs')
    if m:
        # The surname is the unchanged prefix preceding the previous given name.
        previous = m['given_names'].replace(' ', '-')
        if not m['name1'].endswith(' ' + previous):
            return [], text
        name1 = m['name1'][:-len(previous)] + m['given_names']
        return [person('three_liquidators_with_person_corrections', m, name1, 'liquidateur', corrected=True, previous_name=m['name1']), person('three_liquidators_with_person_corrections', m, m['name2'], 'liquidateur'), person('three_liquidators_with_person_corrections', m, m['name3'], 'liquidateur', origin=m['origin3'])], ''

    m = match(rf'\[bisher: Die Gesellschaft hat bei der Gründung vom (?P<founding_date>{DATE}) eine bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]', 'de')
    if m:
        # A residual history is not a new capital decision. Require its current
        # clause in the original source and emit only the historical annotation.
        s = re.search(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\. ' + re.escape(leftover), source_text)
        if not s:
            return [], text
        return [event('conditional_capital_previous_foundation_clause', m, 'capital_changed', historical_annotation=True, decision_date=s['decision_date'])], ''

    conditional = rf'\[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P<previous_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P<initial_date>{DATE}) geändert\.\]\. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) die Statutenbestimmung über die bedingte Kapitalerhöhung vom (?P=previous_date) geändert\.'
    authorized = rf' \[gestrichen: Die Generalversammlung hat mit Beschluss vom (?P=previous_date) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P=initial_date) gemäss näherer Umschreibung in den Statuten angepasst\.\]\. Die Generalversammlung hat mit Beschluss vom (?P=decision_date) den Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom (?P=previous_date) gemäss näherer Umschreibung in den Statuten angepasst\.'
    m = match(conditional + authorized + r' (?P<legacy_clause>.+)', 'de')
    if m and _DE_ADDITIONAL_CONDITIONAL_CAPITAL_INTRODUCED.fullmatch(m['legacy_clause']):
        legacy_events, rest = extract_parser144_leftovers(m['legacy_clause'], language, *context)
        if rest.strip(' .'):
            return [], text
        return [event('conditional_and_authorized_capital_clauses_amended_with_history', m, 'capital_changed')] + legacy_events, ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{NAME}), de (?P<origin>{NAME}) \(et non pas de (?P<previous_origin>{NAME})\)")
    if m:
        return [person('person_origin_corrected_notice_reference', m, m['name'], corrected=True)], ''
    return [], text
