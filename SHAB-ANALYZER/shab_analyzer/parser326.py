from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, UID


def extract_parser326_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize complete residual clauses without replacing existing events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date') and value is not None:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, role, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m['name'], place=m.groupdict().get('place'), role=role, signing=signing, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf'(?P<name>{NAME}), administrateur-président, est nommé liquidateur')
    if m:
        return [person('administrator_president_appointed_liquidator', m, 'Liquidator', previous_role='administrateur-président')], ''

    m = match(rf'Nouvel administrateur: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{3}}), président')
    if m:
        return [person('foreign_resident_administrator_president_appointed', m, 'Verwaltungsratspräsident')], ''

    m = match(rf"Vermögensübertragung: Der Geschäftsinhaber überträgt gemäss Vermögensübertragungsvertrag vom (?P<agreement_date>{DATE}) und Inventarliste per (?P<inventory_date>{DATE}) Aktiven \(inklusive des darin enthaltenden Grundstücks (?P<property_reference>[^()]+)\) von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient_name>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<shares>[\d']+) Namenaktien zu CHF (?P<nominal>{MONEY}) und eine Gutschrift als Forderung von CHF (?P<receivable>{MONEY})", 'de')
    if m:
        return [event('asset_transfer_with_property_and_shares', m, 'ownership_changed', currency='CHF')], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_reference>\d+/\d+)\) est complétée par la radiation de la mention relative à la renonciation au contrôle restreint")
    if m:
        return [event('audit_waiver_mention_removed', m, 'audit_requirement_changed', waiver_mention_removed=True)], ''

    m = match(rf'Der Organisationsmangel wurde innert Frist behoben, woraufhin das (?P<court>{NAME}) mit Verfügung vom (?P<decision_date>{DATE}) das Verfahren als erledigt abgeschrieben hat', 'de')
    if m:
        return [event('organization_defect_proceedings_closed', m, defect_remedied=True, proceedings_closed=True)], ''

    m = match(rf'Nouvel associé indéfinimment responsable: (?P<name>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), lequel signe individuellement')
    if m:
        return [person('unlimited_partner_appointed_individual_signing', m, 'unbeschränkt haftender Gesellschafter', 'Einzelunterschrift')], ''

    m = match(rf"L'entreprise individuelle est radiée, les actifs et passifs ayant été apportés à la société (?P<recipient_name>{NAME}) \((?P<recipient_uid>{UID})\), à (?P<recipient_place>{NAME})")
    if m:
        return [event('sole_proprietorship_deleted_after_contribution', m, 'company_deleted', assets_and_liabilities_contributed=True)], ''

    m = match(rf"Nuova ditta: (?P<liquidation_name>{NAME}) in liquidazione\. Con decisione del (?P<decision_date>{DATE}) la (?P<court>Camera di esecuzione e fallimenti del Tribunale d'appello del Cantone Ticino) ha respinto il reclamo contro la decisione di apertura del fallimento della (?P<lower_court>Pretura del Distretto di Mendrisio-Sud) del (?P<opening_date>{DATE})\. Il fallimento è quindi stato riaperto con effetto a partire dal (?P<reopening_date>{DATE}) alle ore (?P<reopening_time>(?:[01]\d|2[0-3]):[0-5]\d)\. La società è pertanto sciolta\. \[finora: Con decreto del (?P<suspension_date>{DATE}) la (?P=court) ha accordato effetto sospensivo al reclamo inoltrato contro la decisione di apertura del fallimento della (?P=lower_court) del (?P=opening_date)\. L'iscrizione nel registro di commercio relativa allo scioglimento della società a seguito di fallimento viene pertanto cancellata\.\]", 'it')
    if m:
        return [event('bankruptcy_reopened_after_appeal_rejected', m, 'status_changed', bankruptcy_reopened=True, appeal_rejected=True, dissolved=True)], ''

    m = match(rf"Transfert de patrimoine: elon contrat du (?P<agreement_day>\d{{1,2}}) juin (?P<agreement_year>\d{{4}}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à (?P<recipient_name>{NAME}), à (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: (?P<shares>\d+) parts de CHF (?P<nominal>{MONEY}) et une créance de CHF (?P<receivable>{MONEY})")
    if m:
        try:
            agreement_date = datetime(int(m['agreement_year']), 6, int(m['agreement_day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('asset_transfer_shares_and_receivable', m, 'ownership_changed', currency='CHF', agreement_date=agreement_date)], ''

    m = match(rf'\[Die Statutenänderung vom (?P<removed_date>{DATE}) wurde irrtümlich eingetragen und wird aus dem Handelsregistereintrag gestrichen\. Die Gesellschaft beschloss an diesem Datum keine Statutenänderung\. Es gelten nach wie vor die Statuten vom (?P<effective_date>{DATE})\.\]', 'de')
    if m:
        return [event('erroneous_statutes_amendment_removed', m, erroneous_entry_removed=True)], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), et (?P<name3>{NAME}) continuent à signer collectivement à deux, désormais avec (?P<partner1>{NAME})\. (?P<name4>{NAME}), désormais à (?P<place4>{NAME}), (?P<name5>{NAME}), et (?P<name6>{NAME}) continuent à signer collectivement à deux, désormais avec (?P<partner2>{NAME}) ou (?P<partner3>{NAME})')
    if m:
        events = []
        for i in range(1, 7):
            partners = [m['partner1']] if i <= 3 else [m['partner2'], m['partner3']]
            events.append(_person_event(*context, 'signing_authority_changed', 'fr.text.collective_signing_partners_changed.v1', m[f'name{i}'], place=m['place4'] if i == 4 else None, signing='Kollektivunterschrift zu zweien', extra={'action': 'collective_signing_partners_changed', 'name': m[f'name{i}'], 'signing_partners': partners}))
        return events, ''

    return [], leftover
