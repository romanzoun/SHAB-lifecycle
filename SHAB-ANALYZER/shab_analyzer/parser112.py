from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PERSON_NAME_COMPONENTS_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]associé et gérant porte les noms\s+(?P<surname>.+?)\s+"
    r"(?:et|est) les prénoms\s+(?P<given_names>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé\s+(?P<name>.+?)\s+est nommé gérant président\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_CLOSURE_SUSPENDED = re.compile(
    r"^Par décision du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*la clôture de la faillite est suspendue\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATION_ADDRESS_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]adresse de liquidation est\s+(?P<address>.+?),\s*et non pas\s*"
    r"\((?P<previous_address>.+?)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_APPOINTED_INDIVIDUAL = re.compile(
    r"^(?P<name>[^,.;]+),\s*nommé administrateur unique,\s*"
    r"signe désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Das Einzelunternehmen überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s*"
    r"\((?P<liabilities_kind>Fremdkapital)\)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:?\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_ASSET_TRANSFER_UID_BEFORE_PLACE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"auf die\s+(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^.]+)\.\s*Gegenleistung:?\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_TRANSFER_TO_DIRECTOR = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé et directeur pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ASSOCIATE_MANAGERS_TRANSFER_WITHOUT_SIGNATURE = re.compile(
    r"^Jusqu['’]ici chacun titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*les associés-gérants\s+"
    r"(?P<seller1>[^,.;]+),\s*(?P<seller2>[^,.;]+)\s+et\s+"
    r"(?P<seller3>[^,.;]+)\s+détiennent chacun\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+"
    r"chacun à\s+(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"qui n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_HEAD_OFFICE_ID_AND_SEAT_CHANGED = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<head_office_uid>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\[finora:\s*Numero dell['’]identificazione della sede principale:\s*"
    r"(?P<previous_registry_id>CH-[\d.]+-\d)\]\.\s*"
    r"Nuova sede principale:\s*(?P<new_head_office>[^\[]+?)\s*"
    r"\[finora:\s*(?P<previous_head_office>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_TWO_MANAGERS = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*lequel est élu président,\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+),\s*par\s+(?P<buyer_count1>[\d']+)\s+parts à\s+"
    r"(?P<buyer1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et par\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts à\s+(?P<buyer2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+?)(?:\s*\((?P<canton2>[A-Z]{2})\))?,\s*"
    r"tous deux de\s+(?P<origin>[^,.;]+),\s*nouveaux associés avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérants\s*;\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_ROLE_CORRECTION_AND_SECRETARY_APPOINTMENT = re.compile(
    r"^(?P<name1>[^.;]+?)\s+n['’]est pas secrétaire;\s*"
    r"(?:il\s+)?est vice-président\.\s*(?P<name2>[^.;]+?)\s+"
    r"est élue secrétaire\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_REMOVED_LEGACY_ID = re.compile(
    r"^Succursale:\s*\[biffé:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Par arrêt du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé l['’]effet suspensif au recours interjeté le\s+"
    r"(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+contre la décision du faillite du\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\((?P<legal_basis>art\.\s*159,\s*al\.\s*2 ORC)\)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+signe collectivement à deux\s+"
    r"\(et non individuellement comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_CLOSED_AND_DELETED_EX_OFFICIO = re.compile(
    r"^La procédure de faillite étant clôturée par décision du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+du\s+(?P<authority>.+?),\s*"
    r"cette entité juridique est radiée d['’]office conformément aux dispositions de "
    r"l['’](?P<legal_basis>art\.\s*159,\s*al\.\s*5,\s*lit\.\s*b,\s*ORC)\.?$",
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
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser112_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 112."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PERSON_NAME_COMPONENTS_CORRECTED.search(leftover)
    if match:
        consume(match)
        surname = match.group("surname").strip()
        given_names = match.group("given_names").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_components_corrected.v1",
            f"{surname} {given_names}", role="associé-gérant",
            extra={
                "action": "name_corrected", "surname": surname,
                "given_names": given_names, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president.v1",
            match.group("name"), role="gérant président",
            extra={"action": "appointed", "previous_role": "associé"},
        ))

    match = _FR_BANKRUPTCY_CLOSURE_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_closure_suspended.v1",
            {
                "kind": "bankruptcy_closure_suspended",
                "decision_date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_LIQUIDATION_ADDRESS_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.liquidation_address_corrected.v1",
            {
                "scope": "liquidation", "action": "corrected",
                "address": match.group("address").strip(),
                "previous_address": match.group("previous_address").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_SOLE_ADMINISTRATOR_APPOINTED_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_appointed_individual.v1",
            match.group("name"), role="administrateur unique",
            signing="Einzelunterschrift",
            extra={"action": "appointed", "signing_action": "changed"},
        ))

    match = _DE_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.sole_proprietor_asset_transfer.v1",
            {
                "source_kind": "sole_proprietor",
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "currency": "CHF",
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        ))

    match = _FR_ASSOCIATE_MANAGER_TRANSFER_TO_DIRECTOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_manager_transfer_to_director.v1"
        transferred = _count(match.group("transferred"))
        common = {
            "shares_transferred": transferred,
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-directeur",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_count": _count(match.group("buyer_count")),
                    "heimat": match.group("origin").strip(), "new_associate": True,
                },
            ),
        ])

    match = _FR_THREE_ASSOCIATE_MANAGERS_TRANSFER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers_transfer_to_associate_without_signature.v1"
        buyer = match.group("buyer").strip()
        common = {
            "shares_before": _count(match.group("before")),
            "shares_transferred": _count(match.group("transferred")),
            "shares_count": _count(match.group("remaining")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant",
                extra={**common, "action": "shares_transferred", "counterparty": buyer},
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associée",
            extra={
                "action": "shares_received", "new_associate": True,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                "heimat": match.group("origin").strip(), "without_signature": True,
            },
        ))

    match = _IT_BRANCH_HEAD_OFFICE_ID_AND_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.branch_head_office_id_and_seat_changed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", rule_id,
                {
                    "scope": "head_office", "action": "changed",
                    "to": match.group("head_office_uid"),
                    "from": match.group("previous_registry_id"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "head_office_changed",
                    "head_office": match.group("new_head_office").strip(),
                    "previous_head_office": match.group("previous_head_office").strip(),
                    "head_office_uid": match.group("head_office_uid"),
                },
            ),
        ])

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_president_transfer_to_two_managers.v1"
        seller = match.group("seller").strip()
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé-gérant président",
            extra={
                "action": "appointed_president_and_shares_transferred",
                "shares_before": _count(match.group("before")),
                "shares_transferred": _count(match.group("transferred")),
                "shares_count": _count(match.group("remaining")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "counterparties": buyers,
            },
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé-gérant",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller, "new_associate": True,
                    "shares_received": _count(match.group(f"buyer_count{index}")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "heimat": match.group("origin").strip(),
                    **(
                        {"place_canton": match.group("canton2")}
                        if index == 2 and match.group("canton2") else {}
                    ),
                },
            ))

    match = _FR_BOARD_ROLE_CORRECTION_AND_SECRETARY_APPOINTMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_role_correction_and_secretary_appointment.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="vice-président",
                extra={
                    "action": "role_corrected", "previous_role": "secrétaire",
                    "previous_role_invalid": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"), role="secrétaire",
                extra={"action": "appointed"},
            ),
        ])

    match = _FR_BRANCH_REMOVED_LEGACY_ID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_removed_legacy_id.v1",
            {
                "action": "removed", "place": match.group("place").strip(),
                "legacy_registry_id": match.group("registry_id"),
            },
        ))

    match = _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_appeal_suspensive_effect.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "decision_date": _iso_date(match.group("decision_date")),
                "appeal_date": _iso_date(match.group("appeal_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _DE_COMPANY_ASSET_TRANSFER_UID_BEFORE_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.company_asset_transfer_uid_before_place.v1",
            {
                "source_kind": "company", "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "currency": "CHF",
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        ))

    match = _FR_SIGNING_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_corrected_with_notice.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_BANKRUPTCY_CLOSED_AND_DELETED_EX_OFFICIO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.bankruptcy_closed_and_deleted_ex_officio.v1"
        common = {
            "date": _iso_date(match.group("date")),
            "authority": match.group("authority").strip(),
            "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {"kind": "bankruptcy_closed", **common},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", rule_id,
                {"action": "deleted_ex_officio", "reason": "bankruptcy_closed", **common},
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
