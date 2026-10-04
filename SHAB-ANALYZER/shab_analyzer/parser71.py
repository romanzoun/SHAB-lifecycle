from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PAIR_DOMICILE_CHANGED = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont\s+"
    r"(?:maintenant|désormais)\s+domiciliés?\s+à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_PAIR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé(?:e)?\s+président(?:e)?,\s*"
    r"lequel(?:le)?\s+continue\s+à\s+signer\s+individuellement,\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*tous\s+deux\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_ART_155_DELETION_BLOCKED = re.compile(
    r"^,?\s*Sede principale a:\s*Sede principale:\s*(?P<head_office>[^.(]+?)"
    r"(?:\s*\((?P<head_office_country>[A-Z]{2})\))?\.\s*"
    r"Nuove disposizioni per la succursale:\s*La succursale deve essere cancellata "
    r"a seguito della procedura di cui all['’]art\.\s*(?P<article>155)\s+ORC\.\s*"
    r"La cancellazione non può tuttavia essere effettuata mancando il consenso "
    r"delle autorità fiscali federali e cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSLATIONS_SUPPLEMENTED = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que la "
    r"raison sociale comprend une version allemande et une version anglaise\.\s*"
    r"Raison sociale:\s*(?P<name>[^()]+?)\s*\((?P<german>[^()]+)\)\s*"
    r"\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_NAME_WITHOUT_HISTORY = re.compile(
    r"^Firma Hauptsitz neu:\s*(?P<to>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_ROLES_AND_SIGNING_CHANGED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<old_roles>.+?),\s*(?P<old_signing>Einzelunterschrift|"
    r"Kollektivunterschrift(?:\s+zu\s+zweien)?),\s*neu\s+"
    r"(?P<new_role>[^,.;]+),\s*ohne Unterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLVED_LIQUIDATORS_PAIR = re.compile(
    r"^Selon décision de l['’](?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la fondation est dissoute\.\s*"
    r"Liquidateurs:\s*les membres du conseil\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*lesquels continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^Nouveau membre du conseil de fondation sans signature:\s*"
    r"(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_SEAT_WITHOUT_HISTORY = re.compile(
    r"^,?\s*Nuova sede principale:\s*(?P<to>[^()]+?)"
    r"(?:\s*\((?P<country>[A-Z]{2})\))?\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTION_REMOVED_WITHOUT_ROLE = re.compile(
    r"^(?P<name>[^,.;]+)\s+continue à signer collectivement à deux,?\s*"
    r"désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_RENAMED = re.compile(
    r"^L['’]associée?\s+(?P<old_name>.+?)\s+\((?P<old_registry_id>[^)]+)\)\s+"
    r"porte désormais la raison sociale\s+(?P<name>.+?)\s+"
    r"\((?P<registry_id>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_DOMICILE_ADDRESS = re.compile(
    r"^\[bisher:\s*Die Gesellschaft führt an folgender Adresse ihr "
    r"Geschäftsdomizil:\s*(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^\].]+)\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_IDENTIFIER_WITHOUT_HISTORY = re.compile(
    r"^UID neu:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_ORGANIZATION_RENAMED = re.compile(
    r"^(?P<old_name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"porte désormais la raison sociale\s+(?P<name>.+?)\s+"
    r"\((?P<new_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_ERRONEOUS = re.compile(
    r"^\[Die Eintragung des Verzichts auf eine eingeschränkte Revision erfolgte "
    r"irrtümlich,\s*da die Gesellschaft über eine Revisionsstelle verfügt\.\]\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower() or "einzel" in raw.lower()
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
        person_key=person_key(name=clean_name, place=clean_place, uid=uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser71_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 71."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PAIR_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.pair_domicile_changed.v2",
                    match.group(group), place=match.group("place"),
                    extra={"action": "domicile_changed", "domicile_changed": True},
                )
            )

    match = _FR_ADMINISTRATION_PRESIDENT_AND_PAIR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.administration_president_and_pair.v1",
                match.group("president"), role="président",
                signing="Einzelunterschrift",
                extra={"action": "role_changed", "signing_continues": True},
            )
        )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_president_and_pair.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                    },
                )
            )

    match = _IT_BRANCH_ART_155_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.branch_art155_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "scope": "branch",
                    "head_office": match.group("head_office").strip(),
                    "head_office_country": match.group("head_office_country"),
                    "legal_basis": f"art. {match.group('article')} ORC",
                    "deletion_required": True,
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _FR_COMPANY_TRANSLATIONS_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "fr.text.company_translations_supplemented.v1",
                {
                    "action": "translations_added",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "name": match.group("name").strip(),
                    "translations": {
                        "de": match.group("german").strip(),
                        "en": match.group("english").strip(),
                    },
                },
            )
        )

    match = _DE_HEAD_OFFICE_NAME_WITHOUT_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "de.text.head_office_name_without_history.v1",
                {
                    "scope": "head_office",
                    "action": "changed",
                    "to": match.group("to").strip(),
                },
            )
        )

    match = _DE_REGISTERED_PERSON_ROLES_AND_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.roles_and_signing_changed.v1",
                match.group("name"), role=match.group("new_role"),
                extra={
                    "action": "roles_and_signing_changed",
                    "previous_roles": [
                        role.strip() for role in match.group("old_roles").split(",")
                    ],
                    "previous_signing": _signing(match.group("old_signing")),
                    "without_signature": True,
                },
            )
        )

    match = _FR_FOUNDATION_DISSOLVED_LIQUIDATORS_PAIR.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.foundation_dissolved.v1",
                {
                    "kind": "dissolution",
                    "scope": "foundation",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_liquidators_pair.v1",
                    match.group(group), role="liquidateur",
                    signing=_signing(match.group("sign")),
                    extra={"action": "role_changed", "signing_continues": True},
                )
            )

    match = _FR_FOUNDATION_MEMBER_SAME_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.foundation_member_same_origin_place.v1",
                match.group("name"), place=match.group("place"),
                role="membre du conseil de fondation",
                extra={
                    "action": "appointed",
                    "heimat": match.group("place").strip(),
                    "without_signature": True,
                },
            )
        )

    match = _IT_HEAD_OFFICE_SEAT_WITHOUT_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", "it.text.head_office_seat_without_history.v1",
                {
                    "scope": "head_office",
                    "action": "changed",
                    "to": match.group("to").strip(),
                    "country": match.group("country"),
                },
            )
        )

    match = _FR_SIGNING_RESTRICTION_REMOVED_WITHOUT_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_restriction_removed_without_role.v1",
                match.group("name"), signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_continues": True},
            )
        )

    match = _FR_ASSOCIATE_ORGANIZATION_RENAMED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_organization_renamed.v2",
                match.group("name"), role="associée",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("old_registry_id").strip(),
                    "registry_id": match.group("registry_id").strip(),
                },
            )
        )

    match = _DE_PREVIOUS_DOMICILE_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.previous_domicile_address.v1",
                {
                    "action": "removed",
                    "kind": "domicile_address",
                    "address": (
                        f"{match.group('street').strip()}, "
                        f"{match.group('postal_code')} {match.group('locality').strip()}"
                    ),
                    "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            )
        )

    match = _DE_COMPANY_IDENTIFIER_WITHOUT_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed",
                "de.text.company_identifier_without_history.v1",
                {"scope": "organization", "action": "changed", "to": match.group("to")},
            )
        )

    match = _FR_REGISTERED_ORGANIZATION_RENAMED.search(leftover)
    if match and match.group("uid") == match.group("new_uid"):
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.registered_organization_renamed.v1",
                match.group("name"), uid=match.group("new_uid"),
                role="organe de révision",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "uid": match.group("new_uid"),
                },
            )
        )

    match = _DE_AUDIT_WAIVER_ERRONEOUS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.audit_waiver_erroneous.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "corrected",
                    "waiver_declared": False,
                    "auditor_exists": True,
                    "previous_entry_erroneous": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
