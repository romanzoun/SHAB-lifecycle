from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, UID


# Dotted abbreviations occur in the supplied company names. Sentence suffixes
# must not become part of a company name.
COMPANY_NAME = r"(?:[\w’'&()-]+|(?:[A-Z]\.){2,})(?: (?:[\w’'&()-]+|(?:[A-Z]\.){2,}))*"

def extract_parser308_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume complete sample-backed clauses, preserving unsupported input."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, lang, source_pattern=None):
        if language != lang:
            return None
        m = re.fullmatch(pattern + r'\.?', leftover)
        if m and source_pattern:
            source = re.search(source_pattern + r'\.?$', source_text)
            if not source or any((not (source[k].strip() == v.strip() or re.fullmatch(r'[A-Z]\.', v.strip()) and source[k].strip().endswith(v.strip())) if k == 'company_name' else source[k].strip() != v.strip()) for k, v in m.groupdict().items()):
                return None
            m = source
        if m:
            try:
                if 'time' in m.groupdict():
                    datetime.strptime(m['time'], '%H.%M')
                for key, value in m.groupdict().items():
                    if key.endswith('_date'):
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def event(rule, m):
        return _event(*context, 'organization_changed', rule, {'action': rule.split('.')[2], **m.groupdict()})

    def person(rule, m, key='name', **kwargs):
        return _person_event(*context, 'officer_changed', rule, m[key], extra=m.groupdict(), **kwargs)

    m = match(rf"""Nouveau numéro d'identification du siège principal: (?P<uid>{UID}) \[précédemment: Numéro d'identification du siège principal: (?P<previous_uid>CH-\d{{3}}\.\d\.\d{{3}}\.\d{{3}}-\d), \]""", 'fr')
    if m:
        return [event('fr.text.head_office_uid_replaced.v1', m)], ''

    m = match(rf"""Bemerkungen zum Hauptsitz neu: Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) mit Wirkung ab dem (?P<effective_date>{DATE}), (?P<time>\d{{2}}\.\d{{2}}) Uhr, über den bereits aufgelösten Hauptsitz den Konkurs eröffnet""", 'de')
    if m:
        return [event('de.text.head_office_bankruptcy_opened.v1', m)], ''

    m = match(rf"""Procuration collective à deux, sauf entre eux, a été conférée à (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), et à (?P<name2>{NAME}), de (?P<origin2>{NAME}), à (?P<place2>{NAME})""", 'fr')
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.text.two_procurations_except_between_them.v1', m['name' + str(i)], place=m['place' + str(i)], role=None, signing='Kollektivprokura zu zweien', extra={**m.groupdict(), 'signing_restriction': 'sauf entre eux'}) for i in (1, 2)], ''

    m = match(rf"""Par ordonnance du (?P<decision_date>{DATE}), le Tribunal cantonal a suspendu l'exécution du jugement de faillite rendu le (?P<judgment_date>{DATE})\. Par conséquent la raison sociale redevient: (?P<company_name>{COMPANY_NAME})""", 'fr')
    if m:
        return [event('fr.text.bankruptcy_execution_suspended_name_restored.v1', m)], ''

    m = match(rf"""(?P<name1>{NAME}), maintenant à (?P<place1>{NAME}), et (?P<name2>{NAME}), maintenant à (?P<place2>{NAME}), sont nommés liquidateurs(?: avec signature individuelle)?""", 'fr', rf"""(?P<name1>{NAME}), maintenant à (?P<place1>{NAME}), et (?P<name2>{NAME}), maintenant à (?P<place2>{NAME}), sont nommés liquidateurs avec signature individuelle""")
    if m:
        return [_person_event(*context, 'officer_changed', 'fr.text.two_liquidators_domiciles_changed.v1', m['name' + str(i)], place=m['place' + str(i)], role='liquidateur', signing='Einzelunterschrift', extra=m.groupdict()) for i in (1, 2)], ''

    m = match(rf"""Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst\. (?P<company_name>{COMPANY_NAME}|[A-Z]\.) in Liquidation \((?P<translated_name>{COMPANY_NAME}) en liquidation\)\. Die statutarische Klausel betreffend die Übertragbarkeit der Namenaktien ist gelöscht\. Eingetragene Person geändert: (?P<name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, nun Verwaltungsratsmitglied, Liquidator, Einzelunterschrift""", 'de', rf"""Die Gesellschaft ist laut Beschluss der Generalversammlung vom (?P<decision_date>{DATE}) aufgelöst\. Firma neu: (?P<company_name>{COMPANY_NAME}) in Liquidation \((?P<translated_name>{COMPANY_NAME}) en liquidation\)\. Die statutarische Klausel betreffend die Übertragbarkeit der Namenaktien ist gelöscht\. Eingetragene Person geändert: (?P<name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, nun Verwaltungsratsmitglied, Liquidator, Einzelunterschrift""")
    if m:
        return [event('de.text.dissolution_liquidator_transferability_deleted.v1', m), person('de.text.dissolution_liquidator_transferability_deleted.v1', m, role='Verwaltungsratsmitglied, Liquidator', signing='Einzelunterschrift')], ''

    m = match(rf"""Infolge Unmöglichkeit konnten (?P<properties>drei) Grundstücke gemäss Vermögensübertragungsvertrag vom (?P<contract_date>{DATE}) nicht übertragen werden\. Das Kapital wurde nicht vollständig liberiert\. Durch nachträgliche Leistung von Einlagen wurde das Kapital inzwischen vollständig liberiert""", 'de')
    if m:
        return [event('de.text.capital_fully_paid_after_failed_asset_transfer.v1', m)], ''

    m = match(rf"""\[L'indicazione relativa all'organizzazione è cancellata a seguito dell'abrogazione della disposizione di cui all'art\. (?P<article>95 cpv\. 1 lett\. h ORC)\]""", 'it')
    if m:
        return [event('it.text.foundation_organization_entry_deleted.v1', m)], ''

    m = match(rf"""Mit Entscheid vom (?P<decision_date>{DATE}) hat das (?P<court>{NAME}) der Gesellschaft die Verlängerung der definitiven Nachlassstundung um (?P<months>{COUNT}) Monate bewilligt bis (?P<end_date>{DATE})""", 'de')
    if m:
        return [event('de.text.definitive_moratorium_extension_granted.v1', m)], ''

    m = match(rf"""L'inscription n° (?P<entry>{COUNT}) du (?P<entry_date>{DATE}) est rectifiée en ce sens que (?P<name>{NAME}) n'est en réalité pas membre du conseil de fondation, en revanche (?:il )?signe bien collectivement à deux""", 'fr')
    if m:
        return [person('fr.text.foundation_board_membership_denied_signing_corrected.v1', m, signing='Kollektivunterschrift zu zweien')], ''

    m = match(rf"""Nuovo nome: (?P<company_name>{NAME}) in liquidazione\. Nuova organizzazione: \[L'indicazione relativa all'organizzazione è cancellata a seguito dell'abrogazione della disposizione di cui all'art\. (?P<organization_article>92 lett\. j ORC)\.\]\. L'associazione è sciolta per legge ai sensi dell'art\. (?P<dissolution_article>77 CC), in quanto la direzione non può più essere costituita conformemente allo statuto""", 'it')
    if m:
        return [event('it.text.association_dissolved_by_law_organization_deleted.v1', m)], ''

    m = match(rf"""\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<authorization_date>{DATE}) eingeführte genehmigte Kapitalerhöhung infolge Zeitablauf\.\] \[gestrichen: Die Gesellschaft hat bei der Gründung vom (?P=authorization_date) eine genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.\]""", 'de')
    if m:
        return [event('de.text.authorized_capital_expired_clause_deleted.v1', m)], ''

    return [], leftover
