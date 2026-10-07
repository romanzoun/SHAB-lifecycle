from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY, UID


def extract_parser309_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete fixture-backed clauses, retaining unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source_input = source_text.rstrip(' .')
            if source_pattern.startswith('(?P<name1>'):
                start = source_input.find(m['name1'])
                source_input = source_input[start:] if start >= 0 else ''
            source = re.search(source_pattern + r'$', source_input)
            if not source or any(source[k].strip() != v.strip() for k, v in m.groupdict().items()):
                return None
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        if m:
            values = m.groupdict()
            def count(key):
                return int(values[key].replace("'", ''))
            for suffix in ('', '1', '2'):
                previous = 'previous_count' + suffix
                if previous in values and count(previous) != count('transferred_count' + suffix) + count('remaining_count' + suffix):
                    return None
            if 'count3' in values and count('transferred_count') != sum(count('count' + str(i)) for i in (1, 2, 3)):
                return None
        return m

    def event(rule, m):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict()})

    def person(rule, m, index, role, signing):
        return _person_event(*context, 'officer_changed', rule, m['name' + str(index)], place=m.groupdict().get('place' + str(index)), role=role, signing=signing, extra=m.groupdict())

    m = match(rf"""L'inscription No (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que le titulaire porte les prénom (?P<given_names>{NAME}) \(et non pas (?P<previous_given_names>{NAME})\)""", 'fr')
    if m:
        return [event('fr.text.given_names_corrected.v1', m)], ''

    m = match(rf"""Nouveau administrateurs avec signature individuelle: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), présidente, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})""", 'fr', rf"""Nouveau administrateurs avec signature individuelle: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), présidente, et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})""")
    if m:
        return [person('fr.text.two_administrators_individual_signing.v1', m, 1, 'présidente', 'Einzelunterschrift'), person('fr.text.two_administrators_individual_signing.v1', m, 2, 'administrateur', 'Einzelunterschrift')], ''

    m = match(rf"""Eingetragene Personen neu oder mutierend: (?P<name1>{NAME}, {NAME}), von (?P<origin1>{NAME}), in (?P<place1>{NAME}), mit Kollektivunterschrift zu zweien; (?P<name2>{NAME}, {NAME}), von (?P<origin2>{NAME}), in (?P<place2>{NAME}), mit Kollektivunterschrift zu zweien""", 'fr')
    if m:
        return [person('fr.text.german_two_signatories.v1', m, 1, None, 'Kollektivunterschrift zu zweien'), person('fr.text.german_two_signatories.v1', m, 2, None, 'Kollektivunterschrift zu zweien')], ''

    m = match(rf"""(?P<name1>{NAME}) cède (?P<transferred_count1>{COUNT}) de ses (?P<previous_count1>{COUNT}) parts sociales de CHF (?P<nominal1>{MONEY}), privilégiées quant au droit de vote, et (?P<transferred_count2>{COUNT}) de ses (?P<previous_count2>{COUNT}) parts sociales de CHF (?P<nominal2>{MONEY}) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvelle associée-gérante avec signature individuelle, avec (?P=transferred_count1) parts de CHF (?P=nominal1), privilégiées quant au droit de vote, et (?P=transferred_count2) part sociale de CHF (?P=nominal2); (?P=name1), qui reste titulaire de (?P<remaining_count1>{COUNT}) parts sociales de CHF (?P=nominal1), privilégiées quant au droit de vote, et (?P<remaining_count2>{COUNT}) part sociale de CHF (?P=nominal2), est nommé président""", 'fr', rf"""(?P<name1>{NAME}) cède (?P<transferred_count1>{COUNT}) de ses (?P<previous_count1>{COUNT}) parts sociales de CHF (?P<nominal1>{MONEY}), privilégiées quant au droit de vote, et (?P<transferred_count2>{COUNT}) de ses (?P<previous_count2>{COUNT}) parts sociales de CHF (?P<nominal2>{MONEY}) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvelle associée-gérante avec signature individuelle, avec (?P=transferred_count1) parts de CHF (?P=nominal1), privilégiées quant au droit de vote, et (?P=transferred_count2) part sociale de CHF (?P=nominal2); (?P=name1), qui reste titulaire de (?P<remaining_count1>{COUNT}) parts sociales de CHF (?P=nominal1), privilégiées quant au droit de vote, et (?P<remaining_count2>{COUNT}) part sociale de CHF (?P=nominal2), est nommé président""")
    if m:
        return [event('fr.text.voting_privileged_shares_transfer.v1', m), person('fr.text.voting_privileged_shares_transfer.v1', m, 1, 'président', None), person('fr.text.voting_privileged_shares_transfer.v1', m, 2, 'associée-gérante', 'Einzelunterschrift')], ''

    m = match(rf"""Mit superprovisorischen Verfügung vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) die Anweisung erteilt, (?P<name1>{NAME}) als einzelzeichnungsberechtigte Sachwalterin im Handelsregister einzutragen""", 'de')
    if m:
        return [person('de.text.interim_custodian_registered.v1', m, 1, 'Sachwalterin', 'Einzelunterschrift')], ''

    m = match(rf"""Der am (?P<deletion_date>{DATE}) gelöschte Verein wird gemäss Beschlusses des Vorstands wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[gestrichen: Der Verein wird auf Antrag des Vereinsvorstands im Handelsregister gelöscht, da er kein nach kaufmännischer Art geführtes Gewerbe betreibe und damit nicht eintragungspflichtig ist\.\]""", 'de')
    if m:
        return [event('de.text.association_reinstated.v1', m)], ''

    m = match(rf"""Vermögensübertragung: Die Gesellschaft überträgt gemäss Vertrag vom (?P<contract_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}), und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}), auf die (?P<recipient>{NAME}), in (?P<recipient_place>{NAME}) \((?P<recipient_uid>{UID})\)\. Gegenleistung: keine""", 'de')
    if m:
        return [event('de.text.assets_transferred_without_consideration.v1', m)], ''

    m = match(rf"""L'inscription (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que l'associée gérante porte le nom de (?P<surname>{NAME}) \(et non (?P<previous_surname>{NAME})\)""", 'fr')
    if m:
        return [event('fr.text.associate_manager_surname_corrected.v1', m)], ''

    m = match(rf"""Das gelöschte Einzelunternehmen wird auf Antrag der Inhaberin erneut ins Handelsregister eingetragen\. \[bisher: Das Einzelunternehmen ist infolge Geschäftsaufgabe erloschen\.\]""", 'de')
    if m:
        return [event('de.text.sole_proprietorship_reinstated.v1', m)], ''

    m = match(rf"""\[La società ha nominato un ufficio di revisione ed effettua una revisione ordinaria o una revisione limitata\. La seguente iscrizione è avvenuta erroneamente\.\]""", 'it')
    if m:
        return [event('it.text.auditor_erroneous_entry_corrected.v1', m)], ''

    m = match(rf"""(?P<name1>{NAME}), qui est élu président des gérants et continue à signer individuellement, cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé avec (?P=transferred_count) parts de CHF (?P=nominal), gérant avec signature individuelle\. (?P=name1) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)""", 'fr', rf"""(?P<name1>{NAME}), qui est élu président des gérants et continue à signer individuellement, cède (?P<transferred_count>{COUNT}) de ses (?P<previous_count>{COUNT}) parts de CHF (?P<nominal>{MONEY}) à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé avec (?P=transferred_count) parts de CHF (?P=nominal), gérant avec signature individuelle\. (?P=name1) reste titulaire de (?P<remaining_count>{COUNT}) parts de CHF (?P=nominal)""")
    if m:
        return [event('fr.text.manager_president_shares_transfer.v1', m), person('fr.text.manager_president_shares_transfer.v1', m, 1, 'président des gérants', 'Einzelunterschrift'), person('fr.text.manager_president_shares_transfer.v1', m, 2, 'associé, gérant', 'Einzelunterschrift')], ''

    m = match(rf"""(?P<holder1>{NAME}) détient désormais (?P<remaining_count1>{COUNT}) parts de CHF (?P<nominal>{MONEY}) et (?P<holder2>{NAME}) détient désormais (?P<remaining_count2>{COUNT}) parts de CHF (?P=nominal) par suite de cession de (?P<transferred_count>{COUNT}) parts de CHF (?P=nominal) à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), nouvel associé pour (?P<count1>{COUNT}) parts de CHF (?P=nominal), à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), nouvel associé pour (?P<count2>{COUNT}) parts de CHF (?P=nominal), et à (?P<name3>{NAME}), de (?P<origin3>{NAME}), à (?P<place3>{NAME}), nouvel associé pour (?P<count3>{COUNT}) parts de CHF (?P=nominal), tous trois sans signature sociale""", 'fr')
    if m:
        return [event('fr.text.shares_transferred_three_unsigned_associates.v1', m), person('fr.text.shares_transferred_three_unsigned_associates.v1', m, 1, 'associé', 'ohne Zeichnungsberechtigung'), person('fr.text.shares_transferred_three_unsigned_associates.v1', m, 2, 'associé', 'ohne Zeichnungsberechtigung'), person('fr.text.shares_transferred_three_unsigned_associates.v1', m, 3, 'associé', 'ohne Zeichnungsberechtigung')], ''

    return [], leftover
