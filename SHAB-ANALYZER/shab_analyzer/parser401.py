from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser62, parser93, parser98, parser103, parser161, parser204, parser398

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser93, parser98, parser103, parser161, parser204, parser398)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser401_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete bounded residual variants without replacing upstream events."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(r'(?<!\S)' + source_pattern + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name=None, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name or m['name'], role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), 'place': place, **extra})

    pattern = rf'(?P<name>{NAME}), maintenant de (?P<origin>{NAME}), est nommé liquidateur'
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [person('male_liquidator_origin_changed', m, role='liquidateur', signing='Einzelunterschrift')], ''

    m = match(rf'Par suite de fusion de communes, le siège de la succursale \((?P<branch_uid>{UID})\) à (?P<previous_place>{NAME}) devient (?P<place>{NAME})')
    if m:
        return [event('branch_seat_after_municipality_merger', m, 'seat_changed')], ''

    pattern = rf'Nouveau membre du conseil de fondation avec le président ou le vice-président: (?P<name>{NAME}), de (?P<origin>{NAME}), au (?P<place>{NAME})'
    source = pattern.replace('avec le président', 'avec signature collective à deux, avec le président')
    m = match(pattern, source_pattern=source)
    if m:
        return [person('foundation_member_joint_president_or_vice', m, role='membre du conseil de fondation', signing='Kollektivunterschrift zu zweien', place=m['place'], signing_restriction='avec le président ou le vice-président')], ''

    # German wording is tagged French in the supplied publication.
    m = match(rf'Der Eintrag Nr\. (?P<entry>{COUNT}) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id\. (?P<notice_id>{COUNT})\) ist wie folgt ergänzt: Neue Firma: (?P<company_name>[^()\n]+?) \(und nicht (?P<previous_name>[^()\n]+?)\)')
    if m:
        return [event('company_name_supplement_corrected', m, 'company_name_changed')], ''

    pattern = rf"L'associée (?P<seller>[^\n]+?) \((?P<seller_registry_id>[A-Z]\d+)\) détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvelle associée-gérante et présidente pour (?P=count) parts de CHF (?P=nominal)"
    m = match(pattern, source_pattern=pattern + ' avec signature individuelle')
    if m:
        return [event('corporate_associate_transfer_new_president', m, 'ownership_changed', currency='CHF'), person('new_associate_manager_president_individual', m, m['buyer'], role='associée-gérante et présidente', signing='Einzelunterschrift', place=m['place'])], ''

    # The statutes clause belongs to parser103; pass it through that rule unchanged.
    prefix, separator, capital = leftover.partition('. Bei der ordentlichen Kapitalerhöhung')
    if language == 'de' and separator and parser103._DE_STATUTES_DATE_CORRECTION_COMMA.fullmatch(prefix):
        capital_clause = 'Bei der ordentlichen Kapitalerhöhung' + capital
        if capital_clause.endswith('.]') and parser204._DE_DEBT_OFFSET_CAPITAL_INCREASE.fullmatch(capital_clause[:-1]):
            try:
                for date in re.findall(DATE, leftover):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return [], text
            old, rest = parser103.extract_parser103_leftovers(prefix, language, publication_id, published_at, org_uid, plz, canton)
            issued, capital_rest = parser204.extract_parser204_leftovers(capital_clause[:-1], language, publication_id, published_at, org_uid, plz, canton)
            if old and not rest.strip() and issued and not capital_rest.strip():
                return old + issued, ''

    m = match(r'Neu eingetragene Personen: (?P<officers>[^\n]+)')
    if m:
        items = m['officers'].split('; ')
        if all(parser62._DE_INLINE_PERSON.fullmatch(item.strip()) for item in items):
            return [], text
        pattern = rf'(?P<name>{NAME}), (?:genannt (?P<known_as>{NAME}), )?(?:von (?P<origin>{NAME})|(?P<nationality>französische Staatsangehörige)), in (?P<place>{NAME}), Mitglied der Geschäftsleitung, Kollektivunterschrift zu zweien'
        parsed = [re.fullmatch(pattern, item) for item in items]
        if len(parsed) == 5 and all(parsed) and any(p['known_as'] for p in parsed):
            return [person('german_management_members_french_xml', p, role='Mitglied der Geschäftsleitung', signing='Kollektivunterschrift zu zweien', place=p['place']) for p in parsed], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}) continuent de signer collectivement à deux, mais désormais avec un administrateur ou M\. (?P<partner>{NAME})\. (?P<name3>{NAME}) continue de signer collectivement à deux, mais désormais sans autre restriction')
    if m:
        return [person('two_signatories_board_or_named_partner', m, m[key], signing='Kollektivunterschrift zu zweien', signing_restriction='avec un administrateur ou M. ' + m['partner']) for key in ('name1', 'name2')] + [person('single_signatory_restriction_removed', m, m['name3'], signing='Kollektivunterschrift zu zweien', restriction_removed=True)], ''

    pattern = rf"Les gérants (?P<name1>{NAME}), nommé président et (?P<name2>{NAME}), jusqu'ici président, continuent à signer individuellement\. (?P<name3>{NAME}), des (?P<origin3>{NAME}), à (?P<place3>{NAME}) et (?P<name4>{NAME}), de (?P<origin4>{NAME}), à (?P<place4>{NAME}), sont nommés gérants"
    m = match(pattern, source_pattern=pattern + ', avec signature individuelle')
    if m:
        return [person('manager_presidency_and_appointments_individual', m, m['name1'], role='gérant président', signing='Einzelunterschrift'), person('manager_presidency_and_appointments_individual', m, m['name2'], role='gérant', signing='Einzelunterschrift', previous_role='président')] + [person('manager_presidency_and_appointments_individual', m, m[f'name{i}'], role='gérant', signing='Einzelunterschrift', place=m[f'place{i}'], origin=m[f'origin{i}']) for i in (3, 4)], ''

    m = match(rf'\[Mit Verfügung des (?P<authority>[^\[\]\n]+?) vom (?P<decision_date>{DATE}) wurde die Suspendierung der Stiftungsräte aufgehoben\.\] \[gestrichen: (?P<previous>Mit Verfügung vom {DATE} hat die Aufsichtsbehörde sämtliche Stiftungsratsmitglieder bis Ende März 2021 von ihren Ämtern und Funktionen suspendiert sowie [^\[\]\n]+? als Sachwalter mit Einzelunterschrift eingesetzt\.)\]\. Mit Verfügung vom (?P<appointment_date>{DATE}) hat die Aufsichtsbehörde (?P<name>[^\[\]\n]+?) als Sachwalter mit Einzelunterschrift eingesetzt', 'de')
    if m:
        return [event('foundation_board_suspension_lifted', m), person('foundation_custodian_appointment_retained', m, role='Sachwalter', signing='Einzelunterschrift')], ''

    m = match(rf'(?P<name1>{NAME}), qui est maintenant à (?P<place>{NAME}) \((?P<country>{NAME})\), est nommé président\. (?P<name2>{NAME}), qui reste directeur, est nommé gérant')
    if m:
        return [person('president_residence_and_director_manager', m, m['name1'], role='président', place=m['place']), person('president_residence_and_director_manager', m, m['name2'], role='directeur, gérant', place=None, country=None)], ''

    m = match(rf"L'identification de la succursale de (?P<place>{NAME}) sous le numéro (?P<previous_registry_id>CH-\d{{3}}-\d{{7}}-\d) est remplacée par le numéro d'identification des entreprises \(IDE/UID\) (?P<branch_uid>{UID})")
    if m:
        return [event('branch_registry_id_replaced_by_uid', m, 'branch_changed', scope='branch')], ''
    return [], text
