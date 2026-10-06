from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser295_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete sample-backed clauses and preserve unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, **payload):
        return _event(*context, 'organization_changed', rule, payload)

    def person(rule, name, **payload):
        return _person_event(*context, 'officer_changed', rule, name, **payload)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Vermögensübertragung: Die Stiftung überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Verfügung der Aufsichtsbehörde vom (?P<decision_date>{DATE}) den Betrieb des (?P<business>{NAME}) mit Aktiven von CHF (?P<assets>{MONEY}) und Fremdkapital von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: CHF (?P<consideration>{MONEY})', 'de')
    if m and number(m['assets']) - number(m['liabilities']) == number(m['consideration']):
        return [event('de.text.foundation_business_asset_transfer.v1', action='asset_transfer', **m.groupdict())], ''

    m = match(rf"L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE})\) est rectifiée en ce sens que les actifs de la société transférante (?P<name>[^()]+) \((?P<uid>{UID})\), au (?P<place>{NAME}), sont de CHF (?P<assets>{MONEY}), les passifs envers les tiers sont de CHF (?P<liabilities>{MONEY}), et par conséquent l'actif net est de CHF (?P<net_assets>{MONEY})", 'fr')
    if m and number(m['assets']) - number(m['liabilities']) == number(m['net_assets']):
        return [event('fr.text.transfer_balance_corrected.v1', action='transfer_balance_corrected', **m.groupdict())], ''

    m = match(rf'Mit Entscheid des (?P<court>[^,;]+?) vom (?P<decision_date>{DATE}) wurde eine definitive Nachlassstundung für die Dauer von 6 Monaten gewährt, d.h. bis zum (?P<end_date>{DATE})\. \[gestrichen: Mit Entscheid des (?P=court) vom (?P<previous_date>{DATE}) wurde eine provisorische Nachlassstundung für die Dauer von 4 Monaten gewährt, d.h. bis zum (?P<previous_end_date>{DATE})\.\]', 'de')
    if m and datetime.strptime(m['previous_date'], '%d.%m.%Y') < datetime.strptime(m['decision_date'], '%d.%m.%Y') < datetime.strptime(m['previous_end_date'], '%d.%m.%Y') < datetime.strptime(m['end_date'], '%d.%m.%Y'):
        return [event('de.text.definitive_moratorium_replaces_four_months.v1', action='definitive_moratorium', months=6, previous_months=4, **m.groupdict())], ''

    m = match(rf'Fusione: ripresa di attivi e passivi di (?P<name>{NAME}), in (?P<place>{NAME}) \((?P<uid>{UID})\), secondo il contratto di fusione del (?P<agreement_date>{DATE}) e bilancio al (?P<balance_date>{DATE}), che presenta attivi per CHF (?P<assets>{MONEY}) e passivi verso terzi per CHF (?P<liabilities>{MONEY})\. La società assuntrice detiene tutte le azioni della società trasferente, per cui la fusione avviene senza aumento di capitale e senza attribuzione di azioni', 'it')
    if m and datetime.strptime(m['balance_date'], '%d.%m.%Y') <= datetime.strptime(m['agreement_date'], '%d.%m.%Y'):
        return [event('it.text.merger_wholly_owned_transferor.v1', action='merger', capital_increase=False, shares_allocated=False, **m.groupdict())], ''

    m = match(rf'\[bisher: Liberierung Stammkapital: CHF (?P<paid_capital>{COUNT})\.-- Mitteilungen an Gesellschafter: (?P<previous_method>brieflich)\]', 'de')
    if m:
        return [event('de.text.previous_paid_capital_communications.v1', action='previous_provisions', **m.groupdict())], ''

    # Earlier parsers consume the first branches. Require the original heading.
    branch = rf'(?P<place>[^()]+) \((?P<uid>CHE-\d{{3}}\.\s?\d{{3}}\.\d{{3}})\)'
    if language == 'de' and 'Zweigniederlassung neu: ' in source_text:
        parts = leftover.rstrip('.').split('). ')
        matches = [re.fullmatch(branch, part + (')' if i < len(parts) - 1 else '')) for i, part in enumerate(parts)]
        if len(matches) == 7 and all(matches) and source_text.endswith(leftover + ('' if leftover.endswith('.') else '.')):
            return [event('de.text.new_branches_uid_spacing.v1', action='branch_added', place=m['place'], uid=m['uid'], uid_normalized=m['uid'].replace(' ', '')) for m in matches], ''

    m = match(rf"Conseil d'aministration: (?P<name1>[^,;]+), présidente, (?P<name2>{NAME}), vice-président, tous deux de (?P<origin>{NAME}), à (?P<place>{NAME}), F, et (?P<name3>{NAME}), nommé secrétaire, lesquels signent individuellement", 'fr')
    if m:
        rule = 'fr.persons.board_individual_signing_heading_typo.v1'
        return [person(rule, m[key], role=role, signing='Einzelunterschrift', place=m['place'] if key != 'name3' else None, extra={'origin': m['origin'], 'country': 'F'} if key != 'name3' else {}) for key, role in [('name1', 'présidente'), ('name2', 'vice-président'), ('name3', 'secrétaire')]], ''

    # The supplied XML marks this Italian clause as German.
    m = match(rf'Persone dimissionarie e firme cancellate: (?P<name1>[^.;]+?), da (?P<origin1>{NAME}), in (?P<place1>{NAME}), delegato, con firma collettiva a due con il presidente e/o con (?P<partner1>{NAME})\. Nuove persone iscritte o modifiche: (?P<name2>[^.;]+?), da (?P<origin2>{NAME}), in (?P<place2>{NAME}), membro, con firma collettiva a due con il presidente \[finora: membro, con firma collettiva a due con il presidente e/o (?P<partner2>{NAME})\]', 'de')
    if m:
        rule = 'it.persons.departure_restricted_signing_de_xml.v1'
        removed = _person_event(*context, 'officer_removed', rule, m['name1'], role='delegato', place=m['place1'], extra={'origin': m['origin1'], 'previous_signing': 'collettiva a due con il presidente e/o con ' + m['partner1']})
        return [removed, person(rule, m['name2'], role='membro', place=m['place2'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin2'], 'signing_restriction': 'con il presidente', 'previous_signing_partner': m['partner2']})], ''

    m = match(rf"Jusqu'ici titulaire de (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}), l'associé-gérant (?P<seller>{NAME}) détient (?P<remaining>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred>{COUNT}) parts à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé pour (?P=transferred) parts de CHF (?P=nominal), nommé gérant et président avec signature individuelle", 'fr')
    if m and number(m['before']) == number(m['remaining']) + number(m['transferred']) and source_text.endswith(m[0].rstrip('.') + '.'):
        rule = 'fr.persons.share_transfer_new_manager_president.v1'
        return [person(rule, m['seller'], role='associé-gérant', extra={'shares': int(number(m['remaining'])), 'nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant président', place=m['place'], signing='Einzelunterschrift', extra={'shares': int(number(m['transferred'])), 'nominal': m['nominal'], 'origin': m['origin']})], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée gérante présidente avec signature individuelle\. (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)', 'fr')
    if m and number(m['before']) == number(m['transferred']) + number(m['remaining']) and f"{m['buyer']}, de {m['origin']}, à {m['place']}, nouvelle associée gérante présidente avec signature individuelle." in source_text:
        rule = 'fr.persons.share_transfer_female_manager_president.v1'
        return [person(rule, m['seller'], extra={'shares': int(number(m['remaining'])), 'nominal': m['nominal']}), person(rule, m['buyer'], role='associée gérante présidente', place=m['place'], signing='Einzelunterschrift', extra={'shares': int(number(m['transferred'])), 'nominal': m['nominal'], 'origin': m['origin']})], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}), par (?P<each>{COUNT}) parts de CHF (?P=nominal), chacun, à (?P<buyer1>{NAME}), à (?P<place1>{NAME}), et (?P<buyer2>{NAME}), à (?P<place2>{NAME}), tous deux de (?P<origin>{NAME}), nouveaux associés, chacun avec (?P=each) parts de CHF (?P=nominal), sans signature\. (?P=seller), qui reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal), et (?P<signer>{NAME}) signent désormais collectivement à deux", 'fr')
    if m and number(m['before']) == number(m['transferred']) + number(m['remaining']) and number(m['transferred']) == 2 * number(m['each']):
        rule = 'fr.persons.two_share_buyers_collective_managers.v1'
        return [person(rule, m['seller'], role='associé-gérant', signing='Kollektivunterschrift zu zweien', extra={'shares': int(number(m['remaining'])), 'nominal': m['nominal']}), person(rule, m['signer'], signing='Kollektivunterschrift zu zweien')] + [person(rule, m['buyer'+i], role='associé', place=m['place'+i], signing='ohne Zeichnungsberechtigung', extra={'shares': int(number(m['each'])), 'nominal': m['nominal'], 'origin': m['origin']}) for i in ('1', '2')], ''

    m = match(rf"Par décision du (?P<day>\d{{1,2}}) février (?P<year>\d{{4}}), le Département fédéral de l'intérieur a dissous la fondation\. par (?P<name>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nommé liquidateur avec signature individuelle", 'fr')
    if m and re.search(r'La liquidation est opérée sous le nom: .+ en liquidation par ' + re.escape(m['name']) + r', de ' + re.escape(m['origin']) + r', à ' + re.escape(m['place']) + r', nommé liquidateur avec signature individuelle\.$', source_text):
        try:
            decision_date = datetime(int(m['year']), 2, int(m['day'])).strftime('%d.%m.%Y')
        except ValueError:
            return [], leftover
        rule = 'fr.text.foundation_dissolved_liquidator.v1'
        return [event(rule, action='foundation_dissolved', decision_date=decision_date, authority="Département fédéral de l'intérieur"), person(rule, m['name'], role='liquidateur', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    return [], leftover
