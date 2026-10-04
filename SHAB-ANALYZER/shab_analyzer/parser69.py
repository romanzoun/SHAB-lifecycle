from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_PROVISIONAL_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Urteil vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<authority>.+?),\s*in\s+(?P<authority_place>[^,.;]+),\s*die provisorische "
    r"Nachlassstundung zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*jusqu['’]ici avec procuration individuelle,\s*"
    r"nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*Gérants:\s*les associés\s+"
    r"(?P=seller)\s+et\s+(?P=buyer),\s*président,\s*tous deux\s*;\s*"
    r"leurs pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_NAME_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>\d+)/(?P<notice_id>\d+)\)\s+est rectifiée en ce sens "
    r"qu['’]une signature collective à deux avec un\s+(?P<with_role>[^,.;]+)\s+"
    r"est conférée à\s+(?P<name>[^()]+?)\s+\(et non\s+"
    r"(?P<previous_name>[^)]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTION_REMOVED = re.compile(
    r"^L['’](?P<role>administratrice?)\s+(?P<name>[^,.;]+)\s+continue à signer "
    r"collectivement à deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_HEAD_OFFICE_IDENTIFIER = re.compile(
    r"^\[bisher:\s*Identifikationsnummer:\s*(?P<from>CH-[\d.]+-\d)\]\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_WITH_ROLE = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*id\s+(?P<notice_id>\d+)\)\s+"
    r"est rectifiée dans ce sens:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<role>associé(?:e)? gérant(?:e)?),\s*signature\s+"
    r"(?P<sign>individuelle|collective(?:\s+à\s+deux)?),\s*est domicilié(?:e)? à\s+"
    r"(?P<place>[^()]+?)\s+\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_PARTICIPATION_CERTIFICATES_REMOVED_COUNTED = re.compile(
    r"^Genussscheine neu:\s*\[Die\s+(?P<count>[\d']+)\s+Genussscheine sind "
    r"aufgehoben worden\.\]\s*\[gestrichen:\s*Es bestehen\s+(?P=count)\s+"
    r"Genussscheine,\s*(?P<rights>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_EFFECT_SUSPENDED_MESSAGE = re.compile(
    r"^Mit Mitteilung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist dem Rekurs gegen den Entscheid "
    r"des\s+(?P<court>.+?)\s+vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"betreffend Konkurseröffnung aufschiebende Wirkung zuerkannt worden\.\s*"
    r"Demnach wird die Eintragung betreffend Konkurseröffnung über die Gesellschaft "
    r"im Handelsregister gestrichen\.\s*\[bisher:\s*Mit Entscheid der\s+"
    r"(?P<previous_court>.+?)\s+vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"ist über die Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet worden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BANKRUPTCY_DISSOLUTION = re.compile(
    r"^\[gestrichen:\s*Auflösung der Gesellschaft durch Konkurs gemäss "
    r"Konkurserkenntnis des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_APPEAL_DECISION_REVOKED_GENERAL = re.compile(
    r"^In Gutheissung der Beschwerde hat\s+(?P<authority>.+?)\s+mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+den Entscheid des\s+"
    r"(?P<court>.+?)\s+vom\s+(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"aufgehoben\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY_CONTRACT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"auf die\s+(?P<recipient>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^.]+)\.\s*Gegenleistung:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITHOUT_SIGNING = re.compile(
    r"^Nouveau membre du conseil de fondation sans signature:\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_AUDIT_WAIVER = re.compile(
    r"^\[bisher:\s*Gemäss Erklärung des Verwaltungsrates vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_LIQUIDATION = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte Gesellschaft "
    r"wird auf Grund (?:des|der)\s+(?P<document>Urteils|Verfügung)\s+des\s+"
    r"(?P<authority>.+?)\s+vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"zum Zwecke der Liquidation wieder in das Handelsregister eingetragen und besteht "
    r"entsprechend den früheren Eintragungen weiter\.?"
    r"(?:\s*\[bisher:\s*(?P<previous>.+)\])?\.?$",
    re.I | re.UNICODE,
)
_FR_ADDRESS_SUPPLEMENTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée par la nouvelle "
    r"adresse de la société sise\s+(?P<street>.+?)\s+(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
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


def extract_parser69_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 69."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.provisional_moratorium_extended.v1",
                {
                    "kind": "composition_moratorium_extended",
                    "provisional": True,
                    "decision_date": _iso_date(match.group("decision_date")),
                    "until": _iso_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                    "authority_place": match.group("authority_place").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_MANAGER_TRANSFER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_manager_transfer.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_nominal": match.group("nominal"),
                        "manager_powers_modified": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé-gérant président",
                    extra={
                        "action": "shares_received_and_appointed",
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "previous_signing": "procuration individuelle",
                        "manager_powers_modified": True,
                    },
                ),
            ]
        )

    match = _FR_SIGNING_NAME_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.signing_name_correction.v1",
                match.group("name"), signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "name_and_signing_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "signing_with_role": match.group("with_role").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _FR_SIGNING_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.signing_restriction_removed.v1",
                match.group("name"), role=match.group("role"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_continues": True},
            )
        )

    match = _DE_PREVIOUS_HEAD_OFFICE_IDENTIFIER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "de.text.head_office_previous_identifier.v1",
                {"scope": "head_office", "action": "replaced", "from": match.group("from")},
            )
        )

    match = _FR_DOMICILE_CORRECTION_WITH_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.domicile_correction_with_role.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"), signing=_signing(match.group("sign")),
                extra={
                    "action": "domicile_corrected",
                    "previous_place": match.group("previous_place").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                },
            )
        )

    match = _DE_PARTICIPATION_CERTIFICATES_REMOVED_COUNTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.participation_certificates_removed_counted.v1",
                {
                    "kind": "participation_certificates",
                    "action": "removed",
                    "from_count": _count(match.group("count")),
                    "rights": match.group("rights").strip().rstrip("."),
                },
            )
        )

    match = _DE_BANKRUPTCY_EFFECT_SUSPENDED_MESSAGE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_effect_suspended_message.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("court").strip(),
                    "bankruptcy_registration_removed": True,
                },
            )
        )

    match = _DE_REMOVED_BANKRUPTCY_DISSOLUTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_dissolution_removed.v1",
                {
                    "kind": "bankruptcy_dissolution",
                    "action": "removed",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _DE_APPEAL_DECISION_REVOKED_GENERAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.appeal_decision_revoked_general.v1",
                {
                    "kind": "court_decision_revoked",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "original_decision_date": _iso_date(match.group("original_date")),
                    "authority": match.group("authority").strip(),
                    "original_court": match.group("court").strip(),
                },
            )
        )

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY_CONTRACT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_assets_only_contract.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": None,
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _FR_FOUNDATION_MEMBER_WITHOUT_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.foundation_member_without_signing.v1",
                match.group("name"), place=match.group("place"),
                role="membre du conseil de fondation",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                },
            )
        )

    match = _DE_PREVIOUS_AUDIT_WAIVER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.audit_waiver_previous.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "replaced",
                    "previous_date": _iso_date(match.group("date")),
                    "declarant": "Verwaltungsrat",
                },
            )
        )

    match = _DE_COMPANY_REINSTATED_FOR_LIQUIDATION.search(leftover)
    if match:
        consume(match)
        payload = {
            "kind": "registration_reinstated",
            "reason": "liquidation",
            "deletion_date": _iso_date(match.group("deletion_date")),
            "decision_date": _iso_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
            "decision_document": match.group("document").lower(),
            "liquidation_only": True,
            "company_continues": True,
        }
        if match.group("previous"):
            payload["previous"] = match.group("previous").strip()
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.company_reinstated_for_liquidation.v1",
                payload,
            )
        )

    match = _FR_ADDRESS_SUPPLEMENTED.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()} {match.group('postal_code')} "
            f"{match.group('locality').strip()}"
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "fr.text.address_supplemented.v1",
                {
                    "action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "address": address,
                    "street": match.group("street").strip(),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
