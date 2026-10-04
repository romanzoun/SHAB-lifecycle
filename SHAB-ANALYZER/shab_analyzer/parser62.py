from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_NEW_PERSON_SECTION = re.compile(
    r"^Neu eingetragene Personen:\s*(?P<persons>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_INLINE_PERSON = re.compile(
    r"(?P<name>[^,;]+),\s*(?P<nationality>[^,;]+),\s*"
    r"in\s+(?P<place>[^,;]+),\s*(?P<role>[^,;]+),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_RESIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président\s+et\s+"
    r"(?P<member>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,;]+),\s*(?:à|au|aux)\s+(?P<place>[^,;]+),\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+une part de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+au gérant\s+(?P<buyer>[^,.;]+),\s*"
    r"nouvel associé pour une part de\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_CHANGED = re.compile(
    r"^Weitere Adresse neu:\s*(?P<to>.+?)\s*"
    r"\[bisher:\s*(?P<from>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_RESIDUAL = re.compile(
    r"^(?P<changed>[^,.;]+)\s+jusqu['’]ici sans signature maintenant\s+"
    r"(?P<signed>[^,.;]+),\s*de et à\s+(?P<signed_place>[^,.;]+),\s*"
    r"signature collective à deux,\s*"
    r"(?P<unsigned>[^,.;]+),\s*de et à\s+(?P<unsigned_place>[^,.;]+),\s*"
    r"sans signature sont membres du comité\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_COMPLETED_DELETION = re.compile(
    r"^Die Liquidation ist abgeschlossen,\s*die Gesellschaft wird gelöscht\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_REMOVED_SHORT = re.compile(
    r"^Organisation neu:\s*\[Streichung aufgrund geänderter "
    r"Eintragungsvorschriften\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_NON_REGISTERABLE_REMARK_REMOVED_DOTTED = re.compile(
    r"^\[Streichung der Bemerkung,\s*da nicht zum Eintragungstext gehörend\.\]\s*"
    r"\[gestrichen:\s*(?P<removed>[^\]]+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_RESIDUAL_HEADING = re.compile(
    r"^(?:Autres|Nouvelles formes des)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REINSTATED_AFTER_ERRONEOUS_DELETION = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*"
    r"Die Zweigniederlassung wurde irrtümlich gestützt auf eine Meldung gemäss\s+"
    r"(?P<legal_basis>Art\.\s*111 Abs\.\s*2 HRegV)\s+gelöscht\.\s*"
    r"Da die Gesellschaft am Hauptsitz jedoch infolge Fusion gelöscht wurde,\s*"
    r"wurde diese Zweigniederlassung irrtümlich gelöscht\.\s*"
    r"Sie wird entsprechend hiermit wieder eingetragen\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_MORATORIUM_REVOKED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?:der|die)\s+(?P<authority>.+?)\s+die mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+bis zum\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+bewilligte definitive "
    r"Nachlassstundung widerrufen\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_RENAMED = re.compile(
    r"^L['’]associée?\s+(?P<old_name>.+?)\s+"
    r"\((?P<old_registry_id>[^)]+)\)\s+a modifié sa raison de commerce en\s+"
    r"(?P<name>.+?)\s+\((?P<registry_id>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_ORIGIN_CORRECTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+est originaire de\s+(?P<to>.+?)\s+"
    r"\(et non pas de\s+(?P<from>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ART_934_DELETION_BLOCKED_DATE_VARIANT = re.compile(
    r"^Das amtliche Verfahren zur Löschung der Rechtseinheit gemäss\s+"
    r"(?P<legal_basis>Art\.\s*934 OR i\.V\.m\. Art\.\s*153 HRegV)\s+"
    r"ist gemäss rechtskräftiger Verfügung\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+abgeschlossen\.\s*"
    r"Die Rechtseinheit kann mangels Zustimmung der Eidgenössischen und "
    r"kantonalen Steuerverwaltungen noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_REMOVED_DIRECT = re.compile(
    r"^Gelöschte andere Adresse:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "einzel" in raw.lower() or "individ" in raw.lower()
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


def extract_parser62_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 62."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_NEW_PERSON_SECTION.search(leftover)
    if match:
        people = [
            _DE_INLINE_PERSON.fullmatch(chunk.strip())
            for chunk in match.group("persons").split(";")
        ]
        if people and all(people):
            consume(match)
            for person in people:
                assert person is not None
                descriptor = person.group("nationality").strip()
                identity = (
                    {"heimat": descriptor[4:].strip()}
                    if descriptor.lower().startswith("von ")
                    else {"nationality": descriptor}
                )
                events.append(
                    _person_event(
                        publication_id,
                        published_at,
                        org_uid,
                        plz,
                        canton,
                        "officer_changed",
                        "de.persons.mixed_language_new_person.v1",
                        person.group("name"),
                        place=person.group("place"),
                        role=person.group("role").strip(),
                        signing=_signing(person.group("sign")),
                        extra={
                            "action": "appointed",
                            **identity,
                        },
                    )
                )

    match = _FR_ADMINISTRATION_PAIR_RESIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.administration_pair.v1",
                match.group("president"),
                role="président",
                signing="Einzelunterschrift",
                extra={"action": "role_changed"},
            )
        )
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.administration_pair.v1",
                match.group("member"),
                place=match.group("place"),
                role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                },
            )
        )

    match = _FR_SINGLE_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        nominal = match.group("nominal")
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.single_share_transfer.v1",
                seller,
                role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_transferred": 1,
                    "transferred_nominal": nominal,
                },
            )
        )
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.single_share_transfer.v1",
                buyer,
                role="associé-gérant",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "shares_received": 1,
                    "shares_count": 1,
                    "shares_nominal": match.group("buyer_nominal"),
                },
            )
        )

    match = _DE_ADDITIONAL_ADDRESS_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "de.text.additional_address_changed.v1",
                {
                    "kind": "additional_address",
                    "action": "changed",
                    "from": match.group("from").strip(),
                    "to": match.group("to").strip(),
                },
            )
        )

    match = _FR_COMMITTEE_RESIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "signing_authority_changed",
                "fr.persons.committee_group.v1",
                match.group("changed"),
                role="membre du comité",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "modified", "previous_without_signature": True},
            )
        )
        for name_group, place_group, signing in (
            ("signed", "signed_place", "Kollektivunterschrift zu zweien"),
            ("unsigned", "unsigned_place", None),
        ):
            extra = {
                "action": "appointed",
                "heimat": match.group(place_group).strip(),
            }
            if signing is None:
                extra["without_signature"] = True
            events.append(
                _person_event(
                    publication_id,
                    published_at,
                    org_uid,
                    plz,
                    canton,
                    "officer_changed",
                    "fr.persons.committee_group.v1",
                    match.group(name_group),
                    place=match.group(place_group),
                    role="membre du comité",
                    signing=signing,
                    extra=extra,
                )
            )

    match = _DE_LIQUIDATION_COMPLETED_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "company_deleted",
                "de.text.liquidation_deletion.v1",
                {
                    "reason": "liquidation_completed",
                    "note": match.group(0).strip(),
                },
            )
        )

    match = _DE_ORGANIZATION_REMOVED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.organization_removed_short.v1",
                {
                    "action": "removed",
                    "reason": "changed_registration_rules",
                },
            )
        )

    match = _DE_NON_REGISTERABLE_REMARK_REMOVED_DOTTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "organization_changed",
                "de.text.non_registerable_remark_removed.v2",
                {
                    "kind": "registry_remark",
                    "action": "removed",
                    "reason": "not_part_of_registration_text",
                    "removed_fact": match.group("removed").strip(),
                },
            )
        )

    match = _DE_BRANCH_REINSTATED_AFTER_ERRONEOUS_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.branch_reinstated_erroneous_deletion.v1",
                {
                    "kind": "registration_reinstated",
                    "scope": "branch",
                    "reason": "erroneous_deletion",
                    "head_office_deleted_by_merger": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _DE_COMPOSITION_MORATORIUM_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.composition_moratorium_revoked.v1",
                {
                    "kind": "composition_moratorium_revoked",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "previous_decision_date": _iso_date(
                        match.group("previous_decision_date")
                    ),
                    "previous_until": _iso_date(match.group("previous_until")),
                },
            )
        )

    match = _FR_ASSOCIATE_ORGANIZATION_RENAMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.associate_organization_renamed.v1",
                match.group("name"),
                role="associée",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("old_registry_id").strip(),
                    "registry_id": match.group("registry_id").strip(),
                },
            )
        )

    match = _FR_PERSON_ORIGIN_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "officer_changed",
                "fr.persons.origin_corrected.v1",
                match.group("name"),
                extra={
                    "action": "origin_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "from": match.group("from").strip(),
                    "to": match.group("to").strip(),
                },
            )
        )

    match = _DE_ART_934_DELETION_BLOCKED_DATE_VARIANT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "status_changed",
                "de.text.art_934_deletion_blocked.v4",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "procedure_completed": True,
                    "procedure_completed_at": _iso_date(match.group("date")),
                    "tax_authority": "federal_and_cantonal",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _DE_ADDITIONAL_ADDRESS_REMOVED_DIRECT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id,
                published_at,
                org_uid,
                plz,
                canton,
                "address_changed",
                "de.text.additional_address_removed_direct.v1",
                {
                    "kind": "additional_address",
                    "action": "removed",
                    "address": match.group("address").strip(),
                },
            )
        )

    match = _FR_RESIDUAL_HEADING.search(leftover)
    if match:
        consume(match)

    return events, leftover
