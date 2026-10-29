from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser165, parser174, parser209, parser280, parser395

_LEGACY = tuple(p for module in (parser165, parser174, parser209, parser280, parser395)
                for p in vars(module).values() if isinstance(p, re.Pattern))
MONTH = r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)'


def extract_parser432_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete evidenced clauses, leaving historical input intact."""
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
        return _event(*context, kind, f'{language}.text.{action}.v1',
                      {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf"La commandite de l'associé commanditaire (?P<name>{NAME}) \((?P<associate_uid>{UID})\) a été réduite de CHF (?P<previous>{MONEY}) à CHF (?P<amount>{MONEY})")
    if m and number(m['previous']) > number(m['amount']) >= 0:
        return [event('limited_partner_contribution_reduced', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Transfert de patrimoine: selon contrat des (?P<agreement_day1>\d{{1,2}}) et (?P<agreement_day2>\d{{1,2}}) (?P<agreement_month>{MONTH}) (?P<agreement_year>\d{{4}}) et selon décision de l\'autorité de surveillance du (?P<decision_day>\d{{1,2}}) (?P<decision_month>{MONTH}) (?P<decision_year>\d{{4}}), la fondation a transféré des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}) à (?P<recipient>{NAME}), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: (?P<consideration>aucune)')
    if m:
        months = MONTH.removeprefix('(?:').removesuffix(')').split('|')
        try:
            for day, month, year in ((m['agreement_day1'], m['agreement_month'], m['agreement_year']), (m['agreement_day2'], m['agreement_month'], m['agreement_year']), (m['decision_day'], m['decision_month'], m['decision_year'])):
                datetime(int(year), months.index(month) + 1, int(day))
        except ValueError:
            return [], text
        return [event('foundation_asset_transfer_written_dates', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine Anpassung der bedingten Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen', 'de')
    if m:
        return [event('conditional_capital_increase_adjusted', m, 'capital_changed')], ''

    m = match(rf"Administration: (?P<name1>{NAME}), président, (?P<name2>{NAME}), et (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), lesquels signent collectivement à trois\. Les pouvoirs de (?P=name1) et (?P=name2) sont modifiés en ce sens")
    if m:
        return [person('board_collective_signing_three', m, m[f'name{i}'], 'président' if i == 1 else 'administrateur', 'Kollektivunterschrift zu dreien', m.groupdict().get(f'place{i}')) for i in (1, 2, 3)], ''

    m = match(rf'(?P<seller>{NAME}) a cédée (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME})\. Associés: (?P=seller) pour (?P<remaining>{COUNT}) parts de CHF (?P=nominal) et (?P=buyer) pour (?P=count) parts de CHF (?P=nominal)')
    if m and all(number(m[k]) > 0 for k in ('count', 'remaining', 'nominal')):
        return [event('share_transfer_resulting_holdings_typo', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Mit Verfügung des (?P<appeal_court>{NAME}) vom (?P<decision_date>{DATE}) ist der Beschwerde gegen die Verfügung des (?P<court>{NAME}) vom (?P<appealed_date>{DATE}) aufschiebende Wirkung zuerkannt worden\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. \[bisher: Über den Inhaber dieses Einzelunternehmens ist mit Verfügung des (?P=court) vom (?P=appealed_date) mit Wirkung ab dem (?P<opening_date>{DATE}), (?P<opening_time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('sole_proprietor_bankruptcy_appeal_suspensive_effect', m, 'status_changed', suspensive_effect=True, bankruptcy_entry_removed=True)], ''

    m = match(rf'Bemerkungen zum Hauptsitz neu: Das Konkursverfahren ist mit Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) mangels Aktiven eingestellt worden', 'de')
    if m:
        return [event('head_office_bankruptcy_suspended_lack_assets', m, 'status_changed', suspended=True, reason='mangels Aktiven', scope='head_office')], ''

    m = match(r'Cette raison de commerce a été radiée par erreur sans les autorisations des autorités fiscales, elle est donc réinscrite')
    if m:
        return [event('erroneous_deletion_without_tax_authorization_reinstated', m, 'status_changed', reinstated=True)], ''

    m = match(rf"(?P<name>{NAME}) jusqu'ici signature individuelle a maintenant signature collective à deux")
    if m:
        return [person('individual_to_collective_signing_without_commas', m, m['name'], signing='Kollektivunterschrift zu zweien', previous_signing='Einzelunterschrift')], ''

    return [], text
