from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;]+?'


def extract_parser366_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize sample-backed complete residual clauses after earlier rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_suffix=None):
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
            if source_suffix and not re.search(re.escape(leftover.rstrip('.')) + source_suffix + r'\.?$', source_text):
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})


    m = match(r'und das Konkursbegehren abgewiesen', 'de')
    if m and re.search(r'In Gutheissung der Beschwerde hat .+ mit Entscheid vom \d{2}\.\d{2}\.\d{4} .+ aufgehoben und das Konkursbegehren abgewiesen\.?$', source_text):
        return [event('bankruptcy_petition_dismissed_on_appeal', m)], ''

    m = match(rf'Berichtigung des im SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE}) publizierten TR-Eintrags Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}): , wurde irrtümlich gelöscht\. Deshalb erfolgt nachträglich folgender Wiedereintrag', 'de')
    if m:
        source = re.search(rf': (?P<declaration>Gemäss Erklärung vom (?P<declaration_date>{DATE}) wurde auf die eingeschränkte Revision verzichtet), wurde irrtümlich gelöscht\. Deshalb erfolgt nachträglich folgender Wiedereintrag\. (?P=declaration)\.?$', source_text)
        if source:
            try:
                datetime.strptime(source['declaration_date'], '%d.%m.%Y')
            except ValueError:
                return [], leftover
            return [event('audit_waiver_erroneous_deletion_corrected', m, declaration_date=source['declaration_date'])], ''

    m = match(rf'Transfert de patrimoine: selon contrat du (?P<agreement_day>\d{{1,2}}) octobre (?P<agreement_year>\d{{4}}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) à (?P<recipient>{PERSON}), à (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: CHF (?P<consideration>{MONEY})')
    if m:
        try:
            datetime(int(m['agreement_year']), 10, int(m['agreement_day']))
        except ValueError:
            return [], leftover
        return [event('asset_transfer_proprietor_cash_consideration', m, currency='CHF')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>Bezirksgericht [^,;.]+) eine provisorische Nachlassstundung um (?P<extension_months_word>zwei) auf insgesamt (?P<total_months_word>vier) Monate bis zum (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_total_duration', m)], ''

    m = match(rf'Succursale: (?P<place>[^();]+) \((?P<branch_uid>{UID})\) \[précédemment: (?P<previous_place>[^\[\];]+)\]')
    if m:
        return [event('branch_uid_and_previous_place', m)], ''

    m = match(rf"Les administrateurs (?P<name1>{PERSON}), jusqu'ici vice-président, nommé président et (?P<name2>{PERSON}), jusqu'ici président, maintenant vice-président, continuent à signer collectivement à deux")
    if m:
        return [person('board_president_vice_president_exchanged', m, m[f'name{i}'], role='Präsident des Verwaltungsrates' if i == 1 else 'Vizepräsident des Verwaltungsrates', signing='Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf'Signature individuelle a été conférée à (?P<name>[^;]+); ses pouvoirs sont modifiés en ce sens')
    if m:
        return [person('individual_signing_powers_amended', m, m['name'], signing='Einzelunterschrift')], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'associé-gérant (?P<name>{PERSON}) détient (?P<count>\d+) parts de CHF (?P<nominal>{MONEY}) \(et non (?P<previous_count>\d+) parts de CHF (?P=nominal)\)")
    if m:
        return [person('associate_manager_share_count_corrected', m, m['name'], role='Gesellschafter und Geschäftsführer', currency='CHF')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que la raison de commerce du siège principal est: (?P<name>[^()]+?) \(et non (?P<previous_name>[^()]+?), comme publié\)")
    if m:
        return [event('head_office_company_name_corrected', m)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{PERSON}), in (?P<place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF(?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_cash_consideration_no_space', m, currency='CHF')], ''

    m = match(rf'\[gestrichen: (?P<place>[^();]+ \([A-Z]{{2}}\)) \((?P<branch_uid>{UID})\)\]', 'de')
    if m and 'Zweigniederlassung neu: [Folgende Zweigniederlassungen sind aufgehoben worden:]' in source_text and leftover in source_text:
        return [event('branch_with_canton_removed', m)], ''

    m = match(rf"(?P<name1>{PERSON}), de et à (?P<place1>{PERSON}), et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<country2>FRA), sont membres du conseil d'administration avec signatue collective à deux")
    if m:
        return [person('two_board_members_joint_signing_typo', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    return [], leftover
