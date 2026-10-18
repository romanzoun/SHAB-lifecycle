from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, NAME

# Dots are allowed in personal names (initials, civil-status abbreviations).
PERSON = r'[^,;]+?'


def extract_parser355_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events only after all previous parsers have run."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('_date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, kind='organization_changed'):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role=None, signing=None, place=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), 'name': name})

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>[^.;]+?) eine COVID-19-Stundung bis zum (?P<end_date>{DATE}) gemäss der COVID-19-Verordnung Insolvenzrecht bewilligt', 'de')
    if m:
        return [event('covid_moratorium_granted', m)], ''
    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der (?P<court>[^.;]+?) die COVID-19-Stundung um (?P<duration_months>\d+) Monate bis am (?P<end_date>{DATE}) verlängert', 'de')
    if m:
        return [event('covid_moratorium_extended', m)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>[^.;]+?) die am (?P<opening_date>{DATE}) eröffnete und mit Entscheid vom (?P<suspension_date>{DATE}) mangels Aktiven eingestellte konkursamtliche Liquidation wieder aufgenommen\. \[bisher: Das Liquidationsverfahren nach den Vorschriften über den Konkurs ist mit Entscheid des (?P<previous_court>[^.;]+?) vom (?P=suspension_date) mangels Aktiven eingestellt worden\.\]', 'de')
    if m:
        if m['previous_court'] != m['court'].replace('Kantonsgericht ', 'Kantonsgerichts '):
            return [], leftover
        return [event('bankruptcy_liquidation_resumed', m)], ''

    m = match(r"Par prononcé rendu le (?P<decision_day>\d{1,2}) septembre (?P<decision_year>\d{4}), le (?P<court>[^.;]+?) a accordé à la société une prolongation du sursis concordataire définitif jusqu'au (?P<end_day>1er|\d{1,2}) mars (?P<end_year>\d{4})")
    if m:
        try:
            datetime(int(m['decision_year']), 9, int(m['decision_day']))
            datetime(int(m['end_year']), 3, int(m['end_day'].replace('er', '')))
        except ValueError:
            return [], leftover
        return [event('definitive_moratorium_extension_ordered', m)], ''

    m = match(rf"Par suite de changement d'état civil (?P<previous_name>{PERSON}) porte désomais le nom de (?P<name>{NAME})")
    if m:
        return [person('civil_status_name_changed', m, m['name'])], ''

    m = match(rf"L'assemblée générale a introduit une clause statutaire relative à une création autorisée d'un capital-participations par décision du (?P<decision_date>{DATE}); pour les détails, voir les statuts")
    if m:
        return [event('authorized_participation_capital_clause', m, 'capital_changed')], ''

    m = match(rf"Selon décision de l'(?P<authority>[^.;]+?) du (?P<decision_date>{DATE}), la fondation est dissoute\. \. Liquidateurs: les membres (?P<name1>{PERSON}), président et (?P<name2>{PERSON}); lesquels continuent à signer collectivement à deux")
    if m:
        return [event('foundation_dissolution_ordered', m)] + [person('foundation_liquidators_continued_signing', m, m[f'name{i}'], 'Liquidator', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    reference = rf"[Ll]'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), "
    m = match(reference + rf"Id (?P<notice_ref>\d+)\) est complétée dans ce sens: (?P<name>{PERSON}), procuration collective à deux, avec une personne ayant la signature collective à deux, membre de la direction ou du conseil d'administration")
    if m:
        result = person('collective_procuration_supplement', m, m['name'], signing='Kollektivprokura zu zweien')
        result.payload['signing_condition'] = "avec une personne ayant la signature collective à deux, membre de la direction ou du conseil d'administration"
        return [result], ''

    m = match('Rectificatif: ' + reference + r'p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que la raison de commerce de l\'entreprise individuelle, dont les actifs et passifs sont apportés, est "(?P<correct_name>[^";]+)" \(et non "(?P<incorrect_name>[^";]+) comme publié\)')
    if m:
        return [event('contributed_business_name_corrected', m)], ''

    m = match('Rectificatif: ' + reference + rf'Id (?P<notice_ref>\d+)\) est rectifiée dans ce sens: (?P<name>{PERSON}), administrateur, signature individuelle, est domicilié à (?P<place>{PERSON}) \(et non pas à (?P<previous_place>{PERSON})\)')
    if m:
        return [person('director_residence_corrected', m, m['name'], 'Mitglied des Verwaltungsrats', 'Einzelunterschrift', m['place'])], ''

    m = match(rf"(?P<transferor>{PERSON}), originaire de (?P<origin>{PERSON}), a cédé (?P<transferred>\d+) de ses (?P<previous>\d+) parts sociales de CHF (?P<nominal>{MONEY}), dont (?P<count1>\d+) parts à (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), et (?P<count2>\d+) parts à (?P<name2>{PERSON}), d'(?P<origin2>{PERSON}), à (?P<place2>{PERSON}), nouveaux associés\. (?P=transferor), gérant, nommé président, signe désormais collectivement à deux\. (?P=name1) et (?P=name2) sont gérants")
    if m:
        suffix = re.escape(m['name1'] + ' et ' + m['name2']) + r' sont gérants avec signature collective à deux'
        if int(m['transferred']) != int(m['count1']) + int(m['count2']) or int(m['transferred']) > int(m['previous']) or not re.search(suffix + r'\.?$', source_text):
            return [], leftover
        return [event('shares_distributed_to_two_associates', m), person('manager_president_collective_signing', m, m['transferor'], 'Vorsitzender der Geschäftsführung', 'Kollektivunterschrift zu zweien')] + [person('transferee_manager_collective_signing', m, m[f'name{i}'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf"Capital-actions réduit de CHF (?P<previous>{MONEY}) à CHF (?P<reduced>{MONEY}) pour supprimer un excédant de passif constaté au bilan par destruction de (?P<cancelled>{MONEY}) actions de CHF (?P<nominal>{MONEY}) nominatives et \. Augmentation ordinaire simultanée du capital-actions\. Nouveau capital-actions: CHF (?P<new>{MONEY}), entièrement libéré, divisé en (?P<shares>{MONEY}) actions de CHF (?P=nominal) nominatives et liées selon statuts")
    if m:
        from decimal import Decimal
        n = lambda key: Decimal(m[key].replace("'", ''))
        if n('previous') - n('cancelled') * n('nominal') != n('reduced') or n('shares') * n('nominal') != n('new'):
            return [], leftover
        return [event('capital_reduced_and_simultaneously_increased', m, 'capital_changed')], ''

    return [], leftover
