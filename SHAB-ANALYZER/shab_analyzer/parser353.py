from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser353_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed residual facts, retaining prior events and unknown text."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            source = re.search(source_pattern + r'\.?$', source_text)
            if not source or source.groupdict() != m.groupdict():
                return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('_date'):
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict()})

    def person(action, m, name, role, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf"En complément de l'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\), dépôt d'un nouvel exemplaire des statuts")
    if m:
        return [event('statutes_copy_filed_supplement', m)], ''

    pattern = rf'Nouveax membres du conseil de fondation : (?P<name1>{NAME}), de et à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})'
    m = match(pattern, source_pattern=pattern.replace('fondation :', 'fondation avec signature collective à deux:'))
    if m:
        return [person('foundation_members_appointed', m, m[f'name{i}'], 'Stiftungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf"Complément: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est complétée en ce sens que (?P<name>{NAME}) signe collectivement à deux, toutefois limitée aux affaires de la succursale")
    if m:
        return [person('branch_signing_supplement', m, m['name'], None, 'Kollektivunterschrift zu zweien', signing_scope='affaires de la succursale')], ''

    m = match(rf'Liquidateurs: (?P<name1>{NAME}), présidente, et (?P<name2>{NAME}), gérants, lesquels continuent de signer collectivement à deux')
    if m:
        return [person('managers_liquidators_continued_signing', m, m[f'name{i}'], 'Liquidator', 'Kollektivunterschrift zu zweien', previous_role='présidente, gérante' if i == 1 else 'gérant') for i in (1, 2)], ''

    m = match(rf"Rectificatif de l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE})\): la raison de commerce ayant été dissoute par erreur, elle est réinscrite d'office comme ci devant \(FOSC (?P<previous_date>{DATE}), p\. (?P<previous_ref>\d+)\)")
    if m:
        return [event('erroneous_dissolution_reinstatement_correction', m)], ''

    pattern = rf'Nouveaux gérants: (?P<name1>{NAME}), de et à (?P<place1>{NAME}), président et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}})'
    m = match(pattern, source_pattern=pattern + r', avec signature collective à deux')
    if m:
        return [person('managers_collective_signing_appointed', m, m[f'name{i}'], 'Vorsitzender der Geschäftsführung' if i == 1 else 'Geschäftsführer', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    pattern = rf'La membre vice-présidente du conseil de fondation (?P<vice_name>{NAME}), signe désormais individuellement; ses pouvoirs sont modifiés en ce sens\. '
    for i in range(1, 6):
        pattern += (r'et ' if i == 5 else '') + rf'(?P<name{i}>{NAME}), (?:du|de) (?P<origin{i}>{NAME}), à (?P<place{i}>{NAME}), '
    pattern += r'sont membres du conseil de fondation, tous avec le président ou la vice-présidente'
    m = match(pattern, source_pattern=pattern.replace('tous avec le', 'tous avec signature collective à deux, avec le'))
    if m:
        return [person('foundation_vice_president_individual_signing', m, m['vice_name'], 'Vizepräsident des Stiftungsrats', 'Einzelunterschrift')] + [person('foundation_members_restricted_signing', m, m[f'name{i}'], 'Stiftungsrat', 'Kollektivunterschrift zu zweien', m[f'place{i}'], signing_with='président ou vice-présidente') for i in range(1, 6)], ''

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>\d+), TR (?P<entry>\d+) vom (?P<entry_date>{DATE}) und Publikation im SHAB-Nr\. (?P<notice>\d+) vom (?P<notice_date>{DATE}) wurde als letztes SHAB-Zitat irrtümlich SHAB-Nr\. (?P<wrong_notice>\d+) vom (?P<wrong_date>{DATE}) genannt statt korrekt SHAB-Nr\. (?P<correct_notice>\d+) vom (?P<correct_date>{DATE})', 'de')
    if m:
        return [event('previous_notice_reference_corrected', m)], ''

    m = match(rf'Der Eintrag Ref\. (?P<reference>\d+) betreffend Statutendatum vom (?P<wrong_date>{DATE}) erfolgte irrtümlich und ist daher zu streichen\. Korrekter Eintrag unter Ref\. (?P=reference) ist nur dasjenige vom (?P<correct_date>{DATE})', 'de')
    if m:
        return [event('statutes_date_entry_corrected', m)], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito il fondo Part\. No\. (?P<parcel>\d+) RFD (?P<parcel_register>{NAME}) alla (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: CHF (?P<consideration>{MONEY})', 'it')
    if m:
        return [event('real_estate_assets_transferred', m)], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund der Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation wieder in das Handelsregister eingetragen und besteht entsprechen den früheren Eintragungen weiter', 'de')
    if m:
        return [event('liquidation_reinstatement_court_corrected', m)], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), jusqu'ici directeur, nommé président et (?P<name2>{NAME}), jusqu'ici président")
    if m:
        return [person('director_appointed_board_president', m, m['name1'], 'Präsident des Verwaltungsrats', previous_role='directeur'), person('former_president_remains_board_member', m, m['name2'], 'Verwaltungsrat', previous_role='président')], ''

    return [], leftover
