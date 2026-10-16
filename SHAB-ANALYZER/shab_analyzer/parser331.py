from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT, UID


def extract_parser331_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize bounded sample-backed clauses after all existing rules."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
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

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None, kind='officer_changed', **extra):
        return _person_event(*context, kind, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf"Les administrateurs (?P<name1>{NAME}), nommé président, (?P<name2>{NAME}), nommé vice-président, (?P<name3>{NAME}), jusqu'ici vice-président et (?P<name4>{NAME}), jusqu'ici président, lesquels continuent à signer collectivement à deux")
    if m:
        roles = ['Verwaltungsrat, Präsident', 'Verwaltungsrat, Vizepräsident', 'Verwaltungsrat', 'Verwaltungsrat']
        return [person('board_presidency_changed', m, m[f'name{i}'], role, 'Kollektivunterschrift zu zweien', previous_role=('Vizepräsident' if i == 3 else 'Präsident') if i >= 3 else None) for i, role in enumerate(roles, 1)], ''

    m = match(rf"(?P<seller>{NAME}), maintenant président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<transferred>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvel associé-gérant pour (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        if m['transferred'] != m['buyer_count']:
            return [], leftover
        return [event('share_transfer_manager_president', m, 'ownership_changed', currency='CHF'), person('manager_becomes_president', m, m['seller'], 'Gesellschafter, Geschäftsführer, Präsident'), person('new_associate_manager', m, m['buyer'], 'Gesellschafter, Geschäftsführer', place=m['place'])], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La totalità del capitale azionario delle due società partecipanti alla fusione è detenuta dagli stessi azionisti, la fusione avviene dunque senza aumento del capitale e senza attribuzione di azioni\. Conformemente all'attestazione di un perito revisore abilitato, la società assuntrice dispone di fondi propri liberamente disponibili equivalenti almeno all'ammontare dello scoperto e del sovraindebitamento della società trasferente", 'it')
    if m:
        return [event('merger_common_shareholders_coverage', m, 'company_merged', kind='merger', currency='CHF', capital_increase=False, share_allocation=False, free_equity_coverage_confirmed=True)], ''

    m = match(rf"L'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'administrateur (?P<name>{NAME}) dispose de la signature collective à deux \(et non: signature individuelle\)")
    if m:
        return [person('administrator_signing_corrected', m, m['name'], 'Verwaltungsrat', 'Kollektivunterschrift zu zweien', kind='signing_authority_changed', corrected=True, previous_signing='Einzelunterschrift')], ''

    m = match(rf"Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von EUR (?P<assets>{MONEY}) und Fremdkapital von EUR (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}) \((?P<recipient_uid>{UID})\), in (?P<recipient_place>{NAME})\. Gegenleistung: EUR (?P<consideration>{MONEY})", 'de')
    if m:
        return [event('asset_transfer_eur', m, 'ownership_changed', currency='EUR')], ''

    m = match(rf"Grenzüberschreitende Fusion nach den Vorschriften des IPRG: Übernahme der Aktiven und Passiven der (?P<absorbed_name>{NAME}), in (?P<absorbed_place>{NAME}) \(LI\) \((?P<foreign_uid>FL-\d{{4}}\.\d{{3}}\.\d{{3}}-\d)\), eine Aktiengesellschaft nach dem Recht des Fürstentums Liechtenstein \(LI\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Gemäss Bestätigung des zugelassenen Revisionsexperten liegen Rangrücktrittserklärungen im Umfang der Unterdeckung und der Überschuldung der übernehmenden Gesellschaft vor\. Da dieselbe Aktionärin sämtliche Aktien der an der Fusion beteiligten Gesellschaften hält, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt", 'de')
    if m:
        return [event('cross_border_merger_subordination', m, 'company_merged', kind='merger', currency='CHF', country='LI', capital_increase=False, share_allocation=False, subordination_confirmed=True)], ''

    m = match(rf"L'inscription N°(?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée comme suit: les administrateurs (?P<name1>{NAME}) et (?P<name2>{NAME}) ne sont pas directeurs")
    if m:
        return [person('administrators_not_directors_corrected', m, m[f'name{i}'], 'Verwaltungsrat', corrected=True, excluded_role='Direktor') for i in (1, 2)], ''

    m = match(rf"L'inscription No (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) est en réalité domicilié à (?P<place>{NAME}), (?P<country>FRA)")
    if m:
        return [person('person_residence_corrected', m, m['name'], place=m['place'], corrected=True)], ''

    m = match(rf"Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar vom (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und keine Passiven auf die (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})", 'de')
    if m:
        return [event('asset_transfer_without_liabilities', m, 'ownership_changed', currency='CHF', no_liabilities=True)], ''

    m = match(rf'Die Generalversammlung hat mit Beschluss vom (?P<decision_date>{DATE}) eine weitere bedingte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt', 'de')
    if m:
        return [event('additional_conditional_capital', m, 'capital_changed', conditional=True)], ''

    m = match(rf'(?P<name1>{NAME}), (?P<name2>{NAME}), (?P<name3>{NAME}), et (?P<name4>{NAME}), continuent à engager la société par leur procuration collective à deux, désormais avec un administateur')
    if m:
        return [person('collective_procuration_with_administrator', m, m[f'name{i}'], 'Prokurist', 'Kollektivprokura zu zweien', kind='signing_authority_changed', signing_restriction='avec un administateur') for i in (1, 2, 3, 4)], ''

    m = match(rf'Les associées-gérantes (?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent chacune (?P<transferred>{COUNT}) de leurs (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant titulaire de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal)\. (?P=seller1) et (?P=seller2) restent chacune titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        number = lambda key: int(m[key].replace("'", ''))
        if number('before') - number('transferred') != number('remaining') or 2 * number('transferred') != number('buyer_count'):
            return [], leftover
        return [event('two_managers_share_transfer_remaining', m, 'ownership_changed', currency='CHF'), person('new_associate_manager', m, m['buyer'], 'Gesellschafter, Geschäftsführer', place=m['place'])], ''

    return [], leftover
