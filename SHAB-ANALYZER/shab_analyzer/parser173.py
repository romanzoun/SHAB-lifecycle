from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_NEW_ASSOCIATE = re.compile(
    r"^Nouvel associé\s*:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée-gérante avec\s+"
    r"signatu(?:t)?re collective à deux,\s*titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER = re.compile(
    r"\s*Vermögensübertragung:\s*(?P<source>.+?)\s+überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf\s+(?:die|das)\s+"
    r"(?:(?P<recipient_kind>Einzelunternehmen)\s+)?(?P<recipient>.+?)"
    r"(?:,\s*in\s+(?P<place_before>[^()]+?)\s*"
    r"\((?P<uid_before>CHE-\d{3}\.\d{3}\.\d{3})\s*\)|"
    r"\s*\((?P<uid_after>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*in\s+"
    r"(?P<place_after>[^.]+?))\.\s*Gegenleistung:\s*"
    r"(?P<consideration>.+?)(?=\s*Vermögensübertragung:|$)",
    re.I | re.UNICODE,
)
_DE_SHARE_AND_CLAIM_CONSIDERATION = re.compile(
    r"^(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien) zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+und eine Forderung von CHF\s+"
    r"(?P<claim>[\d'.]+)$",
    re.I | re.UNICODE,
)
_DE_CLAIM_OFFSET_CONSIDERATION = re.compile(
    r"^Verrechnung mit einer Forderung von CHF\s+(?P<claim>[\d'.]+)$",
    re.I | re.UNICODE,
)
_IT_PROVISIONAL_BANKRUPTCY_SUSPENSIVE_EFFECT = re.compile(
    r"^Con decisione del\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+al reclamo contro la decisione "
    r"del\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+del\s+"
    r"(?P<bankruptcy_authority>.+?)\s+concernente la dichiarazione di fallimento "
    r"viene provvisoriamente concesso effetto sospensivo\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_REOPENED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<authority>.+?)\s+die Einstellung mangels Aktiven widerrufen und das "
    r"Konkursverfahren wiedereröffnet\.\s*\[bisher:\s*Das Konkursverfahren ist "
    r"mit Verfügung des\s+(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven eingestellt "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_OWN_SHARES_DESTROYED = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"werden\s+(?P<count>[\d']+)\s+eigene Aktien zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+vernichtet\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifié(?:e)? en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas à\s+(?P<previous_place>.+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_HOLDER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le\s+"
    r"(?P<role>[^,.;]+?)\s+porte le nom exact\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_IN_REALITY = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<previous_name>[^,.;]+?)\s+se nomme en réalité\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NOTICE_ROLE_HOLDER_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la\s+"
    r"(?P<role>[^,.;]+?)\s+se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_WITH_PRESIDENT = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres du comité,\s*tous deux avec le "
    r"président\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation autorisée "
    r"du capital,\s*fondée sur la décision d['’]autorisation du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_INHERITANCE_COMMUNITY_MANAGER_NAMED = re.compile(
    r"^Le\s+(?P<role>gérant et membre de la communauté héréditaire)\s+se nomme\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_NON_PUBLIC_CONNECTOR = re.compile(r"^y compris\.?$", re.I | re.UNICODE)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def _consideration(raw: str) -> dict | None:
    clean = raw.strip().rstrip(".")
    if clean.casefold() == "keine":
        return {"consideration_kind": "none"}

    match = _DE_SHARE_AND_CLAIM_CONSIDERATION.fullmatch(clean)
    if match:
        return {
            "consideration_kind": "shares_and_claim",
            "consideration_shares_count": _count(match.group("count")),
            "consideration_share_kind": match.group("share_kind"),
            "consideration_share_nominal": match.group("nominal"),
            "consideration_claim": match.group("claim"),
        }

    match = _DE_CLAIM_OFFSET_CONSIDERATION.fullmatch(clean)
    if match:
        return {
            "consideration_kind": "claim_offset",
            "consideration_claim": match.group("claim"),
        }
    return None


def _asset_transfers(raw: str) -> list[tuple[re.Match[str], dict]] | None:
    transfers: list[tuple[re.Match[str], dict]] = []
    position = 0
    while position < len(raw):
        match = _DE_ASSET_TRANSFER.match(raw, position)
        if not match:
            return None
        consideration = _consideration(match.group("consideration"))
        if consideration is None:
            return None
        transfers.append((match, consideration))
        position = match.end()
    return transfers or None


def _source_kind(source: str) -> str:
    normalized = source.casefold()
    if normalized == "die gesellschaft":
        return "company"
    if normalized.startswith("der verein "):
        return "association"
    return "named_entity"


def extract_parser173_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 173."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_NEW_ASSOCIATE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_associate_same_origin_place.v1",
            match.group("name"), place=match.group("place"), role="associé",
            extra={
                "action": "appointed",
                "origin": match.group("place").strip(),
            },
        )], ""

    match = _FR_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"),
            match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_share_transfer_collective_signing.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "origin": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ], ""

    transfers = _asset_transfers(leftover)
    if transfers:
        rule_id = "de.text.asset_transfer_contract_consideration.v1"
        events = []
        for transfer, consideration in transfers:
            source = transfer.group("source").strip()
            recipient_kind = transfer.group("recipient_kind")
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", rule_id, {
                    "source": source,
                    "source_kind": _source_kind(source),
                    "agreement_date": _iso_date(transfer.group("agreement_date")),
                    "assets": transfer.group("assets"),
                    "liabilities": transfer.group("liabilities"),
                    "liabilities_kind": "third_party_capital",
                    "currency": "CHF",
                    "recipient": transfer.group("recipient").strip(),
                    "recipient_kind": (
                        "sole_proprietorship" if recipient_kind else "company"
                    ),
                    "recipient_uid": (
                        transfer.group("uid_before") or transfer.group("uid_after")
                    ),
                    "recipient_place": (
                        transfer.group("place_before")
                        or transfer.group("place_after")
                    ).strip(),
                    **consideration,
                },
            ))
        if all(
            event.payload["consideration_kind"] != "claim_offset"
            or _amount(event.payload["assets"])
            - _amount(event.payload["liabilities"])
            == _amount(event.payload["consideration_claim"])
            for event in events
        ):
            return events, ""

    match = _IT_PROVISIONAL_BANKRUPTCY_SUSPENSIVE_EFFECT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.provisional_bankruptcy_suspensive_effect.v1",
            {
                "kind": "bankruptcy", "action": "suspensive_effect_granted",
                "provisional": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_decision_date": _iso_date(
                    match.group("bankruptcy_date")
                ),
                "bankruptcy_authority": (
                    match.group("bankruptcy_authority").strip()
                ),
            },
        )], ""

    match = _DE_BANKRUPTCY_REOPENED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_reopened_after_suspension.v1", {
                "kind": "bankruptcy", "action": "reopened",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_action": "suspended_for_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "previous_authority": match.group("previous_authority").strip(),
            },
        )], ""

    match = _DE_OWN_SHARES_DESTROYED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.own_shares_destroyed_on_reduction.v1", {
                "kind": "capital_reduction", "action": "own_shares_destroyed",
                "date": _iso_date(match.group("date")),
                "shares_destroyed": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_no_notice.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_ROLE_HOLDER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.role_holder_name_corrected.v1",
            match.group("name"), role=match.group("role").strip(), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_PERSON_NAME_CORRECTED_IN_REALITY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_corrected_in_reality.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_NOTICE_ROLE_HOLDER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.notice_role_holder_name_corrected.v1",
            match.group("name"), role=match.group("role").strip(), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_COMMITTEE_MEMBERS_WITH_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_members_with_president.v1"
        events = []
        for index in (1, 2):
            place = match.group(f"place{index}")
            origin = place if index == 1 else match.group("origin2")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": origin.strip(),
                    "co_signs_with_roles": ["président"],
                },
            ))
        return events, ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_removed_date.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "basis": "statutes",
            },
        )], ""

    match = _FR_INHERITANCE_COMMUNITY_MANAGER_NAMED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.inheritance_community_manager_named.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "name_recorded",
                "inheritance_community_member": True,
            },
        )], ""

    if _FR_STATUTES_NON_PUBLIC_CONNECTOR.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_non_public_connector.v1", {
                "kind": "statutes_scope",
                "action": "non_public_scope_connector_recognized",
                "fragment": leftover.rstrip("."),
            },
        )], ""

    return [], text
