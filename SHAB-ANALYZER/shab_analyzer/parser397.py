from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, DATE, UID
from . import parser66, parser110, parser146, parser252

NAME = r'[^,;.\[\]\n]+?'
_LEGACY = tuple(p for module in (parser66, parser110, parser146, parser252)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser397_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Sample-backed residual variants; earlier rules retain their payloads."""
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

    def person(action, m, key='name', role=None, signing='Einzelunterschrift', place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', m[key], role=role, signing=signing, place=place, extra={'action': action, **m.groupdict(), **extra, 'name': m[key]})

    m = match(rf'Signature collective à deux à été conférée à la membre du conseil (?P<name>{NAME})')
    if m:
        return [person('female_council_member_joint_signing_typo', m, role='membre du conseil', signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}), maintenant de (?P<origin2>{NAME}), signent désormais individuellement')
    if m:
        return [person('pair_individual_signing_second_new_origin', m, f'name{i}') for i in (1, 2)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>Zivilgericht {NAME}) der Gesellschaft für die Dauer von (?P<months>6) Monaten, d\.h\. bis (?P<until_date>{DATE}), die definitive Nachlassstundung bewilligt und als Sachwalter (?P<commissioner>lic\.iur\. {NAME}), (?P<profession>Advokat), c/o (?P<care_of>{NAME}), (?P<street>{NAME}), Postfach, CH-(?P<postal_code>\d{{4}}) (?P<place>{NAME}), eingesetzt', 'de')
    if m:
        return [event('definitive_moratorium_commissioner_care_of', m, 'status_changed')], ''

    m = match(rf"Nuovi buoni di godimento: (?P<count>{COUNT}) buoni di godimento nominativi che conferiscono il diritto ad una quota dell'utile risultante dal bilancio a norma di statuto\. \[finora: (?P<previous_d>{COUNT}) buoni di godimento nominativi privilegiati di Tipo D, (?P<previous_e>{COUNT}) buoni di godimento nominativi privilegiati di Tipo E, (?P<previous_f>{COUNT}) buoni di godimento nominativi di Tipo F conferiscono il diritto ad una quota dell'utile risultante dal bilancio a norma di statuto\. I buoni di godimento privilegiati garantiscono dei diritti preferenziali nella ripartizione dei dividendi a norma di statuto\. \]", 'it')
    if m:
        return [event('profit_participation_certificates_previous_classes', m)], ''

    m = match(rf'Liquidateurs: les associés gérants (?P<name1>{NAME}), président, (?P<name2>{NAME}) et (?P<name3>{NAME}), lesquels continuent à signer individuellement')
    if m:
        return [person('three_associate_managers_liquidators', m, f'name{i}', role='associé gérant, liquidateur' + (', président' if i == 1 else '')) for i in (1, 2, 3)], ''

    m = match(rf"(?P<name>{NAME}), maintenant domicilié à (?P<place>{NAME}), jusqu'ici (?P<previous_role>directeur), est nommé membre et président du conseil d'administration, continue à signer individuellement")
    if m:
        return [person('director_appointed_board_member_president_new_residence', m, role="membre et président du conseil d'administration", place=m['place'])], ''

    m = match(rf'(?P<name>[^,;.\[\]\n]+?) signe maintenant individuellement')
    if m:
        return [person('individual_signing_now', m)], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>Bezirksgericht {NAME}) die provisorische Nachlassstundung um (?P<extension_months_word>zwei) auf insgesamt (?P<total_months_word>sechs) Monate bis und mit (?P<until_date>{DATE}) verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_to_six_months', m, 'status_changed')], ''

    m = match(rf'Fusion: Übernahme der Aktiven und Passiven der (?P<absorbed_name>[^,;\[\]\n]+?), in (?P<absorbed_place>{NAME}) \((?P<absorbed_uid_raw>CHE-\d{{3}}-\d{{3}}\.\d{{3}})\), gemäss Fusionsvertrag vom (?P<agreement_date>{DATE}) und Bilanz per (?P<balance_date>{DATE})\. Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) gehen auf die übernehmende Gesellschaft über\. Da die Aktionäre der übertragenden Gesellschaft die anlässlich der Fusion erworbenen eigenen Aktien der übernehmenden Gesellschaft erhalten, findet weder eine Kapitalerhöhung noch eine Aktienzuteilung statt', 'de')
    if m:
        return [event('merger_own_shares_published_uid_typo', m, currency='CHF', capital_increase=False, share_allocation=False)], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) auf die neue (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) und Darlehensforderung von CHF (?P<loan_claim>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_new_company_shares_and_loan_claim', m, currency='CHF')], ''

    m = match(rf'Nuove disposizioni per la succursale: \[radiati: Altri locali commerciali:\]\. \[radiati: Altro indirizzo: (?P<street>{NAME}), (?P<postal_code>\d{{4}}) (?P<place>{NAME})\.\]', 'it')
    if m:
        return [event('branch_other_business_address_removed', m, 'address_changed', removed=True)], ''

    m = match(rf'Siège transféré à (?P<place>{NAME})')
    if m:
        return [event('seat_transfer_text_only', m, 'seat_changed')], ''
    return [], text
