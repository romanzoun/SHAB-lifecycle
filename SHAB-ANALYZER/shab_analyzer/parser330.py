from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT

# French written dates occur verbatim in the supplied historical publications.
MONTH = r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)'
WRITTEN_DATE = rf'\d{{1,2}} {MONTH} \d{{4}}'


def extract_parser330_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Append sample-backed events only for complete, bounded remaining clauses."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(r'(?<!\S)' + source_pattern + r'\.?$', source_text)
            if not s or any(s[k] != v for k, v in m.groupdict().items()):
                return None
            m = s
        try:
            months = 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre'.split()
            for k, v in m.groupdict().items():
                if k.endswith('_date'):
                    if re.fullmatch(DATE, v):
                        datetime.strptime(v, '%d.%m.%Y')
                    else:
                        day, month, year = v.split()
                        datetime(int(year), months.index(month) + 1, int(day))
        except (ValueError, TypeError):
            return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role, signing=None, place=None, event_type='officer_changed', **extra):
        return _person_event(*context, event_type, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra, 'name': name.strip(), 'place': place.strip() if place else None})

    m = match(rf"Par jugement du (?P<decision_date>{WRITTEN_DATE}) du (?P<court>{NAME}), un sursis COVID-19 pour une durée de (?P<duration>trois mois), soit jusqu'au (?P<until_date>{WRITTEN_DATE}) a été octroyé\. A été désigné en qualité de commissaire (?P<name>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME})")
    if m:
        return [event('covid_moratorium_commissioner', m, 'status_changed', moratorium_granted=True), person('covid_commissioner_appointed', m, m['name'], 'Sachwalter', place=m['place'])], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'augmentation autorisée du capital-actions selon décision d'autorisation du (?P<authorization_date>{WRITTEN_DATE}) a eu lieu par compensation d'une créance de CHF (?P<claim>{MONEY}) \(et non de CHF (?P<previous_claim>{MONEY}), comme publié\)")
    if m:
        return [event('authorized_capital_offset_corrected', m, 'capital_changed', corrected=True, currency='CHF')], ''

    pattern = rf"L'associée-gérante (?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>FRA), nouvel associé pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal); "
    m = match(pattern + r"n'exerce pas la signature sociale", source_pattern=pattern + r"il n'exerce pas la signature sociale")
    if m:
        if m['transferred'] != m['buyer_count']:
            return [], leftover
        return [event('manager_share_transfer_unsigned_associate', m, 'ownership_changed', currency='CHF'), person('new_foreign_associate_unsigned', m, m['buyer'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', m['place'], without_signing=True)], ''

    m = match(rf"L'assemblée générale a modifié une clause statutaire relative à une augmentation autorisée du capital \(selon décision du (?P<authorization_date>{WRITTEN_DATE}) modifiée en dernier lieu le (?P<previous_decision_date>{WRITTEN_DATE})\) par décision du (?P<decision_date>{WRITTEN_DATE})\. Pour les détails, voir les statuts")
    if m:
        return [event('authorized_capital_clause_amended', m, 'capital_changed')], ''

    m = match(r'\[gestrichen: Geschäftsstelle: (?P<previous_address>[^,;]+), (?P<previous_postal_code>\d{4}) (?P<previous_place>[^.;]+)\.\]\. Geschäftsstelle: (?P<address>[^,;]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+)', 'de')
    if m:
        return [event('business_office_address_replaced', m, 'address_changed', address_kind='Geschäftsstelle')], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée sans signature\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        number = lambda k: int(m[k].replace("'", ''))
        if number('before') - number('transferred') != number('remaining'):
            return [], leftover
        return [event('manager_share_transfer_remaining_unsigned', m, 'ownership_changed', currency='CHF'), person('new_associate_unsigned', m, m['buyer'], 'Gesellschafterin', 'ohne Zeichnungsberechtigung', m['place'], without_signing=True)], ''

    m = match(rf"L'associé gérant (?P<president>{NAME}) a été nommé président\. Nouveaux gérants: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>FRA) et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), lesquels signent individuellement")
    if m:
        return [person('associate_manager_becomes_president', m, m['president'], 'Gesellschafter, Geschäftsführer, Präsident')] + [person('new_managers_individual', m, m[f'name{i}'], 'Geschäftsführer', 'Einzelunterschrift', m[f'place{i}']) for i in (1, 2)], ''

    pattern = rf"Rectificatif: l'inscription n°(?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le capital est exactement divisé en (?P<count1>{COUNT}) actions nominatives de CHF (?P<nominal1>{MONEY}), (?P<count2>{COUNT}) actions nominatives (?P<class2>A0) de CHF (?P<nominal2>{MONEY}), privilégiées quant au produit de liquidation, et (?P<count3>{COUNT}) actions nominatives (?P<class3>A) de CHF (?P<nominal3>{MONEY}), privilégiées quant au produit de liquidation, toutes"
    m = match(pattern, source_pattern=pattern + r' avec restrictions quant à la transmissibilité selon statuts')
    if m:
        return [event('three_registered_share_classes_corrected', m, 'capital_changed', corrected=True, currency='CHF', preferred_rights='produit de liquidation')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) des (?P<court>{NAME}) wurde eine COVID-19-Stundung für (?P<duration>3 Monate) bis am (?P<until_date>{DATE}) bewilligt', 'de')
    if m:
        return [event('covid_moratorium_granted', m, 'status_changed', moratorium_granted=True)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le capital de CHF (?P<capital>{MONEY}) est entièrement libéré")
    if m:
        return [event('fully_paid_capital_corrected', m, 'capital_changed', corrected=True, fully_paid=True, currency='CHF')], ''

    pattern = rf"L'associée-gérante (?P<seller>{NAME}) a cédé à concurrence de (?P<transferred1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer1>{NAME}), jusqu'ici directrice, nouvelle associée pour (?P<buyer_count1>{COUNT}) parts de CHF (?P=nominal), et à concurrence de (?P<transferred2>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer2>{NAME}), du (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé pour (?P<buyer_count2>{COUNT}) parts de CHF (?P=nominal)\. Gérants: les associés (?P=seller), présidente, (?P=buyer1) et (?P=buyer2), tous les trois"
    m = match(pattern, source_pattern=pattern + r' avec signature individuelle')
    if m:
        if any(m[f'transferred{i}'] != m[f'buyer_count{i}'] for i in (1, 2)):
            return [], leftover
        return [event('two_share_transfers_individual_managers', m, 'ownership_changed', currency='CHF'), person('associate_manager_president_individual', m, m['seller'], 'Gesellschafterin, Geschäftsführerin, Präsidentin', 'Einzelunterschrift'), person('director_becomes_associate_manager', m, m['buyer1'], 'Gesellschafterin, Geschäftsführerin', 'Einzelunterschrift', previous_role='Direktorin'), person('new_associate_manager_individual', m, m['buyer2'], 'Gesellschafter, Geschäftsführer', 'Einzelunterschrift', m['place2'])], ''

    m = match(rf"Procuration individuelle a été conférée à (?P<name1>{NAME}), ainsi qu'à (?P<name2>{NAME}), toutes deux de (?P<origin>{NAME}), à (?P<place>{NAME})")
    if m:
        return [person('two_individual_procurations', m, m[f'name{i}'], 'Prokurist', 'Einzelprokura', m['place'], event_type='signing_authority_changed') for i in (1, 2)], ''

    return [], leftover
