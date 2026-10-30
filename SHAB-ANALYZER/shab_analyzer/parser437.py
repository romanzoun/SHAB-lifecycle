from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser55, parser60, parser211

# Search rules retain ownership even when they only consume part of a clause.
_LEGACY = (parser55._FR_STANDALONE_GROUP_SIGNING,
           parser60._FR_SHARE_TRANSFER_RESTRICTION,
           parser211._DE_AUDIT_WAIVER_ERRONEOUS_BRACKET)


def extract_parser437_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only complete, sample-backed residual variants."""
    leftover = text.strip()
    if any(pattern.search(leftover) for pattern in _LEGACY):
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

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, role, signing=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             m.groupdict().get('buyer', m.groupdict().get('name')),
                             role=role, signing=signing, place=m.groupdict().get('place'),
                             extra={'action': action, **m.groupdict()})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) wurde das summarische Konkursverfahren gemäss (?P<legal_basis>Art\. 231 SchKG) angeordnet', 'de')
    if m:
        return [event('summary_bankruptcy_proceedings_ordered_article231', m, 'status_changed', bankruptcy_procedure='summarisch')], ''

    m = match(rf'(?P<seller1>{NAME}) et (?P<seller2>{NAME}) \((?P<seller_uid2>{UID})\) cèdent respectivement (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et (?P<count2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal), gérant (?P=seller1) et (?P=seller2) \((?P=seller_uid2)\) restent respectivement titulaires de (?P<remaining1>{COUNT}) parts de CHF (?P=nominal) et (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        if not all(number(m[k]) > 0 for k in ('count1', 'count2', 'nominal', 'remaining1', 'remaining2')) or number(m['count1']) + number(m['count2']) != number(m['buyer_count']):
            return [], text
        return [event('two_transferors_person_and_company_new_manager', m, 'ownership_changed', currency='CHF'),
                person('recipient_associate_manager_appointed', m, 'associé-gérant')], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée avec (?P=count) parts de CHF (?P=nominal), sans signature\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        if not all(number(m[k]) > 0 for k in ('count', 'remaining', 'nominal')) or number(m['count']) + number(m['remaining']) != number(m['previous_count']):
            return [], text
        return [event('partial_transfer_new_unsigned_female_associate_de_origin', m, 'ownership_changed', currency='CHF'),
                person('new_unsigned_female_associate_de_origin', m, 'associée', 'ohne Zeichnungsberechtigung')], ''

    m = match(r'Nouvelle raison de commerce: (?P<name>[^().,;\n]+ SA) \((?P<german_name>[^().,;\n]+ AG)\) \((?P<english_name>[^().,;\n]+ Ltd)\)')
    if m:
        return [event('company_name_changed_two_translations', m)], ''

    m = match(r'\[Das Opting-out wurde fälschlicherweise eingetragen\.\]', 'de')
    if m:
        return [event('opting_out_erroneous_bracket_corrected', m, 'audit_requirement_changed', kind='limited_audit_waiver', limited_audit_waived=False)], ''

    m = match(r'(?P<name>[^,;.\n]+? [A-Z]\.) est nommé liquidateur')
    if m:
        return [person('liquidator_appointed_name_with_initial', m, 'Liquidator')], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) relative à la radiation ayant été requise par erreur, l'inscription de l'entreprise individuelle est rétablie")
    if m:
        return [event('sole_proprietorship_erroneous_deletion_request_reinstated', m, 'status_changed', reinstated=True, erroneous_deletion_request=True)], ''

    return [], text
