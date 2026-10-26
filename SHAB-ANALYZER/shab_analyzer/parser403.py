from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from . import parser129, parser143, parser148, parser205, parser208, parser214

NAME = r'[^,;.\[\]\n]+?'
# Reuse existing patterns: their formulations remain owned by the earlier parsers,
# even when callers disable those parsers in isolation tests.
_LEGACY = tuple(p for module in (parser129, parser143, parser148, parser205, parser208, parser214)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser403_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual variants supported by the parser-403 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', evidence=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if evidence:
            source = re.search(r'(?<!\S)' + evidence + r'\.(?:\s|$)', source_text)
            if not source or any(source.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
        try:
            for date in re.findall(DATE, m[0]):
                datetime.strptime(date, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(r'\[Die folgende weitere Adresse wird im Handelsregister gelöscht\]', 'de')
    if m:
        return [event('additional_address_deletion_annotation', m, deleted=True)], ''

    pattern = rf"(?P<name1>{NAME}), d'(?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>[A-Z]{{3}}), président et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), sont membres du conseil d'administration, tous deux"
    m = match(pattern, evidence=pattern + ' avec signature individuelle')
    if m:
        return [person('foreign_board_pair_individual', m, m[f'name{i}'], "président du conseil d'administration" if i == 1 else "membre du conseil d'administration", 'Einzelunterschrift', m[f'place{i}'], origin=m[f'origin{i}'], country=m[f'country{i}']) for i in (1, 2)], ''

    m = match(rf'Mit Verfügung vom (?P<order_date>{DATE}) hat das (?P<court>[^;\n]+?) der Beschwerde gegen den Entscheid des Konkursrichters des (?P<bankruptcy_court>{NAME}) vom (?P<decision_date>{DATE}) betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\. Demnach wird die Eintragung betreffend Konkurs im Handelsregister gestrichen\. \[gestrichen: Über den Inhaber dieses Einzelunternehmens ist mit Entscheid des Konkursrichters des (?P=bankruptcy_court) vom (?P=decision_date) mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<effective_time>\d{{2}}\.\d{{2}}) Uhr der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('sole_trader_bankruptcy_entry_removed_suspensive_effect', m, suspensive_effect=True, bankruptcy_entry_removed=True)], ''

    m = match(rf'Liquidateurs: les associés gérants (?P<name1>{NAME}), maintenant domicilié à (?P<place>{NAME}), président, et (?P<name2>{NAME}), lesquels continuent à signer individuellement')
    if m:
        return [person('manager_pair_becomes_liquidators_residence', m, m[f'name{i}'], 'Liquidator', 'Einzelunterschrift', m['place'] if i == 1 else None, previous_role='associé gérant', signing_continued=True, president=i == 1) for i in (1, 2)], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le nom exact de (?P<previous_name>{NAME}) est (?P<name>{NAME})")
    if m:
        canonical = f"L'inscription no {m['entry']} du {m['entry_date']} est rectifiée en ce sens que le nom exact de {m['previous_name']} est {m['name']}"
        return parser129.extract_parser129_leftovers(canonical, language, *context[:2], *context[2:])

    pattern = rf"L'associée-gérante (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) des ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par (?P<count1>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer1>{NAME}), nouvelle associées-gérante présidente, qui continue à signer individuellement, et par (?P<count2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée-gérante (?P=seller), maintenant à (?P<seller_place>{NAME}), reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)"
    evidence = pattern.replace('nouvelle associée-gérante (?P=seller)', r'nouvelle associée-gérante avec signature individuelle\. (?P=seller)')
    m = match(pattern, evidence=evidence)
    if m:
        n = lambda key: Decimal(m[key].replace("'", ''))
        if n('count1') + n('count2') == n('transferred') and n('remaining') + n('transferred') == n('previous'):
            return [event('manager_share_transfer_two_buyers_typo', m, 'ownership_changed', currency='CHF'), person('new_manager_president_continued_signing', m, m['buyer1'], 'associée-gérante présidente', 'Einzelunterschrift', signing_continued=True), person('new_manager_individual_signing', m, m['buyer2'], 'associée-gérante', 'Einzelunterschrift', m['place']), person('selling_manager_residence_changed', m, m['seller'], 'associée-gérante', place=m['seller_place'])], ''

    pattern = rf"Division de la part de CHF (?P<previous_nominal>{MONEY}) de l'associé (?P<name>{NAME}) en (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY})\. également"
    evidence = pattern.replace(r'\. également', rf'\. Statuts modifiés le {DATE} également sur des points non soumis à publication')
    m = match(pattern, evidence=evidence)
    if m and Decimal(m['previous_nominal'].replace("'", '')) == Decimal(m['count'].replace("'", '')) * Decimal(m['nominal'].replace("'", '')):
        return [event('associate_share_split_non_public_statutes_remainder', m, 'ownership_changed', currency='CHF')], ''

    pattern = rf'Les (?P<count1>{COUNT}) actions nominatives de CHF (?P<nominal1>{MONEY}), privilégiées quant au produit de liquidation, et (?P<count2>{COUNT}) actions nominatives de CHF (?P<nominal2>{MONEY}) ne sont désormais plus restreintes quant à la transmissibilité \(art\. 685a, al\. 3 CO\)\. (?P<name>{NAME}), dont la procuration est éteinte, est élu liquidateur'
    m = match(pattern, evidence=pattern + ' avec signature individuelle')
    if m:
        return [event('two_share_classes_transfer_restrictions_removed', m, 'capital_changed', currency='CHF', transfer_restricted=False, preferred_right='produit de liquidation'), person('proxy_holder_elected_liquidator', m, m['name'], 'Liquidator', 'Einzelunterschrift', procuration_extinguished=True)], ''

    m = match(rf"Par décision du (?P<bankruptcy_date>{DATE}), la (?P<bankruptcy_authority>{NAME}), à (?P<place>{NAME}), a prononcé la faillite du titulaire avec effet au (?P<effective_date>{DATE}), à (?P<effective_time>\d{{2}}\.\d{{2}}) heures\. Par arrêt du (?P<order_date>{DATE}), le (?P<court>Tribunal cantonal de Fribourg) a accordé l'effet suspensif au recours interjeté le (?P<appeal_date>{DATE}) contre la décision du (?P=bankruptcy_date) \(art\. 159, al\. 1 let\. b ORC\)")
    if m:
        return [event('sole_trader_bankruptcy_with_suspensive_appeal', m, suspensive_effect=True, legal_basis='art. 159, al. 1 let. b ORC')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<count>{COUNT}) Ansprüche \(Fondsanteile\) am vertraglichen Immobilienanlagefonds (?P<fund>{NAME}) mit einem Nettoinventarwert \(Buchwert \(KAG\) per (?P<valuation_date>{DATE})\) von CHF (?P<nav>{MONEY}) pro Anspruch, mit Wirkung per (?P<effective_date>\d{{1,2}}\. Januar \d{{4}}), zuzüglich CHF (?P<cash_adjustment>{MONEY}) als Spitzenausgleich durch Barabgeltung', 'de')
    if m:
        try:
            datetime.strptime(m['effective_date'].replace('Januar', '01'), '%d. %m %Y')
        except ValueError:
            return [], text
        return [event('company_asset_transfer_fund_claims_book_value', m, 'assets_transferred', currency='CHF')], ''

    m = match(rf'Urkundendatum richtig: (?P<date>{DATE})', 'de')
    if m:
        return [event('deed_date_corrected_short', m, 'publication_corrected', kind='deed_date', date=datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est originaire de (?P<origin>[^();]+?) \(et non (?P<previous_origin>[^();]+?)\)")
    if m:
        return [person('officer_origin_corrected_short_reference', m, m['name'], corrected=True)], ''
    return [], text
