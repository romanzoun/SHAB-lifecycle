from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_MUNICIPAL_MERGER_SEAT = re.compile(
    r"^Par suite de fusion de communes,\s*le siège devient:\s*(?P<seat>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’](?P<role>associé et gérant) de la société est\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^()]+?)\)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_EFFECTIVE_AFTER_RESTITUTION_WITHDRAWAL = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a pris acte du retrait de la requête de restitution "
    r"de délai,\s*révoqué l['’]effet suspensif et dit que le prononcé de faillite "
    r"du\s+(?P<bankruptcy_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"prend effet le\s+(?P<effective_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"à\s+(?P<hour>\d{1,2})h(?P<minute>\d{2})\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_TWO_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président,\s*"
    r"lequel continue à signer individuellement,\s*"
    r"(?P<name2>[^,;]+),\s*de\s+(?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,;]+),\s*(?P<country2>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name3>[^,;]+),\s*de\s+(?P<origin3>[^,;]+),\s*à\s+"
    r"(?P<place3>[^,;]+),\s*(?P<country3>[A-Z]{1,3}),\s*tous deux "
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_MORATORIUM_EXTENSION_REPLACED = re.compile(
    r"^\[gestrichen:\s*Mit Entscheid des\s+(?P<previous_authority>.+?),\s*vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine "
    r"Verlängerung der Nachlassstundung von\s+(?P<previous_duration>\w+)\s+"
    r"Monaten bis zum\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+"
    r"bewilligt\.\]\.?\s*Mit Entscheid der\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine Verlängerung "
    r"der Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ORGANIZATIONS_TRANSFER_SHARES = re.compile(
    r"^(?P<seller1>.+?)\s+et\s+(?P<seller2>.+?),\s*qui ne sont plus "
    r"associées,\s*cèdent respectivement leurs\s+(?P<count1>[\d']+)\s+et\s+"
    r"(?P<count2>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à "
    r"l['’]associée\s+(?P<buyer>.+?),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSLATIONS_AND_MERGER_CLAUSES_REMOVED = re.compile(
    r"^Les versions\s+(?P<language1>[^ ]+)\s+et\s+(?P<language2>[^ ]+)\s+de la "
    r"raison sociale sont radiées\.\s*Raison sociale:\s*(?P<name>.+?)\.\s*"
    r"Les clauses statutaires relatives aux fusions du\s+"
    r"(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et du\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+sont abrogées\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_SURNAME_CHANGED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,;]+),\s*"
    r"(?P<role>[^,;]+),\s*(?P<signing>[^,;]+),\s*nun\s+"
    r"(?P<name>[^,;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_PREVIOUS_REGISTRY_IDS_COMPLETED = re.compile(
    r"^Infolge Systemfehler wurde beim bisher Text die alte Firmennummer der "
    r"Gesellschafterin und der Revisionsstelle nicht aufgeführt\.\s*Korrekt wäre\s+"
    r"\[bisher:\s*(?P<associate>.+?)\s*\((?P<associate_registry>CH-[\d.]+-\d)\)\]\s+"
    r"und\s+\[bisher:\s*(?P<auditor>.+?)\s*"
    r"\((?P<auditor_registry>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGER_SHARE_TRANSFERS = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+détient désormais\s+(?P<remaining1>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal1>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred1>[\d']+)\s+parts de CHF\s+(?P<transfer_nominal1>[\d'.]+)\s+"
    r"à\s+(?P<buyer1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*nouvel associé-gérant pour\s+"
    r"(?P<buyer_count1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+)\s+"
    r"avec signature collective à deux\.\s*"
    r"(?P<seller2>[^,.;]+)\s+détient désormais\s+(?P<remaining2>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal2>[\d'.]+)\s+par suite de cession d['’]une "
    r"part de CHF\s+(?P<transfer_nominal2>[\d'.]+)\s+à\s+(?P<buyer2>[^,.;]+),\s*"
    r"de\s+(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*nouvelle associée-gérante pour une part de "
    r"CHF\s+(?P<buyer_nominal2>[\d'.]+)\s+avec signature collective à deux\.\s*"
    r"(?P<seller3>[^,.;]+)\s+détient désormais\s+(?P<remaining3>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal3>[\d'.]+)\s+par suite de cession d['’]une "
    r"part de CHF\s+(?P<transfer_nominal3>[\d'.]+)\s+à\s+(?P<buyer3>[^,.;]+),\s*"
    r"de\s+(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{2,3}),\s*nouvel associé-gérant pour une part de "
    r"CHF\s+(?P<buyer_nominal3>[\d'.]+)\s+avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_MOVED_AND_SIGNING_CHANGED = re.compile(
    r"^(?P<name>[^,;]+),\s*maintenant domicilié(?:e)? à\s+"
    r"(?P<place>[^,;]+),\s*(?P<country>[A-Z]{1,3})\s+signe désormais "
    r"collectivement à deux;\s*ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_TWO_CONTRACT_DATES = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<contract_date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<contract_date2>\d{2}\.\d{2}\.\d{4})\s+et inventaire du\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers pour CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*(?P<shares>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de\s+(?P<consideration_issuer>.+?)\s+ainsi "
    r"qu['’]une créance de CHF\s+(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_CAPITAL_REDUCTION_AND_SIMULTANEOUS_INCREASE = re.compile(
    r"^Riduzione del capitale azionario di CHF\s+(?P<reduction>[\d'.]+)\s+"
    r"mediante annullamento di\s+(?P<cancelled_count>[\d']+)\s+azioni "
    r"nominative da CHF\s+(?P<cancelled_nominal>[\d'.]+),\s*per eliminare "
    r"un['’]eccedenza passiva accertata nel bilancio\.\s*Il capitale azionario "
    r"è stato simultaneamente aumentato mediante l['’]emissione di\s+"
    r"(?P<issued_count>[\d']+)\s+azioni nominative da CHF\s+"
    r"(?P<issued_nominal>[\d'.]+),\s*interamente liberate\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PRESIDENT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N°|n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"le président du conseil est\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^()]+?)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"\(Fremdkapital\)\s+auf den\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CASH_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<contract_date>\d{2}\.\d{2}\.\d{4})\s+et inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les "
    r"tiers pour CHF\s+(?P<liabilities>[\d'.]+),\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
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
_GERMAN_NUMBERS = {
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


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    token = raw.strip().lower()
    return int(token) if token.isdigit() else _GERMAN_NUMBERS.get(token)


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
        role=role.strip() if role else None,
        signing=signing.strip() if signing else None,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser217_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 217."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MUNICIPAL_MERGER_SEAT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.municipal_merger_seat.v1", {
                "action": "changed", "reason": "municipal_merger",
                "to": match.group("seat").strip(),
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_name_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_BANKRUPTCY_EFFECTIVE_AFTER_RESTITUTION_WITHDRAWAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "fr.text.bankruptcy_effective_after_restitution_withdrawal.v1", {
                "kind": "bankruptcy_opening_effective",
                "action": "effective_after_suspensive_effect_revoked",
                "decision_date": _french_date(match.group("decision_date")),
                "bankruptcy_date": _french_date(match.group("bankruptcy_date")),
                "effective_date": _french_date(match.group("effective_date")),
                "effective_time": f"{int(match.group('hour')):02d}:{match.group('minute')}",
                "authority": match.group("authority").strip(),
                "restitution_request_withdrawn": True,
                "suspensive_effect_revoked": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_TWO_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_and_two_collective.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift", extra={
                "action": "appointed_president", "signing_continues": True,
            },
        )]
        for index in (2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            ))
        return events, ""

    match = _DE_MORATORIUM_EXTENSION_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.moratorium_extension_replaced.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_entry_deleted": True,
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_duration_months": _duration_months(
                    match.group("previous_duration")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_TWO_ORGANIZATIONS_TRANSFER_SHARES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_organizations_transfer_shares.v1"
        buyer = match.group("buyer").strip()
        counts = (_count(match.group("count1")), _count(match.group("count2")))
        events = []
        for index, count in enumerate(counts, 1):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"seller{index}"),
                role="associée", extra={
                    "action": "removed_after_share_transfer", "counterparty": buyer,
                    "shares_transferred": count, "shares_count": 0,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, role="associée", extra={
                "action": "shares_received", "existing_associate": True,
                "counterparties": [
                    match.group("seller1").strip(), match.group("seller2").strip()
                ],
                "shares_received": sum(counts),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        ))
        return events, ""

    match = _FR_TRANSLATIONS_AND_MERGER_CLAUSES_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.translations_and_merger_clauses_removed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "action": "translations_removed",
                    "removed_languages": [
                        match.group("language1").lower(),
                        match.group("language2").lower(),
                    ],
                    "name": match.group("name").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id, {
                    "action": "merger_clauses_repealed",
                    "merger_dates": [
                        _iso_date(match.group("date1")),
                        _iso_date(match.group("date2")),
                    ],
                },
            ),
        ], ""

    match = _DE_PERSON_SURNAME_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.surname_changed.v1", match.group("name"),
            role=match.group("role"), signing=match.group("signing"), extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _DE_TWO_PREVIOUS_REGISTRY_IDS_COMPLETED.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_previous_registry_ids_completed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("associate"),
                role="Gesellschafterin", extra={
                    "action": "previous_registry_id_completed",
                    "previous_registry_id": match.group("associate_registry"),
                    "organization": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("auditor"),
                role="Revisionsstelle", extra={
                    "action": "previous_registry_id_completed",
                    "previous_registry_id": match.group("auditor_registry"),
                    "organization": True,
                },
            ),
        ], ""

    match = _FR_THREE_MANAGER_SHARE_TRANSFERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_manager_share_transfers.v1"
        events: list[Event] = []
        for index in (1, 2, 3):
            transferred = (
                _count(match.group("transferred1")) if index == 1 else 1
            )
            seller = match.group(f"seller{index}").strip()
            buyer = match.group(f"buyer{index}").strip()
            remaining = _count(match.group(f"remaining{index}"))
            buyer_count = (
                _count(match.group("buyer_count1")) if index == 1 else 1
            )
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": remaining + transferred,
                        "shares_transferred": transferred,
                        "shares_count": remaining,
                        "share_nominal": match.group(f"nominal{index}"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group(f"place{index}"), role="associé-gérant",
                    signing="Kollektivunterschrift zu zweien", extra={
                        "action": "shares_received_and_appointed_manager",
                        "counterparty": seller, "new_associate": True,
                        "origin": match.group(f"origin{index}").strip(),
                        "country": (
                            match.group(f"country{index}") if index > 1 else None
                        ),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "share_nominal": match.group(f"buyer_nominal{index}"),
                        "currency": "CHF",
                    },
                ),
            ])
        return events, ""

    match = _FR_PERSON_MOVED_AND_SIGNING_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.moved_and_signing_changed.v1", match.group("name"),
            place=match.group("place"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "domicile_and_signing_changed", "domicile_changed": True,
                "country": match.group("country"), "powers_modified": True,
            },
        )], ""

    match = _FR_ASSET_TRANSFER_TWO_CONTRACT_DATES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_two_contract_dates.v1", {
                "contract_dates": [
                    _iso_date(match.group("contract_date1")),
                    _iso_date(match.group("contract_date2")),
                ],
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "shares_and_receivable",
                "consideration_shares": _count(match.group("shares")),
                "consideration_share_nominal": match.group("nominal"),
                "consideration_issuer": match.group("consideration_issuer").strip(),
                "consideration_receivable": match.group("claim"),
            },
        )], ""

    match = _IT_CAPITAL_REDUCTION_AND_SIMULTANEOUS_INCREASE.fullmatch(leftover)
    if match:
        rule_id = "it.text.capital_reduction_and_simultaneous_increase.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "action": "reduced", "amount": match.group("reduction"),
                    "currency": "CHF",
                    "shares_cancelled": _count(match.group("cancelled_count")),
                    "share_nominal": match.group("cancelled_nominal"),
                    "share_kind": "azioni nominative",
                    "purpose": "cover_balance_sheet_deficit",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "action": "increased", "simultaneous": True,
                    "currency": "CHF",
                    "shares_issued": _count(match.group("issued_count")),
                    "share_nominal": match.group("issued_nominal"),
                    "share_kind": "azioni nominative", "fully_paid": True,
                },
            ),
        ], ""

    match = _FR_BOARD_PRESIDENT_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_president_corrected.v1",
            match.group("name"), role="président du conseil", extra={
                "action": "publication_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_ASSOCIATION_ASSET_TRANSFER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.association_asset_transfer.v1", {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": None, "consideration_kind": "none",
            },
        )], ""

    match = _FR_ASSET_TRANSFER_CASH_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_cash_consideration.v1", {
                "contract_date": _iso_date(match.group("contract_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    return [], leftover
