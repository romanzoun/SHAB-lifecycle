from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CIVIL_NAME_NOW = re.compile(
    r"^Par suite de changement d['’]état civil\s+"
    r"(?P<old_name>.+?)\s+porte désormais le nom de\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_IDENTIFIER = re.compile(
    r"^Nouveau numéro IDE:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[précédemment:\s*(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\]\.?$",
    re.I | re.UNICODE,
)
_IT_DISSOLUTION_BY_ASSEMBLY = re.compile(
    r"^La società è sciolta con decisione dell['’]assemblea generale del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_GRANTED_AND_EXTENDED = re.compile(
    r"^Das\s+(?P<authority>.+?)\s+hat der Gesellschaft mit Entscheid vom\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+die provisorische Nachlassstundung "
    r"für die Dauer von\s+(?P<duration>.+?)\s+bewilligt und als provisorischen "
    r"Sachwalter\s+(?P<commissioner>.+?)\s+eingesetzt\.\s*Mit Entscheid vom\s+"
    r"(?P<extension_date>\d{2}\.\d{2}\.\d{4})\s+ist der Gesellschaft die "
    r"provisorische Nachlassstundung bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert worden\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_AUDITOR_REMOVED = re.compile(
    r"^(?P<name>.+?)\s+\((?P<registry_id>CH-[\d.-]+-\d)\)\s+"
    r"ist nicht mehr Revisionsstelle\.?",
    re.I | re.UNICODE,
)
_DE_MANAGERS_AUDIT_WAIVER = re.compile(
    r"Gemäss Erklärung der Geschäftsführer vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_DE_OFFICIAL_DELETION_NO_OBJECTION = re.compile(
    r"^Nachdem kein begründeter Einspruch gegen die Löschung erhoben wurde,\s*"
    r"wird die Gesellschaft im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*159 Abs\.\s*5 lit\.\s*a\.\s*HRegV)\s+"
    r"von Amtes wegen gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+composant le capital-actions de CHF\s+"
    r"(?P<total>[\d'.]+)\s+ne sont désormais plus restreintes quant à leur "
    r"transmissibilité\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENCY_CHANGED_PAIR = re.compile(
    r"^(?P<new_president>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<old_president>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer\s+"
    r"(?P<sign>collectivement à deux|individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS = re.compile(
    r"^Nouveaux membres du conseil de fondation:\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>présidente?)\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*tous deux sans signature\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_IDENTIFIER_DI = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<seat>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*Numero di identificazione della sede principale:\s*"
    r"(?P<from>CH-[\d.]+-\d)\]\.?$",
    re.I | re.UNICODE,
)
_DE_MIXED_PERSON_CHANGES = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>[^,.;]+),\s*(?P<removed_sign>[^.;]+)\.\s*"
    r"Eingetragene Person geändert:\s*(?P<changed>[^,.;]+),\s*"
    r"(?P<changed_old_role>[^,.;]+),\s*(?P<changed_old_sign>[^,.;]+),\s*"
    r"neu\s+(?P<changed_role>[^,.;]+),\s*(?P<changed_sign>[^.;]+)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von und in\s+"
    r"(?P<added_place>[^,.;]+),\s*(?P<added_role>[^,.;]+),\s*"
    r"(?P<added_sign>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_LIQUIDATORS_TYPO = re.compile(
    r"^Liq(?:au)?idateurs:\s*les associés gérants\s+"
    r"(?P<name1>.+?)\s+et\s+(?P<name2>.+?),\s*lesquels continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement à deux)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_NAME_CORRECTED = re.compile(
    r"^Berichtigung des Eintrages Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\(SHAB vom\s+(?P<publication_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Id\s+(?P<publication_ref>\d+)\):\s*Firma korrekt:\s*"
    r"(?P<name>.+?)\s+\(und nicht\s+(?P<previous>.+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_SPACED_UID = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s+\)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_SUSPENDED_CONTINUES = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung "
    r"betreffend Konkurs im Handelsregister gestrichen und das Unternehmen "
    r"besteht gemäss dem bisherigen Eintrag weiter\.\s*"
    r"\[bisher:\s*Über den Inhaber dieses Einzelunternehmens wurde mit Entscheid "
    r"des\s+(?P<bankruptcy_court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_CAPITAL_BAND = re.compile(
    r"^Kapitalband gemäss näherer Umschreibung in den Statuten\.?$",
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


def extract_parser63_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 63."""
    del language  # Some historical publications contain another language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CIVIL_NAME_NOW.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.civil_name.v5", match.group("name"),
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "reason": "civil_status_change",
                },
            )
        )

    match = _FR_COMPANY_IDENTIFIER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "fr.text.company_identifier.v1",
                {"scope": "organization", "from": match.group("from"), "to": match.group("to")},
            )
        )

    match = _IT_DISSOLUTION_BY_ASSEMBLY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.dissolution_by_assembly.v1",
                {"kind": "dissolution", "date": _iso_date(match.group("date")), "authority": "general_assembly"},
            )
        )

    match = _DE_PROVISIONAL_MORATORIUM_GRANTED_AND_EXTENDED.search(leftover)
    if match:
        consume(match)
        common = {
            "moratorium_type": "provisional",
            "authority": match.group("authority").strip(),
        }
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", "de.text.provisional_moratorium_granted.v1",
                    {
                        "kind": "composition_moratorium_granted",
                        **common,
                        "decision_date": _iso_date(match.group("grant_date")),
                        "duration": match.group("duration").strip(),
                        "commissioner": match.group("commissioner").strip(),
                        "commissioner_status": "provisional",
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", "de.text.provisional_moratorium_extended.v1",
                    {
                        "kind": "composition_moratorium_extended",
                        **common,
                        "decision_date": _iso_date(match.group("extension_date")),
                        "until": _iso_date(match.group("until")),
                    },
                ),
            ]
        )

    match = _DE_LEGACY_AUDITOR_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", "de.persons.legacy_auditor_removed.v1",
                match.group("name"), role="Revisionsstelle",
                extra={"action": "removed", "registry_id": match.group("registry_id")},
            )
        )

    match = _DE_MANAGERS_AUDIT_WAIVER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.managers_audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _iso_date(match.group("date")),
                    "declarants": "managers",
                },
            )
        )

    match = _DE_OFFICIAL_DELETION_NO_OBJECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "de.text.official_deletion_no_objection.v1",
                {
                    "reason": "official_deletion",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "reasoned_objection_received": False,
                },
            )
        )

    match = _FR_SHARE_TRANSFER_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_transfer_restriction_removed.v2",
                {
                    "kind": "share_transfer_restricted",
                    "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "capital_total": match.group("total"),
                },
            )
        )

    match = _FR_PRESIDENCY_CHANGED_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.presidency_changed_pair.v1",
                    match.group("new_president"), role="président", signing=signing,
                    extra={"action": "role_changed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.presidency_changed_pair.v1",
                    match.group("old_president"), role="membre", signing=signing,
                    extra={"action": "role_changed", "previous_role": "président"},
                ),
            ]
        )

    match = _FR_FOUNDATION_MEMBERS.search(leftover)
    if match:
        consume(match)
        for index in range(1, 4):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
            }
            if index > 1:
                extra["without_signature"] = True
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_group.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role=(match.group("role1") if index == 1 else "membre du conseil de fondation"),
                    extra=extra,
                )
            )

    match = _IT_HEAD_OFFICE_IDENTIFIER_DI.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "it.text.head_office_identifier.v3",
                {
                    "scope": "head_office",
                    "head_office_seat": match.group("seat").strip(),
                    "from": match.group("from"),
                    "to": match.group("to"),
                },
            )
        )

    match = _DE_MIXED_PERSON_CHANGES.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", "de.persons.mixed_singular_changes.v1",
                    match.group("removed"), role=match.group("removed_role").strip(),
                    signing=_signing(match.group("removed_sign")), extra={"action": "removed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "de.persons.mixed_singular_changes.v1",
                    match.group("changed"), role=match.group("changed_role").strip(),
                    signing=_signing(match.group("changed_sign")),
                    extra={
                        "action": "modified",
                        "previous_role": match.group("changed_old_role").strip(),
                        "previous_signing": _signing(match.group("changed_old_sign")),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "de.persons.mixed_singular_changes.v1",
                    match.group("added"), place=match.group("added_place"),
                    role=match.group("added_role").strip(), signing=_signing(match.group("added_sign")),
                    extra={"action": "appointed", "heimat": match.group("added_place").strip()},
                ),
            ]
        )

    match = _FR_ASSOCIATE_LIQUIDATORS_TYPO.search(leftover)
    if match:
        consume(match)
        for name_group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_liquidators.v1",
                    match.group(name_group), role="associé-gérant et liquidateur",
                    signing=_signing(match.group("sign")),
                    extra={"action": "role_changed", "signing_continues": True},
                )
            )

    match = _DE_COMPANY_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "de.text.company_name_corrected.v1",
                {
                    "action": "corrected",
                    "from": match.group("previous").strip(),
                    "to": match.group("name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "publication_date": _iso_date(match.group("publication_date")),
                    "publication_reference": match.group("publication_ref"),
                },
            )
        )

    match = _DE_BRANCH_ADDED_SPACED_UID.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.branch_added_spaced_uid.v1",
                {"action": "added", "place": match.group("place").strip(), "branch_uid": match.group("uid")},
            )
        )

    match = _DE_OWNER_BANKRUPTCY_SUSPENDED_CONTINUES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.owner_bankruptcy_effect_suspended.v3",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("time").replace(".", ":"),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "bankruptcy_registration_removed": True,
                    "business_continues": True,
                },
            )
        )

    match = _DE_CAPITAL_BAND.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.capital_band.v1",
                {"kind": "capital_band", "action": "introduced", "basis": "statutes"},
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
