from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser409 import NAME
from . import parser60, parser63, parser95, parser120, parser143, parser151, parser194, parser223, parser228

# Historical compiled patterns retain ownership, also in isolated rule tests.
_LEGACY = tuple(p for module in (parser60, parser63, parser95, parser120, parser143, parser194, parser223, parser228)
                for p in vars(module).values() if isinstance(p, re.Pattern)) + (parser151._DE_COMPOSITION_AGREEMENT_WITH_REMOVED_MORATORIUM,)


def extract_parser423_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete, sample-backed residual clauses; preserve unknown input."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY):
        return [], text
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language not in ((lang,) if isinstance(lang, str) else lang):
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

    m = match(rf'Mit Verfügung des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde das Konkursbegehren aufgehoben\. Infolgedessen besteht die Gesellschaft entsprechend den früheren Eintragungen weiter\. \[bisher: Mit Verfügung des (?P<previous_court>{NAME}) vom (?P<previous_date>{DATE}) ist über diese Gesellschaft mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>(?:[01]\d|2[0-3])\.[0-5]\d) Uhr, der Konkurs eröffnet worden\.\]', 'de')
    if m:
        return [event('bankruptcy_petition_revoked_company_continues', m, 'status_changed', continues=True)], ''

    m = match(rf'Die Gesellschaft wird gemäss Verfügung des (?P<court>{NAME}), in (?P<court_place>{NAME}), vom (?P<decision_date>{DATE}) wieder in das Handelsregister eingetragen, die am (?P<suspension_date>{DATE}) angeordnete Einstellung des Konkursverfahrens aufgehoben und die Wiederaufnahme des Konkursverfahrens angeordnet\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung der Gesellschaft erhoben wurde, wird diese im Sinne von Art\. 159 Abs\. 5 lit\. a HRegV von Amtes wegen gelöscht\.\]', 'de')
    if m:
        return [event('company_reinstated_bankruptcy_resumed', m, 'status_changed', reinstated=True, bankruptcy_resumed=True)], ''

    m = match(rf'Sede principale a: (?P<head_office_place>{NAME}) \((?P<country>[A-Z]{{2}})\)\. Numero di identificazione della sede principale: (?P<head_office_id>[A-Z]{{2}} [A-Z0-9]+)', 'it')
    if m:
        return [event('foreign_head_office_place_identifier', m)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le nom exact de (?P<previous_name>{NAME}) est: (?P<name>{NAME})")
    if m:
        return [person('person_exact_name_corrected_notice_space', m, m['name'], corrected=True)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), jusqu'ici directeur, et (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), lesquels signent individuellement")
    if m:
        return [person('three_board_members_president_former_director', m, m['name1'], 'président', 'Einzelunterschrift'),
                person('three_board_members_president_former_director', m, m['name2'], 'administrateur', 'Einzelunterschrift', previous_role='directeur'),
                person('three_board_members_president_former_director', m, m['name3'], 'administrateur', 'Einzelunterschrift', m['place3'])], ''

    # The supplied German clause carries French publication metadata.
    m = match(rf'Mit Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde der Nachlassvertrag mit Dividendenvergleich genehmigt\. Die bisherige Sachwalterin wird mit dem Vollzug des Nachlassvertrages beauftragt\. Gelöschte Person: (?P<name>{NAME}) \((?P<administrator_uid>{UID})\), Sachwalterin bei Stundung', ('de', 'fr'))
    if m:
        return [event('composition_dividend_agreement_execution', m, 'status_changed', agreement_type='Dividendenvergleich'),
                person('composition_administrator_execution_assignment', m, m['name'], 'Vollzug des Nachlassvertrages', previous_role='Sachwalterin bei Stundung')], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_page>\d+)\) est rectifiée en ce sens que la dernière modification statutaire date du (?P<statutes_date>{DATE}) \(et non le (?P<previous_statutes_date>{DATE}) comme publié\)")
    if m:
        return [event('statutes_last_amendment_date_corrected', m, corrected=True)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), nommée présidente et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})')
    if m:
        return [person('board_president_and_member_without_signing', m, m['name1'], 'présidente'),
                person('board_president_and_member_without_signing', m, m['name2'], 'administrateur', place=m['place2'])], ''

    m = match(rf'Administration: (?P<name1>{NAME}), de et à (?P<place1>{NAME}), présidente et (?P<name2>{NAME}), maintenant domicilié à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}}), lesquels signent individuellement')
    if m:
        return [person('board_president_member_foreign_residence', m, m['name1'], 'présidente', 'Einzelunterschrift', m['place1']),
                person('board_president_member_foreign_residence', m, m['name2'], 'administrateur', 'Einzelunterschrift', m['place2'])], ''

    m = match(rf'Das (?P<court>{NAME}) hat mit Entscheid vom (?P<decision_date>{DATE}) die Wiedereintragung der am (?P<deletion_date>{DATE}) gelöschten Gesellschaft in das Handelsregister angeordnet, (?P<name>{NAME}), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place>{NAME}), als Liquidator eingesetzt und folgende Adresse als Liquidationsadresse bestimmt: (?P<liquidation_address>c/o {NAME}, {NAME} \d+[a-z]?, \d{{4}} {NAME})', 'de')
    if m:
        return [event('court_reinstatement_liquidation_address', m, 'status_changed', reinstated=True),
                person('court_reinstatement_liquidator_appointed', m, m['name'], 'Liquidator', place=m['place']),
                event('court_liquidation_address_determined', m, 'address_changed')], ''

    m = match(rf'\((?P<german_name>[^()\n]+ in Liquidation)\) \((?P<english_name>[^()\n]+ in liquidation)\)\. Liquidateurs: (?P<name1>{NAME}), gérant et président, et (?P<name2>{NAME}), gérant, lesquels continuent à signer individuellement')
    if m:
        return [event('liquidation_translations_manager_president_pair', m),
                person('manager_president_liquidators_individual', m, m['name1'], 'liquidateur', 'Einzelunterschrift', previous_role='gérant et président'),
                person('manager_president_liquidators_individual', m, m['name2'], 'liquidateur', 'Einzelunterschrift', previous_role='gérant')], ''

    m = match(rf'(?P<seller>{NAME}) a cédé (?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME})\. Associés: (?P=seller) et (?P=buyer) pour (?P<holding>{COUNT}) parts de CHF (?P=nominal) chacun')
    if m:
        return [event('share_transfer_equal_holdings_after_transfer', m, 'ownership_changed', currency='CHF')], ''
    return [], text
