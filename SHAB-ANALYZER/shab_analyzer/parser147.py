from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_LIQUIDATION_BY_ORGANIZATION = re.compile(
    r"^La liquidation est opérée sous la raison de commerce:\s*"
    r"(?P<liquidation_name>.+?),\s*par\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*liquidatrice\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_PAIR_SHARED_ORIGIN = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*tous deux de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^();]+)\s*\((?P<country>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_HISTORY_BATCH = re.compile(
    r"^\[bisher:\s*(?P<initial>[^\]]+)\]\.(?P<items>.+)$",
    re.I | re.UNICODE,
)
_DE_BRANCH_HISTORY_ITEM = re.compile(
    r"\s*(?P<place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<previous>[^\]]+)\]\.?",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_BECOME_LIQUIDATORS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*sans signature,\s*tous membres du conseil de "
    r"fondation,\s*sont liquidateurs\.?$",
    re.I | re.UNICODE,
)
_FR_INHERITANCE_ALL_SHARES_TRANSFER = re.compile(
    r"^Par partage du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+de la succession de\s+"
    r"(?P<deceased>[^,.;]+),\s*décédé,\s*la communauté héréditaire représentée "
    r"par\s+(?P<representative>[^,.;]+)\s+a cédé les\s+"
    r"(?P<count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais associé unique pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_RESULTING_HOLDINGS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s+est maintenant associée pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_HOLDING_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que "
    r"l['’](?P<role>associé-gérant président)\s+(?P<name>[^,.;]+)\s+détient\s+"
    r"(?P<count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSETS_AND_LIABILITIES_ASSUMED = re.compile(
    r"^Übernimmt Aktiven und Passiven des Einzelunternehmens\s+(?P<source>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXTENDED = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé le "
    r"sursis concordataire définitif accordé à la société jusqu['’]au\s+"
    r"(?P<until>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ELECTED_PRESIDENT_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*qui est élu président et "
    r"continue à signer individuellement,\s*cède\s+(?P<transferred>[\d']+)\s+de "
    r"ses\s+(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^()]+?)\s*\((?P<canton>[A-Z]{2})\),\s*"
    r"nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant\.?$",
    re.I | re.UNICODE,
)
_FR_ADMIN_PRESIDENT_AND_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*lequel "
    r"continue à signer individuellement\s+et\s+(?P<member>[^,.;]+),\s*"
    r"de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMIN_MOVED_PRESIDENT_PAIR = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+)\s+maintenant domicilié à\s+"
    r"(?P<president_place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*nommé président "
    r"et\s+(?P<member>[^,.;]+),\s*de et à\s+(?P<member_place>[^,.;]+),\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SPLIT_TRANSFER_TO_TWO = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+se ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+par\s+(?P<count1>[\d']+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*et par\s+(?P<count2>[\d']+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*avec signature collective à deux,\s*tous deux "
    r"de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<country>[^)]+)\),\s*nouveaux as+sociés-gérants\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_IDENTIFIER_FRAGMENT = re.compile(
    r"^\[bisher:\s*(?P<from>[A-Z]{2,4}-\d{3}\.\d{3}\.\d{3})\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_EXECUTIVE_PRESIDENT_CORRECTION = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\):\s*"
    r"(?P<name>[^,.;]+),\s*(?P<previous_role>membre du conseil de fondation),\s*"
    r"signature collective à deux,\s*maintenant\s+"
    r"(?P<role>membre du conseil de fondation et présidente de la commission "
    r"exécutive),\s*signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_LLC_CAPITAL_INCREASE_AND_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Gesellschaft mit beschränkter Haftung hat das "
    r"Stammkapital auf CHF\s+(?P<capital>[\d'.]+)\s+erhöht und wird gemäss "
    r"Umwandlungsplan vom\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft umgewandelt\.\s*"
    r"Die Gesellschafter erhält für seinen bisherigen Stammanteil\s+"
    r"(?P<shares>[\d']+)\s+Namenaktien zu CHF\s+(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
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


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _formatted_uid(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 9:
        return raw
    return f"CHE-{digits[:3]}.{digits[3:6]}.{digits[6:]}"


def _legacy_branch(value: str) -> tuple[str, str | None]:
    match = re.match(r"^(?P<place>.+?)\s*\((?P<registry_id>CH-[\d.]+-\d)\)$", value)
    if not match:
        return value.strip(), None
    return match.group("place").strip(), match.group("registry_id")


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


def extract_parser147_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 147."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_LIQUIDATION_BY_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.organization_liquidator_trade_name.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="liquidatrice",
            extra={
                "action": "appointed_liquidator",
                "uid": match.group("uid"),
                "liquidation_name": match.group("liquidation_name").strip(),
            },
        ))

    match = _FR_INDIVIDUAL_SIGNING_PAIR_SHARED_ORIGIN.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.individual_signing_pair_shared_origin.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                place=match.group("place"), signing="Einzelunterschrift",
                extra={
                    "action": "signing_granted",
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country").strip(),
                },
            ))

    match = _DE_BRANCH_HISTORY_BATCH.search(leftover)
    if match:
        items_text = match.group("items")
        item_matches = list(_DE_BRANCH_HISTORY_ITEM.finditer(items_text))
        cursor = 0
        complete = bool(item_matches)
        for item in item_matches:
            if items_text[cursor:item.start()].strip():
                complete = False
                break
            cursor = item.end()
        complete = complete and not items_text[cursor:].strip()
        if complete:
            consume(match)
            rule_id = "de.text.branch_history_batch.v1"
            initial_place, initial_registry_id = _legacy_branch(match.group("initial"))
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "previous_branch_reference_completed",
                    "previous_place": initial_place,
                    "previous_registry_id": initial_registry_id,
                },
            ))
            for item in item_matches:
                previous_place, previous_registry_id = _legacy_branch(item.group("previous"))
                place = item.group("place").strip()
                payload = {
                    "action": (
                        "identifier_assigned"
                        if place.casefold() == previous_place.casefold()
                        else "seat_changed_and_identifier_assigned"
                    ),
                    "place": place,
                    "branch_uid": item.group("uid"),
                    "previous_place": previous_place,
                }
                if previous_registry_id:
                    payload["previous_registry_id"] = previous_registry_id
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", rule_id, payload,
                ))

    match = _FR_FOUNDATION_MEMBERS_BECOME_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_members_become_liquidators.v1"
        for index in (1, 2, 3):
            signing = "Kollektivunterschrift zu zweien" if index < 3 else None
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du conseil de fondation et liquidateur",
                signing=signing,
                extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du conseil de fondation",
                    "without_signing": index == 3,
                },
            ))

    match = _FR_INHERITANCE_ALL_SHARES_TRANSFER.search(leftover)
    if match and (
        _count(match.group("count")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.inheritance_all_shares_transfer.v1",
            match.group("buyer"), role="associé unique",
            extra={
                "action": "all_shares_received",
                "transfer_date": _iso_date(match.group("date")),
                "shares_received": _count(match.group("count")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "source_kind": "succession", "deceased": match.group("deceased").strip(),
                "estate_representative": match.group("representative").strip(),
                "without_signing": True,
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_RESULTING_HOLDINGS.search(leftover)
    if match and (
        match.group("nominal") == match.group("buyer_nominal")
        == match.group("remaining_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        consume(match)
        rule_id = "fr.persons.associate_transfer_resulting_holdings.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "shares_before": _count(match.group("transferred"))
                    + _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée",
                extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"), "new_associate": True,
                },
            ),
        ])

    match = _FR_MANAGER_SHARE_HOLDING_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_share_holding_supplement.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "share_holding_supplemented",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_SOLE_PROPRIETOR_ASSETS_AND_LIABILITIES_ASSUMED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_assets_liabilities_assumed.v1",
            {
                "action": "assumed", "source_kind": "sole_proprietor",
                "source": match.group("source").strip(), "source_uid": match.group("uid"),
                "source_place": match.group("place").strip(),
                "assets_transferred": True, "liabilities_transferred": True,
                "amounts_omitted_in_source": True,
            },
        ))

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_until.v1",
            {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _french_date(match.group("decision_date")),
                "until": _french_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_MANAGER_ELECTED_PRESIDENT_TRANSFER.search(leftover)
    if match and (
        _count(match.group("before")) == 2 * _count(match.group("transferred"))
        and match.group("transferred") == match.group("buyer_count")
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        consume(match)
        rule_id = "fr.persons.manager_elected_president_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                signing="Einzelunterschrift",
                extra={
                    **common, "action": "elected_president_and_shares_transferred",
                    "counterparty": buyer, "signing_continues": True,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("before"))
                    - _count(match.group("transferred")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    **common, "action": "shares_received_and_appointed_manager",
                    "counterparty": seller, "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(),
                    "place_canton": match.group("canton"), "new_associate": True,
                },
            ),
        ])

    match = _FR_ADMIN_PRESIDENT_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_and_member.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("place").strip()},
            ),
        ])

    match = _FR_ADMIN_MOVED_PRESIDENT_PAIR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_moved_president_pair.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="président",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_changed_and_appointed_president",
                    "domicile_changed": True, "country": match.group("country"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="administrateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("member_place").strip()},
            ),
        ])

    match = _FR_MANAGER_SPLIT_TRANSFER_TO_TWO.search(leftover)
    if match and (
        _count(match.group("transferred"))
        == _count(match.group("count1")) + _count(match.group("count2"))
        and _count(match.group("before"))
        == _count(match.group("transferred")) + _count(match.group("remaining"))
        and match.group("nominal") == match.group("remaining_nominal")
    ):
        consume(match)
        rule_id = "fr.persons.manager_split_transfer_to_two_managers.v1"
        seller = match.group("seller").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé-gérant",
            extra={
                **common, "action": "shares_transferred", "counterparties": buyers,
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
            },
        ))
        for index, buyer in enumerate(buyers, start=1):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant",
                signing=(
                    "Einzelunterschrift" if index == 1
                    else "Kollektivunterschrift zu zweien"
                ),
                extra={
                    **common, "action": "shares_received_and_appointed_manager",
                    "counterparty": seller,
                    "shares_received": _count(match.group(f"count{index}")),
                    "shares_count": _count(match.group(f"count{index}")),
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country").strip(), "new_associate": True,
                },
            ))

    match = _DE_PREVIOUS_IDENTIFIER_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_identifier_changed", "de.text.previous_identifier_fragment.v1",
            {
                "scope": "organization", "action": "changed",
                "from": match.group("from"), "to": _formatted_uid(org_uid),
            },
        ))

    match = _FR_FOUNDATION_EXECUTIVE_PRESIDENT_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_executive_president_correction.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").lower(),
                "signing_unchanged": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_LLC_CAPITAL_INCREASE_AND_TRANSFORMATION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.llc_capital_increase_and_transformation.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "share_capital", "action": "increased",
                    "to": match.group("capital"), "currency": "CHF",
                    "from_omitted_in_source": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "legal_form_changed", rule_id,
                {
                    "action": "transformed",
                    "from_legal_form": "Gesellschaft mit beschränkter Haftung",
                    "to_legal_form": "Aktiengesellschaft",
                    "transformation_plan_date": _iso_date(match.group("plan_date")),
                    "balance_sheet_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"), "currency": "CHF",
                    "shares_issued": _count(match.group("shares")),
                    "share_kind": "Namenaktien",
                    "share_nominal": match.group("share_nominal"),
                    "shareholder_count": 1,
                },
            ),
        ])

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
