from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser339_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append complete sample-backed residues; never replace previous events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **{k: v for k, v in m.groupdict().items() if k not in ('name', 'place')}})

    m = match(rf"Par décision du (?P<decision_date>{DATE}), l'assemblée générale a supprimé la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE})", 'fr')
    if m:
        return [event('authorized_capital_clause_removed', m, 'capital_changed')], ''

    m = match(rf"Les administrateurs (?P<name1>{NAME}), désormais à (?P<place1>{NAME}), et (?P<name2>{NAME}), sont nommés liquidateurs Les (?P<count>{COUNT}) actions nominatives de CHF (?P<nominal>{MONEY}), formant l'entier du capital-actions, ne sont plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)", 'fr')
    if m:
        original = leftover.replace('liquidateurs Les', 'liquidateurs avec signature individuelle. Les')
        if original not in source_text:
            return [], leftover
        return [person('administrators_appointed_liquidators', m, m[f'name{i}'], 'Verwaltungsrat und Liquidator', 'Einzelunterschrift', m['place1'] if i == 1 else None) for i in (1, 2)] + [event('registered_share_transfer_restrictions_removed', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Schreibversehen in der CHE-Nummer der übernehmenden Gesellschaft\. Aktiven und Passiven \(Fremdkapital\) gehen infolge Fusion auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\), über\. Die Gesellschaft wird gelöscht', 'de')
    if m:
        return [event('merger_recipient_uid_corrected', m, 'status_changed')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>[^.;]+?) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<share_count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) und Gutschrift von CHF (?P<credit>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_shares_and_credit', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Cognome corretto: (?P<surname>{NAME}), (?P<given_names>{NAME}), da (?P<origin>{NAME}), in (?P<place>{NAME}), con procura collettiva a due', 'it')
    if m:
        return [person('surname_corrected_collective_procuration', m, f"{m['surname']}, {m['given_names']}", signing='Kollektivprokura zu zweien', place=m['place'])], ''

    m = match(rf'\[gestrichen: Die Stiftung wurde mit Verfügung der Aufsichtsbehörde vom (?P<exemption_date>{DATE}) von der Pflicht befreit, eine Revisionsstelle zu bezeichnen\.\]\. Die mit Verfügung der Aufsichtsbehörde vom (?P=exemption_date) gewährte Befreiung von der Revisionsstellenpflicht wird mit Verfügung der Aufsichtsbehörde vom (?P<revocation_date>{DATE}) widerrufen', 'de')
    if m:
        return [event('audit_exemption_revoked', m)], ''

    m = match(rf'\((?P<german_name>[^()]+? in Liquidation)\) \((?P<italian_name>[^()]+? in liquidazione)\) \((?P<english_name>[^()]+? in liquidation)\)\. (?P<name>{NAME}), qui est maintenant à (?P<place>{NAME}), est nommée liquidatrice', 'fr')
    if m:
        if leftover + ' avec signature individuelle' not in source_text:
            return [], leftover
        return [event('liquidation_name_translations', m), person('liquidator_appointed_new_residence', m, m['name'], 'Liquidatorin', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund des Entscheids des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation im Sinne von Art\. 164 Abs\. 1 lit\. d HRegV wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[gestrichen: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft in Anwendung von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('company_reinstated_for_liquidation', m, 'status_changed')], ''

    m = match(rf'La membre du comité (?P<name>{NAME}), nommée trésorière, signe désormais collectivement à deux', 'fr')
    if m:
        return [person('committee_treasurer_collective_signing', m, m['name'], 'Kassierin', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'Vermögensübertragung: Die (?P<transferor>{NAME}), in (?P<transferor_place>{NAME}) \((?P<transferor_uid>{UID})\), überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_cash_consideration', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'(?P<converted_count>{COUNT}) actions nominatives ordiaires de CHF (?P<nominal>{MONEY}) sont désormais privilégiées quant au dividende et au produit de liquidation\. Capital-actions: CHF (?P<capital_integer>{COUNT}), (?P<capital_fraction>\d{{2}}), entièrement libéré, divisé en (?P<ordinary_count>{COUNT}) actions ordinaires de CHF (?P=nominal) et (?P<preferred_count>{COUNT}) actions de CHF (?P=nominal), privilégiées quant au dividende et au produit de liquidation, toutes nominatives', 'fr')
    if m:
        return [event('registered_share_preference_changed', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Vermögensübertragung: Die (?P<transferor>{NAME}) überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<claim_count>{COUNT}) Ansprüche zum Inventarwert von CHF (?P<claim_value>{MONEY}) pro Anspruch an der Anlagegruppe (?P<investment_group>{NAME}) des übernehmenden Rechtsträgers sowie eine Ausgleichszahlung von CHF (?P<cash_adjustment>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_investment_claims', m, 'ownership_changed', currency='CHF')], ''

    return [], leftover
