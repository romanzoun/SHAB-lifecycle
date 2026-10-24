from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import COUNT, MONEY, UID
from . import parser122, parser131, parser132, parser161, parser169, parser213

NAME = r'[^,;.\[\]\n]+?'
DATE = r'\d{2}\.\d{2}\.\d{4}'
# Compiled predecessor patterns retain ownership even in isolation tests.
_LEGACY = tuple(p for module in (parser122, parser131, parser132, parser161, parser169, parser213)
                for p in vars(module).values() if isinstance(p, re.Pattern))


def extract_parser392_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Bounded residual variants; unsupported input is returned unchanged."""
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

    def person(action, m, name, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name,
                             role=role, signing=signing, place=place,
                             extra={'action': action, **m.groupdict(), **extra, 'name': name, 'place': place})

    m = match(rf'(?P<seller>{NAME}), maintenant président, détient désormais (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}) par suite de cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé-gérant pour (?P=count) parts de CHF (?P=nominal)')
    if m:
        return [event('president_share_transfer_new_manager_distinct_origin', m, currency='CHF'),
                person('president_after_domestic_share_transfer', m, m['seller'], 'président'),
                person('new_domestic_associate_manager_after_transfer', m, m['buyer'], 'associé-gérant', place=m['place'])], ''

    m = match(rf'(?P<name1>{NAME}), gérant et président, (?P<name2>{NAME}), gérant, et (?P<name3>{NAME}), gérant et secrétaire, sont nommés liquidateurs (?P=name1) et (?P=name3) ne signant toutefois pas entre eux')
    if m:
        original = leftover.replace('sont nommés liquidateurs ', 'sont nommés liquidateurs avec signature collective à deux, ', 1)
        if original not in source_text:
            return [], text
        return [person('three_managers_liquidators_excluded_pair', m, m['name' + str(i)],
                       role + ', liquidateur', 'Kollektivunterschrift zu zweien',
                       excluded_signing_pair=[m['name1'], m['name3']])
                for i, role in ((1, 'gérant et président'), (2, 'gérant'), (3, 'gérant et secrétaire'))], ''

    m = match(rf'Signature collective à deux a été conférée à (?P<name1>{NAME}), à (?P<place1>{NAME}), et (?P<name2>{NAME}), à (?P<place2>{NAME}), (?P<country_code>[A-Z]), tous deux de France, directeurs')
    if m:
        return [person('two_french_directors_separate_residences', m, m['name' + str(i)], 'directeur',
                       'Kollektivunterschrift zu zweien', m['place' + str(i)], origin='France') for i in (1, 2)], ''

    m = match(rf'Les associés-gérants (?P<seller1>{NAME}) et (?P<seller2>{NAME}) cèdent chacun (?P<count>{COUNT}) part de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvelle associée avec (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal), gérante sans signature; (?P=seller1) et (?P=seller2) restent chacun titulaires de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)')
    if m:
        return [event('two_managers_single_share_transfer_unsigned_manager', m, currency='CHF'),
                person('new_female_associate_manager_unsigned', m, m['buyer'], 'associée-gérante', 'ohne Zeichnungsberechtigung', m['place'])], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat (?P<authority>{NAME}) die gewährte provisorische Nachlassstundung um (?P<duration>\w+) Monate bis (?P<until>{DATE}) verlängert', 'de')
    if m:
        return [event('provisional_moratorium_extended_without_zum', m, 'status_changed')], ''

    # This German publication is explicitly labelled French in its XML metadata.
    m = match(rf'Eingetragene Personen geändert: (?P<previous_company>{NAME}) \((?P<company_uid>{UID})\), Gesellschafterin, (?P<count>{COUNT}) Stammanteile zu CHF (?P<nominal>{MONEY}), Firma neu (?P<company>{NAME}) \((?P=company_uid)\), neu in (?P<company_place>{NAME}); (?P<manager>{NAME}), Geschäftsführer, Einzelunterschrift, neu in (?P<manager_place>{NAME}) \(Gemeindefusion\)\. Neu eingetragene Personen: (?P<name1>{NAME}), von (?P<origin1>{NAME}), in (?P<place1>{NAME}), Kollektivunterschrift zu zweien; (?P<name2>{NAME}), von (?P<origin2>{NAME}), in (?P<place2>{NAME}), Kollektivunterschrift zu zweien')
    if m:
        return [event('corporate_associate_renamed_moved_german_notice', m, currency='CHF'),
                person('manager_residence_municipal_merger', m, m['manager'], 'Geschäftsführer', 'Einzelunterschrift', m['manager_place']),
                *[person('new_collective_signatory_german_notice', m, m['name' + str(i)], signing='Kollektivunterschrift zu zweien', place=m['place' + str(i)], origin=m['origin' + str(i)]) for i in (1, 2)]], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à l'associé-gérant (?P<buyer>{NAME}), désormais titulaires de (?P<buyer_count>{COUNT}) parts de CHF (?P=nominal); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m:
        return [event('manager_share_transfer_existing_manager_plural_typo', m, currency='CHF')], ''

    m = match(rf'Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die "(?P<recipient>[^"\n]+)" \((?P<recipient_uid>{UID})\), in (?P<place>{NAME})\. Gegenleistung: (?P<count>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) und Forderungsgutschrift in der Höhe von CHF (?P<credit>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_registered_shares_credit_amount', m, currency='CHF')], ''

    m = match(rf'Sede principale a: (?P<head_office>{NAME}) \((?P<country>[A-Z]{{2}})\)\. Nuovo capitale sociale/responsabilità della sede principale: Capitale sociale della sede principale: EUR (?P<capital>{MONEY}) interamente liberato', 'it')
    if m:
        return [event('head_office_fully_paid_quota_capital', m, 'capital_changed', currency='EUR', scope='head_office', fully_paid=True)], ''

    m = match(rf'Anteilscheine neu: \[Die Anteilscheine sind aufgehoben worden\.\] \[gestrichen: (?P<previous_nominal>{MONEY})\.--\]\. Mit Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) werden die Anteilscheine aufgehoben und den Reserven gutgeschrieben; die Beachtung der gesetzlichen Vorschriften von Art\. 734 i\.V\.m\. Art\. 874 Abs\. 3 OR wird mit öffentlicher Urkunde vom (?P<deed_date>{DATE}) festgestellt\. \[Weitere Statutenänderungen betreffen keine publikationspflichtigen Tatsachen\.\]', 'de')
    if m:
        return [event('cooperative_certificates_cancelled_credited_reserves', m, 'capital_changed', credited_to_reserves=True)], ''

    m = match(rf'Administration: (?P<name1>{NAME}), à (?P<city1>{NAME}), (?P<state1>[A-Z]{{2}}), USA, président, (?P<name2>{NAME}), à (?P<city2>{NAME}), (?P<state2>[A-Z]{{2}}), USA, tous deux des Etats-Unis, et (?P<name3>{NAME}), lesquels signent individuellement')
    if m:
        return [person('three_administrators_us_residences_individual', m, m['name' + str(i)],
                       'administrateur président' if i == 1 else 'administrateur', 'Einzelunterschrift',
                       f"{m['city' + str(i)]}, {m['state' + str(i)]}, USA" if i < 3 else None,
                       **({'origin': 'Etats-Unis'} if i < 3 else {})) for i in (1, 2, 3)], ''

    m = match(rf"L'associé (?P<seller>{NAME}) est maintenant associé pour (?P<remaining>{COUNT}) parts de CHF (?P<nominal>{MONEY}), suite à la cession de (?P<count>{COUNT}) parts de CHF (?P=nominal) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=count) parts de CHF (?P=nominal)\. Gérants: les assosiés (?P=seller), nommé président, et (?P=buyer), tous deux")
    if m:
        if leftover.rstrip('.') + ' avec signature individuelle' not in source_text:
            return [], text
        return [event('share_transfer_two_managers_assosies_typo', m, currency='CHF'),
                person('associate_manager_president_assosies_typo', m, m['seller'], 'associé-gérant et président', 'Einzelunterschrift'),
                person('new_associate_manager_assosies_typo', m, m['buyer'], 'associé-gérant', 'Einzelunterschrift', m['place'])], ''
    return [], text
