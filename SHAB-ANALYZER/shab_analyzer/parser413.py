from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from .parser132 import _FR_OFFICER_SIGNING_CORRECTION
from .parser176 import _FR_TWO_DIRECTORS_SIGNING_UNRESTRICTED
from .parser178 import _FR_FOUNDATION_PRESIDENCY_CHANGED
from .parser243 import _FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR

_LEGACY = (_FR_OFFICER_SIGNING_CORRECTION,
           _FR_TWO_DIRECTORS_SIGNING_UNRESTRICTED,
           _FR_FOUNDATION_PRESIDENCY_CHANGED,
           _FR_ORIGIN_CHANGED_APPOINTED_LIQUIDATOR)


def extract_parser413_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Handle bounded release 413 residual variants after the existing rules."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(r'(?<!\S)' + source_pattern + r'(?=\.?(?:\s|$))', source_text)
            if not source or any(source[k].strip() != v.strip() for k, v in m.groupdict().items()):
                return None
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra, 'name': name})

    pattern = rf'(?P<name>{NAME}) est nommé membre du conseil ; sa procuration est radiée'
    source = rf'(?P<name>{NAME}) est nommé membre du conseil avec signature collective à deux; sa procuration est radiée'
    m = match(pattern, source_pattern=source)
    if m:
        return [person('council_member_appointed_proxy_revoked', m, m['name'], 'membre du conseil', 'Kollektivunterschrift zu zweien', procuration_revoked=True)], ''

    m = match(rf"(?P<name1>{NAME}), membre du conseil de fondation, nommé président, et (?P<name2>{NAME}), membre du conseil de fondation, jusqu'ici président, continuent de signer collectivement à deux")
    if not m:
        m = match(rf"Les membres du conseil de fondation (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président et (?P<name2>{NAME}), jusqu'ici président, continuent à signer collectivement à deux")
    if m:
        return [person('foundation_presidency_changed_explicit_roles', m, m[f'name{i}'], 'membre du conseil de fondation président' if i == 1 else 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien') for i in (1, 2)], ''

    m = match(rf"Rectification de l'inscription No\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) Id (?P<notice_id>\d+)\): (?P<name>{NAME}), gérant, signature collective à deux \(et non pas signature individuelle\)")
    if m:
        return [person('manager_joint_signing_corrected_notice', m, m['name'], 'Geschäftsführer', 'Kollektivunterschrift zu zweien', corrected=True, previous_signing='Einzelunterschrift')], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), nommés directeurs, signent désormais collectivement à deux sans autre restriction; leurs pouvoirs sont modifiés en ce sens')
    if m:
        return [person('three_directors_signing_unrestricted', m, m[f'name{i}'], 'Direktor', 'Kollektivunterschrift zu zweien', signing_restrictions_removed=True) for i in (1, 2, 3)], ''

    m = match(r'Löschung auf Begehren der Inhaberin, da nicht eintragungspflichtig', 'de')
    if m:
        return [event('owner_requested_deletion_not_required', m, 'status_changed', deleted=True, reason='not_required_to_register', requested_by='owner')], ''

    pattern = rf'Nouveaux bons de jouissance: (?P<count>{COUNT}) bons nominatifs, , donnant droit à une part du produit de liquidation'
    source = rf'Nouveaux bons de jouissance: (?P<count>{COUNT}) bons nominatifs, liées selon statuts, donnant droit à une part du produit de liquidation'
    m = match(pattern, source_pattern=source)
    if m:
        return [event('registered_profit_certificates_liquidation_rights', m, 'capital_changed', security_kind='bons de jouissance', transfer_restricted=True, liquidation_proceeds_right=True)], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifié en en ce sens que l'associée a désormais le nom de (?P<name>[^\n()]+?) \((?P<associate_uid>{UID})\) \(et non pas (?P<previous_name>[^\n()]+?)\)")
    if m:
        return [event('corporate_associate_name_corrected_typo', m, 'ownership_changed', corrected=True)], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P=count) parts de CHF (?P=nominal), sans signature\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        number = lambda k: Decimal(m[k].replace("'", ''))
        if number('before') != number('count') + number('remaining'):
            return [], text
        return [event('share_transfer_new_unsigned_associate_with_holdings', m, 'ownership_changed', currency='CHF'), _person_event(*context, 'officer_changed', 'fr.text.new_unsigned_associate_with_holdings.v1', m['buyer'], role='Gesellschafter', signing='ohne Unterschrift', place=m['place'], extra={'action': 'appointed', 'origin': m['origin']})], ''

    pattern = rf"Nouvelle division du capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives et \(jusqu'ici: (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), nominatives et liées selon statuts\)"
    source = pattern.replace(r"nominatives et \(jusqu'ici:", r"nominatives et liées selon statuts \(jusqu'ici:")
    m = match(pattern, source_pattern=source)
    if m:
        number = lambda k: Decimal(m[k].replace("'", ''))
        if number('capital') != number('count') * number('nominal') or number('capital') != number('previous_count') * number('previous_nominal'):
            return [], text
        return [event('registered_share_split_unchanged_restrictions', m, 'capital_changed', currency='CHF', transfer_restricted=True, fully_paid=True)], ''

    # Parser 401 owns the variant with individual signing. Require the
    # complete source clause without a signing declaration, even when that
    # earlier rule is disabled. An omitted signing right stays unspecified.
    pattern = rf'(?P<name>{NAME}), maintenant de (?P<origin>{NAME}), est nommé liquidateur'
    m = match(pattern, source_pattern=pattern + r'(?=\.?$)')
    if m:
        return [person('liquidator_appointed_origin_changed_short', m, m['name'], 'Liquidator')], ''

    def reference(prefix):
        return rf'Ref\. (?P<{prefix}reference>\d+), TR (?P<{prefix}entry>\d+) vom (?P<{prefix}entry_date>{DATE}) und Publikation im SHAB Nr\. (?P<{prefix}notice>\d+) vom (?P<{prefix}notice_date>{DATE}), publ\. (?P<{prefix}publication>\d+)'
    m = match(rf'Mit der Eintragung {reference("")} wurde als letztes SHAB-Zitat irrtümlich {reference("previous_")} genannt statt korrekt {reference("correct_")}', 'de')
    if m:
        return [event('last_notice_reference_corrected_full_references', m, corrected=True)], ''
    return [], text
