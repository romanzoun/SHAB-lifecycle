from __future__ import annotations

import re

from .keys import person_key
from .parser253 import _event, _french_date, _iso_date, _person_event

DATE = r"\d{2}\.\d{2}\.\d{4}"
MONEY = r"[\d']+(?:\.\d+)?"
NAME = r"[^,.;]+?"


def extract_parser255_leftovers(text, language, publication_id, published_at, org_uid, plz, canton,
                               *, source_text=""):
    """Bounded HR families; source text verifies the branch citation context."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern):
        return re.fullmatch(pattern + r"\.?", leftover, re.I | re.UNICODE)

    def event(kind, rule, payload):
        return _event(*context, kind, rule, payload)

    def person(rule, name, **kwargs):
        return _person_event(*context, "officer_changed", rule, name, **kwargs)

    m = match(r"Suppression des clauses statutaires relatives aux apports en nature, conformément à l'art\. 628, al\. 4 CO")
    if m:
        return [event("statutes_changed", "fr.text.contribution_clauses_removed.v1", {
            "kind": "contributions_in_kind", "action": "clauses_removed", "legal_basis": "art. 628, al. 4 CO",
        })], ""

    m = match(rf"Mit Verfügung vom (?P<date>{DATE}) hat das (?P<court>Gerichtspräsidium {NAME}) die gewährte definitive Nachlassstundung um (?P<months>\d+) Monate verlängert")
    if m:
        return [event("status_changed", "de.text.definitive_moratorium_extended.v1", {
            "kind": "composition_moratorium", "action": "extended", "definitive": True,
            "decision_date": _iso_date(m['date']), "court": m['court'], "extension_months": int(m['months']),
        })], ""

    m = match(rf"Les administrateurs (?P<a>{NAME}) et (?P<b>{NAME}) sont maintenant originaire de (?P<origin>{NAME})")
    if m:
        return [person("fr.persons.two_administrators_origin_changed.v1", m[g], role="administrateur",
                       extra={"action": "origin_changed", "origin": m['origin']}) for g in ('a', 'b')], ""

    notice = rf"(?P<entry>[\d']+) du (?P<date>{DATE}) \(FOSC du (?P<notice>{DATE}),? p\. (?P<ref>[\d/]+)\)"
    m = match(rf"Complément: l'inscription no {notice} est complétée en ce sens que les statuts ont été modifés le (?P<statutes>\d+ [a-zéû]+ \d{{4}})")
    if m:
        return [event("statutes_changed", "fr.text.statutes_date_supplement_typo.v1", {
            "action": "supplemented", "date": _french_date(m['statutes']), "entry": m['entry'],
            "entry_date": _iso_date(m['date']), "notice_date": _iso_date(m['notice']), "notice_ref": m['ref'],
        })], ""

    m = match(rf"Rectificatif: l'inscription n° {notice} est rectifiée en ce sens que la société n'est pas soumise à une révision ordinaire et renonce à une révision restreinte, selon déclaration du (?P<declaration>\d+ [a-zéû]+ \d{{4}}) \(et non du (?P<previous>\d+ [a-zéû]+ \d{{3}}) comme publié\)")
    if m:
        return [event("auditor_changed", "fr.text.audit_waiver_declaration_date_corrected.v1", {
            "kind": "audit_waiver", "action": "date_corrected", "ordinary_audit": False,
            "limited_audit_waived": True, "declaration_date": _french_date(m['declaration']),
            "previous_published_date": m['previous'], "entry": m['entry'],
            "entry_date": _iso_date(m['date']), "notice_date": _iso_date(m['notice']), "notice_ref": m['ref'],
        })], ""

    m = match(rf"Berichtigung des Eintrages Nr\. (?P<entry>\d+) vom (?P<date>{DATE}) \(SHAB vom (?P<notice>{DATE}), Id (?P<ref>\d+)\): (?P<name>{NAME}), Verwaltungsratsmitglied, Einzelunterschrift, von (?P<origin>{NAME}), in (?P<place>{NAME}) \(und nicht von (?P<old_origin>{NAME}), in (?P<old_place>[^()]+)\)")
    if m:
        return [person("de.persons.board_origin_residence_corrected.v1", m['name'], role="Verwaltungsratsmitglied",
                       place=m['place'], signing="Einzelunterschrift", extra={
                           "action": "details_corrected", "origin": m['origin'], "previous_origin": m['old_origin'],
                           "previous_place": m['old_place'], "entry": m['entry'], "entry_date": _iso_date(m['date']),
                           "notice_date": _iso_date(m['notice']), "notice_ref": m['ref'],
                       })], ""

    m = match(rf"L'administrateur (?P<name>{NAME}), désormais à (?P<place>{NAME}), est nommé liquidateur avec signature individuelle")
    if m:
        return [person("fr.persons.administrator_liquidator_residence.v1", m['name'], place=m['place'],
                       role="administrateur liquidateur", signing="Einzelunterschrift",
                       extra={"action": "appointed_liquidator_and_domicile_changed"})], ""

    m = match(rf"(?P<seller>{NAME}) cède (?P<count>\d+) de ses (?P<before>\d+) parts de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), du (?P<origin>{NAME}), à (?P<place>{NAME}), nouvel associé gérant et président avec signature individuelle\. (?P<again>{NAME}) reste titulaire de (?P<remaining>\d+) parts de CHF (?P<remaining_nominal>{MONEY})")
    if (m and m['seller'] == m['again'] and int(m['before']) - int(m['count']) == int(m['remaining'])
            and m['nominal'] == m['remaining_nominal']):
        rule = "fr.persons.partial_share_transfer_new_manager_president.v1"
        common = {"currency": "CHF", "shares_nominal": m['nominal']}
        return [person(rule, m['seller'], extra={**common, "action": "shares_transferred",
                    "shares_before": int(m['before']), "shares_transferred": int(m['count']), "shares_count": int(m['remaining'])}),
                person(rule, m['buyer'], role="associé gérant et président", place=m['place'], signing="Einzelunterschrift",
                       extra={**common, "action": "appointed_and_shares_received", "origin": m['origin'],
                              "shares_received": int(m['count']), "shares_count": int(m['count'])})], ""

    m = match(rf"(?P<seller>{NAME}), jusqu'ici président, détient désormais une part de CHF (?P<remaining>{MONEY}) par suite de cession d'une part de CHF (?P<nominal>{MONEY}) à (?P<buyer>{NAME}), associé-gérant et président désormais pour une part de CHF (?P<buyer_nominal>{MONEY}) avec signature individuelle")
    if m and m['nominal'] == m['buyer_nominal']:
        rule = "fr.persons.unequal_nominal_share_transfer_president.v1"
        return [person(rule, m['seller'], extra={"action": "shareholding_changed", "previous_role": "président",
                    "shares_count": 1, "shares_nominal": m['remaining'], "currency": "CHF"}),
                person(rule, m['buyer'], role="associé-gérant et président", signing="Einzelunterschrift",
                       extra={"action": "shares_received", "shares_received": 1, "shares_count": 1,
                              "shares_nominal": m['nominal'], "currency": "CHF"})], ""

    m = match(rf"(?P<old>{NAME}) n'est plus administrateur; sa signature est radiée\. Nouveaux administrateurs avec signature collective à deux: (?P<a>{NAME}), de (?P<oa>{NAME}), à (?P<pa>{NAME}), président, et (?P<b>{NAME}), de (?P<ob>{NAME}), à (?P<pb>{NAME})")
    if m:
        rule = "fr.persons.board_replacement_president_collective.v1"
        return [person(rule, m['old'], extra={"action": "removed", "previous_role": "administrateur", "signing_revoked": True})] + [
            person(rule, m[g], role="administrateur président" if g == 'a' else "administrateur",
                   place=m['p'+g], signing="Kollektivunterschrift zu zweien",
                   extra={"action": "appointed", "origin": m['o'+g]}) for g in ('a', 'b')], ""

    m = match(rf"Eingetragene Person geändert: (?P<name>{NAME}), Gesellschafter, (?P<count>\d+) Stammanteile zu CHF (?P<nominal>{MONEY}), Geschäftsführer, Einzelunterschrift, neu Geschäftsführer, Einzelunterschrift\. Neu eingetragene Person: (?P<company>[^()]+) \((?P<uid>CHE-\d{{3}}\.\d{{3}}\.\d{{3}})\), in (?P<place>{NAME}), Gesellschafterin, (?P<new_count>\d+) Stammanteile zu CHF (?P<new_nominal>{MONEY})")
    if m:
        rule = "de.persons.manager_shareholder_replaced_by_company.v1"
        manager = person(rule, m['name'], role="Geschäftsführer", signing="Einzelunterschrift", extra={
            "action": "shareholder_role_removed", "previous_role": "Gesellschafter, Geschäftsführer",
            "previous_shares_count": int(m['count']), "previous_shares_nominal": m['nominal'], "currency": "CHF",
        })
        company = person(rule, m['company'], role="Gesellschafterin", place=m['place'], extra={
            "action": "appointed", "uid": m['uid'], "shares_count": int(m['new_count']),
            "shares_nominal": m['new_nominal'], "currency": "CHF",
        })
        company.person_key = person_key(name=m['company'], uid=m['uid'])
        return [manager, company], ""

    m = match(rf"\(FOSC du (?P<date>{DATE}), Id (?P<ref>\d+)\)")
    if m and re.search(rf"La succursale de [^()]+ \(CHE-\d{{3}}\.\d{{3}}\.\d{{3}}\) est radiée {re.escape(leftover)}", source_text):
        return [event("organization_changed", "fr.text.branch_removal_notice_reference.v1", {
            "kind": "branch_removal_notice_reference", "notice_date": _iso_date(m['date']), "notice_ref": m['ref'],
        })], ""
    return [], leftover
