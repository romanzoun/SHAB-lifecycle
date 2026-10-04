from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_MANAGER_PRESIDENT_SPLIT_TRANSFER = re.compile(
    r"^L['’]associé-gérant et président\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*par\s+(?P<buyer1_count>[\d']+)\s+part(?:s)? à\s+"
    r"(?P<buyer1>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et par\s+(?P<buyer2_count>[\d']+)\s+part(?:s)? à\s+"
    r"(?P<buyer2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;()]+?)(?:\s*\((?P<country2>[^)]+)\))?,\s*"
    r"nouveaux associés sans signature\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_RESTRICTED_PROXY_PAIR = re.compile(
    r"^Procuration collective à deux toutefois pas entre eux ni avec\s+"
    r"(?P<excluded>.+?),\s*est conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;()]+?)(?:\s*\((?P<canton2>[A-Z]{2})\))?$",
    re.I | re.UNICODE,
)
_DE_PERSON_NAME_CORRECTION_NOTICE = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+) vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\):\s*"
    r"Eingetragene Person:\s*(?P<surname>[^()]+?)\s*"
    r"\(und nicht:\s*(?P<previous_surname>[^)]+)\)\s*(?P<given_name>[^,.;]+),\s*"
    r"(?P<roles>.+?),\s*(?P<signing>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?)$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_PAIR_AFTER_SIGNING = re.compile(
    r"^Nouveaux membres du conseil de fondation\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*"
    r"(?:à|aux)\s+(?P<place1>[^,.;()]+?)(?:\s*\((?P<country1>[^)]+)\))?,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+)$",
    re.I | re.UNICODE,
)
_DE_BRANCH_IDENTIFIERS_WITH_HISTORY = re.compile(
    r"^\[bisher:\s*(?P<place1>[^()\]]+)\s*\((?P<old_id1>CH-[\d.-]+)\)\]\.?\s*"
    r"(?P<place2>[^()\[]+)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P=place2)\s*\((?P<old_id2>CH-[\d.-]+)\)\]$",
    re.I | re.UNICODE,
)
_FR_PROMOTED_SIGNING_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux a été conférée à\s+(?P<name>.+?),\s*"
    r"nommée\s+(?P<role>[^;]+);\s*sa procuration est radiée$",
    re.I | re.UNICODE,
)
_FR_ADMIN_DOMICILE_CORRECTION_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que "
    r"l['’]administrateur\s+(?P<name>[^,.;]+)\s+est à\s+(?P<place>.+?)\s+"
    r"\((?:et non à\s+)(?P<previous_place>.+?)\s+comme publié\)$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_APPOINTED_INDIVIDUAL = re.compile(
    r"^(?P<name>[^,.;]+),\s*nommé(?:e)?\s+(?P<role>[^,.;]+),\s*"
    r"signe désormais individuellement$",
    re.I | re.UNICODE,
)
_FR_UNLIMITED_PARTNER_ADMIN_PAIR_AFTER_SIGNING = re.compile(
    r"^Nouveaux associés indéfiniment responsables et membres de l['’]administration:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:de\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"tous deux$",
    re.I | re.UNICODE,
)
_FR_BRANCH_TRANSFERRED_SEAT_SUFFIX = re.compile(
    r"^suite à son transfert de siège à\s+(?P<place>.+)$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_AFTER_SIGNING = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:de\s+|d['’])(?P<origin>[^,.;]+),\s*"
    r"(?:à|au|aux)\s+(?P<place>[^,.;]+),\s*(?P<country_code>[A-Z]{2,3}),\s*"
    r"est membre du conseil d['’]administration$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_QUOTA_CAPITAL_CHANGED = re.compile(
    r"^Sede principale a:\s*Sede principale:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuovo capitale sociale/responsabilità della sede principale:\s*"
    r"(?P<currency>[A-Z]{3})\s+(?P<to_total>[\d'.]+)\s+diviso in\s+"
    r"(?P<to_count>[\d']+)\s+quote da\s+(?P=currency)\s+(?P<to_nominal>[\d'.]+)\s+"
    r"interamente liberato\.\s*\[finora:\s*Capitale sociale della sede principale:\s*"
    r"(?P=currency)\s+(?P<from_total>[\d'.]+)\s+diviso in\s+"
    r"(?P<from_count>[\d']+)\s+quote da\s+(?P=currency)\s+(?P<from_nominal>[\d'.]+)\s+"
    r"interamente liberato\]$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER = re.compile(
    r'^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+'
    r'(?P<date>\d{2}\.\d{2}\.\d{4})\s+den Geschäftsbereich\s+"(?P<business_unit>[^"]+)"\s+'
    r"mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+"
    r"von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*Forderung in Höhe von CHF\s+(?P<consideration>[\d'.]+)$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_EXISTING_ASSOCIATE = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé\s+(?P<buyer>[^,.;]+),\s*"
    r"désormais titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s*\((?P=seller_uid)\)\s+"
    r"a maintenant\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)$",
    re.I | re.UNICODE,
)
_DE_COMPLETE_ADDRESS_BRANCH_REGISTRATION = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^.]+)\.\s*"
    r"Eintragung der Zweigniederlassung von\s+(?P<branch_place>[^()]+?)\s*"
    r"\((?P<branch_uid>CHE-\d{3}\.\d{3}\.\d{3})\) im Handelsregister des Kantons\s+"
    r"(?P<register_canton>.+?)\s+am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\(SHAB vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)$",
    re.I | re.UNICODE,
)
_FR_ORPHAN_FOSC_REFERENCE_TAIL = re.compile(
    r"^(?P<month>\d{2})\.(?P<year>\d{4}),\s*p\.\s*"
    r"(?P<page>\d+)/(?P<notice_id>\d+)\)$",
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
    uid: str | None = None,
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


def _split_french_names(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r",\s*(?:et\s+)?|\s+et\s+", raw) if part.strip()]


def extract_parser122_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 122."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_MANAGER_PRESIDENT_SPLIT_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_president_split_transfer_two_new_associates.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"),
            role="associé-gérant et président",
            extra={
                **common, "action": "shares_transferred",
                "previous_shares_count": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
            },
        ))
        for index in (1, 2):
            extra = {
                **common, "action": "appointed", "without_signature": True,
                "heimat": match.group(f"origin{index}").strip(),
                "shares_received": _count(match.group(f"buyer{index}_count")),
                "shares_count": _count(match.group(f"buyer{index}_count")),
            }
            if index == 2 and match.group("country2"):
                extra["country"] = match.group("country2").strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé",
                signing="ohne Zeichnungsberechtigung", extra=extra,
            ))

    match = _FR_RESTRICTED_PROXY_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.restricted_collective_proxy_pair.v1"
        excluded = _split_french_names(match.group("excluded"))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivprokura zu zweien",
                extra={
                    "action": "proxy_granted", "heimat": match.group(f"origin{index}").strip(),
                    "not_with_each_other": True, "excluded_with": excluded,
                    **({"place_canton": match.group("canton2")} if index == 2 else {}),
                },
            ))

    match = _DE_PERSON_NAME_CORRECTION_NOTICE.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname').strip()} {match.group('given_name').strip()}"
        previous_name = f"{match.group('previous_surname').strip()} {match.group('given_name').strip()}"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.name_corrected_notice.v1", name,
            role=match.group("roles").strip(), signing=match.group("signing"),
            extra={
                "action": "name_corrected", "previous_name": previous_name,
                "entry_number": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_FOUNDATION_MEMBER_PAIR_AFTER_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_member_pair_collective_suffix_consumed.v1"
        for index in (1, 2):
            extra = {"action": "appointed", "heimat": match.group(f"origin{index}").strip()}
            country = match.group(f"country{index}") if index == 1 else None
            if country:
                extra["country"] = country.strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _DE_BRANCH_IDENTIFIERS_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.branch_identifiers_with_history.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "previous_identifier_recorded",
                    "place": match.group("place1").strip(),
                    "previous_branch_id": match.group("old_id1"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "identifier_replaced", "place": match.group("place2").strip(),
                    "branch_uid": match.group("uid2"),
                    "previous_branch_id": match.group("old_id2"),
                },
            ),
        ])

    match = _FR_PROMOTED_SIGNING_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.promoted_collective_signing_proxy_revoked.v1",
            match.group("name"), role=match.group("role").strip(),
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_and_signing_changed", "previous_proxy_revoked": True},
        ))

    match = _FR_ADMIN_DOMICILE_CORRECTION_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_domicile_corrected_notice.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            extra={
                "action": "domicile_corrected", "previous_place": match.group("previous_place").strip(),
                "entry_number": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("page"), "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_DIRECTOR_APPOINTED_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_appointed_individual_signing.v1",
            match.group("name"), role=match.group("role").strip(),
            signing="Einzelunterschrift", extra={"action": "appointed_and_signing_changed"},
        ))

    match = _FR_UNLIMITED_PARTNER_ADMIN_PAIR_AFTER_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.unlimited_partner_admin_pair_collective_suffix_consumed.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="associé indéfiniment responsable et membre de l'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group(f"origin{index}").strip()},
            ))

    match = _FR_BRANCH_TRANSFERRED_SEAT_SUFFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_removed_after_seat_transfer.v1",
            {"action": "seat_transferred_and_branch_removed", "to": match.group("place").strip()},
        ))

    match = _FR_BOARD_MEMBER_AFTER_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_collective_suffix_consumed.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration", signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "country_code": match.group("country_code").upper(),
            },
        ))

    match = _IT_HEAD_OFFICE_QUOTA_CAPITAL_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "it.text.head_office_quota_capital_changed.v1",
            {
                "scope": "head_office", "head_office": match.group("head_office").strip(),
                "currency": match.group("currency").upper(),
                "from_total": match.group("from_total"), "to_total": match.group("to_total"),
                "from_count": _count(match.group("from_count")),
                "to_count": _count(match.group("to_count")),
                "from_nominal": match.group("from_nominal"),
                "to_nominal": match.group("to_nominal"), "paid_in_full": True,
            },
        ))

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_asset_transfer_receivable.v1",
            {
                "date": _iso_date(match.group("date")),
                "business_unit": match.group("business_unit").strip(),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(), "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": {"kind": "receivable", "amount": match.group("consideration")},
                "currency": "CHF",
            },
        ))

    match = _FR_ORGANIZATION_TRANSFER_EXISTING_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_transfer_existing_associate_holdings.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                uid=match.group("seller_uid"), role="associée",
                extra={
                    **common, "action": "shares_transferred", "uid": match.group("seller_uid"),
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"), role="associé",
                extra={
                    **common, "action": "shares_received",
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])

    match = _DE_COMPLETE_ADDRESS_BRANCH_REGISTRATION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.complete_address_and_branch_registration.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "street": match.group("street").strip(), "house_number": match.group("house"),
                    "postal_code": match.group("postal_code"), "town": match.group("town").strip(),
                    "complete": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "registered", "place": match.group("branch_place").strip(),
                    "branch_uid": match.group("branch_uid"),
                    "register_canton": match.group("register_canton").strip(),
                    "registration_date": _iso_date(match.group("date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            ),
        ])

    match = _FR_ORPHAN_FOSC_REFERENCE_TAIL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.orphan_fosc_reference_tail.v1",
            {
                "kind": "prior_publication_reference",
                "notice_month": int(match.group("month")),
                "notice_year": int(match.group("year")),
                "notice_page": match.group("page"), "notice_id": match.group("notice_id"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
