from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;.]+?'


def extract_parser364_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses, preserving all earlier parser results."""
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
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    members = ', '.join(rf'(?P<name{i}>{PERSON}), de (?P<origin{i}>{PERSON}), à (?P<place{i}>{PERSON})' for i in range(1, 5))
    m = match(members + rf", et (?P<name5>{PERSON}), de (?P<origin5>{PERSON}), à (?P<place5>{PERSON}), sont membres du conseil de direction, ils n'exercent pas la signature")
    if m:
        return [person('five_direction_council_members_unsigned', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Direktionsrates', 'ohne Zeichnungsberechtigung') for i in range(1, 6)], ''

    m = match(rf"L'associé-gérant (?P<transferor>{PERSON}) a cédé (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), de et à (?P<place>{PERSON}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal), L'associé (?P=transferor) est maintenant titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m:
        return [event('manager_share_transfer_new_associate_remaining', m, currency='CHF')], ''

    m = match(rf'Separazione: la società ha trasferito una parte degli attivi e dei passivi secondo il progetto di scissione del (?P<plan_date>{DATE}) alla (?P<recipient>.+?), in (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Il capitale azionario è stato ridotto di CHF (?P<reduction>{MONEY}) in seguito alla scissione', 'it')
    if m:
        return [event('demerger_with_capital_reduction', m, currency='CHF')], ''

    board = '; '.join(rf'(?P<surname{i}>{PERSON}), (?P<given_name{i}>{PERSON}), von (?P<origin{i}>{PERSON}), in (?P<place{i}>{PERSON}), {role} des Verwaltungsrates, mit Einzelunterschrift \[bisher: in (?P<previous_place{i}>{PERSON}), {role} des Verwaltungsrates, Liquidator, mit Einzelunterschrift\]' for i, role in ((1, 'Präsident'), (2, 'Mitglied')))
    m = match(rf'Mit dem SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Text (?P<entry>\d+/\d{{4}}) wurden nicht die vollständigen bisher Angaben publiziert\. Korrekt wäre ' + board, 'de')
    if m:
        return [person('board_previous_details_corrected', m, m[f'surname{i}'] + ', ' + m[f'given_name{i}'], m[f'place{i}'], role + ' des Verwaltungsrates', 'Einzelunterschrift', previous_role=role + ' des Verwaltungsrates, Liquidator') for i, role in ((1, 'Präsident'), (2, 'Mitglied'))], ''

    m = match(rf'Le directeur (?P<name>{PERSON}), maintenant à (?P<place>{PERSON}), est élu administrateur et continue à signer collectivement à deux')
    if m:
        return [person('director_elected_board_member_joint_signing', m, m['name'], m['place'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die mit Beschluss vom (?P<introduction_date>{DATE}) eingeführte und mit den Beschlüssen vom (?P<amendment1_date>{DATE}), (?P<amendment2_date>{DATE}) und (?P<amendment3_date>{DATE}) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in Art\. (?P<article>\d+[a-z]?) der Statuten geändert\. \[bisher: Die Gesellschaft hat mit Beschluss vom (?P<previous_decision_date>{DATE}) die mit Beschluss vom (?P<previous_introduction_date>{DATE}) eingeführte und mit Beschlüssen vom (?P<previous_amendment1_date>\d{{1,2}}\.\d{{1,2}}\.\d{{4}}) und (?P<previous_amendment2_date>{DATE}) geänderte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\]', 'de')
    if m:
        return [event('authorized_capital_amendment_history', m)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le capital-actions de CHF (?P<capital>{MONEY}), libéré à concurrence de CHF (?P<paid_up>{MONEY}), est divisé en (?P<count>[\d']+) actions nominatives de CHF (?P<nominal>{MONEY}), \(et non divisé en (?P=count) actions nominatives de CHF (?P<previous_nominal>{MONEY}) comme publié\)")
    if m:
        return [event('registered_share_nominal_corrected_notice', m, currency='CHF')], ''

    # Preserve the malformed notice reference verbatim; never infer its year.
    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date_raw>\d{{2}}\.\d{{2}}\.\d{{3}}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{PERSON}), associé, (?P<count>\d+) parts de CHF (?P<nominal>{MONEY}), gérant, signature collective à deux, avec le gérant président \(et non pas associé, (?P=count) parts de CHF (?P<previous_nominal>{MONEY})\)")
    if m:
        return [person('associate_manager_nominal_corrected_malformed_notice', m, m['name'], role='Gesellschafter und Geschäftsführer', signing='Kollektivunterschrift zu zweien', signing_condition='avec le gérant président', currency='CHF')], ''

    m = match(rf"(?P<name1>{PERSON}) est nommée vice-présidente Nouveau membre du conseil de fondation sans signature: (?P<name2>{PERSON}), d'(?P<origin2>{PERSON}), au (?P<place2>{PERSON})")
    if m:
        return [person('foundation_vice_president_appointed', m, m['name1'], role='Vizepräsidentin'), person('foundation_member_appointed_unsigned', m, m['name2'], m['place2'], 'Mitglied des Stiftungsrates', 'ohne Zeichnungsberechtigung')], ''

    m = match(rf'Nouveau domicile de liquidation: (?P<street>[^,;]+), c/o (?P<care_of>{PERSON}), (?P<postal_code>\d{{4}}) (?P<place>{PERSON})')
    if m:
        return [event('liquidation_domicile_with_care_of', m)], ''

    m = match(rf'Bei den Qualifizierten Tatbestände neu: wurde ein falsches Datum aufgeführt\. Korrekt sollte die Eintragung lauten: \[Die Bestimmung über die Sacheinlage/-übernahme bei der Gründung vom (?P<foundation_date>{DATE}) ist aus den Statuten gestrichen worden\.\]', 'de')
    if m:
        return [event('contribution_acquisition_clause_deletion_date_corrected', m)], ''

    m = match(rf"Con decisione della (?P<court>Pretura del Distretto di [^,;.]+) del (?P<decision_date>{DATE}), il compito attribuito al commissario è stato esteso a gestire l'amministrazione corrente e straordinaria della società", 'it')
    if m:
        return [event('commissioner_powers_extended', m, scope='amministrazione corrente e straordinaria')], ''

    return [], leftover
