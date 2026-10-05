from __future__ import annotations

import re
from datetime import datetime

from .parser253 import _event, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
MONEY = r"[\d']+(?:\.\d+)?"


def extract_parser265_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Parse complete sample-backed clauses and recover consumed facts from source."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern):
        m = re.fullmatch(pattern + r'\.?', leftover, re.I)
        if m:
            try:
                for key, value in m.groupdict().items():
                    if key.endswith('date') and value:
                        datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                return None
        return m

    def source(pattern, m):
        s = re.search(pattern + r'\.?$', source_text, re.I) if m else None
        return s if s and all(v is None or s[k].strip() == v.strip() for k, v in m.groupdict().items()) else None

    def event(event_type, rule, **payload):
        return _event(*context, event_type, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(r'Liquidationsadresse: c/o (?P<care_of>[^,]+), (?P<street>[^,]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+ b\. [^.;]+)')
    if m:
        return [event('address_changed', 'de.text.liquidation_address_care_of.v1', **m.groupdict(), kind='liquidation_address')], ''

    m = match(rf"(?P<name>{NAME}), maintenant domiciliée à (?P<place>{NAME}), (?P<country>[A-Z]), nommée (?P<role>membre et vice-présidente du conseil d'administration) continue à signer collectivement à deux")
    if m:
        return [person('fr.persons.vice_president_residence_changed.v1', m['name'], place=m['place'], role=m['role'], signing='Kollektivunterschrift zu zweien', extra={'country': m['country']})], ''

    m = match(r'\[gestrichen: Die Gesellschaft ist nun ohne Geschäftsführung\.\]\. Ausgeschiedene Personen und erloschene Unterschriften: (?P<removed>.+?)\. Eingetragene Personen neu oder mutierend: (?P<changed>.+)')
    if m:
        events = []
        for kind, section in [('officer_removed', m['removed']), ('officer_changed', m['changed'])]:
            for clause in section.split(';'):
                item = re.fullmatch(rf"\s*(?P<surname>[^,;]+), (?P<given>[^,;]+), (?P<origin>[^,;]+), in (?P<place>[^,;]+), (?P<role>Gesellschafter(?: und (?:Vorsitzender der Geschäftsführung|Geschäftsführer))?|Geschäftsführer), (?P<signing>ohne Zeichnungsberechtigung|mit Einzelunterschrift|mit Kollektivunterschrift zu zweien)(?:, mit (?P<count>\d+) Stammanteilen zu je CHF (?P<nominal>{MONEY}))?(?: \[bisher: (?P<previous>Gesellschafter, ohne Zeichnungsberechtigung)\])?", clause)
                if not item or (item['count'] and int(item['count']) <= 0):
                    return [], leftover
                signing = item['signing'].removeprefix('mit ')
                events.append(_person_event(*context, kind, 'de.persons.management_restored_sections.v1', item['surname'] + ', ' + item['given'], place=item['place'], role=item['role'], signing=signing, extra={'origin': item['origin'], **({'shares_count': int(item['count']), 'shares_nominal': item['nominal']} if item['count'] else {}), **({'previous': item['previous']} if item['previous'] else {})}))
        return [event('organization_changed', 'de.text.management_absence_annotation_deleted.v1', action='management_absence_annotation_deleted')] + events, ''

    m = match(rf'Statuten geändert am (?P<date>{DATE}) über nicht publikationspflichtige Tatsachen')
    if m:
        return [event('statutes_changed', 'de.text.unpublished_statutes_changed.v1', date=datetime.strptime(m['date'], '%d.%m.%Y').date().isoformat(), detail='not_subject_to_publication')], ''

    m = match(rf"(?P<seller>{NAME}) a cédé (?P<count>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}); par conséquent (?P=seller) et (?P=buyer) sont maintenant chacun associé pour (?P<remaining>\d+) parts de CHF (?P=nominal)")
    if m and int(m['count']) > 0 and int(m['remaining']) >= int(m['count']):
        rule = 'fr.persons.share_transfer_equal_holdings.v1'
        return [person(rule, m[k], role='associé', extra={'action': action, 'shares_count': int(m['remaining']), 'shares_nominal': m['nominal'], 'transferred_count': int(m['count']), 'counterparty': m[other]}) for k, other, action in [('seller', 'buyer', 'shares_transferred'), ('buyer', 'seller', 'shares_received')]], ''

    pattern = rf'(?P<a>{NAME}), (?P<b>{NAME}), (?P<c>{NAME}), (?P<d>{NAME}) et (?P<e>{NAME}) sont nommés liquidateurs'
    m = match(pattern + rf'(?: avec signature collective à deux\.)? (?P<f>{NAME}) et (?P<g>{NAME}) sont nommés liquidateurs avec signature collective à deux, toutefois pas entre eux')
    s = source(pattern + rf' avec signature collective à deux\. (?P<f>{NAME}) et (?P<g>{NAME}) sont nommés liquidateurs avec signature collective à deux, toutefois pas entre eux', m)
    if s:
        return [person('fr.persons.liquidators_restricted_collective_signing.v1', m[k], role='liquidateur', signing='Kollektivunterschrift zu zweien', extra={'action': 'appointed', **({'signing_restriction': 'not_with_each_other', 'excluded_partner': m['g' if k == 'f' else 'f']} if k in 'fg' else {})}) for k in 'abcdefg'], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens qu'une signature collective à deux a été conférée à (?P<name>{NAME}) \(et non pas (?P<previous_name>[^()]+)\)")
    if m:
        return [person('fr.persons.collective_signatory_name_corrected.v1', m['name'], signing='Kollektivunterschrift zu zweien', extra={**m.groupdict(), 'action': 'corrected'})], ''

    m = match(rf'Vermögensübertragung: Der Verein überträgt gemäss Vertrag vom (?P<agreement_date>{DATE}) und Inventar per (?P<inventory_date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>{NAME}), in (?P<place>{NAME}) \((?P<recipient_uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\)\. Gegenleistung: keine')
    if m:
        return [event('assets_transferred', 'de.text.association_assets_transferred.v1', **m.groupdict(), kind='asset_transfer', currency='CHF', consideration='none')], ''

    pattern = rf'Persona iscritta corretta e nuova persona iscritta: (?P<surname>[^,;]+), (?P<given>[^,;]+), cittadino italiano, in (?P<place>{NAME}), socio, senza diritto di firma, con (?P<count>\d+) quote da CHF (?P<nominal>{MONEY}) '
    tail = rf'; (?P<other_surname>[^,;]+), (?P<other_given>[^,;]+), cittadino italiano, in (?P<other_place>{NAME}), gerente, con firma collettiva a due'
    m = match(pattern + tail)
    s = source(pattern + r'\[no: (?P<previous_role>socio e gerente), con firma collettiva a due\]' + tail, m)
    if s and int(m['count']) > 0:
        rule = 'it.persons.associate_corrected_manager_added.v1'
        return [person(rule, m['surname'] + ', ' + m['given'], place=m['place'], role='socio', signing='ohne Zeichnungsberechtigung', extra={'action': 'corrected', 'previous_role': s['previous_role'], 'shares_count': int(m['count']), 'shares_nominal': m['nominal']}), person(rule, m['other_surname'] + ', ' + m['other_given'], place=m['other_place'], role='gerente', signing='Kollektivunterschrift zu zweien', extra={'action': 'appointed'})], ''

    m = match(rf"L'inscription no\. (?P<entry>\d+) du (?P<entry_date>{DATE}) \(publication FOSC du (?P<notice_date>{DATE}) page (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens qu'un associé-gérant se nomme (?P<name>{NAME}) \(et non (?P<previous_given>[^()]+)\)")
    if m:
        return [person('fr.persons.associate_manager_given_name_corrected.v1', m['name'], role='associé-gérant', extra={**m.groupdict(), 'action': 'corrected'})], ''

    pattern = rf'Secondo dichiarazione del (?P<date>{DATE}) la società non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata'
    m = match(pattern)
    s = source(rf'\[no: Secondo dichiarazione del (?P<previous_date>{DATE}) la società non è soggetta alla revisione ordinaria e rinuncia a una revisione limitata\.\]\. ' + pattern, m)
    if s:
        try:
            datetime.strptime(s['previous_date'], '%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('audit_requirement_changed', 'it.text.audit_opt_out_date_corrected.v1', **s.groupdict(), kind='limited_audit_waiver', action='corrected')], ''

    pattern = rf'Streichung der Statutenbestimmung über die mit Gewährungsbeschluss vom (?P<date>{DATE}) eingeführte bedingte Kapitalerhöhung'
    m = match(pattern)
    s = source(pattern + rf' \[nicht: Streichung der Statutenbestimmung über die mit Gewährungsbeschluss vom (?P<previous_date>{DATE}) eingeführte bedingte Kapitalerhöhung\]', m)
    if s:
        try:
            datetime.strptime(s['previous_date'], '%d.%m.%Y')
        except ValueError:
            return [], leftover
        return [event('capital_changed', 'de.text.conditional_capital_clause_deletion_corrected.v1', **s.groupdict(), action='clause_deleted_corrected')], ''
    return [], leftover
