from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_TRANSFER_TO_NEW_ASSOCIATE_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*qui est maintenant de\s+"
    r"(?P<seller_origin>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+au gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_DIRECTOR_UNRESTRICTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est nommée\s+"
    r"(?P<role>directrice)\s+avec signature collective à deux,\s*"
    r"désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_TRANSFER_EQUAL_HOLDINGS = re.compile(
    r"^L['’]associé-gérant président\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associée-gérante\s+(?P<buyer>[^,.;]+);\s*"
    r"tous deux sont maintenant de\s+(?P<origin>[^,.;]+),\s*désormais titulaires,\s*"
    r"chacun,\s*de\s+(?P<each_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<each_nominal>[\d'.]+);\s*ils continuent de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_DEED_HISTORY_REMOVED = re.compile(
    r"^\[gestrichen:\s*Änderung der Stiftungsurkunde mit Verfügung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+des\s+(?P<authority>.+?),\s*"
    r"in\s+(?P<place>[^.\]]+)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PROXIES_REVOKED = re.compile(
    r"^Les procurations de\s+(?P<name1>[^,.;]+?)\s+et\s+(?!de\b)"
    r"(?P<name2>[^,.;]+?)\s+sont radiées\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_NEW_MANAGER_VICE_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:de|du|des|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Ce dernier est nommé gérant et vice-président avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_IT_REGISTRATION_MAINTAINED = re.compile(
    r"^\[Con decisione della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+è mantenuta l['’]iscrizione nel registro "
    r"di commercio\.\]\s*\[radiati:\s*\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_INVESTOR_SHARES = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*la société a transféré des "
    r"actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>actions-investisseurs)\s+du compartiment\s+"
    r"(?P<compartment>.+?)\s+de\s+(?P<issuer>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_COMMITTEE_MEMBERS_FOREIGN_PLACE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:de|du|des|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[^,.;]+),\s*"
    r"sont membres du comité avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_CONTINUE_INDIVIDUALLY = re.compile(
    r"^Liquidateurs:(?!\s*(?:les?\b|la\b|l['’]))\s*"
    r"(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*"
    r"lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_TIME_LIMIT = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Ablaufs der zeitlichen Befristung\.\]\s*"
    r"\[gestrichen:\s*Die Umschreibung der mit Beschluss der Generalversammlung "
    r"vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eingeführten Bestimmung "
    r"über das genehmigte Kapital wurde mit Beschluss der Generalversammlung "
    r"vom\s+(?P<modified_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_CLOSED_DELETION_DEFERRED_FOR_CLAIMS = re.compile(
    r"^Das Konkursverfahren wurde mit Urteil des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+als geschlossen erklärt und das "
    r"Handelsregisteramt angewiesen,\s*die Löschung der Gesellschaft erst auf "
    r"Anweisung des Konkursamtes hin vorzunehmen\.\s*Die Eintragung bleibt nur "
    r"zum Zweck der Geltendmachung von abgetretenen Ansprüchen nach\s+"
    r"(?P<legal_basis>Art\.\s*260 SchKG)\s+erhalten und die Verfügungsbefugnisse "
    r"der Organe der Gesellschaft leben nicht wieder auf\.?$",
    re.I | re.UNICODE,
)
_FR_EXISTING_ASSOCIATES_SHARE_TRANSFER = re.compile(
    r"^L['’]associée\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à l['’]associée\s+(?P<buyer>[^,.;]+),\s*"
    r"laquelle devient ainsi titulaire de\s+(?P<buyer_count>[\d']+)\s+parts "
    r"sociales de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_TRANSFER_TO_NEW_ASSOCIATE_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*nommé président,\s*détient désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par suite "
    r"de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transferred_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*nouvel associé-gérant "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_SHAREHOLDER_COMMUNICATIONS_EXACT_FORM = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que la forme exacte "
    r"des communications aux actionnaires est:\s*(?P<mode>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_REGISTERED_PERSON = re.compile(
    r"^Neue eingetragene Person:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<nationality>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*(?P<signing>Einzelunterschrift|"
    r"Kollektivunterschrift(?: zu zweien)?)\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month.casefold()]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _event(
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    event_type: str,
    rule_id: str,
    payload: dict,
) -> Event:
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        plz=plz,
        canton=canton,
        payload=payload,
    )


def _person_event(
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    event_type: str,
    rule_id: str,
    name: str,
    *,
    place: str | None = None,
    role: str | None = None,
    signing: str | None = None,
    extra: dict | None = None,
) -> Event:
    clean_name = name.strip()
    clean_place = place.strip() if place else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place),
        plz=plz,
        canton=canton,
        role=role.strip() if role else None,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser246_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 246."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_ASSOCIATE_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len(
            {
                match.group("nominal"),
                match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }
        )
        == 1
    ):
        rule_id = "fr.persons.associate_transfer_new_associate_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé",
                extra={
                    **common,
                    "action": "origin_changed_and_shares_transferred",
                    "origin": match.group("seller_origin").strip(),
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                role="associé-gérant",
                extra={
                    **common,
                    "action": "appointed_associate_and_shares_received",
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _FR_PROXY_REVOKED_DIRECTOR_UNRESTRICTED.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.proxy_revoked_director_unrestricted.v1",
                match.group("name"),
                role=match.group("role"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "proxy_revoked_and_appointed_director",
                    "previous_signing_revoked": True,
                    "signing_restriction_removed": True,
                },
            )
        ], ""

    match = _FR_ASSOCIATE_MANAGERS_TRANSFER_EQUAL_HOLDINGS.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("each_count"))
        and match.group("nominal") == match.group("each_nominal")
    ):
        rule_id = "fr.persons.associate_managers_transfer_equal_holdings.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        each_count = _count(match.group("each_count"))
        common = {
            "origin": match.group("origin").strip(),
            "shares_count": each_count,
            "share_nominal": match.group("nominal"),
            "currency": "CHF",
        }
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé-gérant président",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "origin_changed_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                role="associée-gérante",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "origin_changed_and_shares_received",
                    "counterparty": seller,
                    "shares_before": each_count - transferred,
                    "shares_received": transferred,
                },
            ),
        ], ""

    match = _DE_FOUNDATION_DEED_HISTORY_REMOVED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "statutes_changed",
                "de.text.foundation_deed_history_removed.v1",
                {
                    "kind": "foundation_deed",
                    "action": "previous_entry_removed",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "authority_place": match.group("place").strip(),
                },
            )
        ], ""

    match = _FR_TWO_PROXIES_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_proxies_revoked.v1"
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_removed",
                rule_id,
                match.group(f"name{index}"),
                signing="Prokura erloschen",
                extra={"action": "proxy_revoked", "signing_revoked": True},
            )
            for index in (1, 2)
        ], ""

    match = _FR_MANAGER_TRANSFER_NEW_MANAGER_VICE_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        rule_id = "fr.persons.manager_transfer_new_manager_vice_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé-gérant",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_transferred": transferred,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                place=match.group("place"),
                role="associé-gérant; vice-président",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "appointed_associate_manager_and_vice_president",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _IT_REGISTRATION_MAINTAINED.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "it.text.registration_maintained_by_court.v1",
                {
                    "kind": "registration_maintained",
                    "action": "maintained",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "registry_entry_maintained": True,
                    "removed_history_empty_after_prior_rule": True,
                },
            )
        ], ""

    match = _FR_ASSET_TRANSFER_INVESTOR_SHARES.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "assets_transferred",
                "fr.text.asset_transfer_investor_shares.v1",
                {
                    "source_kind": "company",
                    "agreement_date": _french_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "liabilities_kind": "third_party_liabilities",
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration_kind": "investor_shares",
                    "consideration_share_count": _count(match.group("share_count")),
                    "consideration_share_kind": match.group("share_kind"),
                    "compartment": match.group("compartment").strip(),
                    "consideration_issuer": match.group("issuer").strip(),
                },
            )
        ], ""

    match = _FR_TWO_COMMITTEE_MEMBERS_FOREIGN_PLACE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_committee_members_foreign_place.v1"
        events = []
        for index in (1, 2):
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
            }
            if index == 2:
                extra["country"] = match.group("country2").strip()
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    rule_id,
                    match.group(f"name{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du comité",
                    signing="Kollektivunterschrift zu zweien",
                    extra=extra,
                )
            )
        return events, ""

    match = _FR_TWO_LIQUIDATORS_CONTINUE_INDIVIDUALLY.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_liquidators_continue_individually.v1"
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                match.group(f"name{index}"),
                role="liquidateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            )
            for index in (1, 2)
        ], ""

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_TIME_LIMIT.fullmatch(leftover)
    if match and match.group("date") == match.group("previous_date"):
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "capital_changed",
                "de.text.authorized_capital_expired_time_limit.v1",
                {
                    "kind": "authorized_capital_clause",
                    "action": "removed_after_expiry",
                    "authorization_date": _iso_date(match.group("date")),
                    "last_modified_date": _iso_date(match.group("modified_date")),
                    "reason": "time_limit_expired",
                },
            )
        ], ""

    match = _DE_BANKRUPTCY_CLOSED_DELETION_DEFERRED_FOR_CLAIMS.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.bankruptcy_closed_deletion_deferred_for_claims.v1",
                {
                    "kind": "bankruptcy_closed",
                    "action": "closed_deletion_deferred",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "deletion_requires_bankruptcy_office_instruction": True,
                    "registration_retained_for_assigned_claims": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "governing_bodies_powers_revived": False,
                },
            )
        ], ""

    match = _FR_EXISTING_ASSOCIATES_SHARE_TRANSFER.fullmatch(leftover)
    if match and match.group("nominal") == match.group("buyer_nominal"):
        rule_id = "fr.persons.existing_associates_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        if before < transferred or buyer_count < transferred:
            return [], leftover
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associée",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": before,
                    "shares_transferred": transferred,
                    "shares_count": before - transferred,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                role="associée",
                extra={
                    **common,
                    "action": "shares_received",
                    "counterparty": seller,
                    "shares_before": buyer_count - transferred,
                    "shares_received": transferred,
                    "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _FR_PRESIDENT_TRANSFER_TO_NEW_ASSOCIATE_MANAGER.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len(
            {
                match.group("nominal"),
                match.group("transferred_nominal"),
                match.group("buyer_nominal"),
            }
        )
        == 1
    ):
        rule_id = "fr.persons.president_transfer_new_associate_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                seller,
                role="associé-gérant président",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred,
                    "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                rule_id,
                buyer,
                place=match.group("place"),
                role="associé-gérant",
                signing="Einzelunterschrift",
                extra={
                    **common,
                    "action": "appointed_associate_manager_and_shares_received",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _FR_SHAREHOLDER_COMMUNICATIONS_EXACT_FORM.fullmatch(leftover)
    if match:
        return [
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "fr.text.shareholder_communications_exact_form.v1",
                {
                    "kind": "communications",
                    "action": "exact_form_supplemented",
                    "audience": "shareholders",
                    "to": match.group("mode").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_ref": match.group("notice_ref"),
                },
            )
        ], ""

    match = _DE_NEW_REGISTERED_PERSON.fullmatch(leftover)
    if match:
        return [
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "de.persons.new_registered_person.v1",
                match.group("name"),
                place=match.group("place"),
                role=match.group("role"),
                signing=match.group("signing"),
                extra={
                    "action": "appointed",
                    "nationality": match.group("nationality").strip(),
                },
            )
        ], ""

    return [], leftover
