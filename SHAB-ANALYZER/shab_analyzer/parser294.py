from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, UID


def extract_parser294_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete, sample-backed clauses; keep unsupported residue."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang='fr'):
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

    def person(rule, name, *, event_type='officer_changed', **payload):
        return _person_event(*context, event_type, rule, name, **payload)

    # The supplied XML labels this German wording as French, including its typos.
    m = match(rf'Ein Teil der Aktiven und Passiven geht gemäss Spaltungsvetrag autf die neu gegründete (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>{UID})\) über')
    if m:
        return [event('de.text.spin_off_new_company_typo.v1', action='spin_off', recipient_new=True, **m.groupdict())], ''

    m = match(rf"Liquidateurs: l'associé-gérant (?P<name1>{NAME}) et le directeur (?P<name2>{NAME}), lesquels continuent à signer individuellement")
    if m:
        return [person('fr.persons.two_existing_liquidators.v1', m[key], role='liquidateur', signing='Einzelunterschrift', extra={'previous_role': role, 'signing_continued': True}) for key, role in [('name1', 'associé-gérant'), ('name2', 'directeur')]], ''

    m = match(r"Adjonction d'une version linguistique à la raison sociale de l'établissement principal\. Raison sociale de l'établissement principal: (?P<name>[^()]+) \((?P<translation1>[^()]+)\) \((?P<translation2>[^()]+)\)")
    if m:
        return [event('fr.text.principal_name_language_added.v1', action='principal_name_translations_changed', name=m['name'], translations=[m['translation1'], m['translation2']])], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) wurde der Nachlassvertrag mit Dividendenvergleich bestätigt\. \[bisher: Mit Entscheid vom (?P<previous_date>{DATE}) wurde eine definitive Nachlassstundung für sechs Monate bis (?P<end_date>{DATE}) bewilligt\. Als Sachwalterin wird die (?P<administrator>[^()]+) \((?P<administrator_uid>{UID})\), Mandatsleitung durch (?P<mandate_leader>{NAME}), (?P<address>[^\[\]]+), eingesetzt\.\]', 'de')
    if m and datetime.strptime(m['previous_date'], '%d.%m.%Y') <= datetime.strptime(m['end_date'], '%d.%m.%Y') <= datetime.strptime(m['decision_date'], '%d.%m.%Y'):
        return [event('de.text.dividend_composition_confirmed.v1', action='composition_confirmed', kind='dividend_composition', **m.groupdict())], ''

    m = match(rf'Signature collective à deux est conférée à (?P<name>{NAME})')
    if m:
        return [person('fr.persons.collective_signing_conferred.v1', m['name'], signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>{COUNT}), TR-Nr\. (?P<entry>{COUNT}) vom TR-Datum (?P<entry_date>{DATE}) wurde als letztes SHAB Zitat versehentlich SHAB Nr\. (?P<wrong_notice>{COUNT}) vom (?P<wrong_date>{DATE}) genannt, statt SHAB Nr\. (?P<notice>{COUNT}) vom (?P<notice_date>{DATE})', 'de')
    if m:
        return [event('de.text.previous_notice_citation_corrected.v1', action='notice_reference_corrected', **m.groupdict())], ''

    m = match(rf"L'associé (?P<name>{NAME}) exerce désormais la signature sociale, individuellement")
    if m:
        return [person('fr.persons.associate_individual_signing.v1', m['name'], role='associé', signing='Einzelunterschrift')], ''

    # Validate the entire pair of capital clauses before emitting either event.
    capital = rf'Die Gesellschaft hat mit Beschluss vom (?P<decision_date>{DATE}) die Bestimmungen zur (?P<kind>genehmigten|bedingten) Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\. \. \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P<previous_date>{DATE}) die Bestimmungen zur (?P<previous_kind>genehmigte|bedingten) Kapitalerhöhung gemäss näherer Umschreibung in den Statuten geändert\.\]\. \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P<adjustment1_date>{DATE}) die (?P<adjusted_kind>genehmigte|bedingte) Kapitalerhöhung vom (?P=previous_date) gemäss näherer Umschreibung in den Statuten angepasst\.\]\. \[gestrichen: Die Gesellschaft hat mit Beschluss vom (?P<adjustment2_date>{DATE}) die (?P=adjusted_kind) Kapitalerhöhung vom (?P=previous_date) gemäss näherer Umschreibung in den Statuten angepasst\.\]'
    if language == 'de':
        parts = leftover.rstrip('.').split(']. Die Gesellschaft')
        if len(parts) == 2:
            matches = [re.fullmatch(capital, parts[0] + ']'), re.fullmatch(capital, 'Die Gesellschaft' + parts[1])]
            if all(matches):
                try:
                    valid = [m['kind'] for m in matches] == ['genehmigten', 'bedingten'] and [m['previous_kind'] for m in matches] == ['genehmigte', 'bedingten'] and [m['adjusted_kind'] for m in matches] == ['genehmigte', 'bedingte'] and matches[0]['decision_date'] == matches[1]['decision_date']
                    for m in matches:
                        dates = [datetime.strptime(m[key], '%d.%m.%Y') for key in ('previous_date', 'adjustment1_date', 'adjustment2_date', 'decision_date')]
                        valid = valid and dates == sorted(dates)
                except ValueError:
                    valid = False
                if valid:
                    return [event('de.text.authorized_conditional_capital_amended.v1', action='capital_provisions_amended', **m.groupdict()) for m in matches], ''

    m = match(rf'(?P<name>{NAME}) est nommé sous-directeur(?: avec signature collective à deux;| ;) sa procuration est radiée')
    if m and re.search(re.escape(m['name']) + r' est nommé sous-directeur avec signature collective à deux; sa procuration est radiée\.?$', source_text):
        return [person('fr.persons.deputy_director_procuration_removed.v1', m['name'], role='sous-directeur', signing='Kollektivunterschrift zu zweien', extra={'procuration_removed': True})], ''

    # Preserve the sample's incomplete origin/place wording without repairing it.
    m = match(rf'Signature collective à deux est conférée à (?P<name1>{NAME}), de et (?P<place1>{NAME}), et (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME}), tous deux directeurs')
    if m:
        rule = 'fr.persons.two_directors_signing_incomplete_place.v1'
        return [person(rule, m['name1'], role='directeur', signing='Kollektivunterschrift zu zweien', extra={'origin_place_text': 'de et ' + m['place1']}), person(rule, m['name2'], role='directeur', place=m['place2'], signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin2']})], ''

    m = match(rf'Ausgeschiedene Personen und erloschene Unterschriften: (?P<name1>[^.;]+?), von (?P<origin1>{NAME}), in (?P<place1>{NAME}), Präsident des Verwaltungsrates, mit Einzelunterschrift\. Eingetragene Personen neu oder mutierend: (?P<name2>[^.;]+?), (?P<nationality>{NAME}) Staatsangehöriger, in (?P<place2>{NAME}), Mitglied des Verwaltungsrates, mit Einzelunterschrift \[bisher: Mitglied des Verwaltungsrates, ohne Zeichnungsberechtigung\]')
    if m:
        rule = 'de.persons.board_departure_signing_changed_fr_xml.v1'
        return [person(rule, m['name1'], event_type='officer_removed', role='Präsident des Verwaltungsrates', place=m['place1'], extra={'action': 'removed', 'origin': m['origin1'], 'previous_signing': 'Einzelunterschrift'}), person(rule, m['name2'], role='Mitglied des Verwaltungsrates', place=m['place2'], signing='Einzelunterschrift', extra={'nationality': m['nationality'], 'previous_signing': 'ohne Zeichnungsberechtigung'})], ''

    m = match(rf'Fatti particolari: \[La disposizione statutaria relativa alla prevista assunzione di beni del (?P<provision_date>{DATE}) è abrogata, in quanto sono trascorsi più di 10 anni dalla sua introduzione\. La relativa iscrizione nel registro di commercio è quindi cancellata\]', 'it')
    if m:
        return [event('it.text.planned_asset_acquisition_expired.v1', action='planned_asset_acquisition_provision_removed', reason='over_ten_years', **m.groupdict())], ''

    return [], leftover
