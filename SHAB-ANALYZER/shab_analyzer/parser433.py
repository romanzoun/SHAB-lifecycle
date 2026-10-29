from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser55, parser60, parser105, parser140, parser235, parser326

# Preserve historical ownership, including when those rules are isolated in tests.
_LEGACY = tuple(p for module in (parser55, parser60, parser105, parser140, parser235, parser326)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser433_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse only complete, evidenced residual clauses; retain unknown input."""
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

    def person(action, m, name, role, signing, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1',
                             name, role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Vermögensübertragung: Der Geschäftsinhaber überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) und eine Gutschrift als Forderung von CHF (?P<receivable>{MONEY})', 'de')
    if m and all(number(m[k]) > 0 for k in ('count', 'nominal')):
        return [event('sole_proprietor_asset_transfer_balance_receivable', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf"Division des (?P<previous_count>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY}) en (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}); l'associé-gérant (?P<name>{NAME}) détient ainsi (?P=count) parts de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('previous_count', 'previous_nominal', 'count', 'nominal')) and number(m['previous_count']) * number(m['previous_nominal']) == number(m['count']) * number(m['nominal']):
        return [event('social_shares_split_manager_holdings', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Persona iscritta corretta: (?P<surname>{NAME}), (?P<given_names>{NAME}), cittadina (?P<nationality>{NAME}), in (?P<place>{NAME}), amministratrice unica, con firma individuale', 'it')
    if m:
        return [person('sole_female_administrator_corrected', m, m['surname'] + ', ' + m['given_names'], 'amministratrice unica', 'Einzelunterschrift', m['place'], corrected=True)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_reference>\d+/\d+)\) est rectifiée en ce sens que l'adresse de liquidation exacte est (?P<address>[^()]+) \(et non (?P<previous_address>[^()]+), comme publié\)")
    if m:
        return [event('liquidation_address_corrected_notice_reference', m, 'address_changed', corrected=True, scope='liquidation')], ''

    m = match(rf'(?P<name>{NAME}) est nommée membre de la direction et signe collectivement à deux; sa procuration est radiée')
    if m:
        return [person('female_management_member_appointed_proxy_revoked', m, m['name'], 'membre de la direction', 'Kollektivunterschrift zu zweien', proxy_revoked=True)], ''

    m = match(rf'Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) ne sont plus restreintes quant à la transmissibilité')
    if m and number(m['count']) > 0 and number(m['nominal']) > 0:
        return [event('registered_share_transfer_restrictions_removed_plain', m, 'capital_changed', currency='CHF', transfer_restricted=False)], ''

    m = match(rf'Liquidateurs: les associés gérants (?P<name1>{NAME}) et (?P<name2>{NAME}), lequels continuent à signer collectivement à deux')
    if m:
        return [person('associate_managers_liquidators_typo', m, m[f'name{i}'], 'liquidateur', 'Kollektivunterschrift zu zweien', previous_role='associé gérant') for i in (1, 2)], ''

    m = match(rf'Die im Sinne von (?P<legal_basis>Art\. 159 Abs\. 5 lit\. a aHRegV) am (?P<deletion_date>{DATE}) von Amtes wegen gelöschte Gesellschaft wird wieder in das Handelsregister eingetragen, nachdem der Konkursrichter des (?P<court>{NAME}) mit Urteil vom (?P<decision_date>{DATE}) die Wiedereröffnung des Konkursverfahrens als summarisches Verfahren, angeordnet hat\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]\. \[gestrichen: Das Konkursverfahren ist mit Urteil des Konkursrichters vom (?P<previous_decision_date>{DATE}) mangels Aktiven eingestellt worden\.\]', 'de')
    if m:
        return [event('company_reinstated_summary_bankruptcy_reopened', m, 'status_changed', reinstated=True, bankruptcy_reopened=True, procedure='summarisch')], ''

    m = match(r'\[bisher: Identifikationsnummer Hauptsitz: (?P<previous_head_office_id>CH-\d{3}-\d{7}-\d)\]', 'de')
    if m:
        return [event('previous_head_office_identifier_removed', m, previous=True, scope='head_office')], ''

    return [], text
