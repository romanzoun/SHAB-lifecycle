from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from .parser107 import _DE_CONDITIONAL_CAPITAL_CLAUSE_REPEALED_EXPIRED_RIGHTS
from .parser137 import _FR_SOCIAL_SHARE_SPLIT_FOR_MANAGER
from .parser120 import _FR_DIRECTOR_NAME_CORRECTED

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'


def extract_parser386_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Only the bounded variants attested by the version 386 fixtures."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in (
        _DE_CONDITIONAL_CAPITAL_CLAUSE_REPEALED_EXPIRED_RIGHTS,
        _FR_SOCIAL_SHARE_SPLIT_FOR_MANAGER, _FR_DIRECTOR_NAME_CORRECTED,
    )):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='de'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for date in re.findall(DATE, leftover):
                    datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, kind='organization_changed', **extra):
        return _event(*context, kind, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=extra.get('place'), role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'Fusion: Die Gesellschaft entsteht aus der Kombinationsfusion der (?P<source1>{NAME}), in (?P<place1>{NAME}) \((?P<uid1>{UID})\), und der (?P<source2>{NAME}), in (?P<place2>{NAME}) \((?P<uid2>{UID})\) gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanzen per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets1>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities1>{MONEY}) der (?P=source1) sowie Aktiven von CHF (?P<assets2>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities2>{MONEY}) der (?P=source2) gehen auf die Gesellschaft über\. Die Gesellschafter der übertragenden Gesellschaften erhalten (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY})')
    if m:
        return [event('combination_merger_two_transferors', m, currency='CHF')], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}) et (?P<name4>{NAME}), associés-gérants, sont liquidateurs', 'fr')
    if m:
        if not source_text.endswith(leftover.rstrip('.') + ' avec signature collective à deux.'):
            return [], text
        return [person('four_associate_manager_liquidators', m, m[f'name{i}'], 'associé-gérant liquidateur', 'Kollektivunterschrift zu zweien') for i in range(1, 5)], ''

    m = match(rf'\[Streichung der Statutenbestimmung über die mit Gewährungsbeschluss vom (?P<introduced_date>{DATE}) eingeführte bedingte Kapitalerhöhung infolge Erlöschens der Wandelrechte\.\] \. Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) eine bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen')
    if m:
        return [event('conditional_capital_expired_clause_replaced', m)], ''

    m = match(rf"Division de la part sociale de CHF (?P<previous_nominal>{MONEY}) de (?P<seller>{NAME}) en (?P<count>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY})\. Prestations accessoires, droits de préférence, de préemption ou d'emption: selon statuts\. (?P=seller), maintenant domicilié à (?P<place>{NAME}), a cédé (?P<transferred>{COUNT}) de ses (?P=count) parts sociales de CHF (?P=nominal) à (?P<buyer>{NAME}), nouvelle associée\. Gérants: (?P=seller), nommé président, et (?P=buyer), lesquels signent désormais collectivement à deux", 'fr')
    if m:
        number = lambda key: Decimal(m[key].replace("'", ''))
        if number('previous_nominal') != number('count') * number('nominal') or not 0 < number('transferred') < number('count'):
            return [], text
        return [event('share_split_transfer_new_associate', m, currency='CHF'), person('seller_manager_president_collective', m, m['seller'], 'gérant président', 'Kollektivunterschrift zu zweien', place=m['place']), person('buyer_manager_collective', m, m['buyer'], 'gérante', 'Kollektivunterschrift zu zweien')], ''

    m = match(rf'\[gestrichen: (?P<previous_date>{DATE})\]')
    if m:
        source = re.search(rf'Statutenänderung: (?P<statutes_date>{DATE}) \[gestrichen: {re.escape(m["previous_date"])}\]\.$', source_text)
        if not source:
            return [], text
        try:
            datetime.strptime(source['statutes_date'], '%d.%m.%Y')
        except ValueError:
            return [], text
        return [event('statutes_date_deleted_correction', m, 'publication_corrected', statutes_date=source['statutes_date'])], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund des Entscheids des zuständigen Einzelgerichts vom (?P<decision_date>{DATE}) zum Zwecke der Liquidation im Sinne von Art\. 164 Abs\. 1 lit\. d HRegV wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft in Anwendung von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]')
    if m:
        return [event('reinstatement_liquidation_article164', m, 'status_changed')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die (?P<recipient>{NAME}), (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})')
    if m:
        return [event('asset_transfer_assets_only_cash', m, currency='CHF')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom exact de l'administratrice est (?P<name>{NAME}) \(et non (?P<previous_name>{NAME}), comme publié\)", 'fr')
    if m:
        return [event('administrator_female_name_corrected_notice', m, 'publication_corrected')], ''

    m = match(rf'Das Konkursverfahren ist mit Verfügung des Einzelrichters des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) mangels Aktiven eingestellt worden')
    if m:
        return [event('bankruptcy_suspended_single_judge_order', m, 'status_changed')], ''

    m = match(rf"La société est dissoute au siège principal; par conséquent la raison sociale de la succursale devient: (?P<branch_name>[^;\[\]]+?)\. Nouvelle raison sociale et nouveau numéro d'identification du siège principal: (?P<head_office_name>[^;\[\]]+?) \((?P<head_office_uid>{UID})\)", 'fr')
    if m:
        return [event('branch_head_office_dissolved_name_uid', m, 'status_changed', dissolved_at_head_office=True)], ''

    # This German clause is attested in a publication marked French.
    m = match(rf'Eingetragene Personen geändert: (?P<name>{NAME}), Kollektivunterschrift zu zweien, neu Einzelunterschrift', 'fr')
    if m:
        return [person('officer_plural_header_individual_signing', m, m['name'], None, 'Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Mit Verfügung des Gerichtspräsidiums (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) ist über diese Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, der Konkurs eröffnet worden')
    if m:
        return [event('bankruptcy_opened_presidency_dot_time', m, 'status_changed')], ''
    return [], text
