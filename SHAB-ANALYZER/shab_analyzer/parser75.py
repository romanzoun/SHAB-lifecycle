from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CAPITAL_CORRECTION = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\):\s*"
    r"Capital social:\s*(?P<currency>[A-Z]{3})\s+(?P<to>[\d'.]+)\s+"
    r"\(et non pas\s+(?P=currency)\s+(?P<from>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_SHORT = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que\s+"
    r"(?P<name>.+?) est domicilié(?:e)? à\s+(?P<place>[^()]+?)\s+"
    r"\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED = re.compile(
    r"^\[gestrichen:\s*(?P<place>[^\]()]+?)\s+"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_REMAINS_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>\d+)/(?P<notice_id>\d+)\) est rectifiée en ce sens que\s+"
    r"(?P<name>.+?) reste à\s+(?P<place>[^()]+?)\s+"
    r"\(et non à\s+(?P<previous_place>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_BUSINESS_ADDRESS_REMOVED = re.compile(
    r"^\[gestrichen:\s*Weitere Geschäftsadresse:\s*"
    r"(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+(?P<town>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_SUPPRESSION_DELETION_BLOCKED = re.compile(
    r"^,?\s*Sede principale:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuove disposizioni per la succursale:\s*La succursale deve essere "
    r"cancellata a seguito di soppressione\.\s*La cancellazione non può tuttavia "
    r"essere effettuata mancando il consenso delle autorità fiscali federali e "
    r"cantonali\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS = re.compile(
    r"^Liquidationsadresse:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<town>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_OWNER_BANKRUPTCY = re.compile(
    r"^\[gestrichen:\s*Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}) ist über den Inhaber dieses "
    r"Einzelunternehmens mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2}) Uhr, der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_AND_MANAGERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>.+?) a cédé\s+"
    r"(?P<transferred>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+) à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Gérants:\s*les associés\s+(?P=seller),\s*président,\s*et\s+"
    r"(?P=buyer),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_IT_ASSET_TRANSFER = re.compile(
    r"^Trasferimento di patrimonio:\s*secondo contratto del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}) la società ha trasferito alla\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*attivi per CHF\s+"
    r"(?P<assets>[\d'.]+) e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Contro prestazione:\s*"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FUNDS_CHANGED = re.compile(
    r"^Mittel neu:\s*(?P<funds>.+?)\.?$",
    re.I | re.UNICODE,
)
_MIXED_DE_PERSON_SECTIONS = re.compile(
    r"^Gelöschte Personen:\s*(?P<removed1>[^,.;]+),\s*"
    r"(?P<removed1_role>[^,.;]+),\s*"
    r"(?P<removed1_sign>Kollektivunterschrift(?:\s+zu\s+zweien)?|Einzelunterschrift)\.\s*"
    r"(?P<removed2>[^,.;]+),\s*"
    r"(?P<removed2_sign>Kollektivunterschrift(?:\s+zu\s+zweien)?|Einzelunterschrift)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<added_sign>Kollektivunterschrift(?:\s+zu\s+zweien)?|Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVALS_REMAINDER = re.compile(
    r"^(?:Zweigniederlassung neu:\s*)?"
    r"(?:\[Folgende Zweigniederlassungen sind aufgehoben worden:\]\s*)?"
    r"(?:\]\s*\.\s*)?"
    r"(?P<branches>(?:\[gestrichen:\s*[^()\]]+?\s*"
    r"\(CHE-\d{3}\.\d{3}\.\d{3}\),?\s*\(HR\s+[A-Z]{2}\)\]\.?\s*)+)$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVAL_ITEM = re.compile(
    r"\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),?\s*"
    r"\(HR\s+(?P<register_canton>[A-Z]{2})\)\]\.?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_PART_TRANSFER_WITHOUT_SIGNATURE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>.+?) cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé sans signature\.\s*"
    r"L['’]associé-gérant\s+(?P=seller) reste titulaire de\s+"
    r"(?P<remaining>[\d']+) parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*(?P<role1>secrétaire),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*sont membres du conseil de fondation,\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_ARTICLE_AND_SHARE_TRANSFORMATION = re.compile(
    r"^Raison sociale:\s*(?P<name>.+?)\.\s*Radiation de la mention relative à "
    r"l['’](?P<article>art\.\s*176 ORC)\.\s*Transformation des\s+"
    r"(?P<from_count>[\d']+) actions de CHF\s+(?P<from_nominal>[\d'.]+),\s*"
    r"jusqu['’]ici au porteur,\s*en\s+(?P<to_count>[\d']+) actions de CHF\s+"
    r"(?P<to_nominal>[\d'.]+),\s*nominatives\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<capital_count>[\d']+) actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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


def extract_parser75_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 75."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CAPITAL_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.capital_correction.v1",
                {
                    "action": "corrected",
                    "currency": match.group("currency").upper(),
                    "from": match.group("from"),
                    "to": match.group("to"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_DOMICILE_CORRECTION_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.domicile_correction_pas.v1",
                match.group("name"), place=match.group("place"),
                extra={
                    "action": "domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_LEGACY_BRANCH_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.legacy_branch_removed.v1",
                {
                    "action": "removed",
                    "place": match.group("place").strip(),
                    "branch_registry_id": match.group("registry_id"),
                },
            )
        )

    match = _FR_DOMICILE_REMAINS_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.domicile_remains_corrected.v1",
                match.group("name"), place=match.group("place"),
                extra={
                    "action": "domicile_corrected",
                    "remains_at_place": True,
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_ADDITIONAL_BUSINESS_ADDRESS_REMOVED.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()}, {match.group('postal_code')} "
            f"{match.group('town').strip()}"
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.additional_business_address_removed.v1",
                {
                    "action": "removed",
                    "kind": "additional_business_address",
                    "address": address,
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                },
            )
        )

    match = _IT_BRANCH_SUPPRESSION_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.branch_suppression_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "scope": "branch",
                    "reason": "branch_suppressed",
                    "head_office": match.group("head_office").strip(),
                    "tax_authority": "federal_and_cantonal",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _DE_LIQUIDATION_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.liquidation_address.v1",
                {
                    "kind": "liquidation_address",
                    "to": (
                        f"{match.group('address').strip()}, "
                        f"{match.group('postal_code')} {match.group('town').strip()}"
                    ),
                    "postal_code": match.group("postal_code"),
                    "town": match.group("town").strip(),
                },
            )
        )

    match = _DE_REMOVED_OWNER_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.removed_owner_bankruptcy.v1",
                {
                    "kind": "bankruptcy_opening",
                    "action": "removed",
                    "scope": "owner",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_at": (
                        f"{_iso_date(match.group('effective_date'))}T"
                        f"{match.group('effective_time').replace('.', ':')}"
                    ),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_AND_MANAGERS.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_transfer_and_managers.v2"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant président",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_nominal": match.group("nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée-gérante",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _IT_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "it.text.asset_transfer.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                },
            )
        )

    match = _DE_FUNDS_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "de.text.funds_changed.v1",
                {
                    "kind": "funding",
                    "action": "changed",
                    "to": match.group("funds").strip(),
                },
            )
        )

    match = _MIXED_DE_PERSON_SECTIONS.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.mixed_sections_period_separated.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed1"),
                    role=match.group("removed1_role").strip(),
                    signing=match.group("removed1_sign").strip(),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed2"),
                    signing=match.group("removed2_sign").strip(),
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("added"),
                    place=match.group("place"),
                    signing=match.group("added_sign").strip(),
                    extra={"heimat": match.group("origin").strip()},
                ),
            ]
        )

    match = _DE_BRANCH_REMOVALS_REMAINDER.search(leftover)
    if match:
        branch_matches = list(_DE_BRANCH_REMOVAL_ITEM.finditer(match.group("branches")))
        if branch_matches:
            consume(match)
            for branch in branch_matches:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "branch_changed", "de.text.branch_removal_remainder.v1",
                        {
                            "action": "removed",
                            "place": branch.group("place").strip(),
                            "branch_uid": branch.group("uid"),
                            "register_canton": branch.group("register_canton").upper(),
                        },
                    )
                )

    match = _FR_ASSOCIATE_PART_TRANSFER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_part_transfer_without_signature.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("remaining")),
                        "shares_nominal": match.group("remaining_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": transferred,
                        "shares_nominal": match.group("nominal"),
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _FR_FOUNDATION_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_pair.v1"
        for index, role in ((1, "secrétaire"), (2, "membre du conseil de fondation")):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role=role,
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                    },
                )
            )

    match = _FR_NAME_ARTICLE_AND_SHARE_TRANSFORMATION.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", "fr.text.company_name_confirmed.v1",
                    {
                        "kind": "company_name_confirmation",
                        "name": match.group("name").strip(),
                        "changed": False,
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "fr.text.article_176_mention_removed.v1",
                    {
                        "kind": "legal_mention",
                        "action": "removed",
                        "legal_basis": re.sub(r"\s+", " ", match.group("article")),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", "fr.text.bearer_share_split.v1",
                    {
                        "kind": "share_split_and_conversion",
                        "currency": "CHF",
                        "from_count": _count(match.group("from_count")),
                        "from_nominal": match.group("from_nominal"),
                        "from_kind": "au porteur",
                        "to_count": _count(match.group("to_count")),
                        "to_nominal": match.group("to_nominal"),
                        "to_kind": "nominatives",
                        "capital_total": match.group("total"),
                        "capital_count": _count(match.group("capital_count")),
                        "capital_nominal": match.group("capital_nominal"),
                        "paid_in_full": True,
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
