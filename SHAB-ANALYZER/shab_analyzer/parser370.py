from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, COUNT, UID

PERSON = r'[^,;]+?'
NOTICE_DATE = r'\d{2}[-.]\d{2}[-.]\d{4}'


def extract_parser370_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete sample-backed residual clauses after earlier parsers."""
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
                        datetime.strptime(value.replace('-', '.'), '%d.%m.%Y')
            except (ValueError, TypeError):
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})


    m = match(rf"(?P<seller>{PERSON}), associée-gérante présidente, cède (?P<transferred>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), associée-gérante, désormais titulaire de (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('presiding_associate_share_transfer', m, currency='CHF')], ''

    m = match(rf'Diese infolge Konkurses im Sinne von Art\. (?P<article>159 Abs\. 5 lit\. a HRegV) am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird auf Grund der Verfügung des (?P<court>[^;]+?) vom (?P<decision_date>{DATE}) wieder als durch Konkurs aufgelöst in das Handelsregister eingetragen\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. (?P=article) von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('bankruptcy_dissolved_company_reinstated', m)], ''

    m = match(rf"Liquidateurs: l'associé gérant (?P<name1>{PERSON}) et la directrice (?P<name2>{PERSON}), lesquels continuent à signer individuellement")
    if m:
        return [person('two_liquidators_continued_individual_signing', m, m[f'name{i}'], role='Liquidator', signing='Einzelunterschrift', previous_role='Gesellschafter und Geschäftsführer' if i == 1 else 'Direktor') for i in (1, 2)], ''

    m = match(rf'Mit Entscheid vom (?P<grant_date>{DATE}) hat der (?P<court>[^;]+?) im summarischen Verfahren eine COVID-19-Stundung von drei Monaten gewährt\. Mit Entscheid vom (?P<extension_date>{DATE}) hat der (?P=court) im summarischen Verfahren eine Verlängerung der COVID-19-Stundung um drei Monate bewilligt', 'de')
    if m:
        return [event('covid_moratorium_granted_and_extended', m, initial_duration_months='3', extension_duration_months='3')], ''

    m = match(rf"L'associé-gérant et président (?P<seller>{PERSON}) détient désormais (?P<remaining_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), maintenant domicilié à (?P<place>{PERSON}), désormais associé-gérant pour (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal) et qui continue de signer individuellement")
    if m:
        return [event('share_transfer_to_relocated_associate_manager', m, currency='CHF'), person('recipient_associate_manager_continued_signing', m, m['recipient'], m['place'], 'Gesellschafter und Geschäftsführer', 'Einzelunterschrift')], ''

    m = match(rf"Transformation des (?P<previous_count1>{COUNT}) actions de CHF (?P<previous_nominal1>{MONEY}), et des (?P<previous_count2>{COUNT}) actions de CHF (?P<previous_nominal2>{MONEY}) privilégiées quant au droit de vote et dividende, en (?P<count1>{COUNT}) actions de CHF (?P<nominal1>{MONEY}), (?P<count2>{COUNT}) actions de CHF (?P<nominal2>{MONEY}) privilégiées quant au droit de vote, et (?P<count3>{COUNT}) actions de CHF (?P<nominal3>{MONEY}), privilégiées quant au dividende, toutes nominatives\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count1) actions de CHF (?P=nominal1), (?P=count2) actions de CHF (?P=nominal2) privilégiées quant au droit de vote, et (?P=count3) actions de CHF (?P=nominal3), privilégiées quant au dividende, toutes nominatives")
    if m:
        return [event('registered_share_classes_transformed', m, currency='CHF', fully_paid=True, security_kind='Namenaktien', previous_rights2='vote et dividende', rights2='vote', rights3='dividende')], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{PERSON}), (?P<name2>{PERSON}), (?P<name3>{PERSON}), (?P<name4>{PERSON}) et (?P<name5>{PERSON}) sont élus liquidateurs')
    if m:
        return [person('foundation_members_appointed_liquidators', m, m[f'name{i}'], role='Liquidator', previous_role='Mitglied des Stiftungsrates') for i in range(1, 6)], ''

    m = match(rf'Die Gesellschaft wird gemäss Entscheid des (?P<court>[^;]+?) vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen\. Das mit Entscheid vom (?P<previous_decision_date>{DATE}) eimgestellte Verfahren wird wieder eröffnet\. Datum der Konkurseröffnung: (?P<opening_date>{DATE}), (?P<opening_time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr', 'de')
    if m:
        return [event('bankruptcy_proceedings_reopened_reinstatement', m)], ''

    m = match(r'Zweigniederlassung neu: \[Zweigniederlassung wird infolge Aufhebung gelöscht\] \[gestrichen: (?P<previous_place>[^\[\];]+)\]', 'de')
    if m:
        return [event('branch_deleted_following_closure', m)], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), le (?P<court>[^;]+?) a annulé la faillite du titulaire de l'entreprise prononcée le (?P<bankruptcy_date>{DATE}); l'inscription est rétablie comme ci-devant \(FOSC No (?P<notice_number>\d+) du (?P<notice_date>{DATE}), publ\. No (?P<notice_id>\d+)\)")
    if m:
        return [event('proprietor_bankruptcy_annulled_registration_restored', m)], ''

    m = match(rf'(?P<departing1>{PERSON}) et, (?P<departing2>{PERSON}) ne sont plus administrateurs; leurs pouvoirs sont radiés\. Administration: (?P<name1>{PERSON}), de et à (?P<place1>{PERSON}), président, et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), lesquels signent collectivement à deux')
    if m:
        return ([person('two_administrators_powers_removed_typo', m, m[f'departing{i}'], role='Mitglied des Verwaltungsrates', signing='ohne Zeichnungsberechtigung') for i in (1, 2)] + [person('two_administrators_joint_signing', m, m[f'name{i}'], m[f'place{i}'], 'Präsident des Verwaltungsrates' if i == 1 else 'Mitglied des Verwaltungsrates', 'Kollektivunterschrift zu zweien') for i in (1, 2)]), ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{NOTICE_DATE}) \(FOSC du (?P<notice_date>{NOTICE_DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{PERSON}), admininistratrice, est également présidente")
    if m:
        return [person('administrator_president_corrected_typo', m, m['name'], role='Präsident des Verwaltungsrates')], ''

    return [], leftover
