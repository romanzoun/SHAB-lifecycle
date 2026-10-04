from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CIVIL_NAME = re.compile(
    r"(?:Par suite de changement d['’]état civil,\s*)?"
    r"(?P<old_name>[A-ZÀ-Ÿ][^.;]+?)\s+"
    r"(?:se nomme désormais|porte maintenant le nom(?: de)?)\s+"
    r"(?P<name>(?:de\s+)?[A-ZÀ-Ÿ][^.;]+)\.?,?",
    re.I | re.UNICODE,
)
_IT_CORRECTED_REGISTERED_PERSON = re.compile(
    r"Persona iscritta corretta:\s*(?P<last>[^,.;]+),\s*(?P<first>[^,.;]+),\s*"
    r"da\s+(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*con\s+(?P<sign>firma individuale|firma collettiva(?: a due)?),\s*"
    r"con\s+(?P<count>[\d']+)\s+quote?\s+da\s+CHF\s+(?P<nominal>[\d'.]+)"
    r"(?:\s*\[(?:no|finora):\s*(?P<previous>[^\]]+)\])?\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+et inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+"
    r"(?P<net>[\d'.]+)\s+à la société\s+(?P<recipient>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^.]+)\.\s*"
    r"Contre prestation:\s*(?P<consideration>.+?)(?=\s*$)",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ARTICLE_939_DISSOLUTION = re.compile(
    r"Par décision du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a été déclarée dissoute "
    r"conformément à l['’]article\s+(?P<article>939 CO);\s*sa liquidation a été "
    r"ordonnée selon les dispositions applicables à la faillite\.?,?",
    re.I | re.UNICODE,
)
_FR_LEGAL_BEARER_CONVERSION_TYPO = re.compile(
    r"Le\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*les actions au porteur ont été "
    r"converties de par la loi en actions nominatives\.\s*Les statuts de la société "
    r"n['’]ont pas encore été adaptés à la conversion,\s*mais devront l['’]être lors "
    r"de\s+(?:la|a)\s+prochaine modification\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*"
    r"divisé en\s+(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<kind>nominatives)\.?,?",
    re.I | re.UNICODE,
)
_FR_LEGAL_BEARER_CONVERSION_WITH_DIVISION = re.compile(
    r"Le\s+(?P<conversion_date>\d{2}\.\d{2}\.\d{4}),\s*les actions au porteur "
    r"ont été converties de par la loi en actions nominatives;\s*par décision de "
    r"l['’]assemblée générale du\s+(?P<adaptation_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"les statuts de la société ont été adaptés à la conversion\.\s*Division des\s+"
    r"(?P<from_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*(?P<from_restriction>désormais liées selon statuts),\s*"
    r"en\s+(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*libéré à concurrence de CHF\s+"
    r"(?P<paid>[\d'.]+),\s*divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*(?P<kind>nominatives),\s*"
    r"(?P<restriction>liées selon statuts)\.?,?",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_REMOVED = re.compile(
    r"Suppression de l['’]obligation de fournir des prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption selon statuts\.?,?",
    re.I | re.UNICODE,
)
_FR_SHARE_CLASSES_TRANSFORMED = re.compile(
    r"Transformation des\s+(?P<from_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*en\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*(?P<rights>privilégiées quant au droit de vote),\s*"
    r"et\s+(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\.\s*"
    r"Par conséquent,\s*l['’]associé-gérant\s+(?P<owner>[^.]+?)\s+détient\s+"
    r"(?P<owner_count1>[\d']+)\s+parts de CHF\s+(?P<owner_nominal1>[\d'.]+),\s*"
    r"privilégiées quant au droit de vote,\s*et\s+(?P<owner_count2>[\d']+)\s+"
    r"parts de CHF\s+(?P<owner_nominal2>[\d'.]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_PRIVILEGED_SHARE_TRANSFER = re.compile(
    r"L['’]associé-gérant\s+(?P<seller>.+?)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*(?P<rights>privilégiées quant au droit de vote)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>.+?),\s*nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*privilégiées quant au droit de vote\.?,?",
    re.I | re.UNICODE,
)
_IT_OWNER_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di fallimento aperto nei confronti del(?:la)? titolare il\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"\[(?P<history_label>radiati|finora):\s*(?P<previous>La titolare è stata "
    r"dichiarata in fallimento.+?)\]\.?,?",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_LIQUIDATORS_PAIR = re.compile(
    r"Liquidateurs:\s*l['’]administrateur\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>.+?)\s+lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NEW_SEAT = re.compile(
    r"Nouveau siège de l['’]organe de révision\s+[\"“](?P<name>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*(?P<place>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_DE_NON_PUBLIC_FACTS_NOTE = re.compile(
    r"\[Die Änderungen berühren keine publikationspflichtigen Tatsachen\.\]",
    re.I | re.UNICODE,
)
_MIXED_DE_PERSON_SECTIONS = re.compile(
    r"^\s*Gelöschte Personen:\s*(?P<removed>.+?)\.\s*"
    r"Neu eingetragene Personen:\s*(?P<added>.+?)\.?\s*$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_REMOVED_WITHOUT_SIGNATURE = re.compile(
    r"(?P<name>[^,;]+),\s*(?P<role>[^,;]+),\s*ohne Unterschrift",
    re.I | re.UNICODE,
)
_DE_ADDED_WITHOUT_SIGNATURE = re.compile(
    r"(?P<name>[^,;]+),\s*von\s+(?P<origin>[^,;]+),\s*in\s+(?P<place>[^,;]+),\s*"
    r"(?P<role>[^,;]+),\s*ohne Unterschrift",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_SAME_ORIGIN_PLACE = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*de et à\s+(?P<place2>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration,?",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
        else "Kollektivunterschrift zu zweien"
    )


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
    uid: str | None = None,
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
        person_key=(f"uid:{uid}" if uid else person_key(name=clean_name, place=clean_place)),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser56_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 56."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CIVIL_NAME.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.civil_name.v4", match.group("name"),
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "reason": "civil_status_change" if "état civil" in match.group(0) else None,
                },
            )
        )

    match = _IT_CORRECTED_REGISTERED_PERSON.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('last').strip()}, {match.group('first').strip()}"
        common = {
            "action": "corrected",
            "heimat": match.group("origin").strip(),
            "shares_count": _count(match.group("count")),
            "shares_nominal": match.group("nominal"),
        }
        if match.group("previous"):
            common["previous"] = match.group("previous").strip()
        signing = _signing(match.group("sign"))
        for event_type, rule_id in (
            ("officer_changed", "it.persons.corrected_registered.v1"),
            ("signing_authority_changed", "it.persons.corrected_registered_signing.v1"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, name, place=match.group("place"),
                    role=match.group("role").strip(), signing=signing, extra=common,
                )
            )

    match = _FR_ASSET_TRANSFER_WITH_INVENTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer_with_inventory.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "inventory_date": _iso_date(match.group("inventory_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "net_assets": match.group("net"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": match.group("consideration").strip().rstrip("."),
                },
            )
        )

    match = _FR_ARTICLE_939_DISSOLUTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.article_939_dissolution.v1",
                {
                    "kind": "dissolution",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "legal_basis": match.group("article"),
                    "liquidation": "bankruptcy_provisions",
                },
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_TYPO.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion.v10",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("date")),
                    "from_kind": "actions au porteur",
                    "to_kind": match.group("kind"),
                    "to_count": _count(match.group("count")),
                    "to_nominal": match.group("nominal"),
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "statutes_adapted": False,
                },
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_WITH_DIVISION.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_division.v1",
                {
                    "kind": "bearer_to_registered_conversion_and_share_split",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _iso_date(match.group("conversion_date")),
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "actions au porteur",
                    "to_kind": match.group("kind"),
                    "statutes_adapted": True,
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": match.group("from_nominal"),
                    },
                    "split_to": {
                        "count": _count(match.group("to_count")),
                        "nominal": match.group("to_nominal"),
                    },
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "restriction": match.group("restriction"),
                },
            )
        )

    match = _FR_ANCILLARY_OBLIGATIONS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.ancillary_obligations_removed.v2",
                {
                    "kind": "ancillary_obligations_and_preferential_rights",
                    "action": "removed",
                },
            )
        )

    match = _FR_SHARE_CLASSES_TRANSFORMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_classes_transformed.v1",
                {
                    "kind": "share_classes_transformed",
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "owner": match.group("owner").strip(),
                    "share_classes": [
                        {
                            "count": _count(match.group("count1")),
                            "nominal": match.group("nominal1"),
                            "rights": match.group("rights"),
                        },
                        {
                            "count": _count(match.group("count2")),
                            "nominal": match.group("nominal2"),
                        },
                    ],
                },
            )
        )

    match = _FR_PRIVILEGED_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        nominal = match.group("nominal")
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.privileged_share_transfer.v1", seller,
                role="associé-gérant",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "shares_nominal": match.group("seller_nominal"),
                },
            )
        )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.privileged_share_transfer.v1", buyer,
                place=match.group("place"), role="associé",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                    "share_rights": match.group("rights"),
                    "shares_received": _count(match.group("transferred")),
                    "transferred_nominal": nominal,
                },
            )
        )

    match = _IT_OWNER_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.owner_bankruptcy_effect_suspended.v2",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority").strip(),
                    "previous": match.group("previous").strip(),
                    "previous_entry_removed": match.group("history_label").lower() == "radiati",
                },
            )
        )

    match = _FR_LIQUIDATORS_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (match.group("name1"), None, "administrateur et liquidateur", {}),
            (
                match.group("name2"), match.group("place"), "liquidateur",
                {"heimat": match.group("origin").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.liquidators_pair.v1"),
                ("signing_authority_changed", "fr.persons.liquidators_pair_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role,
                        signing=signing, extra=extra,
                    )
                )

    match = _FR_AUDITOR_NEW_SEAT.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_new_seat.v1", match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="organe de révision", extra={"action": "seat_changed"},
            )
        )

    match = _DE_NON_PUBLIC_FACTS_NOTE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.non_public_facts_note.v1",
                {
                    "kind": "non_public_statute_changes",
                    "publication_relevant_facts": False,
                },
            )
        )

    match = _MIXED_DE_PERSON_SECTIONS.search(leftover)
    if match:
        consume(match)
        for raw in match.group("removed").split(";"):
            person = _DE_REMOVED_WITHOUT_SIGNATURE.fullmatch(raw.strip())
            if not person:
                continue
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", "de.persons.mixed_language_without_signature.v1",
                    person.group("name"), role=person.group("role").strip(),
                    extra={"without_signature": True},
                )
            )
        for raw in match.group("added").split(";"):
            person = _DE_ADDED_WITHOUT_SIGNATURE.fullmatch(raw.strip())
            if not person:
                continue
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "de.persons.mixed_language_without_signature.v1",
                    person.group("name"), place=person.group("place"),
                    role=person.group("role").strip(),
                    extra={
                        "heimat": person.group("origin").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_BOARD_MEMBERS_SAME_ORIGIN_PLACE.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            place = match.group(f"place{index}").strip()
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_same_origin_place.v1",
                    match.group(f"name{index}"), place=place,
                    role="membre du conseil d'administration",
                    extra={"heimat": place},
                )
            )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
