from __future__ import annotations

import re

from .parser253 import _event, _iso_date, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
MONEY = r"[\d']+(?:\.\d+)?"
UID = r'CHE-\d{3}\.\d{3}\.\d{3}'


def extract_parser260_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Consume only complete families evidenced by the parser260 fixtures."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf'Gemäss Gründererklärung vom (?P<date>{DATE}) untersteht die Gesellschaft keiner ordentlichen Revision und verzichtet auf eine eingeschränkte Revision')
    if m:
        return [event('auditor_changed', 'de.text.founders_declaration_audit_opt_out.v1', {'action': 'opted_out', 'declaration_date': _iso_date(m['date']), 'ordinary_audit_required': False, 'limited_audit_waived': True})], ''

    m = match(rf"Par ordonnance du (?P<date>{DATE}), le (?P<court>{NAME}) a suspendu l'exécution du jugement de faillite rendu le (?P<judgment_date>{DATE})\. Par conséquent, la raison sociale redevient: (?P<name>[^.;]+)")
    if m:
        return [event('status_changed', 'fr.text.bankruptcy_execution_suspended_name_restored.v1', {'kind': 'bankruptcy', 'action': 'execution_suspended', 'date': _iso_date(m['date']), 'judgment_date': _iso_date(m['judgment_date']), 'court': m['court'], 'restored_name': m['name']})], ''

    m = match(rf"(?P<statutes_date>{DATE})\. Suppression de la clause statutaire relative à l'augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<date>{DATE}), le délai étant écoulé \[biffé: Augmentation autorisée du capital fondée sur la décision d'autorisation du (?P<old_date>{DATE})\]")
    if m and m['date'] == m['old_date']:
        return [event('capital_changed', 'fr.text.authorized_capital_expired_clause_deleted.v1', {'kind': 'authorized_capital_clause', 'action': 'statutory_provision_deleted', 'authorization_date': _iso_date(m['date']), 'statutes_date': _iso_date(m['statutes_date']), 'reason': 'expired'})], ''

    m = match(rf'Eingetragene Person geändert: (?P<name>{NAME}), Inhaber, Einzelunterschrift, jetzt in (?P<place>{NAME})')
    if m:
        return [person('de.persons.owner_residence_changed.v1', m['name'], role='Inhaber', signing='Einzelunterschrift', place=m['place'], extra={'action': 'domicile_changed'})], ''

    m = match(rf"(?P<name>{NAME}), jusqu'ici directeur, est administrateur unique et continue à signer individuellement")
    if m:
        return [person('fr.persons.director_to_sole_administrator.v1', m['name'], role='administrateur unique', signing='Einzelunterschrift', extra={'action': 'role_changed', 'previous_role': 'directeur'})], ''

    m = match(rf'Nuove persone iscritte o modifiche: (?P<surname_a>{NAME}), (?P<given_a>{NAME}), da (?P<origin_a>{NAME}), in (?P<place_a>{NAME}), presidente, con firma individuale; (?P<surname_b>{NAME}), (?P<given_b>{NAME}), da (?P<origin_b>{NAME}), in (?P<place_b>{NAME}), gerente, con firma individuale, \[finora: in (?P<previous_place>{NAME})\]')
    if m:
        rule = 'it.persons.president_and_manager_residence_changed.v1'
        return [person(rule, f"{m['surname_a']}, {m['given_a']}", role='presidente', signing='Einzelunterschrift', place=m['place_a'], extra={'action': 'new_or_changed', 'origin': m['origin_a']}), person(rule, f"{m['surname_b']}, {m['given_b']}", role='gerente', signing='Einzelunterschrift', place=m['place_b'], extra={'action': 'domicile_changed', 'origin': m['origin_b'], 'previous_place': m['previous_place']})], ''

    m = match(rf'Die am (?P<deletion_date>{DATE}) gelöschte Gesellschaft wird auf Grund des Entscheids des (?P<court>[^.]+) vom (?P<date>{DATE}) zum Zwecke der Liquidation wieder in das Handelsregister eingetragen und besteht entsprechend den früheren Eintragungen weiter\. \[gestrichen: Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde, wird die Gesellschaft in Anwendung von Art\. (?P<article>159 Abs\. 5 lit\. a HRegV) von Amtes wegen gelöscht\.\]')
    if m:
        return [event('status_changed', 'de.text.reinstated_for_liquidation_after_deletion.v1', {'action': 'reinstated', 'purpose': 'liquidation', 'deleted': False, 'deletion_date': _iso_date(m['deletion_date']), 'decision_date': _iso_date(m['date']), 'court': m['court'], 'removed_deletion_legal_basis': m['article']})], ''

    m = match(rf"Transfert de patrimoine: Selon contrat du (?P<date>{DATE}), le titulaire a transféré des actifs pour CHF (?P<assets>{MONEY}) et des passifs envers les tiers pour CHF (?P<liabilities>{MONEY}), à (?P<recipient>[^()]+) \((?P<uid>{UID})\) à (?P<place>{NAME})\. Contre-prestation: CHF (?P<consideration>{MONEY})")
    if m:
        return [event('organization_changed', 'fr.text.sole_proprietor_asset_transfer.v1', dict(m.groupdict(), kind='asset_transfer', currency='CHF', date=_iso_date(m['date'])))], ''

    m = match(rf'Mit Urteil des Konkursrichters des (?P<court>{NAME}) vom (?P<date>{DATE}) ist das Konkursverfahren geschlossen worden\. Das Einzelunternehmen wird von Amtes wegen gelöscht')
    if m:
        return [event('status_changed', 'de.text.sole_proprietor_bankruptcy_closed_deleted.v1', {'kind': 'bankruptcy', 'action': 'closed_and_deleted_ex_officio', 'date': _iso_date(m['date']), 'court': m['court'], 'deleted': True})], ''

    # The legacy address rule stops at the abbreviation "b.". Require the
    # complete source address before consuming its otherwise ambiguous residue.
    m = re.search(r'Weitere Adressen: (?P<address>[^,.;]+), (?P<postal_code>\d{4}) (?P<place>[^.;]+ b\. (?P<tail>[^.;]+))\.$', source_text)
    if m and leftover == m['tail']:
        return [event('address_changed', 'de.text.additional_address_abbreviated_place.v1', {'action': 'added', 'address': m['address'], 'postal_code': m['postal_code'], 'place': m['place']})], ''

    m = match(rf'(?P<seller>{NAME}), maintenant associé pour (?P<remaining>\d+) parts de CHF (?P<nominal>{MONEY}), par suite de cession de (?P<count>\d+) parts de CHF (?P<transfer_nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), (?P<country>[A-Z]), nouvelle associée pour (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), sans signature sociale')
    if m:
        count, remaining = int(m['count']), int(m['remaining'])
        if count <= 0 or count != int(m['received']) or len({m[k] for k in ('nominal', 'transfer_nominal', 'buyer_nominal')}) != 1:
            return [], leftover
        rule = 'fr.persons.share_transfer_remaining_and_new_associate.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        return [person(rule, m['seller'], role='associé', extra=dict(common, action='shares_transferred', shares_count=remaining, shares_transferred=count)), person(rule, m['buyer'], role='associée', signing='ohne Unterschrift', place=m['place'], extra=dict(common, action='appointed_and_shares_received', shares_count=count, shares_received=count, origin=m['origin'], country=m['country']))], ''

    m = match(rf"(?P<seller>{NAME}), cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}), par (?P<count_a>\d+) parts de CHF (?P<nominal_a>{MONEY}) à (?P<a>{NAME}), à (?P<place_a>{NAME}), par (?P<count_b>\d+) parts de CHF (?P<nominal_b>{MONEY}) à (?P<b>{NAME}), à (?P<place_b>{NAME}), et part (?P<count_c>\d+) parts de CHF (?P<nominal_c>{MONEY}) à (?P<c>{NAME}), à (?P<place_c>{NAME}), tous trois du (?P<origin>{NAME}), nouveaux associés-gérants avec signature individuelle, chacun titulaire de (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY})\. (?P<again>{NAME}), qui est nommé président, reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
    if m:
        counts = [int(m['count_'+k]) for k in 'abc']
        count, before, remaining = (int(m[k]) for k in ('count', 'before', 'remaining'))
        if m['seller'] != m['again'] or any(n <= 0 or n != int(m['received']) for n in counts) or sum(counts) != count or before - count != remaining or remaining < 0 or len({m[k] for k in ('nominal', 'nominal_a', 'nominal_b', 'nominal_c', 'buyer_nominal', 'remaining_nominal')}) != 1:
            return [], leftover
        rule = 'fr.persons.share_transfer_three_managers_typo.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        events = [person(rule, m['seller'], role='président', extra=dict(common, action='shares_transferred_and_president_appointed', shares_before=before, shares_transferred=count, shares_count=remaining))]
        events.extend(person(rule, m[k], role='associé-gérant', signing='Einzelunterschrift', place=m['place_'+k], extra=dict(common, action='appointed_and_shares_received', shares_received=n, shares_count=n, origin=m['origin'])) for k, n in zip('abc', counts))
        return events, ''

    return [], leftover
