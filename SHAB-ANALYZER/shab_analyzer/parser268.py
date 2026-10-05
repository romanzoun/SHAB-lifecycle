from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal

from .parser253 import _event, _person_event
from .parser267 import NAME, DATE, COUNT, MONEY


def extract_parser268_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Extract bounded, sample-backed corrections and register changes."""
    leftover = text.strip()
    context = publication_id, published_at, org_uid, plz, canton

    def match(pattern, source_pattern=None):
        m = re.fullmatch(pattern + r'\.?', leftover)
        if not m:
            return None
        if source_pattern:
            s = re.search(source_pattern + r'\.?$', source_text)
            if not s or any(s[k].strip() != v.strip() for k, v in m.groupdict().items() if v is not None):
                return None
            m = s
        try:
            for k, v in m.groupdict().items():
                if k.endswith('date'):
                    datetime.strptime(v, '%d.%m.%Y')
        except ValueError:
            return None
        return m

    def event(kind, rule, **payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, *, removed=False, **kwargs):
        return _person_event(*context, 'officer_removed' if removed else 'officer_changed', rule, name, **kwargs)

    def num(value):
        return Decimal(value.replace("'", ''))

    m = match(rf'Berichtigung der Eintragung Nr\. (?P<entry>\d+) vom (?P<entry_date>{DATE}) \(SHAB vom (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\): (?P<name>{NAME}), Mitglied des Vorstandes, Kassier, Kollektivunterschrift zu zweien, von (?P<origin>[^()]+) \(und nicht (?P<previous_name>{NAME}), von (?P<previous_origin>[^()]+)\)')
    if m:
        return [person('de.persons.board_name_origin_corrected.v1', m['name'], role='Mitglied des Vorstandes, Kassier', signing='Kollektivunterschrift zu zweien', extra=m.groupdict())], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}) p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que (?P<name>{NAME}) est en réalité membre de la direction générale adjoint et non pas membre de la direction générale")
    if m:
        return [person('fr.persons.deputy_general_management_corrected.v1', m['name'], role='membre de la direction générale adjoint', extra={**m.groupdict(), 'previous_role': 'membre de la direction générale'})], ''

    m = match(rf"Complément: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id\. (?P<notice_id>\d+)\) est complétée dans ce sens: Capital-actions nouveau: CHF (?P<capital>{MONEY}), entièrement libéré, divisé en (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), nominatives \(jusqu'ici: (?P=count) actions de CHF (?P=nominal), au porteur\)")
    if m and num(m['count']) > 0 and num(m['nominal']) > 0 and num(m['count'])*num(m['nominal']) == num(m['capital']):
        return [event('capital_changed', 'fr.text.registered_share_conversion_completed.v1', **m.groupdict(), currency='CHF', fully_paid=True, share_kind='registered', previous_share_kind='bearer')], ''

    m = match(rf"Rectificatif: l'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée en ce sens que le titulaire se nomme (?P<name>[^()]+) \(et non (?P<previous_name>{NAME}), comme publié\)")
    if m:
        return [person('fr.persons.proprietor_name_corrected.v1', m['name'], role='titulaire', extra=m.groupdict())], ''

    m = match(rf"En complément de l'inscription (?P<entry>\d+) du (?P<entry_date>{DATE}), dépôt d'un nouvel exemplaire des statuts")
    if m:
        return [event('statutes_changed', 'fr.text.statutes_copy_filed.v1', **m.groupdict(), action='new_copy_filed')], ''

    m = match(rf'Mit Entscheid vom (?P<decision_date>{DATE}) hat der Einzelrichter am Kantonsgericht die definitive Nachlassstundung bis (?P<until_date>{DATE}) verlängert\. \[bisher: Mit Entscheid vom (?P<previous_decision_date>{DATE}) hat der Einzelrichter am Kantonsgericht die definitive Nachlassstundung bis (?P<previous_until_date>{DATE}) verlängert\.\]')
    if m and datetime.strptime(m['until_date'], '%d.%m.%Y') > datetime.strptime(m['decision_date'], '%d.%m.%Y') and datetime.strptime(m['until_date'], '%d.%m.%Y') > datetime.strptime(m['previous_until_date'], '%d.%m.%Y'):
        return [event('status_changed', 'de.text.definitive_moratorium_extended.v1', **m.groupdict(), action='moratorium_extended', definitive=True)], ''

    m = match(rf"Rectificatif: l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), p\. (?P<notice_ref>\d+/\d+)\) est rectifiée comme suit: Apport en nature et reprise de biens selon convention d'apport du (?P<agreement_day>\d{{1,2}}) septembre (?P<agreement_year>\d{{4}}): les parcelles (?P<parcel_from>\d+) à (?P<parcel_to>\d+) de la Commune d'(?P<municipality>[^()]+) \((?P<parcel_canton>[A-Z]{{2}})\) pour CHF (?P<assets>{MONEY}); en contrepartie, est remis (?P<count>{COUNT}) actions de CHF (?P<nominal>{MONEY}), le solde de CHF (?P<balance>{MONEY}) constituant une créance de l'apporteur contre la société \(le solde n'étant pas de CHF (?P<previous_balance>{MONEY}), comme publié\)")
    if m:
        try:
            agreement_date = datetime(int(m['agreement_year']), 9, int(m['agreement_day'])).date().isoformat()
        except ValueError:
            return [], leftover
        if num(m['count']) > 0 and num(m['nominal']) > 0 and num(m['balance']) >= 0 and num(m['count'])*num(m['nominal'])+num(m['balance']) == num(m['assets']) and int(m['parcel_from']) <= int(m['parcel_to']):
            return [event('capital_changed', 'fr.text.contribution_receivable_corrected.v1', **m.groupdict(), agreement_date=agreement_date, currency='CHF', action='contribution_receivable_corrected')], ''

    m = match(rf"L'associé (?P<name>{NAME}) est élu gérant président avec signature individuelle")
    if m:
        return [person('fr.persons.associate_elected_president_manager.v1', m['name'], role='associé gérant président', signing='Einzelunterschrift', extra={'action': 'appointed'})], ''

    m = match(r'Die Gesellschaft wurde irrtümlich gelöscht, obwohl die Voraussetzungen dafür nicht gegeben waren\. Der Eintrag besteht entsprechend den bisherigen Tatsachen weiter\. \[bisher: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft im Sinne von Art\. 159 Abs\. 5 lit\. a\. HRegV von Amtes wegen gelöscht\.\]')
    if m:
        return [event('status_changed', 'de.text.erroneous_deletion_revoked.v1', action='registration_maintained', previous_deletion_revoked=True)], ''

    pattern = rf"Administration: (?P<name1>{NAME}), jusqu'ici secrétaire, nommé président et (?P<name2>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]{{2}}), vice-président, tous deux"
    ending = r'; les pouvoirs de (?P=name1) sont modifiés en ce sens'
    m = match(pattern + r'(?: avec signature collective à deux)?\s*' + ending, pattern + r' avec signature collective à deux' + ending)
    if m:
        rule = 'fr.persons.board_president_vice_president_collective.v1'
        return [person(rule, m['name1'], role='président', signing='Kollektivunterschrift zu zweien', extra={'previous_role': 'secrétaire'}), person(rule, m['name2'], place=m['place'], role='vice-président', signing='Kollektivunterschrift zu zweien', extra={'origin': m['origin'], 'country': m['country']})], ''

    m = match(rf'Les associés-gérants (?P<name1>{NAME}) et (?P<name2>{NAME}), cède chacun (?P<count>{COUNT}) de leurs (?P<before1>{COUNT}) et (?P<before2>{COUNT}) parts de CHF (?P<nominal>{MONEY}) respectives à (?P<recipient>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>{COUNT}) parts de CHF (?P=nominal), sans signature\. (?P=name1) et (?P=name2) restent titulaires respectivement de (?P<remaining1>{COUNT}) et (?P<remaining2>{COUNT}) parts de CHF (?P=nominal)')
    if m and num(m['count']) > 0 and num(m['nominal']) > 0 and num(m['received']) == 2*num(m['count']) and all(num(m['before'+str(i)])-num(m['count']) == num(m['remaining'+str(i)]) >= 0 for i in [1, 2]):
        rule = 'fr.persons.two_managers_partial_share_transfer.v1'
        return [*[person(rule, m['name'+str(i)], role='associé-gérant', extra={'action': 'shares_transferred', 'shares_before': int(num(m['before'+str(i)])), 'shares_count': int(num(m['remaining'+str(i)])), 'shares_transferred': int(num(m['count'])), 'nominal': m['nominal'], 'recipient': m['recipient']}) for i in [1, 2]], person(rule, m['recipient'], place=m['place'], role='associé', extra={'origin': m['origin'], 'shares_count': int(num(m['received'])), 'shares_nominal': m['nominal'], 'without_signature': True, 'action': 'shares_received'})], ''

    m = match(rf"Selon arrêt du (?P<decision_date>{DATE}) du Tribunal cantonal, les modifications apportées par l'inscription n° (?P<entry>\d+) du (?P<entry_date>{DATE}) \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\) sont nulles\. Personnes réinscrites: (?P<name1>{NAME}), de (?P<origin1>{NAME}), à (?P<place1>{NAME}), administratrice, signature individuelle; (?P<name2>{NAME}), du (?P<origin2>{NAME}), à (?P<place2>{NAME}), directeur, signature collective à deux\. Persones radiées: (?P<name3>{NAME}), administrateur, secrétaire, signature individuelle; (?P<name4>{NAME}), administrateur, président, signature collective à deux")
    if m:
        rule = 'fr.persons.court_annulment_reinstatements.v1'
        return [event('organization_changed', rule, action='registration_changes_annulled', **{k: m[k] for k in ['decision_date', 'entry', 'entry_date', 'notice_date', 'notice_id']}), *[person(rule, m['name'+str(i)], removed=i > 2, place=m.groupdict().get('place'+str(i)), role=['administratrice', 'directeur', 'administrateur secrétaire', 'administrateur président'][i-1], signing='Einzelunterschrift' if i % 2 else 'Kollektivunterschrift zu zweien', extra={'action': 'reinstated' if i <= 2 else 'removed', **({'origin': m['origin'+str(i)]} if i <= 2 else {})}) for i in range(1, 5)]], ''

    return [], leftover
