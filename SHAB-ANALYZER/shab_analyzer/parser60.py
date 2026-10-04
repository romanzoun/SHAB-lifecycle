from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_LIQUIDATORS_ADMIN_AND_PERSON = re.compile(
    r"Liquidateurs:\s*l['’](?P<old_role>administratrice?)\s+"
    r"(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*"
    r"tous deux\b",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_SEPARATE_ORIGINS = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),?\s*et\s*"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*de et à\s+"
    r"(?P<place2>[^,.;]+),\s*(?:avec\s+)?"
    r"(?P<sign>signature individuelle|signature collective(?:\s+à\s+deux)?),\s*"
    r"sont membres du conseil d['’]administration",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENED_BY_DECISION = re.compile(
    r"Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"hat\s+(?P<authority>.+?)\s+den Konkurs über die Gesellschaft "
    r"mit Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*eröffnet",
    re.I | re.UNICODE,
)
_FR_ORPHAN_BRANCH_SUBJECT = re.compile(r"^\s*La succursale\s*$", re.I | re.UNICODE)
_DE_PREVIOUS_COOPERATIVE_OBLIGATIONS = re.compile(
    r"\[bisher:\s*Pflichten:\s*(?P<previous>[^\]]+?)\.?\]",
    re.I | re.UNICODE,
)
_FR_PAIR_SIGNING_EXCLUSION = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+?)\s+et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+?)\s+continuent à engager la société "
    r"par leur\s+(?P<sign>signature collective à deux|procuration collective à deux),\s*"
    r"désormais pas entre eux",
    re.I | re.UNICODE,
)
_FR_SINGLE_SIGNING_EXCLUSION = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+?)\s+continue à engager la société "
    r"par (?:sa|son)\s+(?P<sign>signature collective à deux|procuration collective à deux),\s*"
    r"désormais pas avec\s+(?P<not_with>[^.;]+)",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_NAME_CHANGE = re.compile(
    r"(?:,\s*)?Sede principale a:\s*(?P<seat>[^.]+)\.\s*"
    r"Nuovo nome della ditta della sede principale:\s*(?P<to>.+?)\s*"
    r"\[finora:\s*Ditta della sede principale:\s*(?P<from>[^\]]+)\]",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_VARIANT = re.compile(
    r"Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Inventar(?: per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4}))?\s+"
    r"(?:den\s+(?:Teilbetrieb|Geschäftsteil)\s+[\"“](?P<business_unit>.+?)[\"”]\s+mit\s+)?"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) "
    r"von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\s*\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)(?=\s*$)",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_NON_PUBLIC_STATUTES_NOTE = re.compile(
    r"\[Statutenänderung ohne Änderung publikationspflichtiger Tatsachen\]",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_IDENTIFIER_AND_SEAT = re.compile(
    r"(?:,\s*)?Sede principale a:\s*(?P<context_seat>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*(?P<to_id>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*Numero di identificazione della sede principale:\s*(?P<from_id>[^\]]+)\]\.\s*"
    r"Nuova sede principale:\s*(?P<to_seat>[^\[]+?)\s*"
    r"\[finora:\s*(?P<from_seat>[^\]]+)\]",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED = re.compile(
    r"Das Statutendatum datiert richtig vom\s+(?P<to>\d{2}\.\d{2}\.\d{4}),\s*"
    r"nicht vom\s+(?P<from>\d{2}\.\d{2}\.\d{4})",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"\bliées selon statuts\b",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_PARTICIPATION_CAPITAL = re.compile(
    r"L['’]assemblée générale a introduit une clause statutaire relative à la "
    r"création,\s*sous forme d['’]augmentation autorisée,\s*d['’]un "
    r"capital-participation,\s*par décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4});\s*"
    r"pour les détails,\s*voir les statuts",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_SHARE_CERTIFICATE = re.compile(
    r"Anteilscheine neu:\s*CHF\s*(?P<nominal>[\d'.]+)",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGERS_PAIR = re.compile(
    r"Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*président,\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _signing(raw: str) -> str:
    lowered = raw.lower()
    if "procuration" in lowered:
        return "Kollektivprokura zu zweien"
    if "individ" in lowered:
        return "Einzelunterschrift"
    return "Kollektivunterschrift zu zweien"


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


def extract_parser60_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 60."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    if language == "fr":
        match = _FR_LIQUIDATORS_ADMIN_AND_PERSON.search(leftover)
        if match:
            consume(match)
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.liquidators_mixed_pair.v1",
                    match.group("name1"),
                    role="administratrice et liquidatrice",
                    extra={"action": "appointed_as_liquidator", "previous_role": match.group("old_role")},
                )
            )
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.liquidators_mixed_pair.v1",
                    match.group("name2"), place=match.group("place"), role="liquidateur",
                    extra={
                        "action": "appointed_as_liquidator",
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                    },
                )
            )

        match = _FR_BOARD_MEMBERS_SEPARATE_ORIGINS.search(leftover)
        if match:
            consume(match)
            signing = _signing(match.group("sign"))
            for index in (1, 2):
                extra = {"action": "appointed"}
                if index == 1:
                    extra["heimat"] = match.group("origin1").strip()
                else:
                    extra["heimat"] = match.group("place2").strip()
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        "officer_changed", "fr.persons.board_members_separate_origins.v1",
                        match.group(f"name{index}"), place=match.group(f"place{index}"),
                        role="membre du conseil d'administration", signing=signing,
                        extra=extra,
                    )
                )

        while True:
            match = _FR_PAIR_SIGNING_EXCLUSION.search(leftover)
            if not match:
                break
            consume(match)
            signing = _signing(match.group("sign"))
            for name_group, other_group in (("name1", "name2"), ("name2", "name1")):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        "signing_authority_changed", "fr.persons.signing_exclusion_pair.v1",
                        match.group(name_group), signing=signing,
                        extra={
                            "action": "restriction_changed",
                            "continues_signing": True,
                            "not_with": match.group(other_group).strip(),
                        },
                    )
                )

        while True:
            match = _FR_SINGLE_SIGNING_EXCLUSION.search(leftover)
            if not match:
                break
            consume(match)
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.signing_exclusion.v1",
                    match.group("name"), signing=_signing(match.group("sign")),
                    extra={
                        "action": "restriction_changed",
                        "continues_signing": True,
                        "not_with": match.group("not_with").strip(),
                    },
                )
            )

        match = _FR_SHARE_TRANSFER_RESTRICTION.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "fr.text.share_transfer_restriction.v6",
                    {
                        "kind": "share_transfer_restriction",
                        "action": "applied",
                        "restriction": "liées selon statuts",
                    },
                )
            )

        match = _FR_AUTHORIZED_PARTICIPATION_CAPITAL.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "fr.text.authorized_participation_capital.v1",
                    {
                        "kind": "authorized_participation_capital_clause",
                        "action": "introduced",
                        "decision_date": _iso_date(match.group("date")),
                        "details_in_statutes": True,
                    },
                )
            )

        match = _FR_NEW_MANAGERS_PAIR.search(leftover)
        if match:
            consume(match)
            signing = _signing(match.group("sign"))
            people = (
                (1, "gérant", None),
                (2, "gérant et président", match.group("country2")),
            )
            for index, role, country in people:
                common = {
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    **({"country": country} if country else {}),
                }
                for event_type, rule_id in (
                    ("officer_changed", "fr.persons.managers_pair.v2"),
                    ("signing_authority_changed", "fr.persons.managers_pair_signing.v2"),
                ):
                    events.append(
                        _person_event(
                            publication_id, published_at, org_uid, plz, canton,
                            event_type, rule_id, match.group(f"name{index}"),
                            place=match.group(f"place{index}"), role=role,
                            signing=signing, extra=common,
                        )
                    )

        # The address rule has already consumed the predicate and emitted the event.
        # Remove only the exact grammatical subject that it can leave behind.
        match = _FR_ORPHAN_BRANCH_SUBJECT.search(leftover)
        if match:
            consume(match)

    if language == "de":
        match = _DE_BANKRUPTCY_OPENED_BY_DECISION.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", "de.text.bankruptcy_opened.v3",
                    {
                        "kind": "bankruptcy_opened",
                        "decision_date": _iso_date(match.group("decision_date")),
                        "effective_date": _iso_date(match.group("effective_date")),
                        "effective_time": match.group("time").replace(".", ":"),
                        "authority": match.group("authority").strip(),
                    },
                )
            )

        match = _DE_PREVIOUS_COOPERATIVE_OBLIGATIONS.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", "de.text.cooperative_obligations_previous.v1",
                    {
                        "kind": "member_obligations",
                        "action": "previous_value",
                        "obligations": match.group("previous").strip().rstrip("."),
                    },
                )
            )

        match = _DE_ASSET_TRANSFER_VARIANT.search(leftover)
        if match:
            consume(match)
            inventory_date = match.group("inventory_date")
            payload = {
                "date": _iso_date(match.group("date")),
                "inventory_date": _iso_date(inventory_date) if inventory_date else None,
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": re.sub(r"\s+", "", match.group("uid")),
                "consideration": match.group("consideration").strip().rstrip("."),
            }
            if match.group("business_unit"):
                payload["business_unit"] = match.group("business_unit").strip()
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "assets_transferred", "de.text.asset_transfer.v4", payload,
                )
            )

        match = _DE_NON_PUBLIC_STATUTES_NOTE.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "de.text.non_public_statutes_note.v2",
                    {"kind": "non_public_facts", "publishable_facts_changed": False},
                )
            )

        match = _DE_STATUTES_DATE_CORRECTED.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "publication_corrected", "de.text.statutes_date_corrected.v1",
                    {
                        "kind": "statutes_date",
                        "from": _iso_date(match.group("from")),
                        "to": _iso_date(match.group("to")),
                    },
                )
            )

        match = _DE_COOPERATIVE_SHARE_CERTIFICATE.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "de.text.cooperative_share_certificate.v1",
                    {
                        "kind": "cooperative_share_certificate",
                        "currency": "CHF",
                        "nominal": match.group("nominal"),
                    },
                )
            )

    if language == "it":
        match = _IT_HEAD_OFFICE_NAME_CHANGE.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_name_changed", "it.text.head_office_name.v1",
                    {
                        "scope": "head_office",
                        "head_office_seat": match.group("seat").strip(),
                        "from": match.group("from").strip(),
                        "to": match.group("to").strip(),
                    },
                )
            )

        match = _IT_HEAD_OFFICE_IDENTIFIER_AND_SEAT.search(leftover)
        if match:
            consume(match)
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "company_identifier_changed", "it.text.head_office_identifier.v1",
                    {
                        "scope": "head_office",
                        "from": match.group("from_id").strip(),
                        "to": match.group("to_id"),
                    },
                )
            )
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "seat_changed", "it.text.head_office.v2",
                    {
                        "scope": "head_office",
                        "from": match.group("from_seat").strip(),
                        "to": match.group("to_seat").strip(),
                        "context_seat": match.group("context_seat").strip(),
                    },
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
