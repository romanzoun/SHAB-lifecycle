from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY

PERSON = r"[^,;.]+?"
MONTH_DATE = r"\d{1,2} (?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) \d{4}"
MONTHS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()


def extract_parser361_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append bounded residual events, preserving all earlier parser results."""
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
                        if re.fullmatch(DATE, value):
                            datetime.strptime(value, '%d.%m.%Y')
                        else:
                            day, month, year = value.split()
                            datetime(int(year), MONTHS.index(month) + 1, int(day))
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, place):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict()})

    m = match(rf"Par décision rendue le (?P<decision_date>{MONTH_DATE}), le président du Tribunal d'arrondissement de (?P<court_place>{PERSON}) a prolongé le sursis concordataire définitif accordé à la société jusqu'au (?P<end_date>{MONTH_DATE})")
    if m:
        return [event('definitive_moratorium_extended_written_dates', m)], ''

    m = match(rf"Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) werden (?P<count>[\d']+) Namenaktien zu CHF (?P<nominal>{MONEY}) vernichtet und zurückbezahlt; die Beachtung der gesetzlichen Vorschriften von Art\. (?P<article>734 OR) wird mit öffentlicher Urkunde vom (?P<deed_date>{DATE}) festgestellt", 'de')
    if m:
        return [event('share_cancellation_repayment_deed', m, currency='CHF')], ''

    m = match(rf"(?P<transferor>[^;]+?) cède (?P<transferred>\d+) de ses (?P<previous_count>\d+) parts de CHF (?P<nominal>{MONEY}) par (?P<allocation>\d+, \d+, \d+, \d+ et \d+) parts aux gérants (?P<manager1>{PERSON}) et (?P<manager2>{PERSON}), nouveaux associés avec respectivement (?P<count1>\d+) et (?P<count2>\d+) parts de CHF (?P=nominal), à (?P<name1>{PERSON}), (?P<name2>{PERSON}) et (?P<name3>{PERSON}), les trois d'(?P<origin>{PERSON}), à (?P<place>[^,;]+?), nouveaux associés sans signature, avec (?P<each>\d+) parts de CHF (?P=nominal) chacun; (?P=transferor) reste titulaire de (?P<remaining>\d+) part de CHF (?P=nominal)")
    if m:
        allocation = [int(value) for value in re.findall(r'\d+', m['allocation'])]
        transferred = int(m['transferred'])
        if (sum(allocation) != transferred
                or transferred + int(m['remaining']) != int(m['previous_count'])
                or allocation != [int(m['count1']), int(m['count2'])] + [int(m['each'])] * 3):
            return [], leftover
        return [event('share_transfer_five_recipients', m, currency='CHF')], ''

    m = match(r'Aumento ordinario del capitale azionario', 'it')
    if m:
        return [event('ordinary_share_capital_increase_stated', m)], ''

    m = match(rf'Administration: (?P<name1>{PERSON}), maintenant domicilié à (?P<place1>{PERSON}), nommé président, et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), vice-président, lesquels signent individuellement')
    if m:
        return [person('board_president_vice_president_individual_signing', m, m[f'name{i}'], role, 'Einzelunterschrift', m[f'place{i}']) for i, role in ((1, 'Präsident des Verwaltungsrates'), (2, 'Vizepräsident des Verwaltungsrates'))], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) den Geschäftsbereich "(?P<business>[^"\n]+)" mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>[^,]+), in (?P<place>[^()]+?) \((?P<recipient_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('business_asset_transfer_inventory', m, currency='CHF')], ''

    m = match(rf"Procuration collective à deux est conférée à (?P<name1>{PERSON}), à (?P<place1>[^,]+), et (?P<name2>{PERSON}), à (?P<place2>[^,]+), toutes deux des (?P<origin>{PERSON})")
    if m:
        return [person('two_procurists_usage_names', m, m[f'name{i}'], None, 'Kollektivprokura zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf"Capital-actions nouveau: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count1>\d+) actions de CHF (?P<nominal1>{MONEY}), nominatives de type (?P<class1>A), et (?P<count2>\d+) actions de CHF (?P<nominal2>{MONEY}), nominatives de type (?P<class2>B), à droit de vote privilégié, liées selon statuts \(jusqu'ici: (?P<previous_count>\d+) actions de CHF (?P<previous_nominal>{MONEY}), nominatives\)")
    if m:
        return [event('registered_share_classes_voting_privilege', m, currency='CHF')], ''

    m = match(rf"L'assemblée générale a introduit une clause statutaire relative à une augmentation autorisée du capital-actions par décision du (?P<authorization_date>{MONTH_DATE})\. Pour les détails, voir les statuts\. L'assemblée générale a modifié une clause statutaire relative à une augmentation conditionnelle du capital-actions \(selon décision du (?P<previous_decision_date>{MONTH_DATE})\) et introduit une clause statutaire relative à la création conditionnelle d'un capital-participation par décision du (?P<participation_date>{MONTH_DATE})\. Pour les détails, voir les statuts")
    if m:
        return [event('authorized_conditional_participation_capital_clauses', m)], ''

    m = match(rf"Le président du Tribunal de l'arrondissement de (?P<court_place>{PERSON}) a prononcé le (?P<decision_date>{MONTH_DATE}) l'effet suspensif de la procédure de la faillite rendue le (?P<bankruptcy_date>{MONTH_DATE})")
    if m:
        return [event('bankruptcy_procedure_suspensive_effect', m)], ''

    m = match(r"Inscription de la mention selon laquelle la fondation est une fondation de famille qui n'est pas soumise à une surveillance étatique et n'a pas l'obligation de désigner un organe de révision")
    if m:
        return [event('family_foundation_supervision_auditor_exemption', m)], ''

    m = match(rf"Nouveau membre du comité exécutif sans signature: (?P<name>{PERSON}), d'(?P<origin>{PERSON}), à (?P<place>[^,;.]+)")
    if m:
        return [person('executive_committee_member_without_signing', m, m['name'], 'Mitglied des Exekutivkomitees', 'ohne Zeichnungsberechtigung', m['place'])], ''

    return [], leftover
