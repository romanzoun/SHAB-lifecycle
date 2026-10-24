from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY
from . import parser152, parser199, parser200, parser234, parser50, parser51, parser55, parser57, parser59, parser99, parser253, parser355, parser361, parser374, parser377, parser380

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
_LEGACY = tuple(p for module in (parser152, parser199, parser200, parser234, parser50, parser51, parser55, parser57, parser59, parser99, parser253, parser355, parser361, parser374, parser377, parser380) for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser389_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded fixture variants; earlier compiled rules retain ownership."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m or (source and not re.search(source(m), source_text)):
            return None
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

    m = match(rf'Nouveau membre du conseil de fondation avec le/la président\(e\) ou le/la vice-président\(e\): (?P<name>{NAME}), de et à (?P<place>{NAME})', source=lambda m: re.escape('Nouveau membre du conseil de fondation avec signature collective à deux avec le/la président(e) ou le/la vice-président(e): ' + m['name'] + ', de et à ' + m['place']) + r'\.')
    if m:
        return [person('foundation_member_gendered_signing_restriction', m, m['name'], 'membre du conseil de fondation', 'Kollektivunterschrift zu zweien', place=m['place'], signing_restriction='avec le/la président(e) ou le/la vice-président(e)')], ''

    m = match(rf'Liquidateurs: les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}), lesquels signent désormais individuellement')
    if m:
        return [person('administrator_liquidator_now_individual_signing', m, m[f'name{i}'], 'administrateur', 'Einzelunterschrift', liquidator=True) for i in (1, 2)], ''

    m = match(rf'Procuration collective à deux est conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), à (?P<place2>{NAME}), toutes deux de (?P<origin>{NAME})')
    if m:
        return [person('two_proxies_shared_origin', m, m[f'name{i}'], 'Prokurist', 'Kollektivprokura zu zweien', place=m[f'place{i}']) for i in (1, 2)], ''

    m = match(rf'Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Neue Firma: (?P<company>[^()]+? in Liq\.) \((?P<french_name>[^()]+ en liq\.)\) \((?P<english_name>[^()]+ in liq\.)\)', 'de')
    if m:
        return [event('company_dissolved_abbreviated_translated_names', m, 'status_changed', in_liquidation=True)], ''

    m = match(rf"(?P<preferred>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives, , sont désormais privilégiées quant au produit de liquidation\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=preferred) actions de CHF (?P=nominal) privilégiées quant au produit de liquidation, et (?P<ordinary>{COUNT}) actions de CHF (?P=nominal), toutes nominatives, liées selon statuts\. Administration: (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]), et (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME})\. Signature individuelle du président ou collective à deux des deux autres membres du conseil d'administration")
    if m:
        return [event('registered_shares_liquidation_preference_and_board', m, 'capital_changed', currency='CHF', fully_paid=True, transfer_restricted=True)] + [person('board_member_differentiated_signing', m, m[f'name{i}'], 'président' if i == 1 else 'administrateur', 'Einzelunterschrift' if i == 1 else 'Kollektivunterschrift zu zweien', **({'place': m[f'place{i}']} if i > 1 else {})) for i in (1, 2, 3)], ''

    m = match(rf'(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer>{NAME})\. Associés: (?P=seller) et (?P=buyer) chacun pour (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('share_transfer_equal_remaining_holdings', m, currency='CHF')], ''

    m = match(rf'Liquidateurs: les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}), lesquels signent individuellement; les pouvoirs du dernier sont modifiés en ce sens')
    if m:
        return [person('administrator_liquidator_last_powers_changed', m, m[f'name{i}'], 'administrateur', 'Einzelunterschrift', liquidator=True, powers_changed=i == 2) for i in (1, 2)], ''

    m = match(rf"Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}) sont désormais \. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) actions de CHF (?P=nominal), nominatives, liées selon statuts", source=lambda m: re.escape(f"Les {m['count']} actions nominatives de CHF {m['nominal']} sont désormais liées selon statuts."))
    if m:
        return [event('registered_shares_now_transfer_restricted', m, 'capital_changed', currency='CHF', fully_paid=True, transfer_restricted=True)], ''

    m = match(rf'Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) wird das Aktienkapital von CHF (?P<previous>{MONEY}) durch Vernichtung von (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) auf CHF (?P<reduced>0\.00) herabgesetzt\. Gleichzeitig wird das Aktienkapital wieder auf CHF (?P=previous) erhöht durch Ausgabe von (?P=count) Namenaktien zu CHF (?P=nominal)', 'de')
    if m:
        return [event('capital_reduction_zero_simultaneous_restoration', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"(?P<name1>{NAME}), nommée présidente, (?P<name2>{NAME}), nommé vice-président, et (?P<name3>{NAME}), jusqu'ici président, nommé secrétaire, membres du conseil de fondation, continuent de signer collectivement à deux")
    if m:
        return [person('foundation_council_roles_continued_signing', m, m[f'name{i}'], role, 'Kollektivunterschrift zu zweien') for i, role in ((1, 'présidente'), (2, 'vice-président'), (3, 'secrétaire'))], ''

    m = match(rf'Signature collective à deux, limitée à la succursale, est conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('two_branch_limited_collective_signatories', m, m[f'name{i}'], None, 'Kollektivunterschrift zu zweien', place=m[f'place{i}'], signing_restriction='limitée à la succursale') for i in (1, 2)], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici directeur, nommé administrateur et président, signe désormais individuellement")
    if m:
        return [person('director_appointed_administrator_president', m, m['name'], 'administrateur et président', 'Einzelunterschrift', previous_role='directeur')], ''
    return [], text
