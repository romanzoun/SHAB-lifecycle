from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_ERRONEOUS_DELETION_CONSENT_REMARK = re.compile(
    r"^Bemerkungen neu:\s*Die Löschung der Gesellschaft wurde fälschlicherweise "
    r"aufgrund einer irrtümlichen Löschungszustimmung der eidgenössischen "
    r"Steuerverwaltung eingetragen\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_INTRODUCED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ein bedingtes Kapital gemäss "
    r"näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"est membre du comité;\s*n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_NEW_WITHOUT_SIGNATURE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*lequel associé n['’]exerce pas la "
    r"signature sociale\.\s*Par conséquent,\s*(?P=seller)\s+est désormais "
    r"titulaire de\s+(?P<seller_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NAME_CORRECTION_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n[°o]\s*)?(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que l['’]"
    r"as+ocié détenant\s+(?P<shares>[\d']+)\s+parts? de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+est\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_THREE_NAMES = re.compile(
    r"^Signature collective à deux est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>vice-président),\s*et\s+(?P<role1b>délégué),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>.+?),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*(?P<role2>président),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3}),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_NEW = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont chacun cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*par conséquent\s+(?P=seller1)\s+et\s+"
    r"(?P=seller2)\s+sont maintenant chacun associé pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MORATORIUM_EXTENDED_OWNER = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>zuständige Einzelgericht)\s+dem Inhaber die gewährte "
    r"Nachlassstundung um\s+(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+"
    r"Monate,\s*d\.h\.\s*bis am\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+"
    r"verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ADMINISTRATORS_DOMICILE = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+)\s+sont "
    r"maintenant domiciliés à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_FOUNDATION_MEMBER_TYPO = re.compile(
    r"^Peronne radiée:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>membre du conseil de fondation),\s*"
    r"(?P<sign>signature collective à deux)\s+avec\s+"
    r"(?P<with_role>un autre membre du conseil)\.?$",
    re.I | re.UNICODE,
)
_DE_PROPRIETOR_BANKRUPTCY_ENTRY_REMOVED = re.compile(
    r"^Demnach wird die Eintragung betreffend Konkurs im Handelsregister "
    r"gestrichen\.\s*\[bisher:\s*Über den Inhaber dieses Einzelunternehmens "
    r"wurde mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_CONTRACT_ORDER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Verfügung vom\s+"
    r"(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>Keine)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTION_THREE = re.compile(
    r"^L['’]inscription n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens "
    r"qu['’]une signature collective à deux a été conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+)\s*\(et non individuelle\)\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED_GESTRICHEN = re.compile(
    r"^Zweigniederlassung neu:\s*\[Folgende Zweigniederlassung ist aufgehoben "
    r"worden:\]\s*\[gestrichen:\s*(?P<place>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_SIGNING = re.compile(
    r"^L['’]associée\s+(?P<name>[^,.;]+),\s*nommée\s+"
    r"(?P<role>gérante présidente),\s*signe désormais\s+"
    r"(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)


_DE_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    return int(raw) if raw.isdigit() else _DE_NUMBERS[raw.lower()]


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


def extract_parser88_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 88."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_ERRONEOUS_DELETION_CONSENT_REMARK.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.erroneous_tax_deletion_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "action": "corrected",
                    "reason": "erroneous_tax_authority_deletion_consent",
                },
            )
        )

    match = _DE_CONDITIONAL_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.conditional_capital_introduced.v1",
                {
                    "kind": "conditional_capital",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.committee_member_without_signature.v2",
                match.group("name"), place=match.group("place"),
                role="membre du comité",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_NEW_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_new_without_signature.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": _count(match.group("transferred")),
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("place").strip(),
                        "counterparty": seller,
                        "shares_received": _count(match.group("transferred")),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _FR_ASSOCIATE_NAME_CORRECTION_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_name_correction_notice.v1",
                match.group("name"), role="associé",
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "shares_count": _count(match.group("shares")),
                    "shares_nominal": match.group("nominal"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_COLLECTIVE_SIGNING_THREE_NAMES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.collective_signing_three_names.v1"
        for index in (1, 2, 3):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "granted"},
                )
            )

    match = _FR_ADMINISTRATION_THREE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_individual.v1"
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=f"{match.group('role1')} et {match.group('role1b')}",
                signing="Einzelunterschrift", extra={"action": "changed"},
            )
        )
        for index, role in ((2, match.group("role2")), (3, "administrateur")):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role=role,
                    signing="Einzelunterschrift",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                    },
                )
            )

    match = _FR_TWO_ASSOCIATES_TRANSFER_NEW.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associates_transfer_new.v1"
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
                role="associée",
                extra={
                    "action": "shares_received",
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

    match = _DE_MORATORIUM_EXTENDED_OWNER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.owner_composition_moratorium_extended.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "scope": "sole_proprietor",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "until": _iso_date(match.group("until")),
                    "duration_months": _duration(match.group("duration")),
                    "authority": match.group("authority"),
                },
            )
        )

    match = _FR_THREE_ADMINISTRATORS_DOMICILE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_administrators_domicile_changed.v1"
        for index in (1, 2, 3):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group("place"), role="administrateur",
                    extra={
                        "action": "domicile_changed",
                        "country": match.group("country"),
                    },
                )
            )

    match = _FR_REMOVED_FOUNDATION_MEMBER_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", "fr.persons.foundation_member_removed_typo.v1",
                match.group("name"), role=match.group("role"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "removed",
                    "signing_with": match.group("with_role"),
                },
            )
        )

    match = _DE_PROPRIETOR_BANKRUPTCY_ENTRY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.proprietor_bankruptcy_entry_removed.v1",
                {
                    "kind": "bankruptcy",
                    "action": "removed",
                    "scope": "sole_proprietor",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "decision_time": match.group("time").replace(".", ":"),
                    "historical_entry": True,
                },
            )
        )

    match = _DE_FOUNDATION_ASSET_TRANSFER_CONTRACT_ORDER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.foundation_asset_transfer_contract_order.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "order_date": _iso_date(match.group("order_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                    "consideration_kind": "none",
                },
            )
        )

    match = _FR_SIGNING_CORRECTION_THREE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.collective_signing_three_correction.v1"
        for index in (1, 2, 3):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "corrected",
                        "previous_signing": "Einzelunterschrift",
                        "entry": match.group("entry"),
                        "entry_date": _iso_date(match.group("entry_date")),
                    },
                )
            )

    match = _DE_LEGACY_BRANCH_REMOVED_GESTRICHEN.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.legacy_branch_removed_gestrichen.v1",
                {
                    "action": "removed",
                    "place": match.group("place").strip(),
                    "historical_entry": True,
                },
            )
        )

    match = _FR_MANAGER_PRESIDENT_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_president_signing_changed.v1",
                match.group("name"), role=match.group("role"),
                signing="Einzelunterschrift",
                extra={"action": "appointed_and_signing_changed"},
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
