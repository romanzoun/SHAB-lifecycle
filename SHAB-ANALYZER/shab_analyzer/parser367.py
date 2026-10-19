from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;]+?'


def extract_parser367_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed residual clauses; earlier events retain precedence."""
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

    m = match(rf"Complément: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que le capital-actions est formé de (?P<count>\d+) actions nominatives de CHF (?P<nominal>{MONEY})")
    if m:
        return [event('registered_share_composition_supplemented', m, currency='CHF')], ''

    revoked = rf'Gemäss Entscheid des (?P<court>[^,;]+?) vom (?P<decision_date>{DATE}) wird die mit Verfügung vom (?P<grant_date>{DATE}) bewilligte COVID-19-Stundung per (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr widerrufen'
    m = match(revoked + rf'\. \[bisher: Mit Entscheid vom (?P<previous_decision_date>{DATE}) des (?P<previous_court>[^,;]+?) wurde eine COVID-19-Stundung für (?P<months>\d+) Monate bis am (?P<previous_until_date>{DATE}) bewilligt\.\]', 'de')
    if m and int(m['time'][:2]) < 24 and int(m['time'][3:]) < 60:
        return [event('covid_moratorium_revoked_with_previous_grant', m)], ''

    m = match(rf'Das (?P<appeal_court>[^,;]+?) hat der Beschwerde gegen die Verfügung des (?P<revocation_court>[^,;]+?) vom (?P<revocation_date>{DATE}) betreffend Widerruf sowie der Beschwerde gegen die Verfügung des (?P<extension_court>[^,;]+?) vom (?P<extension_date>{DATE}) betreffend Verlängerung der Covid-19-Stundung aufschiebende Wirkung zuerkannt\. Die Stundung wird vorläufig bis zur Rechtskraft des Beschwerdeentscheids verlängert\. \[bisher: ' + revoked + r'\.\]', 'de')
    if m and int(m['time'][:2]) < 24 and int(m['time'][3:]) < 60:
        return [event('covid_moratorium_appeals_suspensive_effect', m)], ''

    m = match(rf'(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>Saint-Cergue) (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), sont gérants et signent collectiement à deux, avec un gérant')
    if m:
        return [person('two_managers_joint_signing_with_manager_typo', m, m[f'name{i}'], m[f'place{i}'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', signing_restriction='avec un gérant') for i in (1, 2)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) est rectifiée dans ce sens: (?P<name>{PERSON}), gérant, signature collective à deux est originaire de (?P<origin>[^()]+?) \(et non pas de (?P<previous_origin>[^()]+)\)")
    if m:
        return [person('manager_origin_corrected', m, m['name'], role='Geschäftsführer', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Les trois parts de CHF (?P<previous_nominal>{MONEY}) sont divisées en (?P<count>\d+) parts de CHF (?P<nominal>{MONEY})\. Les associés (?P<name1>{PERSON}), (?P<name2>{PERSON}), et (?P<name3>{PERSON}) ont désormais chacun (?P<count_each>\d+) parts de CHF (?P=nominal)')
    if m:
        return [event('three_associates_share_split', m, previous_count='3', currency='CHF')], ''

    m = match(r'HR (?P<registry>[^,;.]+)', 'de')
    if m:
        source = re.search(rf'Zweigniederlassung neu: \[Sitz\] (?P<branch_place>[^();]+) \((?P<branch_uid>{UID})\) ' + re.escape(leftover.rstrip('.')) + r'\.?$', source_text)
        if source:
            return [event('branch_commercial_registry', m, **source.groupdict())], ''

    m = match(rf'(?P<name>{PERSON}), désormais président, détient (?P<retained_count>\d+) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred_count>\d+) parts de CHF (?P=nominal) à (?P<recipient>{PERSON}), du (?P<recipient_origin>{PERSON}), à (?P<recipient_place>{PERSON}), nouvel associé-gérant pour (?P<recipient_count>\d+) parts de CHF (?P=nominal)')
    if m:
        return [person('president_share_transfer_new_associate_manager', m, m['name'], role='Präsident der Geschäftsführung', currency='CHF')], ''

    m = match(r'Die Bestimmungen über die Nebenleistungspflichten wurden irrtümlich eingetragen', 'de')
    if m and leftover in source_text and '[nicht: Nebenleistungspflichten, Vorhand-, Vorkaufs- oder Kaufsrechte gemäss näherer Umschreibung in den Statuten.]' in source_text:
        return [event('ancillary_obligations_erroneous_entry_corrected', m)], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que les actions nominatives sont dès la constitution\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>\d+) actions de CHF (?P<nominal>{MONEY}), nominatives, liées selon statuts")
    if m and 'les actions nominatives sont liées selon statuts dès la constitution.' in source_text:
        return [event('registered_share_transfer_restriction_since_incorporation', m, currency='CHF', transfer_restriction='liées selon statuts')], ''

    m = match(rf"L'associée-gérante (?P<name>{PERSON}), désormais à (?P<place>{PERSON}), est nommé liquidatrice")
    if m:
        return [person('associate_manager_appointed_liquidator', m, m['name'], m['place'], 'Liquidatorin')], ''

    m = match(rf"La publication de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{PERSON}), membre et président du conseil d'administration, signe individuellement, et non pas collectivement à deux")
    if m:
        return [person('board_president_individual_signing_corrected', m, m['name'], role='Präsident des Verwaltungsrates', signing='Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    return [], leftover
