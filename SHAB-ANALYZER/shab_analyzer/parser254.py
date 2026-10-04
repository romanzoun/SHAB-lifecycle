from __future__ import annotations

import re

from .models import Event
from .parser253 import _count, _event, _iso_date, _person_event

# Full matches deliberately bound these rules to the supplied HR families.
_DATE = r"\d{2}\.\d{2}\.\d{4}"
_MONEY = r"[\d'.]+"
_UID = r"CHE-\d{3}\.\d{3}\.\d{3}"


def extract_parser254_leftovers(
    text: str, language: str | None, publication_id: str, published_at: str,
    org_uid: str | None, plz: str | None, canton: str | None,
) -> tuple[list[Event], str]:
    """Extract bounded corrections and HR narrative families for parser 254."""
    del language
    leftover = text.strip()
    context = (publication_id, published_at, org_uid, plz, canton)

    def match(pattern: str):
        return re.fullmatch(pattern + r"\.?", leftover, re.I | re.UNICODE)

    def event(kind: str, rule: str, payload: dict):
        return _event(*context, kind, rule, payload)

    def person(rule: str, name: str, **kwargs):
        return _person_event(*context, "officer_changed", rule, name, **kwargs)

    m = match(r"Liquidateurs: les gérants (?P<a>[^,.;]+) et (?P<b>[^,.;]+), lesquels continuent à signer collectivement à deux")
    if m:
        return [person("fr.persons.two_managers_liquidators.v1", m[g],
                       role="gérant liquidateur", signing="Kollektivunterschrift zu zweien",
                       extra={"action": "appointed_liquidator", "signing_unchanged": True})
                for g in ("a", "b")], ""

    m = match(rf"Transfert de patrimoine: selon contrat du (?P<contract>{_DATE}) et décision de l['’]autorité de surveillance du (?P<decision>{_DATE}), la fondation a transféré des actifs de CHF (?P<assets>{_MONEY}) et des passifs envers les tiers de CHF (?P<liabilities>{_MONEY}) à la fondation \"(?P<name>[^\"]+)\", à (?P<place>[^()]+) \((?P<uid>{_UID})\)\. Contre-prestation: aucune")
    if m:
        return [event("organization_changed", "fr.text.foundation_asset_transfer.v1", {
            "kind": "asset_transfer", "agreement_date": _iso_date(m["contract"]),
            "decision_date": _iso_date(m["decision"]), "assets": m["assets"],
            "liabilities": m["liabilities"], "currency": "CHF",
            "recipient_name": m["name"], "recipient_place": m["place"].strip(),
            "recipient_uid": m["uid"], "consideration": "none",
        })], ""

    m = match(rf"Par décision du (?P<decision>{_DATE}), la Cour de justice a accordé l['’]effet suspensif au recours contre le jugement de faillite du (?P<bankruptcy>{_DATE})")
    if m:
        return [event("status_changed", "fr.text.bankruptcy_appeal_suspensive_effect.v1", {
            "kind": "bankruptcy", "action": "appeal_suspensive_effect_granted",
            "decision_date": _iso_date(m["decision"]),
            "bankruptcy_judgment_date": _iso_date(m["bankruptcy"]),
            "court": "Cour de justice",
        })], ""

    m = match(rf"L['’]inscription n° (?P<entry>[\d']+) du (?P<date>{_DATE}) est rectifiée en ce sens que l['’]associé-gérant (?P<name>[^,.;]+) est originaire d['’](?P<origin>[^,.;]+) et domicilié à (?P<place>[^,.;]+), (?P<country>[A-Z]{{3}})")
    if m:
        return [person("fr.persons.associate_manager_origin_residence_corrected.v1", m["name"],
                       role="associé-gérant", place=m["place"], extra={
                           "action": "details_corrected", "origin": m["origin"],
                           "country": m["country"], "entry": m["entry"],
                           "entry_date": _iso_date(m["date"]),
                       })], ""

    m = match(rf"Rectificatif: l['’]inscription no (?P<entry>[\d']+) du (?P<date>{_DATE}) \(FOSC du (?P<notice>{_DATE}) p\. (?P<reference>[\d/]+)\) est rectifiée en ce sens que l['’]administrateur (?P<surname>[^,.;]+) se prénomme (?P<given>[^,.;]+) \(et non (?P<previous>[^()]+) comme publié\)")
    if m:
        return [person("fr.persons.administrator_given_name_corrected_notice.v1",
                       f"{m['surname']} {m['given']}", role="administrateur", extra={
                           "action": "name_corrected", "previous_name": f"{m['surname']} {m['previous']}",
                           "entry": m["entry"], "entry_date": _iso_date(m["date"]),
                           "notice_date": _iso_date(m["notice"]), "notice_ref": m["reference"],
                       })], ""

    m = match(rf"Succursale: (?P<place>[^()]+) \((?P<uid>{_UID})\) \[précédemment: à (?P<previous>[^()]+) \((?P<previous_uid>{_UID})\)\]")
    if m and m["uid"] == m["previous_uid"]:
        return [event("organization_changed", "fr.text.branch_seat_changed.v1", {
            "kind": "branch", "action": "seat_changed", "branch_uid": m["uid"],
            "place": m["place"].strip(), "previous_place": m["previous"].strip(),
        })], ""

    m = match(r"Liquidatrices: les administratrices (?P<a>[^,.;]+), (?P<b>[^,.;]+), et (?P<c>[^,.;]+); lesquelles signent désormais individuellement\. Liquidateurs: (?P<d>[^,.;]+) et (?P<e>[^,.;]+); lesquels signent désormais individuellement")
    if m:
        return [person("fr.persons.five_liquidators_individual_signing.v1", m[g],
                       role="administratrice liquidatrice" if g in "abc" else "liquidateur",
                       signing="Einzelunterschrift", extra={"action": "appointed_liquidator_and_signing_changed"})
                for g in "abcde"], ""

    m = match(rf"\[Das bisherige Urkundendatum vom (?P<date>{_DATE}) wird gestrichen, da ein falsches Datum vermerkt wurde\.\]\. \[Der Hinweis auf den Zweckänderungsvorbehalt wird gestrichen, da die Urkunde keinen solchen vorsieht\.\]")
    if m:
        rule = "de.text.foundation_deed_date_purpose_reservation_corrected.v1"
        return [event("statutes_changed", rule, {
            "kind": "deed_date", "action": "incorrect_date_removed", "previous_date": _iso_date(m["date"]),
        }), event("statutes_changed", rule, {
            "kind": "purpose_change_reservation", "action": "corrected", "purpose_change_reserved": False,
        })], ""

    m = match(r"(?P<a>[^,.;]+), membre du comité, nommé président, exerce désormais la signature sociale, collectivement à deux\. (?P<b>[^,.;]+), membre du comité, jusqu['’]ici président, n['’]exerce plus la signature sociale")
    if m:
        rule = "fr.persons.committee_president_signing_transition.v1"
        return [person(rule, m["a"], role="président du comité", signing="Kollektivunterschrift zu zweien",
                       extra={"action": "appointed_and_signing_granted", "previous_role": "membre du comité"}),
                person(rule, m["b"], role="membre du comité", extra={
                    "action": "signing_revoked", "previous_role": "président", "without_signature": True,
                })], ""

    m = match(rf"Kapitalerhöhung aus genehmigtem Aktienkapital mit Liberierung durch Verrechnung von (?P<claims>\d+) Forderungen von insgesamt CHF (?P<amount>{_MONEY}), wofür (?P<count>[\d']+) Namenaktien zu CHF (?P<nominal>{_MONEY}) ausgegeben werden")
    if m:
        return [event("capital_changed", "de.text.authorized_capital_increase_offset_claims.v1", {
            "kind": "authorized_capital_increase", "payment_method": "offset_claims",
            "claims_count": int(m["claims"]), "offset_amount": m["amount"],
            "shares_count": _count(m["count"]), "shares_nominal": m["nominal"],
            "share_kind": "Namenaktien", "currency": "CHF",
        })], ""

    m = match(rf"L['’]inscription (?P<entry>[\d']+) du (?P<date>{_DATE}) est rectifiée en ce sens que (?P<name>[^,.;]+) n['’]est pas membre du conseil; (?:il )?continue à signer collectivement à deux")
    if m:
        return [person("fr.persons.board_membership_denied_signing_retained.v1", m["name"],
                       signing="Kollektivunterschrift zu zweien", extra={
                           "action": "details_corrected", "board_member": False,
                           "signing_unchanged": True, "entry": m["entry"], "entry_date": _iso_date(m["date"]),
                       })], ""

    m = match(rf"(?P<a>[^,.;]+) et (?P<b>[^,.;]+) détiennent désormais chacun (?P<remaining>\d+) parts de CHF (?P<nominal>{_MONEY}) par suite de cession de (?P<transferred>\d+) parts de CHF (?P<transfer_nominal>{_MONEY}) à (?P<buyers>.+), chacun associé pour (?P<each>\d+) parts de CHF (?P<buyer_nominal>{_MONEY}), tous cinq sans signature sociale")
    if m:
        buyers = re.fullmatch(
            r"(?P<n1>[^,.;]+), de (?P<o1>[^,.;]+), à (?P<p1>[^,.;]+), (?P<c1>[A-Z]), à "
            r"(?P<n2>[^,.;]+), de (?P<o2>[^,.;]+), à (?P<p2>[^,.;]+), (?P<c2>[A-Z]), à "
            r"(?P<n3>[^,.;]+), de (?P<o3>[^,.;]+), à (?P<p3>[^,.;]+), (?P<c3>[A-Z]), à "
            r"(?P<n4>[^,.;]+), de (?P<o4>[^,.;]+), à (?P<p4>[^,.;]+), (?P<c4>[A-Z]), et à "
            r"(?P<n5>[^,.;]+), de (?P<o5>[^,.;]+), à (?P<p5>[^,.;]+), (?P<c5>[A-Z])",
            m["buyers"], re.I | re.UNICODE,
        )
        if (buyers and int(m["transferred"]) == 5 * int(m["each"])
                and m["nominal"] == m["transfer_nominal"] == m["buyer_nominal"]):
            rule = "fr.persons.two_associates_transfer_to_five_unsigned_associates.v1"
            events = [person(rule, m[g], extra={
                "action": "shareholding_changed", "shares_count": int(m["remaining"]),
                "shares_nominal": m["nominal"], "currency": "CHF",
                "reported_transfer_total": int(m["transferred"]),
            }) for g in ("a", "b")]
            events += [person(rule, buyers[f"n{i}"], role="associé", place=buyers[f"p{i}"], extra={
                "action": "shares_received", "shares_count": int(m["each"]),
                "shares_received": int(m["each"]), "shares_nominal": m["buyer_nominal"],
                "currency": "CHF", "origin": buyers[f"o{i}"], "country": buyers[f"c{i}"],
                "without_signature": True,
            }) for i in range(1, 6)]
            return events, ""

    return [], leftover
