from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import DATE, MONEY, UID

PERSON = r'[^,;.]+?'


def extract_parser358_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete supported residual clauses; preserve all earlier events."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=''):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and suffix and not re.search(re.escape(leftover) + re.escape(suffix) + r'\.?$', source_text):
            return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, **extra):
        return _event(*context, 'organization_changed', f'{language}.text.{action}.v1', {'action': action, **m.groupdict(), **extra})

    def person(action, m, name=None, role=None, signing=None, place=None, **extra):
        return _person_event(*context, 'officer_changed', f'{language}.text.{action}.v1', name or m['name'], place=m.groupdict().get('place') if place is None else place, role=role, signing=signing, extra={'action': action, **m.groupdict(), **extra})

    m = match(rf'(?P<name1>{PERSON}), de (?P<origin1>{PERSON}), à (?P<place1>{PERSON}), président et (?P<name2>{PERSON}), de (?P<origin2>{PERSON}), au (?P<place2>{PERSON}), trésorier, sont membres du comité, tous deux', suffix=' avec signature individuelle')
    if m:
        return [person('committee_members_individual_signing', m, m[f'name{i}'], role, 'Einzelunterschrift', place=m[f'place{i}']) for i, role in ((1, 'Präsident'), (2, 'Kassier'))], ''

    m = match(rf"Création ordinaire d'un capital-participation par compensation de créance de CHF (?P<claim>{MONEY}); en contrepartie, est remis (?P<count>[\d']+) bons de participation nominatifs de CHF (?P<nominal>{MONEY})\. Nouveau capital-participation: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P=count) bons de participation nominatifs de CHF (?P=nominal)")
    if m:
        return [event('participation_capital_created_by_claim_offset', m, currency='CHF', fully_paid=True)], ''

    m = match(rf'(?P<name>{PERSON}) continue de signer par procuration, collectivement à deux, mais désormais sans autre restriction')
    if m:
        return [person('collective_procuration_restriction_removed', m, signing='Kollektivprokura zu zweien', signing_restriction_removed=True)], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{PERSON}), Verwaltungsratsmitglied, Geschäftsführer, Kollektivunterschrift zu zweien, neu Geschäftsführer, Kollektivunterschrift zu zweien', 'de')
    if m:
        return [person('board_member_becomes_manager_keeps_collective_signing', m, role='Geschäftsführer', signing='Kollektivunterschrift zu zweien', previous_role='Verwaltungsratsmitglied, Geschäftsführer')], ''

    m = match(rf'Signature collective à deux est conférée à (?P<name>{PERSON}), du et au (?P<place>{PERSON}), directrice')
    if m:
        return [person('director_same_origin_and_residence', m, role='Direktor', signing='Kollektivunterschrift zu zweien', origin=m['place'])], ''

    m = match(rf'Berichtigung des Eintrages Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): Gemäss Verfügung der Aufsichtsbehörde Statuten geändert am (?P<statutes_date>{DATE}) \(und nicht am (?P<previous_statutes_date>{DATE})\)', 'de')
    if m:
        return [event('supervisory_statutes_date_corrected', m)], ''

    m = match(rf'eingetragenen Einzelunternehmen "(?P<business_name>[^"\n]+)", in (?P<place>{PERSON}), zum Preise von höchstens CHF (?P<maximum_price>{MONEY})\.\-\- zu übernehmen\.\]', 'de')
    if m and '[gestrichen: Beabsichtigte Sachübernahme: Die Gesellschaft beabsichtigt, nach der Gründung die Aktiven und Passiven der im Handelsregister ' + leftover in source_text:
        return [event('intended_asset_acquisition_deleted_detail', m, currency='CHF', deleted=True)], ''

    m = match(rf'(?P<transferor>{PERSON}), qui est maintenant à (?P<place>{PERSON}), cède (?P<transferred>\d+) de ses (?P<previous_count>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<recipient>{PERSON}), désormais titulaire de (?P<recipient_count>\d+) parts de CHF (?P=nominal)\. (?P=transferor) a désormais (?P<remaining>\d+) parts de CHF (?P=nominal)')
    if m:
        return [event('shares_transferred_with_remaining_holdings', m)], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est complétée en ce sens que (?P<name>{PERSON}) est originaire de (?P<origin>{PERSON}) et domiciliée à (?P<place>{PERSON})")
    if m:
        return [person('person_origin_residence_entry_completed', m)], ''

    m = match(rf"Séparation: la société (?P<recipient_name>.+?), à (?P<recipient_place>{PERSON}) \((?P<recipient_uid>{UID})\), reprend une partie du patrimoine d'(?P<transferor_name>.+?), à (?P<transferor_place>{PERSON}) \((?P<transferor_uid>{UID})\), selon contrat de scission du (?P<agreement_date>{DATE})\. La société reprend ainsi des actifs de CHF (?P<assets>{MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{MONEY}), soit un actif net de CHF (?P<net_assets>{MONEY})\. La totalité du capital actions et capital social des deux sociétés étant détenue par le même actionnaire et associé, la scission ne donne pas lieu à une augmentation du capital, ni à une attribution d'actions au sein de la société reprenante")
    if m:
        return [event('demerger_common_owner_no_capital_increase', m, currency='CHF', capital_increased=False, shares_allocated=False)], ''

    m = match(rf"Par suite de cession de (?P<transferred>\d+) parts de CHF (?P<nominal>{MONEY}), l'associée (?P<name1>{PERSON}) est désormais titulaire de (?P<remaining>\d+) parts de CHF (?P=nominal), et (?P<name2>{PERSON}), de (?P<origin>{PERSON}), à (?P<place>{PERSON}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal)\. Gérants: les associés (?P=name1), présidente, et (?P=name2), tous deux", suffix=' avec signature individuelle')
    if m:
        return [event('share_transfer_and_managers_appointed', m), person('associate_manager_individual_signing', m, m['name1'], 'Vorsitzender der Geschäftsführung', 'Einzelunterschrift', place=''), person('associate_manager_individual_signing', m, m['name2'], 'Geschäftsführer', 'Einzelunterschrift')], ''

    m = match(rf'Vermögensübertragung: Die (?P<transferor_name>.+?), in (?P<transferor_place>{PERSON}) \((?P<transferor_uid>{UID})\) überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient_name>.+?), in (?P<recipient_place>{PERSON}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: Eine Forderung in Höhe von CHF (?P<consideration>{MONEY})', 'de')
    if m:
        return [event('asset_transfer_claim_consideration', m, currency='CHF', consideration_kind='claim')], ''

    return [], leftover
