from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser63, parser66, parser87, parser122, parser140, parser144, parser164, parser180, parser207, parser220

NAME = r'[^,;.\[\]\n]+?'
FDATE = r'(?:1er|[1-9]|[12]\d|3[01]) décembre \d{4}'
# Existing compiled expressions retain ownership, even in isolated calls.
_LEGACY = tuple(p for module in (parser63, parser66, parser87, parser122,
                                parser140, parser144, parser164, parser180,
                                parser207, parser220)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser396_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, sample-backed residual variants."""
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
                for date in re.findall(FDATE, m[0]):
                    day, _, year = date.split()
                    datetime(int(year), 12, int(day.replace('er', '')))
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name})

    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY}), à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation: une créance de CHF (?P<consideration>{MONEY})')
    if m:
        return [event('sole_proprietor_asset_transfer_net_assets_claim', m, currency='CHF')], ''

    m = match(rf'Par décision du (?P<decision_date>{FDATE}), la (?P<court>Cour des poursuites et faillites du Tribunal cantonal) a rejeté le recours et confirmé le prononcé, la faillite prenant effet le (?P<effective_date>{FDATE}), à (?P<effective_time>(?:[01]?\d|2[0-3])h[0-5]\d)')
    if m:
        return [event('bankruptcy_appeal_rejected_pronouncement_confirmed', m, 'status_changed')], ''

    m = match(rf'Nouveaux membres du conseil de fondation : (?P<name1>{NAME}), à (?P<place1>{NAME}), (?P<name2>{NAME}), à (?P<place2>{NAME}), tous deux de (?P<origin12>{NAME}), et (?P<name3>{NAME}), de et à (?P<place3>{NAME})')
    if m:
        return [person('three_foundation_members_shared_origin', m, m[f'name{i}'], 'membre du conseil de fondation', place=m[f'place{i}'], origin=m['origin12'] if i < 3 else m['place3']) for i in (1, 2, 3)], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant président, (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        n = lambda k: int(m[k].replace("'", ''))
        if n('count') > 0 and n('previous') - n('count') == n('remaining'):
            return [event('share_transfer_new_associate_manager_president', m, currency='CHF')], ''
        return [], text

    m = match(r'\[Die publikationspflichtigen Tatsachen habe keine Änderung erfahren\.\]', 'de')
    if m:
        return [event('publication_facts_unchanged_typo', m, publication_facts_changed=False)], ''

    m = match(rf'Kommanditsumme neu: (?P<amount>{MONEY}) \[bisher: (?P<previous_currency_raw>CHE) (?P<previous_amount>{MONEY})\]', 'de')
    if m:
        # No currency is stated for the new amount; preserve the published typo.
        return [event('limited_partnership_amount_previous_currency_typo', m)], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici (?P<previous_role>administrateur), signe désormais par procuration individuelle; ses pouvoirs sont modifiés en ce sens")
    if m:
        return [person('former_administrator_individual_proxy', m, m['name'], signing='Einzelprokura')], ''

    # Require the extra comma-separated name component; ordinary names belong to old rules.
    m = match(rf'Signature collective à deux a été conférée à (?P<name>{NAME}, {NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        return [person('collective_signatory_comma_in_name', m, m['name'], signing='Kollektivunterschrift zu zweien', place=m['place'])], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) der Gesellschaft die provisorische Nachlassstundung bis zum (?P<until_date>{DATE}) bewilligt und mit Verfügung vom (?P<appointment_date>{DATE}) die (?P<commissioner>{NAME}) \((?P<commissioner_uid>{UID})\), (?P<commissioner_address>{NAME}), (?P<commissioner_postal_code>\d{{4}}) (?P<commissioner_place>{NAME}), als provisorische Sachwalterin eingesetzt', 'de')
    if m:
        return [event('provisional_moratorium_separate_commissioner_decision', m, 'status_changed')], ''

    m = match(rf'Stauts modifiés le (?P<statutes_date>{DATE}) sur des points nons soumis à publication')
    if m:
        return [event('statutes_non_public_changes_double_typo', m)], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), qui sont maintenant à (?P<place>{NAME}), sont nommés liquidateurs')
    if m:
        return [person('two_liquidators_shared_new_residence', m, m[f'name{i}'], 'liquidateur', place=m['place']) for i in (1, 2)], ''

    m = match(rf'Les membres du conseil de fondation (?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), et (?P<name4>{NAME}) sont nommé liquidateurs')
    if m:
        return [person('four_foundation_members_liquidators_typo', m, m[f'name{i}'], 'membre du conseil de fondation, liquidateur') for i in (1, 2, 3, 4)], ''
    return [], text
