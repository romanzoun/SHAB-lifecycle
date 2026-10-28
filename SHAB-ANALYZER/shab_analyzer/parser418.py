from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser313 import NAME as LEGACY_NAME
from .parser126 import _DE_DEBT_OFFSET_CAPITAL_INCREASE
from .parser109 import _FR_COMMITTEE_MEMBERS_PAIR
from .parser140 import _FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED
from .parser218 import _FR_ASSOCIATE_MANAGER_SIGNATURE_REVOKED
from .parser241 import _FR_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE
from .parser230 import _FR_SIGNING_CORRECTED_COLLECTIVE_FROM_INDIVIDUAL

_LEGACY = (_DE_DEBT_OFFSET_CAPITAL_INCREASE, _FR_COMMITTEE_MEMBERS_PAIR, _FR_SIGNING_GRANTED_ROLE_AND_PROXY_REVOKED,
           _FR_ASSOCIATE_MANAGER_SIGNATURE_REVOKED, _FR_SIGNING_CORRECTED_COLLECTIVE_FROM_INDIVIDUAL, _FR_SHARE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE)
# Origins can contain abbreviations, such as St. Antoni.
ORIGIN = r'[^,;\n]+?'


def extract_parser418_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses; preserve existing rules and unknown input."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
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

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    def number(m, key):
        return Decimal(m[key].replace("'", ''))

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{ORIGIN}), à (?P<place>{NAME}), nouvelle associée sans signature, avec (?P=count) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        if number(m, 'before') != number(m, 'count') + number(m, 'remaining'):
            return [], text
        return [event('partial_transfer_new_unsigned_associate_explicit_holding', m, 'ownership_changed', currency='CHF'),
                person('new_unsigned_associate_explicit_holding', m, m['buyer'], 'associée', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf"(?P<seller>{NAME}) détient maintenant (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par suite de cession de CHF (?P<count>{COUNT}) parts de CHF (?P=nominal) à l'associée (?P<buyer>{NAME}), laquelle détient désormais (?P<buyer_total>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('share_transfer_extraneous_currency_before_count', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'(?P<name1>{NAME}), de (?P<origin1>{ORIGIN}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{ORIGIN}), à (?P<place2>{NAME}), sont membres du comité')
    if m and leftover + ' avec signature collective à deux' in source_text:
        # Parser 313 owns the same wording without abbreviated origins, including
        # when called directly on its residual with that parser disabled.
        legacy_pair = rf'(?P<name1>{LEGACY_NAME}), de (?P<origin1>{LEGACY_NAME}), à (?P<place1>{LEGACY_NAME}), et (?P<name2>{LEGACY_NAME}), de (?P<origin2>{LEGACY_NAME}), à (?P<place2>{LEGACY_NAME}), sont membres du comité'
        if re.fullmatch(legacy_pair, leftover):
            return [], text
        return [person('committee_pair_distinct_origins_collective_signing', m, m[f'name{i}'], 'membre du comité', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)], ''

    m = match(r'\((?P<branch_address>[^();\n]+ \d+[a-z]?)\)')
    if m and re.search(rf"Radiation de la mention de l'existence d'une succursale à [^();]+ \({UID}\) " + re.escape(leftover) + r'\.?$', source_text):
        return [event('deleted_branch_address_annotation', m, historical_annotation=True)], ''

    m = match(rf'Signature individuelle a été conférée à (?P<name>{NAME}), maintenant domicilié à (?P<place>{NAME}); sa procuration est radiée')
    if m:
        return [person('individual_signing_residence_proxy_revoked', m, m['name'], signing='Einzelunterschrift', place=m['place'], procuration_revoked=True)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name1>{NAME}) et (?P<name2>{NAME}), signent collectivement à deux \(et non individuellement\)")
    if m:
        return [person('two_signatures_corrected_collective', m, m[f'name{i}'], signing='Kollektivunterschrift zu zweien', corrected=True, previous_signing='Einzelunterschrift') for i in (1, 2)], ''

    m = match(rf"L'associé gérant (?P<name>{NAME}) n'exerce plus la signature sociale")
    if m:
        return [person('associate_manager_signing_revoked_without_previous_signing', m, m['name'], 'associé gérant', 'ohne Zeichnungsberechtigung')], ''

    m = match(rf'Bei der genehmigten Kapitalerhöhung vom (?P<decision_date>{DATE}) wird eine Forderung in der Höhe von CHF (?P<claim>{MONEY}) verrechnet, wofür (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) ausgegeben werden', 'de')
    if m:
        return [event('authorized_capital_increase_claim_offset', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), le président du (?P<court>{NAME}) a prolongé le sursis concordataire de (?P<duration>six mois), échéant le (?P<end_date>{DATE})")
    if m:
        return [event('composition_moratorium_extended_six_months', m, 'status_changed')], ''

    m = match(rf"Les associés-gérants (?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent chacun (?P<count>{COUNT}) de leurs (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<buyer>{NAME}), désormais titulaire de (?P<buyer_total>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) et (?P=seller2) restent titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacun")
    if m:
        if number(m, 'before') != number(m, 'count') + number(m, 'remaining') or number(m, 'buyer_total') < 2 * number(m, 'count'):
            return [], text
        return [event('two_managers_partial_transfers_existing_manager', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"(?P<seller1>{NAME}) \((?P<seller_uid>{UID})\) et la gérante (?P<seller2>{NAME}), qui ne sont plus associées, cèdent respectivement (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et (?P<count2>{COUNT}) part de CHF (?P=nominal) à (?P<buyer>{NAME}) \((?P<buyer_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée, titulaire de (?P<buyer_total>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        if number(m, 'buyer_total') != number(m, 'count1') + number(m, 'count2'):
            return [], text
        return [event('company_and_manager_transfer_new_company_associate', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"Augmentation conditionnelle du capital-participation fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}), porté CHF (?P<previous_capital>{MONEY}) à CHF (?P<capital>{MONEY}) par l'émission de (?P<issued_count>{COUNT}) bons de CHF (?P<nominal>{MONEY}), nominatifs, liés selon statuts\. Capital-participation: CHF (?P=capital), entièrement libéré, divisé en (?P<count>{COUNT}) bons de CHF (?P=nominal) nominatifs, liés selon statuts")
    if m:
        if number(m, 'capital') != number(m, 'count') * number(m, 'nominal') or number(m, 'capital') - number(m, 'previous_capital') != number(m, 'issued_count') * number(m, 'nominal'):
            return [], text
        return [event('conditional_participation_capital_authorization_increase', m, 'capital_changed', currency='CHF', fully_paid=True, transfer_restricted=True)], ''
    return [], text
