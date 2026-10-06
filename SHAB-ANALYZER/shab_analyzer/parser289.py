from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser289_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete sample-backed clauses and retain unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr', suffix=''):
        if language != lang:
            return None
        m = re.fullmatch(pattern + ('(?:' + re.escape(suffix) + ')?' if suffix else '') + r'\.?', leftover)
        if not m:
            return None
        if suffix and leftover.removesuffix('.').removesuffix(suffix) + suffix + '.' not in source_text:
            return None
        try:
            for key, value in m.groupdict().items():
                if key.endswith('date') and value:
                    datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(rule, **kw):
        return _event(*context, 'organization_changed', rule, kw)

    def person(rule, name, **kw):
        return _person_event(*context, 'officer_changed', rule, name, **kw)

    def number(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'(?P<name>{NAME}), associée-gérante, désormais de (?P<origin>{NAME}), est nommée liquidatrice', suffix=' avec signature individuelle')
    if m:
        return [person('fr.persons.associate_manager_liquidator_origin.v1', m['name'], role='associée-gérante liquidatrice', signing='Einzelunterschrift', extra={'origin': m['origin']})], ''

    m = match(rf'Mit Entscheid des (?P<court>{NAME}) vom (?P<decision_date>{DATE}) wurde die definitive Nachlassstundung um (?P<extension>vier) Monate, d.h. bis zum (?P<until_date>{DATE}) verlängert\. \[bisher: Mit Entscheid des (?P=court) vom (?P<previous_date>{DATE}) wurde eine definitive Nachlassstundung für die Dauer von (?P<previous_months>{COUNT}) Monaten gewährt\.\]', 'de')
    if m and datetime.strptime(m['previous_date'], '%d.%m.%Y') < datetime.strptime(m['decision_date'], '%d.%m.%Y') < datetime.strptime(m['until_date'], '%d.%m.%Y') and number(m['previous_months']) > 0:
        return [event('de.text.definitive_moratorium_extended_previous.v1', action='definitive_moratorium_extended', extension_months=4, **m.groupdict())], ''

    for with_change in (True, False):
        tail = rf'\. Signature collective à deux, sans autre restriction, a été conférée à (?P<name4>{NAME}); ses pouvoirs sont modifiés en ce sens' if with_change else ''
        m = match(rf"(?P<name1>{NAME}), jusqu'ici vice-président(?P<female>e)?, nommée? président(?:e)?, (?P<name2>{NAME}), nommé vice-président, et (?P<name3>{NAME}), (?:maintenant domicilié à (?P<place3>{NAME}), )?jusqu'ici président, continuent à signer collectivement à deux" + tail)
        if m:
            rule = 'fr.persons.board_roles_collective_unrestricted.v1' if with_change else 'fr.persons.board_roles_collective_residence.v1'
            events = [person(rule, m['name1'], role='présidente' if m['female'] else 'président', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'vice-présidente' if m['female'] else 'vice-président'}), person(rule, m['name2'], role='vice-président', signing='Kollektivunterschrift zu zweien'), person(rule, m['name3'], place=m['place3'], signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'président'})]
            if with_change:
                events.append(person(rule, m['name4'], signing='Kollektivunterschrift zu zweien', extra={'restriction_removed': True}))
            return events, ''

    m = match(rf'Liquidationsadresse: (?P<address>c/o [^;\n]+?, [^,;\n]+?, \d{{4}} [^.;\n]+?) \[bisher: Liquidationsadresse: (?P<previous_address>c/o [^;\n]+?, [^,;\n]+?, \d{{4}} [^;\n]+?)\.\]', 'de')
    if m:
        return [event('de.text.liquidation_address_previous.v1', action='liquidation_address_changed', **m.groupdict())], ''

    m = match(rf"Administration: (?P<name1>{NAME}), nommé président, et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), secrétaire\. Signature individuelle du président ou collective à deux du secrétaire du conseil d'administration")
    if m:
        rule = 'fr.persons.board_president_secretary_distinct_signing.v1'
        return [person(rule, m['name1'], role='administrateur président', signing='Einzelunterschrift'), person(rule, m['name2'], role='administrateur secrétaire', place=m['place'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin']})], ''

    m = match(rf"L'associé (?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>F), nouvel associé, lequel n'exerce pas la signature sociale")
    if m and 0 < number(m['transferred']) < number(m['previous']) and number(m['nominal']) > 0:
        rule = 'fr.persons.share_transfer_new_associate_no_signing.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['seller'], role='associé', extra={'shares': int(number(m['previous']) - number(m['transferred'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'country': m['country'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"L'effet suspensif a été accordé au recours, à l'encontre de la décision de faillite du (?P<bankruptcy_date>{DATE}), selon décision du (?P<court>{NAME}) du (?P<decision_date>{DATE})")
    if m and datetime.strptime(m['bankruptcy_date'], '%d.%m.%Y') <= datetime.strptime(m['decision_date'], '%d.%m.%Y'):
        return [event('fr.text.bankruptcy_appeal_suspensive_effect.v1', action='bankruptcy_appeal_suspensive_effect', **m.groupdict())], ''

    m = match(rf"(?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), (?P<country1>FRA), délégué et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), (?P<country2>FRA), sont membres du conseil d'administration", suffix=' avec signature individuelle')
    if m:
        rule = 'fr.persons.board_delegate_two_individual_signatures.v1'
        return [person(rule, m['name' + i], role='administrateur délégué' if i == '1' else 'administrateur', place=m['place' + i], signing='Einzelunterschrift', extra={'origin': m['origin' + i], 'country': m['country' + i]}) for i in ('1', '2')], ''

    m = match(rf"eingetragenen Einzelunternehmens (?P<transferor>[^;\n]+?), in (?P<place>{NAME}), gemäss Vertrag vom (?P<contract_date>{DATE}) und Bilanz per (?P<balance_date>{DATE}) mit Aktiven von CHF (?P<assets>{MONEY}) und Passiven von CHF (?P<liabilities>{MONEY}), wofür (?P<shares>{COUNT}) Namenaktien zu CHF (?P<nominal>{MONEY}) zugeteilt und CHF (?P<claim>{MONEY}) als Forderung gutgeschrieben werden", 'de')
    if m and all(number(m[k]) > 0 for k in ('assets', 'shares', 'nominal', 'claim')) and number(m['liabilities']) >= 0 and number(m['assets']) - number(m['liabilities']) == number(m['shares']) * number(m['nominal']) + number(m['claim']) and 'Sacheinlage/Sachübernahme: Die Gesellschaft übernimmt bei der Gründung das Geschäft des im Handelsregister ' + leftover.removesuffix('.') + '.' in source_text and '[nicht: Sacheinlage/Sachübernahme:' in source_text:
        return [event('de.text.contribution_acquisition_balance_corrected.v1', action='contribution_acquisition_corrected', correction=True, currency='CHF', **m.groupdict())], ''

    m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), d'(?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P=transferred) parts de CHF (?P=nominal), sans signature\. L'associé-gérant (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P=nominal)")
    if m and all(number(m[k]) > 0 for k in ('transferred', 'previous', 'nominal', 'remaining')) and number(m['transferred']) + number(m['remaining']) == number(m['previous']):
        rule = 'fr.persons.manager_share_transfer_remaining.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['seller'], role='associé-gérant', extra={'shares': int(number(m['remaining'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé', place=m['place'], signing='ohne Zeichnungsberechtigung', extra={'origin': m['origin'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    m = match(rf"Jusqu'ici titulaire de (?P<previous>{COUNT}) parts de CHF (?P<nominal>{MONEY}), l'associée-gérante (?P<seller>{NAME}) détient (?P<remaining>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred>{COUNT}) parts à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvel associé-gérant pour (?P=transferred) parts de CHF (?P=nominal), nommé président", suffix=' avec signature individuelle')
    if m and all(number(m[k]) > 0 for k in ('previous', 'nominal', 'remaining', 'transferred')) and number(m['remaining']) + number(m['transferred']) == number(m['previous']):
        rule = 'fr.persons.share_transfer_new_manager_president.v1'
        return [event(rule, action='share_transfer', **m.groupdict()), person(rule, m['seller'], role='associée-gérante', extra={'shares': int(number(m['remaining'])), 'share_nominal': m['nominal']}), person(rule, m['buyer'], role='associé-gérant président', place=m['place'], signing='Einzelunterschrift', extra={'origin': m['place'], 'shares': int(number(m['transferred'])), 'share_nominal': m['nominal']})], ''

    return [], leftover
