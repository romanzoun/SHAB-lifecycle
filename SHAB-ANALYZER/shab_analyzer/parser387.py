from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
# Reuse the old patterns, including in isolation when an earlier extractor is disabled.
from . import parser83, parser87, parser91, parser94, parser96, parser102, parser181, parser185, parser193, parser197, parser218, parser236, parser248

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
_LEGACY = tuple(p for module in (parser83, parser87, parser91, parser94, parser96, parser102, parser181, parser185, parser193, parser197, parser218, parser236, parser248) for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser387_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded variants from the 387 fixtures; preserve every earlier event."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', value=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover if value is None else value)
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=extra.get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    # Earlier numeric extraction consumes the decimal suffix and recipient. Only
    # the complete source clause can supply the actual liabilities and recipient.
    pattern = rf'Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom (?P<agreement_date1>{DATE})/(?P<agreement_date2>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine'
    source = re.search(pattern + r'\.', source_text) if language == 'de' else None
    if source:
        m = match(pattern, 'de', source[0])
        if m and leftover == (f"Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom {m['agreement_date1']}/{m['agreement_date2']} Aktiven von CHF {m['assets']} und Passiven (Fremdkapital) von CHF {m['liabilities'].split('.')[0]} Gegenleistung: keine"):
            return [event('association_transfer_two_contract_dates', m, currency='CHF', consideration='keine')], ''

    m = match(rf'Kapital Hauptsitz neu: Aktienkapital: CHF (?P<capital>{COUNT}\.--); Liberierung: CHF (?P<paid_up>{COUNT}\.--) \[bisher: Kapital Hauptsitz: Aktienkapital: CHF (?P<previous_capital>{COUNT}\.--); Liberierung: CHF (?P<previous_paid_up>{COUNT}\.--)\]', 'de')
    if m:
        return [event('head_office_share_capital_paid_up', m, currency='CHF')], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) a cédé (?P<first_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<manager>{NAME})\. L'associé-gérant (?P=manager) a cédé (?P<second_count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}) \((?P<buyer_uid>{UID})\), à (?P<place>{NAME}), nouvelle associée pour (?P=second_count) parts de CHF (?P=nominal)\. Associés: (?P=seller) pour (?P<seller_remaining>{COUNT}) parts de CHF (?P=nominal), (?P=buyer) \((?P=buyer_uid)\) pour (?P=second_count) parts de CHF (?P=nominal) et (?P=manager) pour (?P<manager_remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('successive_manager_corporate_share_transfers', m, currency='CHF')], ''

    m = match(rf"Fusion: reprise des actifs et passifs de (?P<transferor>{NAME}), à (?P<place>{NAME}) (?P<transferor_uid>{UID})\), selon contrat de fusion du (?P<agreement_date>{DATE}) et bilan au (?P<balance_date>{DATE}), présentant des actifs de CHF (?P<assets>{MONEY}), des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_integer>[\d']+), (?P<net_cents>\d{{2}})\. La société reprenante détenant l'ensemble des actions de la société transférante, la fusion ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions")
    if m:
        number = lambda s: Decimal(s.replace("'", ''))
        if number(m['assets']) - number(m['liabilities']) == number(m['net_integer'] + '.' + m['net_cents']):
            return [event('merger_missing_open_parenthesis_split_decimal', m, currency='CHF')], ''
        return [], text

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('foundation_assets_only_cash_transfer', m, currency='CHF')], ''

    m = match(r'\[Löschung der Bestimmung über die genehmigte Kapitalerhöhung infolge Ablauf der Frist\.\] \. \[Löschung der Bestimmung über die bedingte Kapitalerhöhung infolge Ablauf der Frist\]', 'de')
    if m:
        return [event('authorized_conditional_capital_clauses_expired', m)], ''

    m = match(rf"(?P<name1>{NAME}), membre du comité, nommé membre du bureau et secrétaire, exerce désormais la signature sociale, collectivement à deux\. (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), est membre du comité; n'exerce pas la signature sociale")
    if m:
        return [person('committee_secretary_collective_signing', m, m['name1'], 'membre du bureau et secrétaire', 'Kollektivunterschrift zu zweien'), person('committee_member_without_signing', m, m['name2'], 'membre du comité', 'ohne Zeichnungsberechtigung', place=m['place'])], ''

    m = match(rf'Signature collective à deux, sauf avec (?P<excluded1>{NAME}), (?P<excluded2>{NAME}), (?P<excluded3>{NAME}) ou (?P<excluded4>{NAME}), été conférée à (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME})')
    if m:
        return [person('collective_signing_four_exclusions_typo', m, m['name'], None, 'Kollektivunterschrift zu zweien', place=m['place'], signing_exclusions=[m[f'excluded{i}'] for i in range(1, 5)])], ''

    m = match(rf'Das Kantonsgericht des Kantons (?P<court_canton>[^;\[\]]+?) hat mit Entscheid vom (?P<decision_date>{DATE}) die Beschwerde abgewiesen und den Konkurs per (?P<effective_date>{DATE}), um (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr neu eröffnet', 'de')
    if m:
        return [event('bankruptcy_reopened_cantonal_appeal_rejected', m, 'status_changed')], ''

    m = match(rf'(?P<seller>{NAME}), maintenant président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), nouvel associé-gérant pour (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('president_share_transfer_foreign_manager', m, currency='CHF'), person('share_transfer_seller_president', m, m['seller'], 'président', None), person('share_transfer_new_associate_manager', m, m['buyer'], 'associé-gérant', None, place=m['place'])], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au gérant (?P<buyer>{NAME}), nouvel associé avec (?P=count) parts de CHF (?P=nominal)\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        n = lambda key: int(m[key].replace("'", ''))
        if n('count') > 0 and n('previous_count') == n('count') + n('remaining'):
            return [event('share_transfer_to_existing_manager_remaining', m, currency='CHF')], ''
        return [], text

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que \(et non pas du (?P<previous_decision_date>{DATE})\)")
    if m:
        source = re.search(rf"L'inscription No {re.escape(m['entry'])} du {re.escape(m['entry_date'])} est rectifiée en ce sens que la société est dissoute par décision de l'assemblée des associés du (?P<decision_date>{DATE}) \(et non pas du {re.escape(m['previous_decision_date'])}\)\.", source_text)
        if source:
            try:
                datetime.strptime(source['decision_date'], '%d.%m.%Y')
            except ValueError:
                return [], text
            return [event('dissolution_decision_date_corrected_fragment', m, 'publication_corrected', decision_date=source['decision_date'])], ''
    return [], text
