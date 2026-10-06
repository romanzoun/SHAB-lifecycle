from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID

MONTHS = {'janvier': 1, 'avril': 4, 'juillet': 7}
FDATE = r'\d{1,2} (?:janvier|avril|juillet) \d{4}'


def extract_parser298_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses; preserve unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, suffix=''):
        if language != lang:
            return None
        m = re.fullmatch(pattern + re.escape(suffix) + r'\.?', leftover)
        if not m or (suffix and not source_text.endswith(leftover.rstrip('.') + '.')):
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date'):
                    if re.fullmatch(DATE, value):
                        datetime.strptime(value, '%d.%m.%Y')
                    else:
                        day, month, year = value.split()
                        datetime(int(year), MONTHS[month], int(day))
        except (ValueError, KeyError):
            return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, event_type='officer_changed', **payload):
        return _person_event(*context, event_type, rule, name, **payload)

    transfer = rf'Transfert de patrimoine: selon contrat du (?P<agreement_date>{FDATE}), (?P<transferor>le titulaire|la société) a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}) à (?P<recipient>[^,;]+), à (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Contre-prestation: '
    m = match(transfer + rf"(?P<count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et créance de CHF (?P<claim>{MONEY})", 'fr')
    if m:
        return [event('fr.text.asset_transfer_shares_claim.v1', action='asset_transfer', **m.groupdict())], ''
    m = match(transfer + rf"(?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), le solde de CHF (?P<premium>{MONEY}) constituant un agio", 'fr')
    if m:
        return [event('fr.text.asset_transfer_shares_premium.v1', action='asset_transfer', **m.groupdict())], ''

    m = match(rf'Mit Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) die gewährte definitve Nachlassstundung um (?P<months>{COUNT}) Monate verlängert', 'de')
    if m:
        return [event('de.text.definitive_moratorium_extended_typo.v1', action='moratorium_extended', **m.groupdict())], ''

    m = match(rf"L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est complétée en ce sens que la fondation dispose également d'une autre adresse sise à (?P<street>[^,;]+), (?P<postal_code>\d{{4}}) (?P<place>{NAME})", 'fr')
    if m:
        return [event('fr.text.foundation_additional_address_completed.v1', action='additional_address_completed', **m.groupdict())], ''

    m = match(rf'Par décision du (?P<decision_date>{FDATE}), le président de la (?P<court>{NAME}) a rejeté le recours et dit que le prononcé de faillite du (?P<bankruptcy_date>{FDATE}) prend effet le (?P<effective_date>{FDATE}), à (?P<hour>[01]?\d|2[0-3])h(?P<minute>[0-5]\d)', 'fr')
    if m:
        return [event('fr.text.bankruptcy_appeal_rejected_effective.v1', action='bankruptcy_appeal_rejected', **m.groupdict())], ''

    m = match(rf"Par décision du (?P<decision_date>{FDATE}), le Président du (?P<court>{NAME}) a prolongé de trois mois le sursis concordataire définitif accordé au titulaire, soit jusqu'au (?P<end_date>{FDATE})", 'fr')
    if m:
        return [event('fr.text.sole_proprietor_moratorium_extended.v1', action='moratorium_extended', months=3, **m.groupdict())], ''

    m = match(r'Die Liste der Belege wurde geändert', 'de')
    if m:
        return [event('de.text.supporting_documents_changed.v1', action='supporting_documents_changed')], ''

    # German publication text labelled French in the supplied XML, including its typo.
    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) eine definitive Nachlassstundung von sechts Monaten bis zum (?P<end_date>{DATE}) bewilligt\. Eingetragene Person: (?P<name>[^();]+) \((?P<administrator_uid>{UID})\), in (?P<place>{NAME}), Sachwalterin', 'fr')
    if m:
        rule = 'de.text.moratorium_administrator_fr_xml.v1'
        return [event(rule, action='moratorium_granted', months=6, **m.groupdict()), person(rule, m['name'], role='Sachwalterin', place=m['place'], extra={'administrator_uid': m['administrator_uid']})], ''

    m = match(rf'La succursale à (?P<previous_place>{NAME}) \((?P<branch_uid>{UID})\) a transféré son siège à (?P<place>{NAME})', 'fr')
    if m:
        return [event('fr.text.branch_seat_transferred.v1', action='branch_seat_transferred', **m.groupdict())], ''

    m = match(rf'(?P<name1>{NAME}) et (?P<name2>{NAME}) continuent de signer collectivement à deux, désormais avec (?P<partner1>{NAME}) ou (?P<partner2>{NAME})', 'fr')
    if m:
        rule = 'fr.persons.collective_signing_partners_changed.v1'
        return [person(rule, m[key], signing='Kollektivunterschrift zu zweien', extra={'signing_partners': [m['partner1'], m['partner2']]}) for key in ('name1', 'name2')], ''

    m = match(rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), FRA, et (?P<name2>{NAME}), d'(?P<origin2>{NAME}), à (?P<place2>{NAME}), ITA, sont membres du conseil de fondation, tous deux", 'fr', ' avec signature collective à deux')
    if m:
        rule = 'fr.persons.two_foreign_foundation_board_members.v1'
        return [person(rule, m['name' + i], role='membre du conseil de fondation', place=m['place' + i], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin' + i], 'country': country}) for i, country in [('1', 'FRA'), ('2', 'ITA')]], ''

    m = match(rf'Etablissement principal ayant son siège à (?P<main_place>{NAME})\. (?P<name>{NAME}) étant inscrit au siège principal avec la même fonction et les mêmes pouvoirs de représentation que dans la succursale, son incription est radié dans la succursale', 'fr')
    if m:
        return [person('fr.persons.branch_duplicate_registration_removed_typo.v1', m['name'], 'officer_removed', extra={'main_place': m['main_place'], 'reason': 'registered_at_main_office'})], ''

    return [], leftover
