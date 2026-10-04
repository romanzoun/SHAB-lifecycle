from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CONDITIONAL_SHARE_CAPITAL_CLAUSE = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation du capital-actions au moyen d['’]un capital conditionnel,\s*"
    r"par décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4});\s*"
    r"pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel(?:le)? associée? avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),?\s*"
    r"(?P<unsigned>sans signature)?(?:\.\s*|,\s*)?"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENDED_DIRECT = re.compile(
    r"^Mit Verfügung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde der Gesellschaft gegen das "
    r"erstinstanzliche Konkurserkenntnis die aufschiebende Wirkung erteilt\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_CONTRACT_AND_INVENTORY = re.compile(
    r"^Vermögensübertragung\.\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+und Inventar vom\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+au nouvel "
    r"associé\s+(?P<buyer>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"Par conséquent,\s*(?P=seller)\s*\((?P=seller_uid)\)\s+est maintenant associée "
    r"pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.\s*Signature individuelle a été conférée à "
    r"l['’]associé\s+(?P=buyer)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}),\s*le titulaire a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s+à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<shares_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+et une créance de CHF\s+"
    r"(?P<receivable>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_ONE_ABROAD = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’])"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont membres du conseil\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_COLLECTIVE_LAST_CHANGED = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*présidente et\s+(?P<member>[^,.;]+),\s*"
    r"lesquelles signent collectivement à deux;\s*les pouvoirs de la dernière "
    r"sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED = re.compile(
    r"^L['’]organe de révision\s+(?P<previous_name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+a modifié sa raison "
    r"sociale en\s+(?P<name>.+?)\s*\((?P=uid)\)\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED = re.compile(
    r"^Das\s+(?P<authority>.+?)\s+hat der Beschwerde gegen die Verfügung des\s+"
    r"(?P<court>.+?)\s+vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt\.\s*Demnach wird "
    r"die Eintragung betreffend Konkurs im Handelsregister gestrichen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ADMINISTRATION_ROLE_CHANGES_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<president_previous_role>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<secretary>[^,.;]+),\s*nommé secrétaire,\s*lesquels continuent à "
    r"signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_PARTICIPATION_CAPITAL_CREATION = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eine bedingte Schaffung bzw\. Erhöhung des Partizipationskapitals gemäss "
    r"näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_PLACE = re.compile(
    r"^\[bisher:\s*(?P<previous_place>Unterstammheim)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_SEAT_CHANGED_BY_AUTHORITY = re.compile(
    r"^\[Sitzänderung der Zweigniederlassung von Amtes wegen infolge "
    r"Gemeindefusion\.\]\.?$",
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
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser121_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 121."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_CONDITIONAL_SHARE_CAPITAL_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_share_capital_clause.v1",
            {
                "kind": "conditional_share_capital_clause", "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_to_new_associate_with_holdings.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred",
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé",
                signing=("ohne Zeichnungsberechtigung" if match.group("unsigned") else None),
                extra={
                    **common, "action": "appointed", "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "without_signature": bool(match.group("unsigned")),
                },
            ),
        ])

    match = _DE_BANKRUPTCY_APPEAL_SUSPENDED_DIRECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspended_direct.v1",
            {
                "kind": "bankruptcy_effect_suspended", "action": "suspensive_effect_granted",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_ASSET_TRANSFER_CONTRACT_AND_INVENTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_contract_inventory_period.v1",
            {
                "date": _iso_date(match.group("date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"), "currency": "CHF",
            },
        ))

    match = _FR_ORGANIZATION_TRANSFER_TO_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_transfer_new_associate_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                role="associée", uid=match.group("seller_uid"),
                extra={
                    "action": "shares_transferred", "uid": match.group("seller_uid"),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé", signing="Einzelunterschrift",
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_asset_transfer_shares_receivable.v1",
            {
                "date": _french_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "currency": "CHF",
                "consideration": {
                    "shares_count": _count(match.group("shares_count")),
                    "share_nominal": match.group("share_nominal"),
                    "receivable": match.group("receivable"),
                },
            },
        ))

    match = _FR_TWO_BOARD_MEMBERS_ONE_ABROAD.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_one_abroad.v1"
        for index in (1, 2):
            extra = {"action": "appointed", "heimat": match.group(f"origin{index}").strip()}
            if index == 1:
                extra["country"] = match.group("country1")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil", extra=extra,
            ))

    match = _FR_ADMINISTRATION_PAIR_COLLECTIVE_LAST_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_collective_last_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="présidente",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_president", "heimat": match.group("origin").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("member"),
                role="administratrice", signing="Kollektivunterschrift zu zweien",
                extra={"action": "signing_changed"},
            ),
        ])

    match = _FR_AUDITOR_RENAMED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_renamed_same_uid.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "registered_name_changed",
                "previous_name": match.group("previous_name").strip(),
                "uid": match.group("uid"),
                "previous_uid": match.group("uid"),
            },
        ))

    match = _DE_OWNER_BANKRUPTCY_APPEAL_ENTRY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.owner_bankruptcy_appeal_entry_removed.v1",
            {
                "kind": "bankruptcy_effect_suspended", "action": "registry_entry_removed",
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _FR_ADMINISTRATION_ROLE_CHANGES_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_role_changes_individual.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"), role="président",
                signing="Einzelunterschrift",
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("president_previous_role").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"), role="secrétaire",
                signing="Einzelunterschrift", extra={"action": "role_changed"},
            ),
        ])

    match = _DE_CONDITIONAL_PARTICIPATION_CAPITAL_CREATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_participation_capital_creation.v1",
            {
                "kind": "conditional_participation_capital",
                "action": "creation_or_increase_authorized",
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _DE_BRANCH_PREVIOUS_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_previous_place_without_uid.v1",
            {
                "action": "previous_place_recorded",
                "previous_place": match.group("previous_place").strip(),
            },
        ))

    match = _DE_BRANCH_SEAT_CHANGED_BY_AUTHORITY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_seat_changed_by_municipal_merger.v1",
            {
                "action": "seat_changed_by_authority",
                "reason": "municipal_merger",
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
