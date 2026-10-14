from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, MONEY, COUNT


def extract_parser327_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Add complete sample-backed residual clauses after all earlier parsers."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date') and value is not None:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(action, m, event_type='organization_changed', **extra):
        return _event(*context, event_type, f'{language}.text.{action}.v1', {**m.groupdict(), 'action': action, **extra})

    def person(action, m, name, role=None, signing=None, place=None, event_type='officer_changed', **extra):
        return _person_event(*context, event_type, f'{language}.text.{action}.v1', name, role=role, signing=signing, place=place, extra={**m.groupdict(), 'action': action, **extra})

    m = match(rf"Radiation des mentions relatives aux apports en nature et à la reprise de biens effectués à la constitution de la société\. La mention relative à l'organisation de la société est radiée, celle-ci n'étant plus obligatoire\. Administration: (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président, et (?P<name2>{NAME}), jusqu'ici président, nommé secrétaire, lesquels continuent de signer individuellement")
    if m:
        return [event('historical_contribution_and_organization_mentions_removed', m, historical_mentions_removed=True), person('administrator_roles_exchanged', m, m['name1'], 'Verwaltungsratspräsident', 'Einzelunterschrift', previous_role='secrétaire'), person('administrator_roles_exchanged', m, m['name2'], 'Sekretär', 'Einzelunterschrift', previous_role='président')], ''

    m = match(rf'(?P<seller>{NAME}) cède (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé sans signature, avec (?P<buyer_count>{COUNT}) part de CHF (?P<buyer_nominal>{MONEY}); (?P=seller) reste titulaire de (?P<remaining>{COUNT}) parts de CHF (?P<remaining_nominal>{MONEY})')
    if m:
        if int(m['before'].replace("'", '')) != int(m['transferred'].replace("'", '')) + int(m['remaining'].replace("'", '')) or m['transferred'] != m['buyer_count'] or not m['nominal'] == m['buyer_nominal'] == m['remaining_nominal']:
            return [], leftover
        return [event('share_transfer_new_unsigned_associate', m, 'ownership_changed', currency='CHF'), person('new_unsigned_associate', m, m['buyer'], 'Gesellschafter', 'ohne Zeichnungsberechtigung', place=m['place'], without_signing=True)], ''

    m = match(rf"L'associé (?P<seller>{NAME}) a cédé (?P<transferred>{COUNT}) de ses (?P<before>{COUNT}) parts sociales de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvelle associée\. Gérants: (?P=seller), nommé président, et (?P=buyer), lesquels signent individuellement")
    if m:
        if int(m['transferred'].replace("'", '')) > int(m['before'].replace("'", '')):
            return [], leftover
        return [event('share_transfer_and_managers_appointed', m, 'ownership_changed', currency='CHF'), person('associate_manager_president_appointed', m, m['seller'], 'Gesellschafter, Geschäftsführer, Präsident', 'Einzelunterschrift'), person('associate_manager_appointed', m, m['buyer'], 'Gesellschafterin, Geschäftsführerin', 'Einzelunterschrift', m['place'])], ''

    m = match(rf'Bemerkungen zum Hauptsitz neu: Mit Urteil vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) den Entscheid des (?P<foreign_court>{NAME}) vom (?P<foreign_decision_date>{DATE}), Verfahrens-Nr\. (?P<case_reference>[^,]+), betreffend die Eröffnung eines insolvenzrechtlichen Sanierungsverfahrens im Sinne von Art\. 175 IPRG mit Wirkung ab dem (?P<effective_date>{DATE}) für das Gebiet der Schweizerischen Eidgenossenschaft anerkannt\. Demzufolge treten für das in der Schweiz belegene Vermögen die Stundungswirkungen gemäss Art\. 297 Abs\. 1, Abs\. 3, Abs\. 5 sowie Abs\. 6 SchKG ein\. Die Stundung wird auf die Dauer von einstweilen zwölf Monaten bis (?P<end_date>{DATE}) befristet', 'de')
    if m:
        return [event('foreign_restructuring_recognized_swiss_stay', m, 'status_changed', foreign_proceedings_recognized=True, stay_months=12, scope='Swiss assets')], ''

    # The supplied publication labels this German clause as French.
    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), vorsitzender Geschäftsführer, Kollektivunterschrift zu zweien, neu Geschäftsführer, Einzelunterschrift')
    if m:
        return [person('manager_role_and_signing_changed', m, m['name'], 'Geschäftsführer', 'Einzelunterschrift', previous_role='vorsitzender Geschäftsführer', previous_signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"(?P<name>{NAME}), maintenant domiciliée à (?P<place>{NAME}), jusqu'ici présidente, reste seule administratrice et continue à signer individuellement")
    if m:
        return [person('president_becomes_sole_administrator', m, m['name'], 'Verwaltungsrat', 'Einzelunterschrift', m['place'], previous_role='présidente', sole_administrator=True)], ''

    m = match(rf"L'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) est rectifiée en ce sens que l'associée, gérante et présidente est (?P<name1>.+?) et que (?P<name2>{NAME}) est gérant")
    if m:
        return [person('associate_manager_roles_corrected', m, m['name1'], 'Gesellschafterin, Geschäftsführerin, Präsidentin', associate=True, corrected=True), person('associate_manager_roles_corrected', m, m['name2'], 'Geschäftsführer', corrected=True)], ''

    m = match(rf"Le membre du conseil (?P<name1>{NAME}), nommé président, lequel continue à signer individuellement\. (?P<name2>{NAME}), de et à (?P<place>{NAME}), secrétaire, et (?P<name3>{NAME}), trésorier, sont membres du conseil")
    if m:
        return [person('council_president_appointed', m, m['name1'], 'Präsident', 'Einzelunterschrift'), person('council_members_roles_recorded', m, m['name2'], 'Sekretär', place=m['place']), person('council_members_roles_recorded', m, m['name3'], 'Kassier')], ''

    m = match(rf'Unter TR-Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) wurde der Bisher-Text unvollständig wiedergegeben: \[bisher: (?P<previous_name>[^,]+, [^,]+), (?P<previous_nationality>{NAME}), in (?P<previous_place>{NAME}), Präsident des Verwaltungsrates, mit Einzelunterschrift\]', 'de')
    if m:
        return [event('previous_officer_text_corrected', m, 'publication_corrected', previous_role='Präsident des Verwaltungsrates', previous_signing='Einzelunterschrift')], ''

    m = match(rf'Con decreto della (?P<court>{NAME}) del (?P<decision_date>{DATE}), al titolare è stata concessa una moratoria in via definitiva a scopo di concordato di (?P<months>\d+) mesi a partire dal (?P<effective_date>{DATE})\. \[finora: Con decreto della (?P=court) del (?P<previous_decision_date>{DATE}), al titolare è stata concessa una moratoria provvisoria a scopo di concordato di (?P<previous_months>\d+) mesi\.\]', 'it')
    if m:
        return [event('definitive_composition_stay_granted', m, 'status_changed', definitive_stay=True)], ''

    m = match(rf"(?P<name1>{NAME}) et (?P<name2>[^;]+?) ne sont plus gérants; leurs pouvoirs sont radiés\. (?P<name3>{NAME}), d'(?P<origin3>{NAME}), à (?P<place3>{NAME}), vice-présidente, et (?P<name4>{NAME}), des (?P<origin4>{NAME}), à (?P<place4>{NAME}), président, sont gérants")
    if m:
        return [person('managers_departed_powers_removed', m, m[f'name{i}'], 'Geschäftsführer', powers_removed=True) for i in (1, 2)] + [person('manager_vice_president_appointed', m, m['name3'], 'Geschäftsführerin, Vizepräsidentin', place=m['place3']), person('manager_president_appointed', m, m['name4'], 'Geschäftsführer, Präsident', place=m['place4'])], ''

    m = match(rf'Persona iscritta corretta: (?P<name>[^,]+, [^,]+), cittadina (?P<nationality>{NAME}), in (?P<place>{NAME}) \((?P<country>[A-Z]{{2}})\), membro, con firma collettiva a tre', 'it')
    if m:
        return [person('registered_member_corrected_collective_three', m, m['name'], 'Mitglied', 'Kollektivunterschrift zu dreien', m['place'], corrected=True)], ''

    return [], leftover
