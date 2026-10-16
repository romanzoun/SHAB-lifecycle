from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser333_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Add complete sample-backed clauses after all existing parsers."""
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
        return _event(*context, kind, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) au nouvel associé (?P<buyer1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}) et (?P<count2>{COUNT}) parts de CHF (?P=nominal) au nouvel associé (?P<buyer2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>[A-Z]{{3}})\. Par conséquent, (?P=seller) est désormais titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)\. Signature collective à deux a été conférée aux nouveaux associés-gérants (?P=buyer1) et (?P=buyer2)", 'fr')
    if m:
        return [event('shares_transferred_two_new_managers', m, 'ownership_changed', currency='CHF'), *[person('new_associate_manager_collective_signing', m, m[f'buyer{i}'], 'Gesellschafter und Geschäftsführer', 'Kollektivunterschrift zu zweien', m[f'place{i}']) for i in (1, 2)]], ''

    m = match(rf"Administration: (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président, et (?P<name2>{NAME}), jusqu'ici président, nommé secrétaire, lesquels continuent de signer individuellement", 'fr')
    if m:
        return [person('board_president_secretary_exchanged', m, m[f'name{i}'], role, 'Einzelunterschrift', previous_role=previous) for i, role, previous in [(1, 'Verwaltungsrat, Präsident', 'Sekretär'), (2, 'Verwaltungsrat, Sekretär', 'Präsident')]], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<recipient_place>{NAME})\. Gegenleistung: Keine', 'de')
    if m:
        return [event('company_asset_transfer_no_consideration', m, 'ownership_changed', currency='CHF', no_consideration=True)], ''

    m = match(rf'Genussscheine neu: \[Die Genussscheine sind aufgehoben worden\.\] \[gestrichen: Genussscheine: Es sind (?P<previous_count>{COUNT}) Genussscheine ausgegeben, welche Anspruch auf Anteil am Reingewinn gemäss näherer Umschreibung in den Statuten gewähren\.\]', 'de')
    if m:
        return [event('participation_certificates_cancelled', m, 'capital_changed')], ''

    m = match(r'Zweigniederlassung neu: \[gestrichen: (?P<place>[^()\[\]]+) \((?P<branch_uid>CHE-\d{3}\. ?\d{3}\.\d{3})\)\]', 'de')
    if m:
        # The earlier parser removes the explicit closure sentence: retain only
        # the register deletion evidenced by this residue, with the UID verbatim.
        return [event('branch_uid_register_entry_removed', m)], ''

    m = match(rf'Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) wird der Nennwert der (?P<count>{COUNT}) Namenaktien zu CHF (?P<previous_nominal>{MONEY}) auf CHF (?P<nominal>{MONEY}) herabgesetzt und je CHF (?P<repayment>{MONEY}) pro Aktie zurückbezahlt', 'de')
    if m:
        number = lambda k: Decimal(m[k].replace("'", ''))
        if number('previous_nominal') - number('nominal') != number('repayment') or number('repayment') <= 0:
            return [], leftover
        return [event('registered_share_nominal_reduced_repaid', m, 'capital_changed', currency='CHF')], ''

    m = match(rf'Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale sociale delle due società è detenuta dallo stesso socio, la fusione avviene dunque senza aumento del capitale e senza attribuzione di quote sociali', 'it')
    if m:
        return [event('merger_common_member_no_capital_increase', m, 'company_merged', currency='CHF', capital_increase=False, share_allocation=False)], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}) sont maintenant domiciliées à (?P<place>{NAME})', 'fr')
    if m:
        return [person('officer_residence_changed', m, m[f'name{i}'], place=m['place']) for i in (1, 2)], ''

    m = match(rf'Nouveau gérant: (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), sans signature', 'fr')
    if m:
        return [person('new_manager_without_signing', m, m['name'], 'Geschäftsführer', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(r'Nuove traduzioni della ditta: \[Le traduzioni sono radiate dal Registro di commercio\]', 'it')
    if m:
        return [event('company_name_translations_removed', m)], ''

    m = match(r'Zweigniederlassung gestrichen: (?P<place>(?:St\. )?[^.\[\];]+?)', 'de')
    if m:
        return [event('branch_register_place_removed', m)], ''

    m = match(rf"Administration: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), président, (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), secrétaire, et (?P<name3>{NAME}), lesquels signent collectivement à deux; les pouvoirs du dernier sont modifiés en ce sens", 'fr')
    if m:
        return [person('board_collective_signing_updated', m, m[f'name{i}'], role, 'Kollektivunterschrift zu zweien', m[f'place{i}'] if i < 3 else None) for i, role in [(1, 'Verwaltungsrat, Präsident'), (2, 'Verwaltungsrat, Sekretär'), (3, None)]], ''

    return [], leftover
