from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_REGISTERED_OFFICE_ADDRESS_MISSING = re.compile(
    r"^La société ne dispose plus d['’]adresse à son siège statutaire\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_AFTER_TRANSLATIONS = re.compile(
    r"^(?P<translations>(?:\([^()]+\)\s*)+)\.\s*"
    r"L['’]administrateur\s+(?P<name>[^,.;]+),\s*dont la signature est radiée,\s*"
    r"est nommé liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_REMAINS_CORRECTION_FRAGMENT = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la raison de "
    r"commerce reste\s+(?P<name>.+?)\s+\(et non\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_INDIVIDUAL_FRAGMENT = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*tous trois\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_SERIES = re.compile(
    r"^(?P<branches>(?:(?:St\.\s+)?[^.]+?\s*"
    r"\(CHE-\d{3}\.\d{3}\.\d{3}\)(?:\.\s*|$))+)$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ITEM = re.compile(
    r"(?P<place>(?:St\.\s+)?[^.]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)(?:\.\s*|$)",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+?)(?:\s*\((?P<country>[^)]+)\))?,\s*"
    r"nouvel associé sans signature\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_RESTRICTED_ADMINISTRATORS_FRAGMENT = re.compile(
    r"^Nouveaux administrateurs toutefois avec le/la président/e,\s*"
    r"le/la vice-président/e ou le directeur:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_COMPANY_DELETION_REVOKED = re.compile(
    r"^\[Die Löschung der Aktiengesellschaft unter der TR Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+erfolgte irrtümlich und wird "
    r"hiermit in allen Teilen widerrufen\.\]\.?\s*"
    r"\[gestrichen:\s*Löschungsdatum:\s*(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_FIRST_APPOINTED_PRESIDENT = re.compile(
    r"^Gérants:\s*(?P<president>[^,.;]+),\s*nommée présidente,\s*et\s*"
    r"(?P<manager>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_AUDIT_WAIVER = re.compile(
    r"^\[bisher:\s*Gemäss Erklärung der Gründerin vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_LEGAL_FORM_SUFFIX = re.compile(
    r"^(?P<legal_form>Sàrl)$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_BANKRUPTCY_OPENED = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+des\s+(?P<authority>.+?)\s+"
    r"wurde über den Hauptsitz der Konkurs eröffnet\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à la nouvelle associée\s+(?P<buyer>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s+est maintenant associé pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_LEGACY_IDENTIFIERS_AND_RELOCATION = re.compile(
    r"^\[bisher:\s*(?P<same_place>[^()]+?)\s*"
    r"\((?P<same_old_id>CH-[\d.-]+)\)\]\.?\s*"
    r"\[Sitz neu:\]\s*(?P<to_place>[^()]+?)\s*"
    r"\((?P<to_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<from_place>[^()]+?)\s*"
    r"\((?P<from_id>CH-[\d.-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_IT_ASSOCIATION_RESOURCES = re.compile(
    r"^Mezzi:\s*(?P<resources>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME_CORRECTION_WITH_FALSE_SIGNING = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que par suite de "
    r"changement d['’]état civil,\s*(?P<previous_name>[^()]+?)\s+porte désormais "
    r"le nom de\s+(?P<name>[^()]+?)\s*\(et non pas\s+"
    r"(?P<incorrect>signature collective à deux,\s*limitée aux affaires de la "
    r"succursale,\s*a été conférée à\s+[^)]+)\)\.?$",
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


def extract_parser136_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 136."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_REGISTERED_OFFICE_ADDRESS_MISSING.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.registered_office_address_missing.v1",
            {
                "kind": "registered_office_address", "action": "removed",
                "address_available": False, "scope": "statutory_seat",
            },
        ))

    match = _FR_LIQUIDATOR_AFTER_TRANSLATIONS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.liquidator_after_company_name_translations.v1"
        translations = re.findall(r"\(([^()]+)\)", match.group("translations"))
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id,
                {"action": "translations_recorded", "translations": translations},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="administrateur et liquidateur", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_liquidator", "previous_role": "administrateur",
                    "previous_signature_revoked": True,
                },
            ),
        ])

    match = _FR_COMPANY_NAME_REMAINS_CORRECTION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.company_name_remains_correction_fragment.v1",
            {
                "kind": "company_name", "action": "confirmed_unchanged",
                "name": match.group("name").strip(), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_THREE_MANAGERS_INDIVIDUAL_FRAGMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers_individual_fragment.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _DE_BRANCH_SERIES.search(leftover)
    if match:
        branches = list(_DE_BRANCH_ITEM.finditer(match.group("branches")))
        if branches:
            consume(match)
            rule_id = "de.text.branch_series_added.v1"
            for item in branches:
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", rule_id,
                    {
                        "action": "added", "place": item.group("place").strip(" ."),
                        "branch_uid": item.group("uid"),
                    },
                ))

    match = _FR_ASSOCIATE_TRANSFER_TO_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_to_unsigned_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", signing="ohne Zeichnungsberechtigung",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")),
                },
            ),
        ])

    match = _FR_TWO_RESTRICTED_ADMINISTRATORS_FRAGMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_restricted_administrators_fragment.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group(f"origin{index}").strip(),
                    "signing_restriction": "with president, vice-president, or director",
                },
            ))

    match = _DE_ERRONEOUS_COMPANY_DELETION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.erroneous_company_deletion_revoked_exact.v1",
            {
                "kind": "registration_reinstated", "action": "deletion_revoked",
                "reason": "erroneous_deletion", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "deletion_date": _iso_date(match.group("deletion_date")),
                "registry_reinstated": True,
            },
        ))

    match = _FR_TWO_MANAGERS_FIRST_APPOINTED_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_first_appointed_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="gérante présidente", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("place"), role="gérant", signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        ])

    match = _DE_PREVIOUS_AUDIT_WAIVER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.previous_audit_waiver_removed.v1",
            {
                "kind": "limited_audit_waiver", "action": "previous_entry_removed",
                "declaration_date": _iso_date(match.group("date")),
                "limited_audit_waived": False,
            },
        ))

    match = _FR_COMPANY_NAME_LEGAL_FORM_SUFFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_legal_form_suffix.v1",
            {
                "kind": "parsed_name_suffix", "action": "retained",
                "legal_form": match.group("legal_form"),
            },
        ))

    match = _DE_HEAD_OFFICE_BANKRUPTCY_OPENED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_bankruptcy_opened.v1",
            {
                "kind": "bankruptcy", "action": "opened", "scope": "head_office",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_TO_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                uid=match.group("uid"), role="associée",
                extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "uid": match.group("uid"), "shares_received": transferred,
                    "shares_count": transferred, "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_BRANCH_LEGACY_IDENTIFIERS_AND_RELOCATION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.branch_legacy_identifiers_and_relocation.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "identifier_replaced",
                    "place": match.group("same_place").strip(),
                    "previous_branch_id": match.group("same_old_id"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "seat_changed", "from": match.group("from_place").strip(),
                    "to": match.group("to_place").strip(),
                    "previous_branch_id": match.group("from_id"),
                    "branch_uid": match.group("to_uid"),
                },
            ),
        ])

    match = _IT_ASSOCIATION_RESOURCES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "it.text.association_resources.v1",
            {
                "kind": "association_resources", "action": "recorded",
                "resources": match.group("resources").strip(),
            },
        ))

    match = _FR_CIVIL_NAME_CORRECTION_WITH_FALSE_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.civil_name_correction_false_signing.v1",
            match.group("name"),
            extra={
                "action": "name_corrected", "previous_name": match.group("previous_name").strip(),
                "reason": "civil_status_change", "scope": "branch",
                "incorrect_statement": re.sub(r"\s+", " ", match.group("incorrect")),
                "signing_grant_applies": False, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
