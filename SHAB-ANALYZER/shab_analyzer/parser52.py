from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SUPERVISORY_AUDIT_WAIVER_REVOKED = re.compile(
    r"L['’]autorité de surveillance a révoqué la dispense d['’]organe de révision "
    r"octroyée à la [Ff]ondation par décision du (?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)
_DE_SOLE_PROPRIETOR_DELETION_REVOKED = re.compile(
    r"Die Löschung dieses Einzelunternehmens erfolgte irrtümlich und wird in allen "
    r"Teilen widerrufen\.\s*Das Einzelunternehmen besteht gemäss den früheren "
    r"Einträgen weiter\.\s*\[bisher:\s*(?P<previous>Das Einzelunternehmen wird "
    r"infolge Geschäftsüberganges gelöscht\.)\]\.?,?",
    re.I,
)
_FR_BEARER_CONVERSION_WITH_REPORTED_BEARER_CAPITAL = re.compile(
    r"Conversion des actions au porteur en actions nominatives\.\s*"
    r"Capital-actions:\s*(?P<currency>[A-Z]{3})\s+(?P<total>[\d'.]+),\s*"
    r"libéré à concurrence de [A-Z]{3}\s+(?P<paid>[\d'.]+),\s*divisé en\s*"
    r"(?P<count>[\d']+)\s+actions de [A-Z]{3}\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<reported_kind>au porteur)\.?,?",
    re.I,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATES = re.compile(
    r"L['’]assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation conditionnelle du capital\s*\(selon décision"
    r"(?: relative à l['’]octroi de droits de l['’]assemblée générale)? du "
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4})"
    r"(?:,\s*modifiée en dernier lieu le\s*(?P<last_date>\d{2}\.\d{2}\.\d{4}))?\)\s*"
    r"par décision du (?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?,?",
    re.I,
)
_DE_HEAD_OFFICE_REMARKS_HEADING = re.compile(
    r"Bemerkungen zum Hauptsitz neu:\s*", re.I
)
_DE_REMOVED_PERSON_IN_FOREIGN_LANGUAGE = re.compile(
    r"Gelöschte Person:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<sign>Kollektivprokura zu zweien)\.?,?",
    re.I,
)
_FR_LEGAL_BEARER_CONVERSION_SHARES_FIRST = re.compile(
    r"Actions:\s*(?P<to_count>[\d']+)\s+actions\s+(?P<to_kind>nominatives)\s+de "
    r"CHF\s+(?P<to_nominal>[\d'.]+)\s*\[précédemment:\s*"
    r"(?P<from_count>[\d']+)\s+actions\s+(?P<from_kind>au porteur)\s+de "
    r"CHF\s+(?P<from_nominal>[\d'.]+)\]\.\s*Le\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*les actions au porteur ont été converties "
    r"de par la loi en actions nominatives\.?,?",
    re.I,
)
_FR_ASSOCIATION_DISSOLUTION = re.compile(
    r"Selon décision de son assemblée générale du (?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]association a prononcé sa dissolution\.?,?",
    re.I,
)
_FR_ASSOCIATION_LIQUIDATORS = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*maintenant à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+)\s+sont nommés liquidateurs\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_ASSET_TRANSFER = re.compile(
    r"Transfert de patrimoine:\s*selon contrat du\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*l['’]association a transféré des actifs "
    r"pour CHF\s*(?P<assets>[\d'.]+) et des passifs envers les tiers pour CHF\s*"
    r"(?P<liabilities>[\d'.]+) à\s*(?P<recipient>.+?),\s*à\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>[^.]+)\.?,?",
    re.I | re.DOTALL,
)
_IT_LEGAL_BEARER_PARTICIPATION_CONVERSION = re.compile(
    r"Nuovi buoni di partecipazione:\s*(?P<to_count>[\d']+)\s+buoni di "
    r"partecipazione\s+(?P<to_kind>nominativi)\s+da CHF\s*"
    r"(?P<to_nominal>[\d'.]+)\s*\[finora:\s*(?P<from_count>[\d']+)\s+buoni "
    r"di partecipazione\s+(?P<from_kind>al portatore)\s+da CHF\s*"
    r"(?P<from_nominal>[\d'.]+)\]\.\s*Il\s+(?P<date>\d{1,2}\.\s*"
    r"(?:gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|"
    r"ottobre|novembre|dicembre)\s+\d{4})\s+i buoni di partecipazione al portatore "
    r"sono stati convertiti per legge in buoni di partecipazione nominativi\.\s*"
    r"Gli statuti della società non sono ancora stati adeguati;\s*l['’]adeguamento "
    r"deve avvenire in occasione della prossima modifica statutaria\.?,?",
    re.I,
)
_FR_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des)\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,(.;]+)(?:\s*\((?P<country1>[^)]+)\))?,\s*"
    r"sans signature,\s*et\s*(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*"
    r"(?:du|de la|des)\s+(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,(.;]+)(?:\s*\((?P<country2>[^)]+)\))?,\s*"
    r"sans signature,\s*sont membres? du conseil d['’]administration\.?,?",
    re.I | re.UNICODE,
)
_FR_THREE_MEMBER_ADMINISTRATION = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommée\s+(?P<role1>présidente),\s*"
    r"laquelle continue à signer\s+(?P<sign1>individuellement),\s*"
    r"(?P<name2>[^,.;]+),\s*d['’](?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+),\s*(?P<role2>vice-présidente)\s+et\s*"
    r"(?P<name3>[^,.;]+),\s*d['’](?P<origin3>[^,.;]+),\s*à\s*"
    r"(?P<place3>[^,.;]+),\s*(?P<role3>secrétaire),\s*"
    r"toutes deux avec\s+(?P<sign23>signature collective à deux)\.?,?",
    re.I | re.UNICODE,
)
_FR_AUTOMATIC_BEARER_CONVERSION_CORRECTED = re.compile(
    r"La conversion d['’]office a eu lieu à tort,\s*la société ayant converti ses "
    r"actions au porteur en actions nominatives par décision de l['’]assemblée générale "
    r"du (?P<date>\d{2}\.\d{2}\.\d{4})\.?,?",
    re.I,
)


_FR_MONTHS = {
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
_IT_MONTHS = {
    "gennaio": 1,
    "febbraio": 2,
    "marzo": 3,
    "aprile": 4,
    "maggio": 5,
    "giugno": 6,
    "luglio": 7,
    "agosto": 8,
    "settembre": 9,
    "ottobre": 10,
    "novembre": 11,
    "dicembre": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _written_date(raw: str, months: dict[str, int]) -> str:
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().lower()).split()
    return f"{int(year):04d}-{months[month]:02d}-{int(day.rstrip('.')):02d}"


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


def extract_parser52_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 52."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SUPERVISORY_AUDIT_WAIVER_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed",
                "fr.text.supervisory_audit_waiver_revoked.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "revoked",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": "supervisory_authority",
                },
            )
        )

    match = _DE_SOLE_PROPRIETOR_DELETION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.sole_proprietor_reinstated.v2",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_deletion",
                    "business_continues": True,
                    "removed_fact": match.group("previous").strip(),
                },
            )
        )

    match = _FR_BEARER_CONVERSION_WITH_REPORTED_BEARER_CAPITAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.bearer_conversion_reported_capital.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "currency": match.group("currency").upper(),
                    "capital_total": match.group("total"),
                    "paid": match.group("paid"),
                    "shares_count": _count(match.group("count")),
                    "nominal": match.group("nominal"),
                    "from_kind": match.group("reported_kind").lower(),
                    "to_kind": "nominatives",
                },
            )
        )

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATES.search(leftover)
    if match:
        consume(match)
        payload = {
            "kind": "conditional_capital_clause_modified",
            "action": "modified",
            "original_decision_date": _iso_date(match.group("original_date")),
            "decision_date": _iso_date(match.group("date")),
        }
        if match.group("last_date"):
            payload["last_modified_date"] = _iso_date(match.group("last_date"))
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.conditional_capital_clause.v3", payload,
            )
        )

    match = _DE_HEAD_OFFICE_REMARKS_HEADING.fullmatch(leftover.strip(" .;"))
    if match:
        leftover = ""
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "de.text.head_office_remarks_heading.v1",
                {"scope": "head_office", "kind": "remarks_section"},
            )
        )

    match = _DE_REMOVED_PERSON_IN_FOREIGN_LANGUAGE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", "de.persons.removed_person_foreign_language.v1",
                match.group("name"), signing=match.group("sign"),
                extra={"language_override": "de"},
            )
        )

    match = _FR_LEGAL_BEARER_CONVERSION_SHARES_FIRST.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion.v7",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _written_date(match.group("date"), _FR_MONTHS),
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "from_kind": match.group("from_kind").lower(),
                    "to_count": _count(match.group("to_count")),
                    "to_nominal": match.group("to_nominal"),
                    "to_kind": match.group("to_kind").lower(),
                },
            )
        )

    match = _FR_ASSOCIATION_DISSOLUTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.association_dissolution.v1",
                {"kind": "dissolution", "date": _iso_date(match.group("date"))},
            )
        )

    match = _FR_ASSOCIATION_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        for name, place in (
            (match.group("name1"), match.group("place1")),
            (match.group("name2"), None),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.association_liquidators.v1",
                    name, place=place, role="liquidateur",
                )
            )

    match = _FR_ASSOCIATION_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.association_asset_transfer.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip(),
                },
            )
        )

    match = _IT_LEGAL_BEARER_PARTICIPATION_CONVERSION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "it.text.legal_bearer_participation_conversion.v1",
                {
                    "kind": "bearer_to_registered_conversion",
                    "instrument": "participation_certificates",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": _written_date(match.group("date"), _IT_MONTHS),
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "from_kind": match.group("from_kind").lower(),
                    "to_count": _count(match.group("to_count")),
                    "to_nominal": match.group("to_nominal"),
                    "to_kind": match.group("to_kind").lower(),
                    "statutes_adapted": False,
                },
            )
        )

    match = _FR_BOARD_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_without_signature.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    extra={
                        "heimat": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                        "without_signature": True,
                    },
                )
            )

    match = _FR_THREE_MEMBER_ADMINISTRATION.search(leftover)
    if match:
        consume(match)
        people = (
            (match.group("name1"), None, match.group("role1"), "Einzelunterschrift", {}),
            (
                match.group("name2"), match.group("place2"), match.group("role2"),
                "Kollektivunterschrift zu zweien", {"heimat": match.group("origin2")},
            ),
            (
                match.group("name3"), match.group("place3"), match.group("role3"),
                "Kollektivunterschrift zu zweien", {"heimat": match.group("origin3")},
            ),
        )
        for name, place, role, signing, extra in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.three_member_administration.v1",
                    name, place=place, role=role, signing=signing, extra=extra,
                )
            )

    match = _FR_AUTOMATIC_BEARER_CONVERSION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_corrected.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "action": "corrected",
                    "actual_basis": "shareholders_resolution",
                    "decision_date": _iso_date(match.group("date")),
                    "automatic_conversion_removed": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
