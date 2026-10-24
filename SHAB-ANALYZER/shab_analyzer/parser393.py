from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from . import parser66, parser68, parser181, parser248

NAME = r'[^,;.\[\]\n]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
_LEGACY = tuple(p for module in (parser66, parser68, parser181, parser248)
                for p in vars(module).values() if isinstance(p, re.Pattern))
REFERENCE = rf"l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\)"


def extract_parser393_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Only complete residual variants; predecessors retain their patterns."""
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
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf"La commandite de l'associé commanditaire (?P<name>{NAME}) est portée de CHF (?P<previous_amount>{COUNT})\.- à CHF (?P<amount>{COUNT})\.-, ses pouvoirs sont radiés")
    if m:
        return [event('limited_partner_contribution_increased_powers_deleted', m, 'capital_changed', currency='CHF'),
                person('limited_partner_powers_deleted', m, m['name'], 'associé commanditaire', 'ohne Zeichnungsberechtigung')], ''

    m = match(rf'(?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent chacun (?P<count>{COUNT}) de leurs (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature, avec (?P<received>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) et (?P=seller2) restent titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal) chacun')
    if m:
        return [event('two_holders_transfer_unsigned_associate', m, currency='CHF'),
                person('new_unsigned_associate_two_sellers', m, m['buyer'], 'associé', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}), dont les procurations sont éteintes, engagement désormais la société par leur signature individuelle')
    if m:
        return [person('three_proxies_replaced_individual_signing_typo', m, m[f'name{i}'], signing='Einzelunterschrift', procuration_extinguished=True) for i in (1, 2, 3)], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>\d{{2}}-\d{{2}}-\d{{4}}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le but est le suivant: (?P<purpose>[^\n]+ \(cf\. statuts pour but complet\))")
    if m:
        try:
            datetime.strptime(m['notice_date'], '%d-%m-%Y')
        except ValueError:
            return [], text
        return [event('purpose_corrected_hyphenated_notice_date', m)], ''

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) mit Nachtrag vom (?P<addendum_date>{DATE}) und Verfügung der Aufsichtsbehörde vom (?P<authority_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine\. Organisation neu: \[Streichung aufgrund geänderter Eintragungsvorschriften\.\]', 'de')
    if m:
        return [event('foundation_asset_transfer_addendum_authority', m, currency='CHF', no_consideration=True, organization_entry_deleted=True)], ''

    m = match(rf"Suite à une fusion de communes, la commune d'origine du titulaire est (?P<origin>{NAME})")
    if m:
        return [event('owner_origin_municipal_merger', m)], ''

    m = match(rf'Trasferimento di patrimonio: secondo contratto del (?P<agreement_date>{DATE}), la società ha trasferito attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY}) alla (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Controprestazione: CHF (?P<consideration>{MONEY})', 'it')
    if m:
        return [event('asset_transfer_cash_consideration', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf'Der am (?P<opening_date>{DATE}) durch die (?P<opening_authority>{NAME}) eröffnete Konkurs der Gesellschaft wird mit Entscheid des (?P<appeal_authority>{NAME}) vom (?P<decision_date>{DATE}) nachträglich aufgehoben', 'de')
    if m:
        return [event('bankruptcy_subsequently_revoked', m, 'status_changed')], ''

    m = match(rf'Par décision du (?P<decision_date>{DATE}) le tribunal a autorisé le sursis concordataire Covid-19 provisoire pour une durée de (?P<months>{COUNT}) mois')
    if m:
        return [event('provisional_covid_moratorium_authorized', m, 'status_changed')], ''

    m = match(rf'Complément: {REFERENCE} est complétée en ce sens que les fondés de procuration (?P<name1>{NAME}), (?P<name2>{NAME}) et (?P<name3>{NAME}) ne peuvent pas signer entre eux')
    if m:
        return [person('proxy_signing_exclusion_notice_completed', m, m[f'name{i}'], excluded_signing_group=[m[f'name{j}'] for j in (1, 2, 3)]) for i in (1, 2, 3)], ''

    m = match(rf"Rectificatif: {REFERENCE} est rectifiée en ce sens que l'augmentation ordinaire du capital-actions a lieu en espèces et par compensation de créances de CHF (?P<claims>{MONEY}) et qu'en contrepartie de ces créances, est remis (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}) \(et non que l'augmentation ordinaire du capital-actions a lieu en espèces et par compensation de créances de CHF (?P<previous_claims>{MONEY}) et qu'en contrepartie de ces créances, est remis (?P<previous_count>{COUNT}) actions de CHF (?P=nominal)\)")
    if m:
        return [event('ordinary_capital_increase_claims_corrected', m, 'capital_changed', currency='CHF')], ''

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) de ses (?P<previous>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvel associé, lequel n'exerce pas la signature sociale")
    if m:
        return [event('share_transfer_domestic_unsigned_associate', m, currency='CHF'),
                person('new_domestic_unsigned_associate', m, m['buyer'], 'associé', 'ohne Zeichnungsberechtigung', m['place'], origin=m['place'])], ''
    return [], text
