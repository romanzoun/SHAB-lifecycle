from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_CONVERSION_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) "
    r"eine Bestimmung über Wandlungskapital nach (?P<legal_basis>Art\.\s*11 Abs\.\s*1 "
    r"Bst\.\s*b BankG und Art\.\s*13 BankG) gemäss näherer Umschreibung in den "
    r"Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_TO_COLLECTIVE = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que "
    r"(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*signe collectivement à deux "
    r"et non pas individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_IDENTIFIER_REPLACED = re.compile(
    r"^(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[bisher:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_id>CH-[\d.-]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SELLER_TRANSFERS_EQUAL_SHARES_TO_TWO_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+) détient désormais (?P<seller_count>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) par suite de cession de (?P<transferred_each>[\d']+) "
    r"parts de CHF (?P=nominal) à (?P<buyer1>[^,.;]+),\s*associé-gérant désormais "
    r"pour (?P<buyer1_count>[\d']+) parts de CHF (?P<buyer1_nominal>[\d'.]+) et à "
    r"(?P<buyer2>[^,.;]+),\s*associé-gérant et président désormais pour "
    r"(?P<buyer2_count>[\d']+) parts de CHF (?P<buyer2_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_AND_SHARE_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+),\s*qui est maintenant à (?P<seller_place>[^,.;]+),\s*"
    r"cède (?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à (?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à (?P<buyer_place>[^,.;]+),\s*"
    r"nouvelle associée,\s*avec (?P<buyer_count>[\d']+) part(?:s)? de CHF "
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller) reste titulaire de "
    r"(?P<remaining>[\d']+) parts de CHF (?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*(?P<seller_role>associé-gérant président),\s*"
    r"cède (?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à la gérante (?P<buyer>[^,.;]+),\s*nouvelle associée "
    r"avec (?P<buyer_count>[\d']+) parts de CHF (?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller) reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_IDENTIFIER_CORRECTED_AND_RENAMED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_ref>[\d/]+)\) "
    r"est rectifiée en ce sens que le numéro d['’]identification de l['’]organe de "
    r"révision (?P<previous_name>.+?) est le\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\) "
    r"\(et non le\s*\((?P<incorrect_uid>CHE-\d{3}\.\d{3}\.\d{3})\) comme publié\)\.\s*"
    r"L['’]organe de révision (?P=previous_name) a modifié sa raison de commerce en "
    r"(?P<name>.+?)\s*\((?P=uid)\)\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_MANAGER_TRANSFER_AND_BUYER_APPOINTED_MANAGER = re.compile(
    r"^L['’]associée-gérante (?P<seller>[^,.;]+) cède "
    r"(?P<transferred>[\d']+) de ses (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à l['’]associé (?P<buyer>[^,.;]+),\s*"
    r"désormais titulaire de (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+),\s*lequel est élu gérant\s*"
    r"(?P=seller) reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SUPPLEMENT_REFERENCE_PREFIX = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\) est complétée en ce sens que\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_RESTRICTION_REMOVED = re.compile(
    r"^(?P<name>[^,.;]+) continue à engager la société par sa procuration "
    r"collective à deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_AND_PROXY_GRANTED = re.compile(
    r"^Signature individuelle est conférée à (?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"(?P<role1>directeur),\s*et procuration individuelle est conférée à "
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*tous deux à (?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MIXED_REMOVED_CHANGED_AND_ADDED_PERSONS = re.compile(
    r"^Gelöschte Personen:\s*(?P<removed1>[^,;]+),\s*(?P<removed_role1>[^,;]+),\s*"
    r"(?P<removed_sign1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<removed2>[^,;]+),\s*(?P<removed_role2>[^,;]+),\s*"
    r"(?P<removed_sign2>Kollektivunterschrift zu zweien)\.\s*"
    r"Eingetragene Personen geändert:\s*(?P<changed>[^,;]+),\s*"
    r"(?P<changed_sign>Kollektivunterschrift zu zweien),\s*neu in "
    r"(?P<changed_place>[^,.;]+)\.\s*Neu eingetragene Person:\s*"
    r"(?P<added>[^,;]+),\s*(?P<nationality>[^,;]+),\s*in "
    r"(?P<added_place>[^,;(]+)\s*\((?P<country>[A-Z]{2,3})\),\s*"
    r"(?P<added_role>[^,;]+),\s*(?P<added_sign>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SEAT_TRANSFERRED = re.compile(
    r"^La succursale de (?P<from_place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\) a transféré son siège à "
    r"(?P<to_place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_GRANTED = re.compile(
    r"^Signature individuelle est conférée à (?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE_CHANGED = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Gegenstand des Unternehmens sind "
    r"(?P<purpose>.+?)\.\s*\[bisher:\s*Gegenstand des Unternehmens sind "
    r"(?P<previous_purpose>.+?)\.?\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_BY_JUDGMENT = re.compile(
    r"^Mit Urteil vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) hat "
    r"(?P<authority>.+?),\s*in (?P<authority_place>[^,.;]+),\s*die definitive "
    r"Nachlassstundung bis zum (?P<until>\d{2}\.\d{2}\.\d{4}) verlängert\.?$",
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser139_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 139."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_CONVERSION_CAPITAL_CLAUSE_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conversion_capital_clause_introduced.v1",
            {
                "kind": "conversion_capital_clause", "action": "introduced",
                "decision_date": _iso_date(match.group("decision_date")),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_SIGNING_CORRECTED_TO_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_corrected_to_collective.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "corrected", "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_BRANCH_IDENTIFIER_REPLACED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_identifier_replaced.v1",
            {
                "action": "identifier_replaced", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_place": match.group("previous_place").strip(),
                "previous_branch_id": match.group("previous_id"),
            },
        ))

    match = _FR_SELLER_TRANSFERS_EQUAL_SHARES_TO_TWO_MANAGERS.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer1_nominal"),
        match.group("buyer2_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.equal_share_transfers_to_two_managers.v1"
        seller = match.group("seller").strip()
        transferred_each = _count(match.group("transferred_each"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparties": [
                        match.group("buyer1").strip(), match.group("buyer2").strip(),
                    ],
                    "shares_transferred_each": transferred_each,
                    "shares_transferred": transferred_each * 2,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer1"),
                role="associé-gérant",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred_each,
                    "shares_count": _count(match.group("buyer1_count")),
                    "share_nominal": match.group("buyer1_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer2"),
                role="associé-gérant et président",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred_each,
                    "shares_count": _count(match.group("buyer2_count")),
                    "share_nominal": match.group("buyer2_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_DOMICILE_AND_SHARE_TRANSFER_TO_ORGANIZATION.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.domicile_and_share_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé",
                extra={
                    "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer, "counterparty_uid": match.group("buyer_uid"),
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                uid=match.group("buyer_uid"), role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "new_associate": True, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_MANAGER.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.manager_president_transfer_to_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role=match.group("seller_role"),
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associée-gérante",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "new_associate": True, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_AUDITOR_IDENTIFIER_CORRECTED_AND_RENAMED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.auditor_identifier_corrected_and_renamed.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {
                    "kind": "auditor_identifier", "action": "corrected",
                    "auditor_name": match.group("previous_name").strip(),
                    "to": match.group("uid"), "from": match.group("incorrect_uid"),
                    **reference,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                uid=match.group("uid"), role="organe de révision",
                extra={
                    "action": "trade_name_changed",
                    "previous_name": match.group("previous_name").strip(),
                    **reference,
                },
            ),
        ])

    match = _FR_FEMALE_MANAGER_TRANSFER_AND_BUYER_APPOINTED_MANAGER.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.manager_transfer_and_buyer_appointed_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée-gérante",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "shares_received_and_appointed_manager",
                    "counterparty": seller, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_SUPPLEMENT_REFERENCE_PREFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.supplement_reference_prefix.v1",
            {
                "kind": "registry_entry", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_PROXY_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.proxy_restriction_removed.v1",
            match.group("name"), signing="Kollektivprokura zu zweien",
            extra={"action": "restriction_removed", "signing_continues": True},
        ))

    match = _FR_INDIVIDUAL_SIGNING_AND_PROXY_GRANTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.individual_signing_and_proxy_granted.v1"
        place = match.group("place")
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"), place=place,
                role=match.group("role1"), signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"), place=place,
                signing="Einzelprokura",
                extra={
                    "action": "proxy_granted", "origin": match.group("origin2").strip(),
                },
            ),
        ])

    match = _DE_MIXED_REMOVED_CHANGED_AND_ADDED_PERSONS.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.removed_changed_and_added_mixed_language.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed1"),
                role=match.group("removed_role1"), signing=match.group("removed_sign1"),
                extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed2"),
                role=match.group("removed_role2"), signing=match.group("removed_sign2"),
                extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("changed"),
                place=match.group("changed_place"), signing=match.group("changed_sign"),
                extra={"action": "domicile_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("added"),
                place=match.group("added_place"), role=match.group("added_role"),
                signing=match.group("added_sign"),
                extra={
                    "action": "appointed", "nationality": match.group("nationality").strip(),
                    "country": match.group("country"),
                },
            ),
        ])

    match = _FR_BRANCH_SEAT_TRANSFERRED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_seat_transferred.v1",
            {
                "action": "seat_transferred", "branch_uid": match.group("uid"),
                "from": match.group("from_place").strip(),
                "to": match.group("to_place").strip(),
            },
        ))

    match = _FR_INDIVIDUAL_SIGNING_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_signing_granted.v1",
            match.group("name"), signing="Einzelunterschrift",
            extra={"action": "signing_granted"},
        ))

    match = _DE_BRANCH_PURPOSE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "de.text.branch_purpose_changed.v1",
            {
                "scope": "branch", "from": match.group("previous_purpose").strip(),
                "to": match.group("purpose").strip(),
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_BY_JUDGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_by_judgment.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
                "authority_place": match.group("authority_place").strip(),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
