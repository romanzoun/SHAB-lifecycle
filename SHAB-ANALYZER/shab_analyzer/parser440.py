from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event
from .parser267 import DATE, COUNT, MONEY, UID, NAME
from . import parser55, parser60


def extract_parser440_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete new variants without taking historical clauses."""
    if any(p.search(text) for p in (parser55._FR_STANDALONE_GROUP_SIGNING,
                                    parser60._FR_SHARE_TRANSFER_RESTRICTION)):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', text.strip())
        if m:
            try:
                for date in re.findall(DATE, m[0]):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def result(m, action, event_type='organization_changed', **extra):
        return [_event(*context, event_type, f'{language}.text.{action}.v1',
                       {'action': action, **m.groupdict(), **extra})], ''

    m = match(rf'Die Aktennummer (?P<previous_identifier>CH-\d{{3}}-\d{{7}}-\d) wird durch die Unternehmensidentifikationsnummer \(UID\) (?P<uid>{UID}) ersetzt', 'de')
    if m:
        return result(m, 'file_number_replaced_by_uid')

    m = match(rf"Nuovi buoni di godimento: (?P<count>{COUNT}) buoni di godimento conferiscono il diritto ad una quota dell'utile risultante dal bilancio ed all'avanzo della liquidazione conformemente allo statuto", 'it')
    if m:
        return result(m, 'profit_and_liquidation_participation_certificates', 'capital_changed', profit_right=True, liquidation_surplus_right=True)

    m = match(rf"Capital-actions nouveau: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives \(jusqu'ici (?P<previous_count>{COUNT}) actions de CHF (?P<previous_nominal>{MONEY}), au porteur\)\. L'inscription concernant la communication aux actionnaires est radiée\. Satuts modifiés le (?P<statutes_date>{DATE})")
    if m:
        return result(m, 'registered_shares_communication_deleted_statutes_typo', 'capital_changed', currency='CHF', fully_paid=True, share_kind='nominatives', previous_share_kind='au porteur', shareholder_communication_deleted=True)

    m = match(rf"Rectification: l'inscription no (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) reste titulaire de (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) \(et non de (?P<previous_count>{COUNT}) parts de CHF (?P<previous_nominal>{MONEY}), comme publié\)")
    if m:
        return result(m, 'retained_share_count_corrected', 'capital_changed', currency='CHF')

    m = match(rf'Transfert de patrimoine: Selon contrat du (?P<agreement_date>{DATE}) et avenant du (?P<amendment_date>{DATE}), la société a transféré des actifs pour un montant de CHF (?P<assets>{MONEY}) à la société (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<place>{NAME})\. Contre-prestation: CHF (?P<consideration>{MONEY})')
    if m:
        return result(m, 'asset_transfer_contract_and_amendment', currency='CHF')

    # Earlier name extraction leaves a fragment of the English translation.
    # Consume it only with the complete, adjacent source clause as evidence.
    m = match(r"Par décision du président du Tribunal de l'arrondissement de (?P<court_place>[^,.;]+) du (?P<day>\d{1,2}) (?P<month>janvier) (?P<year>\d{4}), la société a été déclarée dissoute; sa liquidation a été ordonnée selon les dispositions applicables à la faillite\. \. Co in liquidation\)")
    if m:
        clause = text.strip().split(';')[0]
        evidence = re.search(re.escape(clause) + r"; sa liquidation a été ordonnée selon les dispositions applicables à la faillite\. La raison de commerce devient: (?P<name>[^()]+ en liquidation) \((?P<german_name>[^()]+ in Liquidation)\) \((?P<italian_name>[^()]+ in liquidazione)\) \((?P<english_name>[^()]+ Ltd liab\. Co in liquidation)\)\.?$", source_text)
        if evidence:
            try:
                datetime(int(m['year']), 1, int(m['day']))
            except ValueError:
                return [], text
            return result(m, 'court_dissolution_bankruptcy_with_translations', 'status_changed', dissolved=True, bankruptcy_liquidation=True, **evidence.groupdict())
    return [], text
