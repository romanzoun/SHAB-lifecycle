from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import DATE, COUNT, MONEY, UID
from .parser112 import _FR_BRANCH_REMOVED_LEGACY_ID
from .parser126 import _FR_ASSOCIATE_MANAGER_EXACT_NAME_CORRECTED
from .parser133 import _FR_SOLE_MANAGER_APPOINTED
from .parser151 import _DE_SIMULTANEOUS_CAPITAL_CHANGE_NO_INCREASE_DATE
from .parser165 import _FR_TWO_BOARD_MEMBERS_SIGN_INDIVIDUALLY
from .parser178 import _IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS

PERSON = r'[^,;.]+?'
_LEGACY_PATTERNS = {
    'fr': (_FR_BRANCH_REMOVED_LEGACY_ID, _FR_ASSOCIATE_MANAGER_EXACT_NAME_CORRECTED,
           _FR_SOLE_MANAGER_APPOINTED, _FR_TWO_BOARD_MEMBERS_SIGN_INDIVIDUALLY),
    'de': (_DE_SIMULTANEOUS_CAPITAL_CHANGE_NO_INCREASE_DATE,),
    'it': (_IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS,),
}


def extract_parser374_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Recognize only the sample-backed variants left by earlier parsers."""
    leftover = text.strip()
    if any(p.fullmatch(leftover) for p in _LEGACY_PATTERNS.get(language, ())):
        return [], leftover
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', *, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            s = re.search(r'(?:^|\. )' + source_pattern + r'\.$', source_text)
            if not s or any(s.groupdict().get(k) != v for k, v in m.groupdict().items()):
                return None
            m = s
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name, place=None, role=None, signing=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name, place=place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Bei der Kapitalherabsetzung vom (?P<decision_date>{DATE}) werden (?P<destroyed_count>{COUNT}) Namenaktien zu CHF (?P<destroyed_nominal>{MONEY}) vernichtet\. Gleichzeitig werden (?P<issued_count>{COUNT}) voll liberierte Namenaktien zu CHF (?P<issued_nominal>{MONEY}) ausgegeben', 'de')
    if m:
        return [event('registered_shares_cancelled_and_issued', m, 'capital_changed', currency='CHF', issued_fully_paid=True)], ''

    conversion = rf"Transformation de (?P<converted_count>{COUNT}) actions de CHF (?P<nominal>{MONEY}) en actions privilégiées quant au produit de liquidation\. Capital-actions: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<ordinary_count>{COUNT}) actions ordinaire de CHF (?P=nominal) et en (?P<preferred_count>{COUNT}) actions de CHF (?P=nominal), privilégiées quant au produit de liquidation, toutes nominatives, "
    dates = rf'\. Statuts modifiés les (?P<statutes_date>{DATE}) et (?P<second_statutes_date>{DATE})'
    m = match(conversion + dates, source_pattern=conversion + 'liées selon statuts' + dates + ', ainsi que sur des points non soumis à publication')
    if m and number(m['converted_count']) == number(m['preferred_count']) and (number(m['ordinary_count']) + number(m['preferred_count'])) * number(m['nominal']) == number(m['capital']):
        return [event('shares_converted_liquidation_preference_singular', m, 'capital_changed', currency='CHF', fully_paid=True, transfer_restricted=True, share_classes=[{'count': m[k], 'nominal': m['nominal'], 'kind': 'registered', 'liquidation_preferred': k == 'preferred_count'} for k in ('ordinary_count', 'preferred_count')])], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'un des gérants porte le nom exact (?P<name>[^()]+?) \(et non pas (?P<previous_name>[^()]+)\)")
    if m:
        return [person('one_manager_exact_name_corrected', m, m['name'], role='Geschäftsführer')], ''

    transfer = rf'(?P<seller>{PERSON}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{PERSON}), du (?P<origin>{PERSON}), à (?P<place>{PERSON}), nouvelle associée-gérante présidente'
    ending = rf" (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)"
    m = match(transfer + ending, source_pattern=transfer + r' avec signature individuelle\.' + ending)
    if m and number(m['before']) == number(m['transferred']) + number(m['remaining']):
        return [event('share_transfer_new_female_presiding_manager', m, currency='CHF'), person('share_transfer_new_female_presiding_manager', m, m['buyer'], m['place'], 'Gesellschafterin und Präsidentin der Geschäftsführung', 'Einzelunterschrift')], ''

    manager = rf'(?P<name>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}) est gérante unique'
    m = match(manager, source_pattern=manager + ' avec signature individuelle')
    if m:
        return [person('sole_female_manager_individual_signing', m, m['name'], m['place'], 'gérante unique', 'Einzelunterschrift')], ''

    m = match(rf"Selon décision de l'(?P<authority>Autorité cantonale de surveillance des fondations et des institutions de prévoyance) du (?P<decision_date>{DATE}), la fondation est dissoute\. Liquidateurs: les membre du conseil de fondation (?P<name1>{PERSON}), présidente et (?P<name2>{PERSON}) trésorier, lesquels continuent à signer collectivement à deux")
    if m:
        return [event('foundation_dissolved_two_liquidators_typo', m), *[person('foundation_dissolved_two_liquidators_typo', m, m[f'name{i}'], role='Liquidator', signing='Kollektivunterschrift zu zweien', organization_role='présidente' if i == 1 else 'trésorier') for i in (1, 2)]], ''

    m = match(rf"Sede principale a: (?P<head_office>[^()]+) \((?P<country>[A-Z]{{2}})\)\. Nuovo capitale sociale/responsabilità della sede principale: Capitale emesso: GBP (?P<capital>{MONEY}) suddiviso in (?P<count>{MONEY}) azioni di nominali GBP (?P<nominal>{MONEY}) liberate per GBP (?P<paid_per_share>{MONEY})\. \[Le informazioni sui conferimenti effettuati sono state pubblicate erroneamente, l'ammontare dei conferimenti effettuati è pari a GBP (?P=paid_per_share) per ogni azione, per un conferimento totale di GBP (?P<paid_total>{MONEY}); \[non come erroneamente pubblicato: Capitale emesso e liberato: GBP (?P<previous_capital>{MONEY}) suddiviso in (?P<previous_count>{COUNT}) azioni di nominali GBP (?P<previous_nominal>{MONEY}) interamente liberate\]", 'it')
    if m and number(m['count']) == number(m['count']).to_integral_value() and number(m['count']) * number(m['nominal']) == number(m['capital']) and number(m['count']) * number(m['paid_per_share']) == number(m['paid_total']) and number(m['paid_per_share']) <= number(m['nominal']):
        return [event('head_office_share_payment_corrected', m, 'capital_changed', currency='GBP')], ''

    correction = rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que les statuts ne contiennent pas de clause selon laquelle"
    m = match(correction, source_pattern=correction + r" les fondateurs se réservent expressément la possibilité de faire modifier le but par l'autorité de surveillance, en application de l'article 86a CC")
    if m:
        return [event('founder_purpose_reservation_absence_corrected', m, purpose_change_reserved=False, legal_basis='article 86a CC')], ''

    m = match(rf"(?P<name1>{PERSON}), nommé président, et (?P<name2>{PERSON}), jusqu'ici président, membres du conseil d'administration, signent désormais individuellement")
    if m:
        return [person('board_presidency_changed_individual_signing', m, m[f'name{i}'], role='Präsident des Verwaltungsrates' if i == 1 else 'Mitglied des Verwaltungsrates', signing='Einzelunterschrift', **({'previous_role': 'Präsident des Verwaltungsrates'} if i == 2 else {})) for i in (1, 2)], ''

    # Only the second origin's "du" variant; parser369 owns the "de" form.
    m = match(rf"(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), et (?P<name2>{PERSON}), du (?P<origin2>{PERSON}), à (?P<place2>{PERSON}), sont membres du conseil de fondation; ils n'exercent pas la signature sociale")
    if m:
        return [person('two_foundation_members_unsigned_second_du_origin', m, m[f'name{i}'], m[f'place{i}'], 'Mitglied des Stiftungsrates', 'ohne Zeichnungsberechtigung') for i in (1, 2)], ''

    m = match(r'Succursale: \[biffé: (?P<place>[^()\];.]+)\]')
    if m:
        return [event('branch_removed_without_register_identifier', m)], ''

    m = match(rf"Fusione: ripresa di attivi e passivi di (?P<absorbed_name>[^,;]+?) , in (?P<absorbed_place>{PERSON}) \((?P<absorbed_uid>{UID})\), secondo contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}), e passivi verso terzi per CHF (?P<liabilities>{MONEY}), con un'eccedenza passiva di CHF (?P<deficit>{MONEY})\. Conformemente all'attestazione di un perito revisore abilitato, dei crediti per un ammontare almeno equivalente allo scoperto e al sovraindebitamento sono stati postergati\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento del capitale e senza attribuzione di azioni", 'it')
    if m and number(m['liabilities']) - number(m['assets']) == number(m['deficit']):
        return [event('wholly_owned_merger_deficit_subordinated_claims', m, 'company_merged', currency='CHF', wholly_owned=True, capital_increase=False, share_allocation=False, claims_subordinated=True)], ''

    return [], leftover
