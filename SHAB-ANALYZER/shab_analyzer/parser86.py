from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_UNPUBLISHED_STATUTES_POINTS = re.compile(
    r"^sur des points non soumis à la publication\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR_RESIDUAL = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres du conseil d['’]administration,\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_SPLIT_TRANSFER_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<buyer1_received>[\d']+)\s+parts à\s+(?P<buyer1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*nouvelle\s+"
    r"associée-gérante présidente,\s*sans signature,\s*titulaire de\s+"
    r"(?P<buyer1_count>[\d']+)\s+parts de CHF\s+(?P<buyer1_nominal>[\d'.]+),\s*"
    r"et par\s+(?P<buyer2_received>[\d']+)\s+parts à\s+(?P<buyer2>[^,.;]+),\s*"
    r"de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*nouvel\s+"
    r"associé-gérant,\s*sans signature,\s*avec\s+(?P<buyer2_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer2_nominal>[\d'.]+);\s*(?P=seller)\s+reste\s+"
    r"titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont chacun cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*nommé en outre gérant\s+"
    r"Par conséquent,\s*(?P=seller1)\s+et\s+(?P=seller2)\s+sont\s+"
    r"mai(?:n)?tenant associés chacun pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_CLASSES_TRANSFORMED = re.compile(
    r"^Les\s+(?P<from_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"sont transformées en\s+(?P<count1>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*et\s+(?P<count2>[\d']+)\s+actions nominatives "
    r"de CHF\s+(?P<nominal2>[\d'.]+),\s*(?P<rights>privilégiées quant au droit "
    r"de vote),\s*toutes\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s*(?P<notice_id>\d+)\)\s+"
    r"est rectifiée dans ce sens que\s+(?P<name>[^,.;]+)\s+est domicilié(?:e)? à\s+"
    r"(?P<place>[^()]+?)\s*\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ACTIVITY_REMOVED = re.compile(
    r"^Le titulaire n['’]exploite plus\s+(?P<activity>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATEMENT_JUDICIAL = re.compile(
    r"^Par décision judiciaire du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"prononcée par\s+(?P<authority>.+?),\s*(?:il\s+)?a été ordonné la "
    r"réinscription de cette société radiée comme société en liquidation\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_MANAGER_REPLACED = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>Leiter der Zweigniederlassung),\s*"
    r"(?P<removed_sign>Kollektivunterschrift zu zweien)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<changed>[^,.;]+),\s*"
    r"(?P<previous_role>Stellvertretender Leiter der Zweigniederlassung),\s*"
    r"(?P<previous_sign>Kollektivunterschrift zu zweien),\s*neu\s+"
    r"(?P<role>Leiter der Zweigniederlassung),\s*"
    r"(?P<sign>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CORRECTION_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s*(?P<notice_id>\d+)\)\s+"
    r"est rectifiée dans ce sens que\s+(?P<name>[^,.;]+)\s+est originaire de\s+"
    r"(?P<origin>[^()]+?)\s*\(et non pas de\s+(?P<previous_origin>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_THREE = re.compile(
    r"^Signature collective à deux est conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*tous deux de\s+(?P<origin12>[^,.;]+),\s*à\s+"
    r"(?P<place12>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*de et à\s+"
    r"(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_SIGNING_RESTRICTION_REMOVED_GROUP = re.compile(
    r"^Les membres du conseil de fondation\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*désormais à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+)\s+continuent à signer collectivement à deux\s+"
    r"désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_ROLE_CORRECTION = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que:\s*"
    r"signature individuelle a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"(?P<role>directeur général),\s*et non pas\s+(?P<previous_role>directeur)\.?$",
    re.I | re.UNICODE,
)
_FR_INTERCANTONAL_SEAT_TRANSFER_DELETION = re.compile(
    r"^Par suite de transfert de siège à\s+(?P<place>[^,.;]+),\s*la société a été "
    r"inscrite au registre du commerce du canton de\s+(?P<canton_name>[^.]+)\.\s*"
    r"En conséquence,\s*elle est radiée d['’]office du registre du commerce du\s+"
    r"(?P<previous_registry>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE_STATEMENT = re.compile(
    r"^Zweck ist\s+(?P<purpose>der Handel,\s*die Produktion,\s*die Verpackung,\s*"
    r"die Distribution,\s*der Import und Export,\s*der Grosshandel und der "
    r"Einzelhandel von kosmetischen Produkten und medizinischen Geräten)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_PROXY_REVOKED = re.compile(
    r"^Signature\s+(?P<sign>individuelle)\s+a été conférée à\s+"
    r"(?P<name>[^,.;]+);\s*sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser86_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 86."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_UNPUBLISHED_STATUTES_POINTS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "fr.text.unpublished_statutes_points.v2",
                {"kind": "non_public_amendment", "publication_required": False},
            )
        )

    match = _FR_BOARD_MEMBERS_PAIR_RESIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_members_pair_residual.v1"
        people = (
            (match.group("name1"), match.group("place1"), match.group("place1")),
            (match.group("name2"), match.group("place2"), match.group("origin2")),
        )
        for name, place, origin in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name, place=place,
                    role="membre du conseil d'administration",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", "heimat": origin.strip()},
                )
            )

    match = _FR_SHARE_SPLIT_TRANSFER_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_split_transfer_two_managers.v1"
        seller = match.group("seller").strip()
        buyer1 = match.group("buyer1").strip()
        buyer2 = match.group("buyer2").strip()
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparties": [buyer1, buyer2],
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "shares_nominal": match.group("seller_nominal"),
                },
            )
        )
        buyers = (
            (1, buyer1, "associée-gérante présidente"),
            (2, buyer2, "associé-gérant"),
        )
        for index, buyer, role in buyers:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group(f"place{index}"), role=role,
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "counterparty": seller,
                        "shares_received": _count(match.group(f"buyer{index}_received")),
                        "shares_count": _count(match.group(f"buyer{index}_count")),
                        "shares_nominal": match.group(f"buyer{index}_nominal"),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_TWO_ASSOCIATES_TRANSFER_TO_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associates_transfer_to_manager.v1"
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        for group in ("seller1", "seller2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(group), role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                        "shares_nominal": match.group("seller_nominal"),
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    "action": "shares_received_and_appointed",
                    "heimat": match.group("origin").strip(),
                    "counterparties": [
                        match.group("seller1").strip(),
                        match.group("seller2").strip(),
                    ],
                    "shares_received": transferred * 2,
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"),
                },
            )
        )

    match = _FR_REGISTERED_SHARE_CLASSES_TRANSFORMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.registered_share_classes_transformed.v1",
                {
                    "kind": "share_classes_transformed",
                    "currency": "CHF",
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "registered": True,
                    "entire_share_capital": True,
                    "share_classes": [
                        {
                            "count": _count(match.group("count1")),
                            "nominal": match.group("nominal1"),
                            "registered": True,
                        },
                        {
                            "count": _count(match.group("count2")),
                            "nominal": match.group("nominal2"),
                            "registered": True,
                            "rights": match.group("rights"),
                        },
                    ],
                },
            )
        )

    match = _FR_DOMICILE_CORRECTION_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.domicile_correction_notice.v1",
                match.group("name"), place=match.group("place"),
                extra={
                    "action": "domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_SOLE_PROPRIETOR_ACTIVITY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.sole_proprietor_activity_removed.v1",
                {
                    "kind": "business_activity",
                    "action": "ceased",
                    "scope": "sole_proprietor",
                    "activity": match.group("activity").strip(),
                },
            )
        )

    match = _FR_COMPANY_REINSTATEMENT_JUDICIAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.company_reinstatement_judicial.v1",
                {
                    "kind": "registration_reinstated",
                    "action": "ordered",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "in_liquidation": True,
                },
            )
        )

    match = _DE_BRANCH_MANAGER_REPLACED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.branch_manager_replaced.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    role=match.group("removed_role"), signing=match.group("removed_sign"),
                    extra={"action": "removed", "scope": "branch"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("changed"),
                    role=match.group("role"), signing=match.group("sign"),
                    extra={
                        "action": "role_changed",
                        "scope": "branch",
                        "previous_role": match.group("previous_role"),
                        "previous_signing": match.group("previous_sign"),
                    },
                ),
            ]
        )

    match = _FR_ORIGIN_CORRECTION_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.origin_correction_notice.v1",
                match.group("name"),
                extra={
                    "action": "origin_corrected",
                    "from": match.group("previous_origin").strip(),
                    "to": match.group("origin").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_COLLECTIVE_SIGNING_THREE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.collective_signing_three.v1"
        people = (
            (match.group("name1"), match.group("place12"), match.group("origin12")),
            (match.group("name2"), match.group("place12"), match.group("origin12")),
            (match.group("name3"), match.group("place3"), match.group("place3")),
        )
        for name, place, origin in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, name, place=place,
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "granted", "heimat": origin.strip()},
                )
            )

    match = _FR_FOUNDATION_SIGNING_RESTRICTION_REMOVED_GROUP.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_signing_restriction_removed_group.v1"
        for index in (1, 2, 3):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    place=match.group("place2") if index == 2 else None,
                    role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "restriction_removed",
                        "signing_continues": True,
                        **({"domicile_changed": True} if index == 2 else {}),
                    },
                )
            )

    match = _FR_DIRECTOR_ROLE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.director_role_correction.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Einzelunterschrift",
                extra={
                    "action": "role_corrected",
                    "previous_role": match.group("previous_role").lower(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_INTERCANTONAL_SEAT_TRANSFER_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", "fr.text.intercantonal_seat_transfer_deletion.v1",
                {
                    "action": "transferred",
                    "to": match.group("place").strip(),
                    "register_canton": match.group("canton_name").strip(),
                    "previous_registry": match.group("previous_registry").strip(),
                    "deleted_from_previous_registry": True,
                },
            )
        )

    match = _DE_BRANCH_PURPOSE_STATEMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "purpose_changed", "de.text.branch_purpose_statement.v1",
                {"scope": "branch", "purpose": match.group("purpose").strip()},
            )
        )

    match = _FR_SIGNING_GRANTED_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_granted_proxy_revoked.v1",
                match.group("name"), signing="Einzelunterschrift",
                extra={
                    "action": "signing_replaced",
                    "previous_signing": "procuration",
                    "previous_signing_revoked": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
