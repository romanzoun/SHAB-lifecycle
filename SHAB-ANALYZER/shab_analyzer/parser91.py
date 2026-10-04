from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SOLE_PROPRIETOR_DELETED_AFTER_BUSINESS_TRANSFER = re.compile(
    r"^L['’]entreprise individuelle est radiée par suite de remise de commerce\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_DEED_NON_PUBLIC_CHANGES = re.compile(
    r"^\[Stiftungsurkundenänderung ohne publikationspflichtigen Tatsachen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_COURT_ORDERED_DISSOLUTION = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wird die Betroffene mit Rechtskraft "
    r"des vorliegenden Entscheids aufgelöst und ihre Liquidation nach den "
    r"Vorschriften über den Konkurs angeordnet\.?$",
    re.I | re.UNICODE,
)
_FR_SPLIT_TRANSFER_TO_TWO_NEW_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<buyer1_received>[\d']+)\s+parts de CHF\s+(?P<buyer1_nominal>[\d'.]+)\s+"
    r"à\s+(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et,?\s*par\s+(?P<buyer2_received>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer2_nominal>[\d'.]+)\s+à\s+(?P<buyer2>[^,.;]+),\s*"
    r"de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+(?:\s*\([^)]+\))?),\s*"
    r"nouveaux associés-gérants\s*;\s*(?P=seller),\s*qui reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*"
    r"est nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_APPOINTED_WAIVER_REMOVED = re.compile(
    r"^Ogane de révision:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s*(?P<place>[^.;]+)\.\s*"
    r"Radiation de la mention relative à la renonciation à un contrôle restreint\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ORGANIZATIONS_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller1>.+?)\s*\((?P<registry1>[\d ]+ R\.C\.S\. [^)]+)\)\s+et\s+"
    r"(?P<seller2>.+?)\s*\((?P<registry2>[\d ]+ R\.C\.S\. [^)]+)\)\s+"
    r"ne sont plus associées;\s*leurs\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+et\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+ont été cédées à l['’]associé-gérant\s+"
    r"(?P<buyer>.+?)\s+qui détient ainsi les\s+(?P<buyer_count>[\d']+)\s+parts "
    r"de CHF\s+(?P<buyer_nominal>[\d'.]+)\s+formant le capital de CHF\s+"
    r"(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_TRANSLATIONS_REMOVED = re.compile(
    r"^Uebersetzungen der Firma neu:\s*Die Übersetzungen werden im "
    r"Handelsregister gelöscht\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_INVENTORY = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"mit Inventar sowie Verfügung der Aufsichtsbehörde vom\s+"
    r"(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_SUPPLEMENT_REFERENCE = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est complétée comme suit\s*:\s*$",
    re.I | re.UNICODE,
)
_FR_PREMATURE_DELETION_REINSTATED = re.compile(
    r"^La radiation de l['’]entreprise ayant été opérée prématurément,\s*"
    r"l['’]inscription n[o°]\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est annulée et l['’]entreprise "
    r"est par conséquent réinscrite\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_INDIVIDUAL_SIGNING = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+"
    r"(?P<place1>.+?)\s*\(France\),\s*et\s+(?P<name2>[^,.;]+),\s*à\s+"
    r"(?P<place2>.+?)\s*\(France\),\s*président,\s*tous deux de France,\s*"
    r"gérants\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_ERRONEOUS_DELETION = re.compile(
    r"^\[Wiedereintragung der Gesellschaft,\s*welche am\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s*irrtümlich gelöscht wurde\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_LIABILITIES_NO_CONSIDERATION_UID_FIRST = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Passiven \(Fremdkapital\) von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_AND_CHANGED_PERSON_PLURAL = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>[^,.;]+),\s*"
    r"(?P<removed_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.\s*"
    r"Eingetragene Personen geändert:\s*(?P<changed>[^,.;]+),\s*"
    r"(?P<previous_role>.+?),\s*"
    r"(?P<previous_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?),\s*"
    r"neu\s+(?P<role>.+?),\s*"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé,?\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "einzel" in raw.lower()
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser91_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 91."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SOLE_PROPRIETOR_DELETED_AFTER_BUSINESS_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.sole_proprietor_deleted_business_transfer.v1",
                {
                    "reason": "business_transfer",
                    "scope": "sole_proprietor",
                },
            )
        )

    match = _DE_FOUNDATION_DEED_NON_PUBLIC_CHANGES.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.foundation_deed_non_public_changes.v1",
                {"kind": "non_public_changes", "document": "foundation_deed"},
            )
        )

    match = _DE_COURT_ORDERED_DISSOLUTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.court_ordered_dissolution_bankruptcy.v1",
                {
                    "kind": "court_ordered_dissolution",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "effective_on_finality": True,
                    "liquidation_under_bankruptcy_rules": True,
                },
            )
        )

    match = _FR_SPLIT_TRANSFER_TO_TWO_NEW_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.split_transfer_two_new_managers.v1"
        seller = match.group("seller").strip()
        transferred = _count(match.group("transferred"))
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant, président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            )
        )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role="associé-gérant",
                    extra={
                        "action": "appointed",
                        "new_associate": True,
                        "heimat": match.group(f"origin{index}").strip(),
                        "shares_received": _count(match.group(f"buyer{index}_received")),
                        "shares_count": _count(match.group(f"buyer{index}_received")),
                        "share_nominal": match.group(f"buyer{index}_nominal"),
                        "currency": "CHF",
                        "transfer_total": transferred,
                    },
                )
            )

    match = _FR_AUDITOR_APPOINTED_WAIVER_REMOVED.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.auditor_appointed_typo.v1",
                    match.group("name"), place=match.group("place"), uid=match.group("uid"),
                    role="organe de révision", extra={"action": "appointed"},
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "audit_requirement_changed", "fr.text.audit_waiver_mention_removed.v1",
                    {
                        "kind": "limited_audit_waiver",
                        "action": "revoked",
                        "waiver_mention_removed": True,
                    },
                ),
            ]
        )

    match = _FR_TWO_ORGANIZATIONS_TRANSFER_TO_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_organizations_transfer_to_manager.v1"
        counts = [_count(match.group("count1")), _count(match.group("count2"))]
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group(f"seller{index}"), role="associée",
                    extra={
                        "action": "removed_after_share_transfer",
                        "foreign_registry_id": match.group(f"registry{index}"),
                        "shares_transferred": counts[index - 1],
                        "share_nominal": match.group(f"nominal{index}"),
                        "currency": "CHF",
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"), role="associé-gérant",
                extra={
                    "action": "shares_received",
                    "shares_received": sum(counts),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "capital": match.group("capital"),
                    "currency": "CHF",
                },
            )
        )

    match = _DE_COMPANY_TRANSLATIONS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "de.text.company_translations_removed.v1",
                {"action": "translations_removed", "registry_updated": True},
            )
        )

    match = _DE_FOUNDATION_ASSET_TRANSFER_INVENTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.foundation_asset_transfer_inventory_order.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "inventory_attached": True,
                    "supervisory_order_date": _iso_date(match.group("order_date")),
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

    match = _FR_REGISTRATION_SUPPLEMENT_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "fr.text.registration_supplement_reference.v1",
                {
                    "action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _FR_PREMATURE_DELETION_REINSTATED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.premature_deletion_reinstated.v1",
                {
                    "kind": "registration_reinstated",
                    "reason": "premature_deletion",
                    "cancelled_entry": match.group("entry"),
                    "cancelled_entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_TWO_MANAGERS_INDIVIDUAL_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_individual_signing.v1"
        for index, role in ((1, "gérant"), (2, "gérant, président")):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"), role=role,
                    signing="Einzelunterschrift",
                    extra={"action": "granted", "heimat": "France", "country": "France"},
                )
            )

    match = _DE_COMPANY_REINSTATED_ERRONEOUS_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.company_reinstated_erroneous_deletion.v2",
                {
                    "kind": "registration_reinstated",
                    "reason": "erroneous_deletion",
                    "deletion_date": _iso_date(match.group("date")),
                },
            )
        )

    match = _DE_ASSET_TRANSFER_LIABILITIES_NO_CONSIDERATION_UID_FIRST.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_liabilities_uid_first.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration").lower(),
                    "gratuitous": True,
                },
            )
        )

    match = _DE_REMOVED_AND_CHANGED_PERSON_PLURAL.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.removed_and_role_changed_plural.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    role=match.group("removed_role").strip(),
                    signing=_signing(match.group("removed_sign")),
                    extra={"action": "removed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("changed"),
                    role=match.group("role").strip(), signing=_signing(match.group("sign")),
                    extra={
                        "action": "role_changed",
                        "previous_role": match.group("previous_role").strip(),
                        "previous_signing": _signing(match.group("previous_sign")),
                    },
                ),
            ]
        )

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_new_associate.v2"
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associé",
                    extra={
                        "action": "shares_transferred",
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé",
                    extra={
                        "action": "appointed",
                        "new_associate": True,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
