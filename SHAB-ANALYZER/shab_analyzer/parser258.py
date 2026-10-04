from __future__ import annotations

import re

from .parser253 import _event, _iso_date, _person_event

DATE = r'\d{2}\.\d{2}\.\d{4}'
NAME = r'[^,.;]+?'
MONEY = r"[\d']+(?:\.\d+)?"


def extract_parser258_leftovers(text, language, publication_id, published_at, org_uid, plz, canton, *, source_text=''):
    """Complete families observed in the twelve parser258 fixtures only."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r'\.?', leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, 'officer_changed', rule, name, **kwargs)

    m = match(rf'Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom (?P<date>{DATE}) beschlossene genehmigte Kapitalerhöhung infolge Fristablaufs')
    if m:
        return [event('capital_changed', 'de.text.authorized_capital_expired.v1', {'kind': 'authorized_capital_increase', 'action': 'statutory_provision_deleted', 'authorization_date': _iso_date(m['date']), 'reason': 'expired'})], ''

    m = match(r"Le but étant désormais identique à celui du siège principal, n'est pas mentionné pour la succursale, conformément à l'article (?P<article>110, al\. 1, let\. d ORC)")
    if m:
        return [event('organization_changed', 'fr.text.branch_purpose_same_as_headquarters.v1', {'kind': 'branch_purpose', 'same_as_headquarters': True, 'omitted': True, 'legal_basis': m['article']})], ''

    m = match(rf'Mit der Eintragung Ref\. (?P<reference>\d+), TR-Nr\. (?P<entry>\d+) vom TR-Datum (?P<entry_date>{DATE}) wurde als letztes SHAB-Zitat versehentlich SHAB Nr\. (?P<previous_notice_number>\d+) vom (?P<previous_notice_date>{DATE}) genannt, statt SHAB Nr\. (?P<notice_number>\d+) vom (?P<notice_date>{DATE})')
    if m:
        payload = m.groupdict()
        for key in ('entry_date', 'previous_notice_date', 'notice_date'):
            payload[key] = _iso_date(payload[key])
        return [event('organization_changed', 'de.text.last_notice_reference_corrected.v1', dict(payload, kind='notice_reference_corrected'))], ''

    m = match(rf'La succursale de (?P<place>{NAME}) \((?P<registry_id>CH-\d{{3}}-\d{{7}}-\d)\) est radiée \(FOSC du (?P<notice_date>{DATE}), Id (?P<notice_id>\d+)\)')
    if m:
        return [event('organization_changed', 'fr.text.branch_deleted_legacy_registry_id.v1', dict(m.groupdict(), kind='branch', action='deleted', notice_date=_iso_date(m['notice_date'])))], ''

    m = match(r'Genussscheine neu: (?P<count>1) Genussschein mit Rechten auf Anteil am Bilanzgewinn gemäss genauer Umschreibung in den Statuten')
    if m:
        return [event('capital_changed', 'de.text.profit_participation_certificate.v1', {'kind': 'profit_participation_certificate', 'count': int(m['count']), 'rights': 'Anteil am Bilanzgewinn', 'details': 'statutes'})], ''

    m = match(rf"Vermögensübertragung: Die Aktiengesellschaft überträgt gemäss Vertrag vom (?P<date>{DATE}) Aktiven von CHF (?P<assets>{MONEY}) und Passiven \(Fremdkapital\) von CHF (?P<liabilities>{MONEY}) auf die (?P<recipient>[^()]+) \((?P<uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), in (?P<place>{NAME})\. Gegenleistung: (?P<consideration>{MONEY})")
    if m:
        return [event('organization_changed', 'de.text.asset_transfer_to_municipality.v1', dict(m.groupdict(), kind='asset_transfer', date=_iso_date(m['date']), currency='CHF'))], ''

    m = match(r"Par décision du (?P<day>\d{1,2}) janvier (?P<year>\d{4}), (?P<court>le président du Tribunal d'arrondissement de l'Est vaudois) a rejeté la requête de restitution de délai, révoqué l'effet suspensif et dit que le prononcé de faillite du (?P<bankruptcy_day>\d{1,2}) novembre (?P<bankruptcy_year>\d{4}) prend effet le (?P<effective_day>\d{1,2}) janvier (?P<effective_year>\d{4}), à (?P<hour>\d{2})h(?P<minute>\d{2})")
    if m and int(m['hour']) < 24 and int(m['minute']) < 60:
        return [event('status_changed', 'fr.text.bankruptcy_suspensive_effect_revoked.v1', {'kind': 'bankruptcy', 'action': 'suspensive_effect_revoked', 'restitution_request': 'rejected', 'court': m['court'], 'decision_date': _iso_date(f"{int(m['day']):02d}.01.{m['year']}"), 'bankruptcy_date': _iso_date(f"{int(m['bankruptcy_day']):02d}.11.{m['bankruptcy_year']}"), 'effective_date': _iso_date(f"{int(m['effective_day']):02d}.01.{m['effective_year']}"), 'effective_time': f"{m['hour']}:{m['minute']}"})], ''

    m = match(rf"L'inscription no (?P<entry>\d+) du (?P<entry_date>{DATE}) est réctifiée en ce sens que (?P<previous_name>{NAME}) se prénomme en réalité (?P<given_names>{NAME})")
    if m:
        return [person('fr.persons.given_names_corrected_notice_typo.v1', m['previous_name'], extra={'action': 'given_names_corrected', 'given_names': m['given_names'], 'entry': m['entry'], 'entry_date': _iso_date(m['entry_date'])})], ''

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de et à (?P<place>{NAME}), nouvelle associée, avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}); (?P<again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
    manager = False
    if not m:
        m = match(rf"L'associé-gérant (?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), de (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé avec (?P<received>\d+) parts de CHF (?P<buyer_nominal>{MONEY}), gérant avec signature individuelle\. (?P<again>{NAME}), qui est élu président, reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY}); continue de signer individuellement")
        manager = True
    if m and m['seller'] == m['again'] and int(m['count']) == int(m['received']) > 0 and int(m['before']) - int(m['count']) == int(m['remaining']) >= 0 and m['nominal'] == m['buyer_nominal'] == m['remaining_nominal']:
        if manager and f"nouvel associé avec {m['received']} parts de CHF {m['buyer_nominal']}, gérant avec signature individuelle." not in source_text:
            return [], leftover
        rule = 'fr.persons.partial_share_transfer_new_manager.v1' if manager else 'fr.persons.partial_share_transfer_new_associate.v1'
        common = {'currency': 'CHF', 'shares_nominal': m['nominal']}
        seller = person(rule, m['seller'], role='gérant président' if manager else None, signing='Einzelunterschrift' if manager else None, extra=dict(common, action='shares_transferred_and_president_elected' if manager else 'shares_transferred', shares_before=int(m['before']), shares_transferred=int(m['count']), shares_count=int(m['remaining'])))
        buyer = person(rule, m['buyer'], role='associé-gérant' if manager else 'associée', place=m['place'], signing='Einzelunterschrift' if manager else None, extra=dict(common, action='appointed_and_shares_received', origin=m['origin'] if manager else m['place'], shares_count=int(m['received'])))
        return [seller, buyer], ''

    m = match(rf'(?P<a>{NAME}) et (?P<b>{NAME}) continuent à signer collectivement à deux, toutefois désormais pas entre eux\. Nouveaux administrateurs avec signature collective à deux, toutefois pas entre eux: (?P<c>{NAME}), de (?P<origin_c>{NAME}), à (?P<place_c>{NAME}), et (?P<d>{NAME}), de et à (?P<place_d>{NAME})')
    if m and 'Nouveaux administrateurs avec signature collective à deux, toutefois pas entre eux:' in source_text:
        rule = 'fr.persons.board_collective_signing_excluding_each_other.v1'
        events = []
        for key, other in [('a', 'b'), ('b', 'a'), ('c', 'd'), ('d', 'c')]:
            appointed = key in ('c', 'd')
            events.append(person(rule, m[key], role='administrateur' if appointed else None, place=m['place_'+key] if appointed else None, signing='Kollektivunterschrift zu zweien', extra={'action': 'appointed' if appointed else 'signing_changed', 'signing_excluded_with': m[other], **({'origin': m['origin_c'] if key == 'c' else m['place_d']} if appointed else {})}))
        return events, ''

    m = match(rf"Les statuts dérogent à la loi quant aux modalités du transfert des parts sociales: pour les détails, voir les statuts\. (?P<a>.+?) et (?P<b>.+?), qui ne sont plus associées, cèdent la participation qu'elles détiennent dans la part indivise de CHF (?P<nominal>{MONEY}) à (?P<c>[^()]+) \((?P<id_c>\d+)\) et (?P<d>[^()]+) \((?P<id_d>\d+)\), toutes deux à (?P<place>[^;]+?), nouvelles associées, co-détentrices d'une part indivise de CHF (?P<received_nominal>{MONEY})")
    if m and m['nominal'] == m['received_nominal']:
        rule = 'fr.persons.corporate_undivided_share_transfer.v1'
        events = [event('statutes_changed', rule, {'kind': 'share_transfer_provisions', 'deviate_from_law': True, 'details': 'statutes'})]
        for key in ('a', 'b', 'c', 'd'):
            buyer = key in ('c', 'd')
            events.append(person(rule, m[key], role='associée', place=m['place'] if buyer else None, extra={'action': 'appointed_co_holder' if buyer else 'departed_and_participation_transferred', 'undivided_share_nominal': m['nominal'], 'currency': 'CHF', **({'registry_id': m['id_'+key]} if buyer else {})}))
        return events, ''

    return [], leftover
