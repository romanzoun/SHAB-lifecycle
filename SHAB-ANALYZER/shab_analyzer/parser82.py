from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATION_THREE_POWERS_CHANGED = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>président(?:e)?),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<place3>[^,.;]+),\s*lesquels signent\s*"
    r"(?P<sign>collectivement\s+à\s+deux);\s*les pouvoirs de\s*"
    r"(?P<changed>[^,.;]+)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDITIONAL_ADDRESSES_WITH_HEADING = re.compile(
    r"^\[Folgende weitere Adressen werden im Handelsregister gelöscht:\]\s*"
    r"(?P<items>(?:\[gestrichen:\s*Weitere Adresse:\s*[^\]]+\]\.?(?:\s*|$))+)$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDITIONAL_ADDRESS_ITEM = re.compile(
    r"\[gestrichen:\s*Weitere Adresse:\s*(?P<address>[^\]]+?)\]\.?(?:\s*|$)",
    re.I | re.UNICODE,
)
_FR_TOTAL_ASSET_TRANSFER = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat authentique du\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré la totalité "
    r"des actifs pour CHF\s*(?P<assets>[\d'.]+)\s+à la société\s+"
    r"(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*CHF\s*(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATED_WRITTEN_DATE_SHORT = re.compile(
    r"^La société est réinscrite au registre du commerce conformément à la décision\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_TRANSLATIONS_ADDED = re.compile(
    r"^Nuove traduzioni della ragione sociale:\s*"
    r"\((?P<german>[^()]+)\)\s*\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCHES_REMOVED_AFTER_ASSET_TRANSFER = re.compile(
    r"^Die Zweigniederlassungen von\s+(?P<branches>.+?)\s+sind infolge Übertragung "
    r"ihrer Aktiven und Passiven auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<recipient_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+gelöscht\s*"
    r"\(Eintragung Nr\.\s*(?P<entry>[\d']+) vom\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*SHAB vom\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s*(?P<notice_id>\d+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_ITEM = re.compile(
    r"(?:^|,\s*|\s+und\s+)(?P<place>.+?)\s*"
    r"\((?P<registry_id>CH-\d{3}-\d{7}-\d)\)",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_SPELLING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le nom de\s+"
    r"(?P<previous>[^,.;]+?)\s+s['’]orthgraphie en réalité\s+"
    r"(?P<corrected>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_CURRENCY_CAPITAL = re.compile(
    r"^Nouveau capital:\s*(?P<currency>[A-Z]{3})\s*"
    r"(?P<total>[\d'.]+),\s*(?P<paid>entièrement libéré)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_SIGNS_INDIVIDUALLY = re.compile(
    r"^Le\s+(?P<role>directeur)\s+(?P<name>[^,.;]+)\s+signe\s+"
    r"(?P<sign>individuellement)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_RESTRICTED_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s*"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"sont membres du conseil avec le président ou le vice-président\.?$",
    re.I | re.UNICODE,
)
_DE_DUPLICATE_PERSON_DELETION_CORRECTION = re.compile(
    r"^Mit dem SHAB Nr\.\s*(?P<notice_number>\d+) vom\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Text\s*"
    r"(?P<entry>\d+/\d{4})\s+wurde die Löschung von\s*"
    r"(?P<person1>.+?)\s+und\s+(?P<person2>.+?)\s+publiziert\.\s*"
    r"Die Löschung dieser beiden Personen wurde jedoch bereits mit TR Nr\.\s*"
    r"(?P<previous_entry>\d+) vom\s*(?P<previous_entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und SHAB Nr\.\s*(?P<previous_notice_number>\d+) vom\s*"
    r"(?P<previous_notice_date>\d{2}\.\d{2}\.\d{4})\s+durchgeführt\.?$",
    re.I | re.UNICODE,
)
_FR_LEGACY_BRANCH_REMOVED = re.compile(
    r"^La succursale de\s+(?P<place>.+?)\s*"
    r"\((?P<registry_id>CH-\d{3}-\d{7}-\d)\)\s+est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_OFFICES_REMOVED = re.compile(
    r"^(?P<items>(?:\[gestrichen:\s*Geschäftsstelle:\s*[^\]]+\]\.?(?:\s*|$))+)$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_OFFICE_ITEM = re.compile(
    r"\[gestrichen:\s*Geschäftsstelle:\s*(?P<address>[^\]]+?)\]\.?(?:\s*|$)",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_EFFECT_SUSPENDED_WITH_HISTORY = re.compile(
    r"^Con decisione del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo al reclamo inoltrato "
    r"contro la decisione di fallimento aperto nei confronti del titolare il\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*L['’]iscrizione nel registro "
    r"di commercio relativa al fallimento del titolare viene pertanto cancellata\.\s*"
    r"\[finora:\s*Il titolare è stato dichiarato in fallimento con decreto della\s+"
    r"(?P<bankruptcy_authority>.+?)\s+del\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+a far tempo dal\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+alle ore\s+"
    r"(?P<effective_time>\d{1,2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ART_934_SHAB_NOTICE_SINGULAR_DELETION_BLOCKED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 OR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlasste und im SHAB mit Meldungsnummer\s+(?P<issue>[A-Z0-9-]+)\s+"
    r"publizierte Aufforderung haben sich keine weiteren Betroffenen gemeldet\.\s*"
    r"Das amtliche Verfahren zur Löschung der Rechtseinheit ist damit abgeschlossen\.\s*"
    r"Sie kann mangels Zustimmung der Eidgenössischen Steuerverwaltung jedoch noch "
    r"nicht gelöscht werden\.?$",
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
    return f"{year}-{month}-{day}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser82_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 82."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ADMINISTRATION_THREE_POWERS_CHANGED.search(leftover)
    if match:
        consume(match)
        changed = match.group("changed").strip()
        signing = "Kollektivunterschrift zu zweien"
        people = (
            ("name1", "place1", "origin1", match.group("role1").lower()),
            ("name2", "place2", "origin2", "administrateur"),
            ("name3", "place3", None, "administrateur"),
        )
        for name_group, place_group, origin_group, role in people:
            name = match.group(name_group).strip()
            extra = {"action": "appointed", "signing_mode": "collective_two"}
            if origin_group:
                extra["heimat"] = match.group(origin_group).strip()
            if name == changed:
                extra.update({"action": "powers_and_domicile_changed", "powers_changed": True})
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_three_powers_changed.v1",
                    name, place=match.group(place_group), role=role, signing=signing,
                    extra=extra,
                )
            )

    match = _DE_REMOVED_ADDITIONAL_ADDRESSES_WITH_HEADING.search(leftover)
    if match:
        items = list(_DE_REMOVED_ADDITIONAL_ADDRESS_ITEM.finditer(match.group("items")))
        if items:
            consume(match)
            for item in items:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "address_changed", "de.text.additional_addresses_removed_with_heading.v1",
                        {
                            "kind": "additional_address",
                            "action": "removed",
                            "address": item.group("address").strip().rstrip("."),
                        },
                    )
                )

    match = _FR_TOTAL_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer_total_assets.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "scope": "all_assets",
                    "assets": match.group("assets"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": match.group("consideration"),
                    "currency": "CHF",
                },
            )
        )

    match = _FR_COMPANY_REINSTATED_WRITTEN_DATE_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.company_reinstated_written_date_short.v1",
                {
                    "kind": "registration_reinstated",
                    "date": _french_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _IT_COMPANY_TRANSLATIONS_ADDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "it.text.company_translations_added.v1",
                {
                    "action": "translations_added",
                    "translations": {
                        "de": match.group("german").strip(),
                        "en": match.group("english").strip(),
                    },
                },
            )
        )

    match = _DE_BRANCHES_REMOVED_AFTER_ASSET_TRANSFER.search(leftover)
    if match:
        branch_items = list(_DE_LEGACY_BRANCH_ITEM.finditer(match.group("branches")))
        if branch_items:
            consume(match)
            common = {
                "action": "removed",
                "reason": "asset_and_liability_transfer",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("recipient_uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            }
            for item in branch_items:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "branch_changed", "de.text.branches_removed_after_asset_transfer.v1",
                        {
                            **common,
                            "place": item.group("place").strip(),
                            "registry_id": item.group("registry_id"),
                        },
                    )
                )

    match = _FR_PERSON_NAME_SPELLING_CORRECTED.search(leftover)
    if match:
        consume(match)
        previous = match.group("previous").strip()
        suffix = previous.partition(" ")[2]
        name = f"{match.group('corrected').strip()} {suffix}".strip()
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.name_spelling_corrected.v1", name,
                extra={
                    "action": "name_corrected",
                    "previous_name": previous,
                    "corrected_spelling": match.group("corrected").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_FOREIGN_CURRENCY_CAPITAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.foreign_currency_capital.v1",
                {
                    "action": "changed",
                    "capital_total": match.group("total"),
                    "currency": match.group("currency").upper(),
                    "paid_in_full": True,
                },
            )
        )

    match = _FR_DIRECTOR_SIGNS_INDIVIDUALLY.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.director_signing_granted.v1",
                match.group("name"), role=match.group("role").lower(),
                signing="Einzelunterschrift", extra={"action": "granted"},
            )
        )

    match = _FR_BOARD_MEMBERS_RESTRICTED_SIGNING.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_restricted_signing.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil", signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "country": match.group(f"country{index}"),
                        "signing_with": "président ou vice-président",
                    },
                )
            )

    match = _DE_DUPLICATE_PERSON_DELETION_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "de.text.duplicate_person_deletion_correction.v1",
                {
                    "action": "duplicate_deletion_corrected",
                    "persons": [match.group("person1").strip(), match.group("person2").strip()],
                    "notice_number": match.group("notice_number"),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "entry": match.group("entry"),
                    "previous_entry": match.group("previous_entry"),
                    "previous_entry_date": _iso_date(match.group("previous_entry_date")),
                    "previous_notice_number": match.group("previous_notice_number"),
                    "previous_notice_date": _iso_date(match.group("previous_notice_date")),
                },
            )
        )

    match = _FR_LEGACY_BRANCH_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.legacy_branch_removed.v1",
                {
                    "action": "removed",
                    "place": match.group("place").strip(),
                    "registry_id": match.group("registry_id"),
                },
            )
        )

    match = _DE_BUSINESS_OFFICES_REMOVED.search(leftover)
    if match:
        items = list(_DE_BUSINESS_OFFICE_ITEM.finditer(match.group("items")))
        if items:
            consume(match)
            for item in items:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "address_changed", "de.text.business_offices_removed_sequence.v1",
                        {
                            "kind": "business_office",
                            "action": "removed",
                            "address": item.group("address").strip().rstrip("."),
                        },
                    )
                )

    match = _IT_BANKRUPTCY_EFFECT_SUSPENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.bankruptcy_effect_suspended_with_history.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_authority": match.group("bankruptcy_authority").strip(),
                    "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("effective_time"),
                    "appeal_effect_suspended": True,
                    "bankruptcy_registration_cancelled": True,
                },
            )
        )

    match = _DE_ART_934_SHAB_NOTICE_SINGULAR_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.art_934_shab_notice_singular_deletion_blocked.v1",
                {
                    "kind": "deletion_blocked",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                    "procedure_completed": True,
                    "issues": [match.group("issue")],
                    "affected_parties_responded": False,
                    "tax_authority": "Eidgenössische Steuerverwaltung",
                    "tax_authority_consent_missing": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
