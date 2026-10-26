from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser56, parser95, parser119, parser125, parser149, parser206

_LEGACY = tuple(pattern for module in (parser56, parser95, parser119, parser125, parser149, parser206)
                for pattern in vars(module).values() if isinstance(pattern, re.Pattern))

NAME = r'[^,;.\[\]\n]+?'


def extract_parser398_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Narrow residual variants; source guards protect partially consumed clauses."""
    leftover = text.strip()
    if any(pattern.fullmatch(leftover) for pattern in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source_match = re.search(source_pattern + r'\.(?:\s|$)', source_text)
            if not source_match or any(source_match.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
            m = source_match
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, key='name', role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', m[key], role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': m[key]})

    tail = r'eingetragene Adresse des Aktionärs bzw\. Nutzniessers\. Sofern weder das Gesetz noch diese Statuten zwingend eine schriftliche Mitteilung vorschreiben, kann die Gesellschaft Mitteilungen auch an die letzte im Aktienbuch eingetragene E-Mail-Adresse des Aktionärs bzw\. Nutzniessers zustellen'
    m = match(tail, 'de', r'Schriftliche Mitteilungen der Gesellschaft erfolgen brieflich an die letzte im Aktienbuch ' + tail)
    if m:
        return [event('shareholder_communications_post_and_email_residual', m, methods=['brieflich', 'E-Mail'], recipients='Aktionäre bzw. Nutzniesser')], ''

    m = match(rf'Das Konkursverfahren ist mit Entscheid des (?P<court>zuständigen Einzelgerichts) vom (?P<decision_date>{DATE}) mangels Aktiven eingestellt worden', 'de')
    if m:
        return [event('bankruptcy_suspended_single_court_decision', m, 'status_changed')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) signe individuellement \(et non collectivement à deux comme publié\)")
    if m:
        return [person('individual_signing_corrected_notice_page', m, signing='Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"Le siège de la succursale de (?P<previous_place>{NAME}), dont le no d'identification des entreprises est \((?P<branch_uid>{UID})\), devient (?P<place>{NAME})")
    if m:
        return [event('branch_seat_municipality_changed', m, 'seat_changed')], ''

    transfer = rf'Les associés-gérants (?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent chacun (?P<transferred>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>{COUNT}) parts de CHF (?P=nominal), gérant'
    retained = rf'(?P=seller1) et (?P=seller2) sont désormais titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacun'
    m = match(transfer + ' ' + retained, source_pattern=transfer + r' avec signature collective à deux\. ' + retained)
    if m:
        return [event('two_managers_partial_transfer_new_joint_manager', m, 'ownership_changed', currency='CHF')], ''

    m = match('s', source_pattern=rf'Statuts modifiés le (?P<statutes_date>{DATE}) sur des points non soumis à publications')
    if m:
        return [event('statutes_non_public_plural_typo_residual', m, 'statutes_changed')], ''

    m = match(rf'Division des (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}) en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY})\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<capital_count>{COUNT}) actions de CHF (?P<capital_nominal_raw>\d+, \d+), nominatives')
    if m:
        return [event('share_split_published_comma_nominal', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Gelöschte Person: (?P<removed_name>{NAME}), vorsitzender Geschäftsführer, Einzelunterschrift\. Eingetragene Person geändert: (?P<previous_name>{NAME}), neu (?P<name>Dr\. {NAME})\. Neu eingetragene Person: (?P<appointed_name>Dr\. {NAME}), (?P<appointed_origin>deutscher Staatsangehöriger), in (?P<appointed_place>{NAME}) \((?P<appointed_country>[A-Z]{{2}})\), vorsitzender Geschäftsführer, Kollektivunterschrift zu zweien')
    if m:
        return [person('chair_manager_removed_title_corrected_appointed', m, 'removed_name', role='vorsitzender Geschäftsführer', signing='Einzelunterschrift', kind='officer_removed'), person('manager_doctor_title_added', m), person('chair_manager_joint_signing_appointed', m, 'appointed_name', role='vorsitzender Geschäftsführer', signing='Kollektivunterschrift zu zweien', place=m['appointed_place'])], ''

    conversion = rf'Les (?P<previous_count>{COUNT}) actions nominatives de CHF (?P<previous_nominal>{MONEY})'
    ending = rf' formant la totalité du capital-actions, sont transformées en (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), avec restrictions quant à la transmissibilité selon statuts'
    m = match(conversion + ending, source_pattern=conversion + ' avec restrictions quant à la transmissibilité selon statuts,' + ending)
    if m:
        return [event('registered_share_split_retained_transfer_restrictions', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'(?P<name>{NAME}), nommé sous-directeur de la succursale, lequel contine à signer collectivement à deux, signature limitée aux affaires de la succursale')
    if m:
        return [person('branch_deputy_director_contine_typo', m, role='sous-directeur de la succursale', signing='Kollektivunterschrift zu zweien', signing_scope='affaires de la succursale')], ''

    m = match(rf'Persona iscritta corretta: (?P<name>[^,;]+, [^,;]+), (?P<origin>cittadino italiano), in (?P<place>{NAME}), socio e gerente, con firma individuale, con (?P<count>{COUNT}) quote da CHF (?P<nominal>{MONEY})', 'it')
    if m:
        return [person('italian_associate_manager_name_corrected', m, role='socio e gerente', signing='Einzelunterschrift', place=m['place'])], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>Einzelgericht des Bezirksgerichts {NAME}) die provisorische Nachlassstundung bis am (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_until_am', m, 'status_changed')], ''
    return [], text
