from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_OTHER_POSTAL_ADDRESS = re.compile(
    r"^Autre adresse postale:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_SHARE_CAPITAL_RESOLVED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ein bedingtes Aktienkapital "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_BY_GENERAL_ASSEMBLY = re.compile(
    r"^Der Verein ist mit Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADJUSTMENT_ITEM = re.compile(
    r"\s*\[gestrichen:\s*(?P<previous>[^\]]+)\]\.\s*"
    r"(?P<place>[^\[\]()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNERSHIP_CAPITAL_REDUCED = re.compile(
    r"^Contrat de société modifié le\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Le montant de la commandite est réduit de CHF\s+"
    r"(?P<previous>[\d'.]+)\s+à CHF\s+(?P<total>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_INVENTORY_CASH_CURRENCY_TYPO = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>Gesellschaft)\s+überträgt "
    r"gemäss Vermögensübertragungsvertrag\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von\s+"
    r"(?P<liabilities_currency>CHF|CH)\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_BANKRUPTCY_OPENED = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*Mit Entscheid des\s+"
    r"(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde über den Hauptsitz mit "
    r"Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_INVENTORY_APPROVAL = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+sowie Verfügung der "
    r"Aufsichtsbehörde vom\s+"
    r"(?P<approval_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>Keine)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED_NOTICE_ID = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:n°|no°|no)\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+est domiciliée? à\s+(?P<place>[^()]+?)\s*"
    r"\(et non pas à\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_OMITTED_PREVIOUS_AUDITOR = re.compile(
    r"^Mit Tagesregister\s+(?P<entry>\d+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*publiziert im SHAB\s+"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+wurde "
    r"versehentlich der Bishertext nicht aufgeführt\.\s*Dieser lautet:\s*"
    r"\[bisher:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<role>Revisionsstelle)\]\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<previous_name>[^,.;]+?)\s+se nomme en réalité\s+"
    r"(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_POSTAL_LOCALITY_REMAINDER = re.compile(
    r"^,?\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[A-Za-zÀ-ÿ][^,.;]*)\.?$",
    re.UNICODE,
)
_FR_VOTING_PREFERRED_SHARE_SPLIT_AND_TRANSFER = re.compile(
    r"^La clause statutaire relative à la reprise de biens à la constitution est "
    r"supprimée conformément à\s+(?P<legal_basis>l['’]art\.\s*628,\s*al\.\s*4,\s*CO)\.\s*"
    r"Division de la part de CHF\s+(?P<from_nominal>[\d'.]+)\s+de "
    r"l['’]associé-gérant\s+(?P<seller>[^.]+?)\s+en\s+"
    r"(?P<ordinary_count>[\d']+)\s+parts ordinaires de CHF\s+"
    r"(?P<ordinary_nominal>[\d'.]+)\s+et\s+"
    r"(?P<preferred_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*à droit de vote privilégié\.\s*"
    r"L['’]associé-gérant\s+(?P=seller)\s+détient\s+"
    r"(?P<seller_preferred_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_preferred_nominal>[\d'.]+),\s*à droit de vote privilégié,\s*"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts ordinaires "
    r"de CHF\s+(?P<transfer_nominal>[\d'.]+)\s+à l['’]associée\s+"
    r"(?P<buyer>.+?)\s+qui détient ainsi\s+(?P<buyer_count>[\d']+)\s+parts "
    r"ordinaires de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_SHARED_ORIGIN_PLACE = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*tous deux de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*sont membres du "
    r"conseil d['’]administration"
    r"(?:\s+avec\s+(?P<signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_FOR_SHARES_NO_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature\.\s*(?P=seller)\s*\((?P=seller_uid)\)\s+reste titulaire "
    r"de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
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
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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


def _branch_adjustments(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> list[Event] | None:
    matches: list[re.Match[str]] = []
    position = 0
    while position < len(text):
        match = _DE_BRANCH_ADJUSTMENT_ITEM.match(text, position)
        if not match or match.end() == position:
            return None
        matches.append(match)
        position = match.end()
    if not matches:
        return None

    rule_id = "de.text.branch_adjustment_sequence.v1"
    events: list[Event] = []
    for match in matches:
        previous = match.group("previous").strip()
        previous_uid_match = re.search(r"\((CH-[^)]+)\)$", previous)
        previous_place = re.sub(r"\s*\(CH-[^)]+\)$", "", previous).strip()
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "removed", "place": previous_place,
                    **(
                        {"previous_registry_id": previous_uid_match.group(1)}
                        if previous_uid_match else {}
                    ),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "added", "place": match.group("place").strip(),
                    "branch_uid": match.group("uid"),
                },
            ),
        ])
    return events


def extract_parser214_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 214."""
    leftover = text.strip()

    match = _FR_OTHER_POSTAL_ADDRESS.fullmatch(leftover)
    if match:
        address = match.group("address").strip()
        postal_code = match.group("postal_code")
        locality = match.group("locality").strip()
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.other_postal_address.v1", {
                "kind": "additional_postal_address", "action": "added",
                "address": address, "postal_code": postal_code,
                "locality": locality,
                "full_address": f"{address}, {postal_code} {locality}",
            },
        )], ""

    match = _DE_CONDITIONAL_SHARE_CAPITAL_RESOLVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_share_capital_resolved.v1", {
                "kind": "conditional_share_capital", "action": "resolved",
                "decision_date": _iso_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_ASSOCIATION_DISSOLVED_BY_GENERAL_ASSEMBLY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.association_dissolved_general_assembly.v1", {
                "kind": "dissolution", "action": "dissolved",
                "scope": "association",
                "decision_body": "general_assembly",
                "decision_date": _iso_date(match.group("decision_date")),
            },
        )], ""

    branch_events = _branch_adjustments(
        leftover, publication_id, published_at, org_uid, plz, canton
    )
    if branch_events:
        return branch_events, ""

    match = _FR_LIMITED_PARTNERSHIP_CAPITAL_REDUCED.fullmatch(leftover)
    if match and _amount(match.group("total")) < _amount(match.group("previous")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.limited_partnership_capital_reduced.v1", {
                "kind": "limited_partnership_capital", "action": "reduced",
                "partnership_agreement_date": _french_date(
                    match.group("decision_date")
                ),
                "from": match.group("previous"), "to": match.group("total"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_INVENTORY_CASH_CURRENCY_TYPO.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_inventory_cash_currency_typo.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "liabilities_currency_as_published": match.group(
                    "liabilities_currency"
                ).upper(),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_currency": "CHF", "consideration_kind": "cash",
            },
        )], ""

    match = _DE_HEAD_OFFICE_BANKRUPTCY_OPENED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_bankruptcy_opened.v1", {
                "kind": "bankruptcy", "action": "opened",
                "scope": "head_office",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
            },
        )], ""

    match = _DE_FOUNDATION_ASSET_TRANSFER_INVENTORY_APPROVAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.foundation_asset_transfer_inventory_approval.v1", {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "supervisory_approval_date": _iso_date(
                    match.group("approval_date")
                ),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration").lower(),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _FR_DOMICILE_CORRECTED_NOTICE_ID.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_notice_id.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        )], ""

    match = _DE_OMITTED_PREVIOUS_AUDITOR.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.omitted_previous_auditor_restored.v1", {
                "kind": "auditor_entry", "action": "previous_text_restored",
                "reason": "previous_text_erroneously_omitted",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "auditor": match.group("name").strip(),
                "auditor_uid": match.group("uid"),
                "role": match.group("role"),
            },
        )], ""

    match = _FR_PERSON_NAME_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_corrected_with_notice.v1",
            match.group("name"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_POSTAL_LOCALITY_REMAINDER.fullmatch(leftover)
    if match and (language or "").lower() == "fr":
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.address_postal_locality_remainder.v1", {
                "kind": "address_postal_locality", "action": "specified",
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        )], ""

    match = _FR_VOTING_PREFERRED_SHARE_SPLIT_AND_TRANSFER.fullmatch(leftover)
    if match:
        ordinary_count = _count(match.group("ordinary_count"))
        preferred_count = _count(match.group("preferred_count"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        valid = (
            _amount(match.group("from_nominal"))
            == ordinary_count * _amount(match.group("ordinary_nominal"))
            + preferred_count * _amount(match.group("preferred_nominal"))
            and preferred_count == _count(match.group("seller_preferred_count"))
            and transferred == ordinary_count
            and len({
                match.group("preferred_nominal"),
                match.group("seller_preferred_nominal"),
            }) == 1
            and len({
                match.group("ordinary_nominal"),
                match.group("transfer_nominal"),
                match.group("buyer_nominal"),
            }) == 1
            and buyer_count >= transferred
        )
        if valid:
            rule_id = "fr.persons.voting_preferred_share_split_and_transfer.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", rule_id, {
                        "kind": "founding_asset_acquisition_clause",
                        "action": "removed",
                        "legal_basis": re.sub(
                            r"\s+", " ", match.group("legal_basis")
                        ),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id, {
                        "kind": "social_share_split", "action": "split",
                        "currency": "CHF",
                        "split_from": {
                            "count": 1, "nominal": match.group("from_nominal")
                        },
                        "split_to": [
                            {
                                "count": ordinary_count,
                                "nominal": match.group("ordinary_nominal"),
                                "class": "ordinary",
                            },
                            {
                                "count": preferred_count,
                                "nominal": match.group("preferred_nominal"),
                                "class": "voting_preferred",
                            },
                        ],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_split_and_transferred",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "transferred_share_class": "ordinary",
                        "transferred_share_nominal": match.group(
                            "transfer_nominal"
                        ),
                        "shares_count": preferred_count,
                        "share_nominal": match.group("preferred_nominal"),
                        "share_class": "voting_preferred", "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associée", extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_before": buyer_count - transferred,
                        "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"),
                        "share_class": "ordinary", "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_TWO_BOARD_MEMBERS_SHARED_ORIGIN_PLACE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_shared_origin_place.v1"
        signing = "Einzelunterschrift" if match.group("signing") else None
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), role="administrateur",
                signing=signing, extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_ASSET_TRANSFER_FOR_SHARES_NO_LIABILITIES.fullmatch(leftover)
    if match and (
        _amount(match.group("assets"))
        == _count(match.group("share_count"))
        * _amount(match.group("share_nominal"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_for_registered_shares.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "currency": "CHF",
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "shares",
                "consideration_shares_count": _count(
                    match.group("share_count")
                ),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_currency": "CHF",
            },
        )], ""

    match = _FR_CORPORATE_ASSOCIATE_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.fullmatch(
        leftover
    )
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred"))
        == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.corporate_associate_transfer_new_unsigned_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {
            "share_nominal": match.group("nominal"), "currency": "CHF"
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                uid=match.group("seller_uid"), role="associée", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "counterparty_uid": match.group("seller_uid"),
                    "origin": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True, "without_signature": True, **common,
                },
            ),
        ], ""

    return [], leftover
