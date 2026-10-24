from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY
from . import parser111, parser138, parser150, parser152, parser161, parser213, parser260

NAME = r'[^,;.\[\]]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
# Reuse earlier patterns even when the earlier extractor is disabled in isolation.
_LEGACY = tuple(p for module in (parser111, parser138, parser150, parser152, parser161, parser213, parser260) for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser390_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Narrow residual variants; existing events and rule ownership are preserved."""
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

    def person(action, m, name, role, signing, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'(?P<name>{NAME}), maintenant de (?P<origin>{NAME}), dont la procuration est éteinte, est nommé membre de la direction et engage désormais la société par sa signature collective à deux')
    if m:
        return [person('proxy_revoked_management_new_origin', m, m['name'], 'membre de la direction', 'Kollektivunterschrift zu zweien', procuration_revoked=True)], ''
    m = match(rf'Nouvelle personne incrite: (?P<name>[^()]+) \((?P<uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), à (?P<place>{NAME}), organe de révision\. La clause de renonciation au contrôle restreint du (?P<waiver_date>{DATE}) est abrogée')
    if m:
        return [event('auditor_appointed_waiver_repealed_typo', m, waiver_repealed=True)], ''
    m = match(rf'(?P<seller1>{NAME}), (?P<seller2>{NAME}) et (?P<seller3>{NAME}) cèdent chacun (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant avec (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) reste titulaire de (?P<remaining1>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller2) et (?P=seller3) restent titulaires de (?P<remaining23>{COUNT}) parts de CHF (?P=nominal) chacun')
    if m:
        return [event('three_associates_transfer_remaining_holdings', m, currency='CHF')], ''
    m = match(rf"Con delibera del (?P<decision_date>{DATE}) l'assemblea generale ha introdotto una clausola statutaria relativa ad un aumento autorizzato del capitale azionario\. Per i dettagli si veda lo statuto\. \[finora: Con delibera del (?P<previous_date>{DATE}) l'assemblea generale ha introdotto una clausola statutaria relativa ad un aumento autorizzato del capitale azionario\. Per i dettagli si veda lo statuto\.\]", 'it')
    if m:
        return [event('authorized_capital_clause_replaced', m, 'capital_changed')], ''
    m = match(rf'Organe de révision: (?P<name>[^()]+) \(CHE(?P<uid_digits>\d{{3}}\.\d{{3}}\.\d{{3}})\), à (?P<place>{NAME})')
    if m:
        return [event('auditor_uid_missing_hyphen', m, uid='CHE-' + m['uid_digits'])], ''
    m = match(rf'Mit Verfügung des Gerichtspräsidiums (?P<court_place>{NAME}) vom (?P<decision_date>{DATE}) wurde die Nachlassstundung aufgehoben\. \[gestrichen: Mit Verfügung vom (?P<previous_date>{DATE}) hat das Gerichtspräsidium (?P=court_place) im summarischen Verfahren eine definitive Nachlassstundung von (?P<months>\d+) Monaten gewährt\.\]', 'de')
    if m:
        return [event('composition_moratorium_lifted_previous_order', m, 'status_changed')], ''
    m = match(r"Prestations accessoires, droits de préférence, de préemption ou d'emption: selon statuts")
    if m:
        return [event('ancillary_obligations_preference_rights_statutes', m)], ''
    m = match(rf"(?P<seller>{NAME}) associé-gérant, maintenant également président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) au nouvel associé-gérant (?P<buyer>{NAME}), jusqu'ici directeur")
    if m:
        return [event('share_transfer_manager_president_former_director', m, currency='CHF'), person('associate_manager_now_president', m, m['seller'], 'associé-gérant et président', None), person('director_now_associate_manager', m, m['buyer'], 'associé-gérant', None, previous_role='directeur')], ''
    m = match(rf"(?P<statutes_date>{DATE})\. Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<authorization_date>{DATE}) \. \[biffé: Augmentation ordinaire du capital-actions\]")
    if m:
        return [event('authorized_capital_clause_removed_residual', m, 'capital_changed')], ''
    m = match(rf'Bemerkungen zum Hauptsitz neu: Mit Entscheid vom (?P<decision_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, hat der (?P<court>{NAME}) über die Gesellschaft "(?P<company>[^"\n]+)" den Konkurs eröffnet', 'de')
    if m:
        if int(m['time'][:2]) > 23 or int(m['time'][3:]) > 59:
            return [], text
        return [event('head_office_bankruptcy_opened_timed', m, 'status_changed', scope='head_office')], ''
    m = match(rf"L'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}), page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le gérant (?P<name>{NAME}) dispose de la signature individuelle \(et non: signature collective à deux\)")
    if m:
        return [person('manager_individual_signing_corrected_notice', m, m['name'], 'gérant', 'Einzelunterschrift', previous_signing='Kollektivunterschrift zu zweien')], ''
    m = match(r'Sede principale a: Sede principale: (?P<head_office>[^.\[\]]+)\. Nuove osservazioni della sede principale: \[radiati: Osservazioni della sede principale: Altro indirizzo: (?P<previous_address>[^,\[\]]+), (?P<postal_code>\d{4}) (?P<place>[^.\[\]]+)\.\]', 'it')
    if m:
        return [event('head_office_other_address_deleted', m, scope='head_office')], ''
    return [], text
