from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, COUNT, UID

PERSON = r'[^,;]+?'
NOTICE_DATE = r'\d{2}[-.]\d{2}[-.]\d{4}'


def extract_parser369_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
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

    m = match(r'\[gestrichen: (?P<previous_place1>[^();]+) \((?P<previous_register1>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\. (?P<place2>[^();]+) \((?P<uid2>' + UID + r')\)\. \[gestrichen: (?P=place2) \((?P<previous_register2>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]\. (?P<place3>[^();]+) \((?P<uid3>' + UID + r')\)\. \[gestrichen: (?P=place3) \((?P<previous_register3>CH-\d{3}\.\d\.\d{3}\.\d{3}-\d)\)\]', 'de')
    if m:
        return [event('branch_register_references_updated', m)], ''

    reference = rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{NOTICE_DATE}) \(FOSC du (?P<notice_date>{NOTICE_DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que "
    m = match(reference + rf'(?P<name>{PERSON}) est unique associé et non gérant')
    if m:
        return [person('sole_associate_not_manager_corrected', m, m['name'], role='Gesellschafter', excluded_role='Geschäftsführer', sole_associate=True)], ''

    m = match(rf"Aktienkapital neu: CHF (?P<capital>{MONEY}), vollständig liberiert, eingeteilt in (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) \(Bisher: (?P<previous_count>{COUNT}) Inhaberaktien zu CHF (?P<previous_nominal>{MONEY})\)\. Statuten geändert am (?P<statutes_date>{DATE})", 'de')
    if m:
        return [event('bearer_to_registered_shares_statutes_changed', m, currency='CHF', fully_paid=True, security_kind='Namenaktien', previous_security_kind='Inhaberaktien')], ''

    m = match(rf"Les associés-gérants (?P<seller1>{PERSON}) et (?P<seller2>{PERSON}) cèdent chacun (?P<transferred>{COUNT}) de leur avec (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé (?P<recipient>{PERSON}) maintenant titulaire de (?P<recipient_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) et (?P=seller2) restent titulaires de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal) chacun")
    if m:
        return [event('two_associate_managers_share_transfer_typo', m, currency='CHF')], ''

    m = match(rf"Par décision du (?P<decision_date>{DATE}), le juge unique compétent a prolongé le sursis concordataire définitif accordé à la société jusqu'au (?P<end_date>{DATE})")
    if m:
        return [event('definitive_composition_moratorium_extended', m)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>[^;]+?) wurde eine COVID-19-Stundung von drei Monaten bis zum (?P<end_date>{DATE}) bewilligt', 'de')
    if m:
        return [event('covid_moratorium_granted_three_months', m, duration_months='3')], ''

    m = match(reference + rf'(?P<name>{PERSON}) est originaire de (?P<origin>[^();]+) \(et non de (?P<previous_origin>[^();]+)\)')
    if m:
        return [person('officer_origin_corrected_notice_reference', m, m['name'])], ''

    m = match(rf"(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), sont membres du conseil de fondation; ils n'exercent pas la signature sociale")
    if m:
        return [person('two_foundation_members_unsigned', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Stiftungsrates', 'ohne Zeichnungsberechtigung') for i in (1, 2)], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associé-gérant se nomme (?P<name>[^();]+) \(et non (?P<previous_given_name>[^(),;]+) comme publié\)")
    if m:
        return [person('associate_manager_name_corrected', m, m['name'], role='Gesellschafter und Geschäftsführer')], ''

    m = match(rf'Signature collective à deux, toutefois pas entre eux ni avec (?P<excluded_signers>[^;]+?), est conférée à (?P<name1>{PERSON}), de (?P<origin1>{PERSON}), au (?P<place1>{PERSON}), sous-directeur, (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), (?P<name3>{PERSON}), de (?P<origin3>{PERSON}), à (?P<place3>{PERSON}), et (?P<name4>{PERSON}), de (?P<origin4>{PERSON}), à (?P<place4>[^,;.]+?)')
    if m:
        return [person('four_officers_restricted_joint_signing', m, m[f'name{i}'], m[f'place{i}'], 'Vizedirektor' if i == 1 else None, 'Kollektivunterschrift zu zweien', signing_restriction='pas entre eux ni avec ' + m['excluded_signers']) for i in range(1, 5)], ''

    m = match(rf"L'associée (?P<name>{PERSON}) est nommé gérante présidente")
    if m:
        return [person('associate_appointed_presiding_manager', m, m['name'], role='Präsident der Geschäftsführung')], ''

    m = match(rf'Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<previous_authorization_date>{DATE}) beschlossene genehmigte Kapitalerhöhung infolge Fristablaufs\. \. Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt', 'de')
    if m:
        return [event('expired_authorized_capital_replaced', m)], ''

    return [], leftover
