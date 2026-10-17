from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT


def extract_parser340_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed complete clauses without replacing earlier events."""
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

    m = match(rf'Grenzüberschreitende Fusion nach den Vorschriften des IPRG: Übernahme der Aktiven und Passiven der (?P<absorbed_name>{NAME}), in (?P<absorbed_place>[^()]+?) \(LI\) \((?P<absorbed_foreign_id>FL-\d{{4}}\.\d{{3}}\.\d{{3}}-\d)\), eine Aktiengesellschaft nach dem Recht des Fürstentums Liechtenstein, gemäss Fusionsvertrag vom (?P<contract_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die übernehmende Gesellschaft sämtliche Aktien der übernommenen Gesellschaft hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('cross_border_merger_wholly_owned', m, 'ownership_changed', currency='CHF', absorbed_country='LI')], ''

    m = match(rf"(?P<name1>{NAME}) et (?P<name2>(?:Dr\. )?{NAME}) ne sont plus membres du comité\. (?P<name3>(?:Dr\. )?{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), DEU, et (?P<name4>{NAME}), des (?P<origin4>{NAME}), à (?P<place4>{NAME}), NLD, sont nommés membres du comité sans pouvoir de signature")
    if m:
        return [person('committee_members_departed', m, m[f'name{i}'], 'Vorstandsmitglied', membership_ended=True) for i in (1, 2)] + [person('committee_members_appointed_unsigned', m, m[f'name{i}'], 'Vorstandsmitglied', 'ohne Zeichnungsberechtigung', m[f'place{i}']) for i in (3, 4)], ''

    m = match(r'(?P<name1>[^,;]+?), (?P<name2>[^,;]+?) et (?P<name3>[^,;]+?) ne sont plus membres du conseil de fondation; leurs pouvoirs sont radiés')
    if m:
        return [person('foundation_members_departed_powers_cancelled', m, m[f'name{i}'], 'Stiftungsrat', membership_ended=True, powers_cancelled=True) for i in (1, 2, 3)], ''

    m = match(rf'Parts sociales: CHF (?P<nominal>{MONEY})')
    if m:
        return [event('cooperative_share_nominal', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), directeurs, signent désormais individuellement')
    if m:
        return [person('directors_individual_signing', m, m[f'name{i}'], 'Direktor', 'Einzelunterschrift') for i in (1, 2, 3)], ''

    m = match(rf'Signature collective à deux limitée à la succursale est conférée à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        return [person('branch_limited_collective_signing', m, m['name'], signing='Kollektivunterschrift zu zweien beschränkt auf die Zweigniederlassung', place=m['place'], signing_scope='succursale')], ''

    m = match(rf"Nouveaux membres du conseil de fondation avec le/la président\(e\) ou le/la vice-président\(e\): (?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), et (?P<name4>{NAME}), d'(?P<origin4>{NAME}), à (?P<place4>{NAME})")
    if m:
        original = leftover.replace('avec le/la président', 'avec signature collective à deux avec le/la président')
        if original not in source_text:
            return [], leftover
        return [person('foundation_members_restricted_collective_signing', m, m[f'name{i}'], 'Stiftungsrat', 'Kollektivunterschrift zu zweien mit dem Präsidenten oder dem Vizepräsidenten', m[f'place{i}'], signing_with='président(e) ou vice-président(e)') for i in (1, 2, 3, 4)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que les traductions de la nouvelle raison sociale sont: \[(?P<translation1>[^\[\]]+)\] \[(?P<translation2>[^\[\]]+)\] \(et non pas \[(?P<previous_translation1>[^\[\]]+)\] \[(?P<previous_translation2>[^\[\]]+)\]\)")
    if m:
        return [event('company_name_translations_corrected', m)], ''

    reference = rf"Rectificatif: l'inscription (?:n°|no )(?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que "
    m = match(reference + r"les statuts n'ont pas été modifiés, contrairement à ce qui a été publié")
    if m:
        return [event('statutes_amendment_notice_corrected', m)], ''

    m = match(rf"(?P<previous_officer>{NAME}) est nommé vice-président\. Nouvel administrateur toutefois pas avec (?P<excluded_signatory>{NAME}): (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>[^.;]+?)")
    if m:
        original = leftover.replace('Nouvel administrateur toutefois', 'Nouvel administrateur avec signature collective à deux, toutefois')
        if original not in source_text:
            return [], leftover
        return [person('administrator_appointed_vice_president', m, m['previous_officer'], 'Vizepräsident'), person('administrator_restricted_collective_signing', m, m['name'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien, nicht mit ' + m['excluded_signatory'], m['place'])], ''

    m = match(reference + rf"le capital-actions de CHF (?P<capital>{MONEY}) \(et non de CHF (?P<previous_capital>{MONEY}) comme publié\) a été libéré ultérieurement à concurrence d'un montant de CHF (?P<subsequent_payment>{MONEY})")
    if m:
        return [event('subsequent_capital_payment_corrected', m, 'capital_changed', currency='CHF')], ''

    m = match(reference + rf"l'associé-gérant se nomme (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}), comme publié\)")
    if m:
        return [person('associate_manager_name_corrected', m, m['name'], 'Gesellschafter und Geschäftsführer')], ''

    return [], leftover
