from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_NEW_BRANCHES_PAIR = re.compile(
    r"^Neue Zweigniederlassungen:\s*"
    r"(?P<place1>[^(),]+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"Eintragung Nr\.\s*(?P<entry1>[\d']+)\s+vom\s+"
    r"(?P<entry_date1>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(SHAB vom\s+(?P<notice_date1>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Id\s+(?P<notice_id1>\d+)\),\s*und\s+"
    r"(?P<place2>[^(),]+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"Eintragung Nr\.\s*(?P<entry2>[\d']+)\s+vom\s+"
    r"(?P<entry_date2>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(SHAB vom\s+(?P<notice_date2>\d{2}\.\d{2}\.\d{4}),\s*"
    r"Id\s+(?P<notice_id2>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_CONTRACT_DATES = re.compile(
    r"^Vermögensübertragung:\s*Die\s+"
    r"(?P<transferor>Gesellschaft|Geschäftsinhaberin)\s+überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<contract_dates>\d{2}\.\d{2}\.\d{4}(?:/\d{2}\.\d{2}\.\d{4})?)"
    r"(?:\s+und Inventar per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4}))?\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven "
    r"\(Fremdkapital\) von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_EXISTING_MANAGER = re.compile(
    r"^L['’](?P<seller_role>associée?)\s+(?P<seller>[^,.;]+?)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"l['’](?P<buyer_role>associé-gérant|associée-gérante)\s+"
    r"(?P<buyer>[^,.;]+?)\s+qui possède désormais\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_JUDGMENT_EXECUTION_SUSPENDED = re.compile(
    r"^Par ordonnance du\s+(?P<order_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>le Tribunal cantonal)\s+a suspendu l['’]exécution du "
    r"jugement de faillite rendu le\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_ALTERNATE_ADDRESS_REMOVED = re.compile(
    r"^\[radiati:\s*Altro indirizzo:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_STATUS_CORRECTION = re.compile(
    r"^L['’]inscription n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+n['’]est pas\s+(?P<role>gérante?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTION = re.compile(
    r"^L['’]inscription n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"l['’](?P<role>associé-gérant|associée-gérante)\s+se nomme\s+"
    r"(?P<name>[^()]+?)\s*\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_SHARE_TRANSFER = re.compile(
    r"^L['’](?P<seller_role>associée-gérante?)\s+(?P<seller>[^,.;]+?)\s+"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel\s+(?P<buyer_role>associé-gérant)\s+avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+"
    r"parts? de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATION_RESOURCES = re.compile(
    r"^Nouvelles ressources:\s*(?P<resources>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+a cédé\s+(?P<transferred>[\d']+)\s+"
    r"parts? de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts? de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel associé est en outre nommé\s+(?P<buyer_role>gérant-président)\s+"
    r"Par conséquent,\s*(?P=seller)\s+est maintenant associée pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés gérants\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<president>président),\s*et\s+"
    r"(?P<name2>[^,.;]+);\s*lesquels continuent à signer\s+"
    r"(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_PARTICIPATION_CAPITAL_INCREASE = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Erhöhung des "
    r"Partizipationskapitals gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_ROLES_AND_BRANCH_PROCURATION_CORRECTION = re.compile(
    r"^L['’]inscription n[°o]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce "
    r"se(?:ns|s) que\s+(?P<director1>[^,.;]+?)\s+et\s+"
    r"(?P<director2>[^,.;]+?)\s+sont\s+(?P<director_role>directeurs adjoints)\.\s*"
    r"(?P<proxy1>[^,.;]+?)\s+et\s+(?P<proxy2>[^,.;]+?)\s+signent avec\s+"
    r"(?P<sign>procuration collective à deux),\s*limitée à\s+"
    r"(?P<scope>l['’]établissement principal)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte Bestimmung "
    r"betreffend genehmigter Kapitalerhöhung gemäss näherer Umschreibung in "
    r"den Statuten geändert\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_REPLACES_PROCURATION = re.compile(
    r"^Signature\s+(?P<sign>collective à deux)\s+a été conférée à\s+"
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


def extract_parser87_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 87."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_NEW_BRANCHES_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.new_branches_pair.v1"
        for index in (1, 2):
            events.append(
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", rule_id,
                    {
                        "action": "registered",
                        "place": match.group(f"place{index}").strip(),
                        "uid": match.group(f"uid{index}"),
                        "entry": match.group(f"entry{index}"),
                        "entry_date": _iso_date(match.group(f"entry_date{index}")),
                        "notice_date": _iso_date(match.group(f"notice_date{index}")),
                        "notice_id": match.group(f"notice_id{index}"),
                    },
                )
            )

    match = _DE_ASSET_TRANSFER_CONTRACT_DATES.search(leftover)
    if match:
        consume(match)
        dates = [_iso_date(value) for value in match.group("contract_dates").split("/")]
        inventory_date = match.group("inventory_date")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_contract_dates.v1",
                {
                    "transferor_kind": match.group("transferor"),
                    "contract_dates": dates,
                    "date": dates[0],
                    "inventory_date": _iso_date(inventory_date) if inventory_date else None,
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_EXISTING_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_existing_manager.v1"
        common = {
            "shares_transferred": _count(match.group("transferred")),
            "shares_nominal": match.group("nominal"),
        }
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role=match.group("seller_role").lower(),
                    extra={
                        "action": "shares_transferred",
                        "counterparty": match.group("buyer").strip(),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    role=match.group("buyer_role").lower(),
                    extra={
                        "action": "shares_received",
                        "counterparty": match.group("seller").strip(),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_BANKRUPTCY_JUDGMENT_EXECUTION_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_judgment_execution_suspended.v1",
                {
                    "kind": "bankruptcy_execution_suspended",
                    "order_date": _iso_date(match.group("order_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "authority": match.group("authority"),
                },
            )
        )

    match = _IT_ALTERNATE_ADDRESS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "it.text.alternate_address_removed.v1",
                {
                    "action": "removed",
                    "kind": "alternate_address",
                    "address": match.group("address").strip(),
                    "postal_code": match.group("postal_code"),
                    "place": match.group("place").strip(),
                },
            )
        )

    match = _FR_MANAGER_STATUS_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.manager_status_correction.v1",
                match.group("name"), role=match.group("role").lower(),
                extra={
                    "action": "role_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "never_held_role": True,
                },
            )
        )

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_manager_name_correction.v1",
                match.group("name"), role=match.group("role").lower(),
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_ASSOCIATE_MANAGER_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_manager_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role=match.group("seller_role").lower(),
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": _count(match.group("transferred")),
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role=match.group("buyer_role").lower(),
                    extra={
                        "action": "shares_received_and_appointed",
                        "counterparty": seller,
                        "heimat": match.group("origin").strip(),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_NEW_ASSOCIATION_RESOURCES.search(leftover)
    if match:
        consume(match)
        resources = [value.strip() for value in match.group("resources").split(";")]
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.association_resources_changed.v1",
                {"kind": "resources", "action": "changed", "resources": resources},
            )
        )

    match = _FR_SHARE_TRANSFER_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée",
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
                    role=match.group("buyer_role").lower(),
                    extra={
                        "action": "shares_received_and_appointed",
                        "counterparty": seller,
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_ASSOCIATE_MANAGERS_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_managers_liquidators.v1"
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    role=(
                        "associé-gérant président et liquidateur"
                        if index == 1
                        else "associée-gérante et liquidatrice"
                    ),
                    signing="Einzelunterschrift",
                    extra={"action": "appointed_liquidator", "signing_continues": True},
                )
            )

    match = _DE_AUTHORIZED_PARTICIPATION_CAPITAL_INCREASE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_participation_capital_increase.v1",
                {
                    "kind": "authorized_participation_capital_increase",
                    "action": "authorized",
                    "decision_date": _iso_date(match.group("decision_date")),
                },
            )
        )

    match = _FR_ROLES_AND_BRANCH_PROCURATION_CORRECTION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.roles_and_branch_procuration_correction.v1"
        common = {
            "action": "corrected",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"director{index}"),
                    role="directeur adjoint", extra=common,
                )
            )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"proxy{index}"),
                    signing="Kollektivprokura zu zweien",
                    extra={**common, "scope": "établissement principal"},
                )
            )

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_clause_modified.v3",
                {
                    "kind": "authorized_capital_clause",
                    "action": "modified",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "introduction_date": _iso_date(match.group("introduction_date")),
                },
            )
        )

    match = _FR_COLLECTIVE_SIGNING_REPLACES_PROCURATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.collective_signing_replaces_procuration.v1",
                match.group("name"), signing="Kollektivunterschrift zu zweien",
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
