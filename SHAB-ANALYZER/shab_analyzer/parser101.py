from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ONE_MANAGER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que "
    r"l['’]un des gérants se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_BY_DEPARTMENT_PRESIDENT = re.compile(
    r"^Der Abteilungspräsident der\s+(?P<department>.+?)\s+des\s+"
    r"(?P<authority>.+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die Konkurseröffnung "
    r"erhobenen Beschwerde aufschiebende Wirkung zuerkannt\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*hat\s+"
    r"(?P<court>.+?)\s+über die Gesellschaft den Konkurs eröffnet;\s*"
    r"demnach ist die Gesellschaft aufgelöst\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_THREE_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé à concurrence de\s+"
    r"(?P<count1>[\d']+) parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*jusqu['’]ici gérant,\s*nouvel associé pour\s+"
    r"(?P<buyer_count1>[\d']+) parts de CHF\s+(?P<buyer_nominal1>[\d'.]+),\s*"
    r"n['’]exerce plus la signature sociale;\s*ses pouvoirs sont modifiés dans ce sens;\s*"
    r"à concurrence de\s+(?P<count2>[\d']+) parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count2>[\d']+) parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"et à concurrence de\s+(?P<count3>[\d']+) parts de CHF\s+"
    r"(?P<nominal3>[\d'.]+)\s+à\s+(?P<buyer3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count3>[\d']+) parts de CHF\s+(?P<buyer_nominal3>[\d'.]+)\.\s*"
    r"Gérants:\s*les associés\s+(?P=buyer2)\s+et\s+(?P=buyer3),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_OFFICE_REMOVED = re.compile(
    r"^\[gestrichen:\s*Weiteres Geschäftslokal:\s*(?P<address>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_ENTRY_REMOVED = re.compile(
    r"^Mit Mitteilung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist dem Rekurs gegen den "
    r"Entscheid des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung "
    r"betreffend Konkurseröffnung über die Gesellschaft im Handelsregister gestrichen\.\s*"
    r"\[bisher:\s*Mit Entscheid des\s+(?P<previous_court>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+ist über die Gesellschaft mit "
    r"Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_VICE_PRESIDENT_AND_RESTRICTED_ADMINISTRATORS = re.compile(
    r"^(?P<vice>.+?),\s*administratrice,\s*est nommée vice-présidente\.\s*"
    r"Nouveaux administrateurs toutefois pas entre eux ni avec\s+(?P=vice):\s*"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>délégué),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+?)(?:\s*\((?P<country2>[^)]+)\))?\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_PERSON_WITHOUT_SIGNATURE_MIXED_LANGUAGE = re.compile(
    r"^Neu eingetragene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*ohne Unterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_DUPLICATE_CURRENCY = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s+(?:CHF\s+)?(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSFER_WITH_ASSOCIATE_SUMMARY = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<count1>[\d']+) parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+)\s+et\s+"
    r"(?P<count2>[\d']+) parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z])\.\s*Associés:\s*"
    r"(?P=buyer1) pour\s+(?P<buyer_count1>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal1>[\d'.]+),\s*(?P=buyer2) pour\s+"
    r"(?P<buyer_count2>[\d']+) parts de CHF\s+(?P<buyer_nominal2>[\d'.]+),\s*"
    r"(?P=seller) pour\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\s+et\s+(?P<other>.+?) pour\s+"
    r"(?P<other_count>[\d']+) parts de CHF\s+(?P<other_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_MANAGER_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveau gérant sans signature:\s*(?P<name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDRESS_PORTFOLIO_CHANGED = re.compile(
    r"^(?P<removed>(?:\[gestrichen:\s*(?:Geschäftsstelle|Weitere Adresse):\s*"
    r"[^\]]+\]\.?\s*)+)(?P<added>(?:[^.]+\.\s*){3}[^.]+\.?)$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDRESS_ITEM = re.compile(
    r"\[gestrichen:\s*(?P<kind>Geschäftsstelle|Weitere Adresse):\s*"
    r"(?P<address>[^\]]+?)\]\.?",
    re.I | re.UNICODE,
)
_FR_BRANCH_PROCURATION_CONFERRED = re.compile(
    r"^Procuration collective à deux pour les affaires de la succursale a été "
    r"conférée à\s+(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MULTI_NOMINAL_REDUCTION_TO_RESERVES = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird der Nennwert der\s+(?P<count1>[\d']+)\s+(?P<kind>Stammanteile) zu CHF\s+"
    r"(?P<from1>[\d'.]+)\s+um CHF\s+(?P<reduction1>[\d'.]+)\s+auf CHF\s+"
    r"(?P<to1>[\d'.]+),\s*der Nennwert des einen Stammanteils zu CHF\s+"
    r"(?P<from2>[\d'.]+)\s+um CHF\s+(?P<reduction2>[\d'.]+)\s+auf CHF\s+"
    r"(?P<to2>[\d'.]+)\s+sowie der Nennwert der\s+(?P<count3>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<from3>[\d'.]+)\s+um CHF\s+"
    r"(?P<reduction3>[\d'.]+)\s+auf CHF\s+(?P<to3>[\d'.]+)\s+herabgesetzt "
    r"und CHF\s+(?P<assigned>[\d'.]+)\s+den gesetzlichen Reserven aus "
    r"Kapitaleinlagen zugewiesen;\s*die Beachtung der gesetzlichen Vorschriften "
    r"von\s+(?P<legal_basis>Art\.\s*782 Abs\.\s*4 i\.V\.m\.\s*734 OR)\s+"
    r"wird mit öffentlicher Urkunde vom\s+"
    r"(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+festgestellt\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED_WITH_HISTORY = re.compile(
    r"^Diese Gesellschaft, welche am\s+(?P<deleted_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"infolge Konkurses im Sinne von\s+(?P<legal_basis>Art\.\s*159 HRegV)\s+"
    r"gelöscht wurde, wird gemäss Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder als durch Konkurs "
    r"aufgelöst in das Handelsregister eingetragen\.\s*Datum der "
    r"Konkurseröffnung:\s*(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr\.\s*"
    r"\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_EXACT_SURNAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que le "
    r"nom exact de\s+(?P<previous_surname>\S+)\s+(?P<given_names>.+?)\s+est\s+"
    r"(?P<surname>\S+)\.?$",
    re.I | re.UNICODE,
)
_FR_FIRST_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que le "
    r"prénom de l['’](?P<role>associée-gérante|associé-gérant)\s+"
    r"(?P<surname>[^,.;]+?)\s+est\s+(?P<first_name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_first_name>[^)]+)\)\.?$",
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


def extract_parser101_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 101."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ONE_MANAGER_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.one_manager_name_corrected.v1",
            match.group("name"), role="gérant",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_BY_DEPARTMENT_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspensive_president.v1",
            {
                "kind": "bankruptcy",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "department": match.group("department").strip(),
                "court": match.group("court").strip(),
                "dissolution_suspended": True,
            },
        ))

    match = _FR_MANAGER_THREE_SHARE_TRANSFERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_three_share_transfers.v1"
        transferred = sum(_count(match.group(f"count{i}")) for i in range(1, 4))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("seller"), role="associé-gérant",
            extra={"action": "shares_transferred", "shares_transferred": transferred},
        ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer1"), role="associé",
            extra={
                "action": "shares_received_and_management_ended",
                "previous_role": "gérant",
                "shares_received": _count(match.group("count1")),
                "shares_count": _count(match.group("buyer_count1")),
                "share_nominal": match.group("buyer_nominal1"),
                "currency": "CHF",
                "without_signature": True,
            },
        ))
        for index in (2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé-gérant",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_and_shares_received",
                    "heimat": match.group(f"origin{index}").strip(),
                    "shares_received": _count(match.group(f"count{index}")),
                    "shares_count": _count(match.group(f"buyer_count{index}")),
                    "share_nominal": match.group(f"buyer_nominal{index}"),
                    "currency": "CHF",
                },
            ))

    match = _DE_BUSINESS_OFFICE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.business_office_removed_singular.v1",
            {
                "kind": "business_office",
                "action": "removed",
                "address": match.group("address").strip().rstrip("."),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_ENTRY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_entry_removed.v1",
            {
                "kind": "bankruptcy",
                "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "court": match.group("court").strip(),
                "previous_court": match.group("previous_court").strip(),
                "bankruptcy_entry_removed": True,
            },
        ))

    match = _FR_VICE_PRESIDENT_AND_RESTRICTED_ADMINISTRATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.vice_president_restricted_administrators.v1"
        vice = match.group("vice").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, vice, role="vice-présidente",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_vice_president", "previous_role": "administratrice"},
        ))
        for index in (1, 2):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
                "signing_restriction": f"not with each other or {vice}",
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country.strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role=match.group("role1") if index == 1 else "administrateur",
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _DE_NEW_PERSON_WITHOUT_SIGNATURE_MIXED_LANGUAGE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.new_person_without_signature_mixed_language.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "without_signature": True,
            },
        ))

    match = _FR_ASSET_TRANSFER_DUPLICATE_CURRENCY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_duplicate_currency.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "currency": "CHF",
            },
        ))

    match = _FR_COMPANY_TRANSFER_WITH_ASSOCIATE_SUMMARY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.company_transfer_associate_summary.v1"
        seller = match.group("seller").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé",
            extra={
                "action": "shares_transferred",
                "shares_transferred": _count(match.group("count1")) + _count(match.group("count2")),
                "shares_count": _count(match.group("seller_count")),
                "share_nominal": match.group("seller_nominal"),
                "currency": "CHF",
            },
        ))
        for index in (1, 2):
            extra = {
                "action": "shares_received",
                "counterparty": seller,
                "shares_received": _count(match.group(f"count{index}")),
                "shares_count": _count(match.group(f"buyer_count{index}")),
                "share_nominal": match.group(f"buyer_nominal{index}"),
                "currency": "CHF",
            }
            if index == 2:
                extra.update({
                    "heimat": match.group("origin2").strip(),
                    "country": match.group("country2"),
                })
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group("place2") if index == 2 else None,
                role="associé", extra=extra,
            ))

    match = _FR_NEW_MANAGER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_manager_without_signature.v1",
            match.group("name"), place=match.group("place"), role="gérant",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "without_signature": True,
            },
        ))

    match = _DE_ADDRESS_PORTFOLIO_CHANGED.search(leftover)
    if match:
        removed_items = list(_DE_REMOVED_ADDRESS_ITEM.finditer(match.group("removed")))
        added_items = [
            item.strip().rstrip(".")
            for item in re.split(r"\.\s+", match.group("added").strip())
            if item.strip().rstrip(".")
        ]
        if removed_items and added_items:
            consume(match)
            rule_id = "de.text.address_portfolio_changed.v1"
            for item in removed_items:
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", rule_id,
                    {
                        "kind": (
                            "business_office"
                            if item.group("kind").lower() == "geschäftsstelle"
                            else "additional_address"
                        ),
                        "action": "removed",
                        "address": item.group("address").strip().rstrip("."),
                    },
                ))
            for address in added_items:
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", rule_id,
                    {"kind": "additional_address", "action": "added", "address": address},
                ))

    match = _FR_BRANCH_PROCURATION_CONFERRED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.branch_procuration_conferred.v1"
        common = {
            "place": match.group("place"),
            "signing": "Kollektivprokura zu zweien",
            "extra": {
                "action": "granted",
                "heimat": match.group("origin").strip(),
                "scope": "branch_business",
            },
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), **common,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name"), **common,
            ),
        ])

    match = _DE_MULTI_NOMINAL_REDUCTION_TO_RESERVES.search(leftover)
    if match:
        consume(match)
        share_classes = []
        for index, count in ((1, match.group("count1")), (2, "1"), (3, match.group("count3"))):
            share_classes.append({
                "shares_count": _count(count),
                "from_nominal": match.group(f"from{index}"),
                "reduction_per_share": match.group(f"reduction{index}"),
                "to_nominal": match.group(f"to{index}"),
            })
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.multi_nominal_reduction_to_reserves.v1",
            {
                "kind": "nominal_value_reduction",
                "date": _iso_date(match.group("date")),
                "share_kind": match.group("kind"),
                "share_classes": share_classes,
                "currency": "CHF",
                "assigned_to_capital_contribution_reserves": match.group("assigned"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "confirmation_date": _iso_date(match.group("confirmation_date")),
            },
        ))

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated_history.v1",
            {
                "kind": "bankruptcy_company_reinstated",
                "deleted_date": _iso_date(match.group("deleted_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "previous": match.group("previous").strip(),
                "dissolved_by_bankruptcy": True,
                "registry_reinstated": True,
            },
        ))

    match = _FR_EXACT_SURNAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname')} {match.group('given_names')}"
        previous_name = f"{match.group('previous_surname')} {match.group('given_names')}"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.exact_surname_corrected.v1", name,
            extra={
                "action": "name_corrected",
                "previous_name": previous_name,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_FIRST_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname')} {match.group('first_name')}"
        previous_name = f"{match.group('surname')} {match.group('previous_first_name')}"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.first_name_corrected.v1", name,
            role=match.group("role"),
            extra={
                "action": "name_corrected",
                "previous_name": previous_name,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
