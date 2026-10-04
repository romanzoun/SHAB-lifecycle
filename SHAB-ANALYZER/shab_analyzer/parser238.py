from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+au gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_EXIT_TRANSFER_TO_SOLE_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+),\s*(?P<seller2>[^,.;]+)\s+ne sont plus "
    r"associés ni gérants;\s*leurs pouvoirs sont radiés;\s*par suite de "
    r"cession de leurs\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+)\s+maintenant unique "
    r"associé-gérant pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_TWO_UNSIGNED_ASSOCIATES = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{2,3}),\s*nouvelle associée "
    r"pour\s+(?P<buyer_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal1>[\d'.]+),\s*et\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+(?P<buyer2>[^,.;]+),\s*d['’]"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal2>[\d'.]+)\.\s*Les associés\s+(?P=buyer1)\s+et\s+"
    r"(?P=buyer2)\s+n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER_INVENTORY = re.compile(
    r'^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss '
    r'Vermögensübertragungsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+'
    r'und Inventar per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+einen Teil '
    r'der Aktiven auf die\s+(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*'
    r'\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*nämlich den Betriebsteil\s+'
    r'["“](?P<business_unit>.+?)["”],\s*wonach die übertragenen Aktiven das '
    r'für den Betrieb des\s+(?P<business_name>.+?)\s+notwendige Warenlager im '
    r'Wert von CHF\s+(?P<assets>[\d\'.]+)\s+umfasst\.\s*Gegenleistung:\s*'
    r'(?P<consideration>keine)\.?$',
    re.I | re.DOTALL | re.UNICODE,
)
_FR_MIXED_SHAREHOLDING_AND_DOMICILE = re.compile(
    r"^(?P<count1>[\d']+)\s+parts sociales de CHF\s+(?P<nominal1>[\d'.]+)\s+"
    r"et\s+(?P<count2>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<nominal2>[\d'.]+),\s*détenues par\s+(?P<name>[^,.;]+),\s*qui est "
    r"maintenant à\s+(?P<place>[^().,;]+)\s*\((?P<country>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_MOVED_TWO_DIRECTORS_SIGNING_GRANTED = re.compile(
    r"^(?P<moved_name>[^,.;]+)\s+est maintenant au\s+"
    r"(?P<moved_place>[^,.;]+)\.\s*Signature collective à deux est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*tous deux directeurs\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_VICE_PRESIDENT_AND_NEW_MEMBER = re.compile(
    r"^Le membre du comité\s+(?P<vice_president>[^,.;]+),\s*nommé "
    r"vice-président,\s*signe désormais collectivement à deux sans autre "
    r"restriction\.\s*(?P<member>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est membre du comité avec signature collective à deux,\s*avec la "
    r"présidente ou le vice-président\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_AND_MANAGER_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*l['’]associé-gérant\s+(?P<name1>[^,.;]+)\s+et le "
    r"gérant\s+(?P<name2>[^,.;]+),\s*lesquels continuent à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_NOMINATIVE_SHARE_STRUCTURE_RECTIFICATION = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d']+)\)\s+est rectifiée en ce sens que le capital-actions "
    r"est divisé en\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*avec restrictions quant à la transmissibilité "
    r"selon statuts\s*\(et non\s+(?P<previous_count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<previous_nominal>[\d'.]+),\s*avec "
    r"restrictions quant à la transmissibilité selon statuts,\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*du\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^(),.;]+)\s*\((?P<country>[^)]+)\),\s*nouvel associé-gérant "
    r"président avec signature individuelle,\s*titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+a maintenant\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_NO_THIRD_PARTY_LIABILITIES = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*la société "
    r"a transféré des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et aucun passif "
    r"envers les tiers à\s+(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_PRICE_ADJUSTMENT_MAY_CHANGE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+),\s*welche gemäss "
    r"vertraglicher Preisanpassungsklausel angepasst werden kann\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]administrateur\s+(?P<previous_name>[^,.;]+)\s+se nomme en réalité\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER_FOR_SHARES = re.compile(
    r"^Vermögensübertragung:\s*Das Einzelunternehmen überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:?\s*(?P<shares>[\d']+)\s+Stammanteile zu je CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+der\s+(?P<issuer>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_DIRECTOR_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*et le "
    r"directeur\s+(?P<director>[^,.;]+),\s*lesquels continuent à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_LIQUIDATOR_AND_RESTRICTION_REMOVED_FRAGMENT = re.compile(
    r"^par\s+(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*liquidatrice\.\s*Les\s+(?P<count>[\d']+)\s+actions "
    r"nominatives de CHF\s+(?P<nominal>[\d'.]+),\s*formant l['’]entier du "
    r"capital-actions,\s*ne sont plus restreintes quant à la transmissibilité\s*"
    r"\((?P<legal_basis>art\.\s*685a,\s*al\.\s*3\s*CO)\)\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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


def extract_parser238_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 238."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_SIMPLE_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before - transferred == remaining
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.simple_associate_share_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé et gérant", extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": buyer_count,
                    },
                ),
            ], ""

    match = _FR_TWO_MANAGERS_EXIT_TRANSFER_TO_SOLE_MANAGER.fullmatch(leftover)
    if match and match.group("nominal") == match.group("buyer_nominal"):
        rule_id = "fr.persons.two_managers_exit_transfer_to_sole_manager.v1"
        buyer = match.group("buyer").strip()
        common = {
            "currency": "CHF", "share_nominal": match.group("nominal"),
            "shares_transferred": _count(match.group("transferred")),
        }
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group),
                role="associé-gérant", extra={
                    **common, "action": "removed_and_signing_revoked",
                    "counterparty": buyer,
                },
            )
            for group in ("seller1", "seller2")
        ]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, role="associé-gérant unique",
            signing="Einzelunterschrift", extra={
                **common, "action": "became_sole_associate_manager",
                "shares_count": _count(match.group("buyer_count")),
                "counterparties": [
                    match.group("seller1").strip(), match.group("seller2").strip(),
                ],
            },
        ))
        return events, ""

    match = _FR_MANAGER_TRANSFER_TO_TWO_UNSIGNED_ASSOCIATES.fullmatch(leftover)
    if match:
        counts_match = all(
            _count(match.group(f"count{index}"))
            == _count(match.group(f"buyer_count{index}"))
            for index in (1, 2)
        )
        nominals = {
            match.group(f"{prefix}{index}")
            for index in (1, 2)
            for prefix in ("nominal", "buyer_nominal")
        }
        if counts_match and len(nominals) == 1:
            rule_id = "fr.persons.manager_transfer_to_two_unsigned_associates.v1"
            seller = match.group("seller").strip()
            buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
            events = [_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    "action": "shares_transferred", "currency": "CHF",
                    "share_nominal": match.group("nominal1"),
                    "shares_transferred": sum(
                        _count(match.group(f"count{index}")) for index in (1, 2)
                    ),
                    "counterparties": buyers,
                },
            )]
            for index, gendered_role in ((1, "associée"), (2, "associé")):
                count = _count(match.group(f"count{index}"))
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"buyer{index}"),
                    place=match.group(f"place{index}"), role=gendered_role, extra={
                        "action": "appointed_and_shares_received", "currency": "CHF",
                        "share_nominal": match.group(f"nominal{index}"),
                        "shares_received": count, "shares_count": count,
                        "origin": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                        "without_signature": True, "counterparty": seller,
                    },
                ))
            return events, ""

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER_INVENTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_asset_transfer_inventory.v1", {
                "source_kind": "Gesellschaft",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": None,
                "currency": "CHF", "asset_scope": "part",
                "business_unit": match.group("business_unit").strip(),
                "business_name": match.group("business_name").strip(),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "none",
            },
        )], ""

    match = _FR_MIXED_SHAREHOLDING_AND_DOMICILE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.mixed_shareholding_and_domicile.v1",
            match.group("name"), place=match.group("place"), role="associé", extra={
                "action": "shareholding_and_domicile_changed", "domicile_changed": True,
                "country": match.group("country").strip(), "currency": "CHF",
                "shareholdings": [
                    {
                        "shares_count": _count(match.group(f"count{index}")),
                        "share_nominal": match.group(f"nominal{index}"),
                    }
                    for index in (1, 2)
                ],
            },
        )], ""

    match = _FR_PERSON_MOVED_TWO_DIRECTORS_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.person_moved_two_directors_signing_granted.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("moved_name"),
            place=match.group("moved_place"), extra={"action": "domicile_changed"},
        )]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="directeur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_and_signing_granted",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))
        return events, ""

    match = _FR_COMMITTEE_VICE_PRESIDENT_AND_NEW_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_vice_president_and_new_member.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice_president"),
                role="membre du comité et vice-président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_vice_president_and_signing_changed",
                    "signing_restriction": None,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "signing_with": "présidente ou vice-président",
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_MANAGER_AND_MANAGER_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_manager_and_manager_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="associé-gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
        ], ""

    match = _FR_NOMINATIVE_SHARE_STRUCTURE_RECTIFICATION.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        previous_count = _count(match.group("previous_count"))
        nominal = _count(match.group("nominal"))
        previous_nominal = _count(match.group("previous_nominal"))
        if count * nominal == previous_count * previous_nominal:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.nominative_share_structure_rectification.v1", {
                    "kind": "share_structure", "action": "publication_corrected",
                    "currency": "CHF", "shares_count": count,
                    "share_nominal": match.group("nominal"),
                    "share_kind": "actions nominatives",
                    "previous_shares_count": previous_count,
                    "previous_share_nominal": match.group("previous_nominal"),
                    "previous_transfer_restricted": True,
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_ref": match.group("notice_ref"),
                },
            )], ""

    match = _FR_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before - transferred == remaining
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.transfer_to_new_manager_president.v2"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant président", signing="Einzelunterschrift", extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": buyer_count,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country").strip(),
                    },
                ),
            ], ""

    match = _FR_ASSET_TRANSFER_NO_THIRD_PARTY_LIABILITIES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_no_third_party_liabilities.v1", {
                "agreement_date": _french_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": "0",
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_PRICE_ADJUSTMENT_MAY_CHANGE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_price_adjustment_may_change.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": None,
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "price_adjustment_clause": True,
                "price_adjustment_status": "may_change",
            },
        )], ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected_reality.v1",
            match.group("name"), role="administrateur", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER_FOR_SHARES.fullmatch(leftover)
    if match and match.group("recipient").strip() == match.group("issuer").strip():
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_asset_transfer_for_shares.v1", {
                "source_kind": "Einzelunternehmen",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": None,
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": {
                    "shares_count": _count(match.group("shares")),
                    "share_nominal": match.group("nominal"),
                    "issuer": match.group("issuer").strip(),
                },
                "consideration_kind": "llc_interests",
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_DIRECTOR_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_and_director_individual.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="administrateur président", signing="Einzelunterschrift", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                role="directeur", signing="Einzelunterschrift", extra={
                    "action": "signing_confirmed", "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_CORPORATE_LIQUIDATOR_AND_RESTRICTION_REMOVED_FRAGMENT.fullmatch(leftover)
    if match:
        rule_id = "fr.text.corporate_liquidator_and_restriction_removed_fragment.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                uid=match.group("uid"), place=match.group("place"),
                role="liquidatrice", extra={"action": "appointed_liquidator"},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "share_kind": "actions nominatives", "entire_share_capital": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
        ], ""

    return [], leftover
