from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_NAME_AND_ORIGIN_CHANGED = re.compile(
    r"^(?P<previous_name>[^,.;]+?)\s+porte désormais le nom de\s+"
    r"(?P<name>[^,.;]+?),\s*(?:il\s+)?est maintenant originaire de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>.+?),\s*nouvel associé-gérant\s+"
    r"titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller),\s*qui est nommé président,\s*"
    r"a maintenant\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVED_NESTED_LABEL = re.compile(
    r"^Zweigniederlassung neu:\s*\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<registry_id>CH-[\d.-]+-\d)\)\s+HR\s+(?P<register_canton>[A-Z]{2})\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_UNSIGNED = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée sans "
    r"signature,\s*titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+a désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MISSING_LEGACY_COMPANY_NUMBER_SUPPLEMENT = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<issue_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag\s+"
    r"(?P<entry>[\d'/]+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde im bisher-Text die Firmennummer nicht publiziert\.\s*Deshalb erfolgt "
    r"hiermit der Nachtrag:\s*\[bisher:\s*(?P<company>.+?),?\s*"
    r"\((?P<registry_id>CH-[\d.-]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Mit Urteil vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde vom\s+"
    r"(?P<appeal_date>\d{2}\.\d{2}\.\d{4})\s+gegen das "
    r"Konkurseröffnungsurteil vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"die aufschiebende Wirkung erteilt\.?$",
    re.I | re.UNICODE,
)
_DE_DEED_DATE = re.compile(
    r"^Urkundendatum:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_EXACT_PERSON_NAME_CORRECTED_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact de\s+"
    r"(?P<previous_name>[^,.;]+?)\s+est\s+(?P<name>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSLATIONS_AND_MANAGER_LIQUIDATOR = re.compile(
    r"^\((?P<german>[^()]+)\)\s*\((?P<italian>[^()]+)\)\s*"
    r"\((?P<english>[^()]+)\)\.\s*L['’]associé-gérant\s+"
    r"(?P<name>[^,.;]+?)\s+est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die "
    r"definitive Nachlassstundung um\s+(?P<duration>\d+)\s+Monate ab\s+"
    r"(?P<effective_from>\d{2}\.\d{2}\.\d{4})\s+verlängert,\s*d\.h\.\s*bis "
    r"zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\s*\[bisher:\s*Mit "
    r"Entscheid vom\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die "
    r"definitive Nachlassstundung für\s+"
    r"(?P<previous_duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+Monate "
    r"bis\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITHOUT_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag und Inventar vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})/(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+ohne Passiven\s*\(Fremdkapital\)\s+"
    r"auf die\s+(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*CHF\s+"
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_PREVIOUS_TEXT_COMPLETED = re.compile(
    r"^Mit dem im SHAB-Nr\.\s*(?P<issue_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag\s+"
    r"(?P<entry>[\d'/]+)\s+wurde nicht der vollständige bisherige Text publiziert\.\s*"
    r"Korrekt wäre:\s*(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*Revisionsstelle\s*\[bisher:\s*"
    r"(?P<previous_name>.+?)\s*\((?P<previous_registry_id>CH-[\d.-]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+den Betriebsteil\s+"
    r"(?P<business_unit>.+?)\s+mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und "
    r"Passiven\s*\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^,.;]+)\.\s*Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_SEAT_CHANGED_WITHOUT_IDENTIFIER = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<to>[^\[]+?)\s*"
    r"\[bisher:\s*(?P<from>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_LLC_TO_CORPORATION_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Gesellschaft mit beschränkter Haftung wird gemäss "
    r"Umwandlungsplan vom\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft umgewandelt\.\s*"
    r"Der Gesellschafter erhält für seine bisherigen Stammanteile\s+"
    r"(?P<shares>[\d']+)\s+Namenaktien zu CHF\s+(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_QUALIFIED_FACTS_CORRECTION_REMAINDER = re.compile(
    r'^eingetragenen,\s*Einzelunternehmens\s+"(?P<business>.+?)",\s*in\s+'
    r"(?P<place>[^,.;]+),\s*gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Übernahmebilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"wofür\s+(?P<shares>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+ausgegeben und CHF\s+"
    r"(?P<receivable>[\d'.]+)\s+als Forderung gutgeschrieben werden\.?$",
    re.I | re.UNICODE,
)


_DE_NUMBERS = {
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


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    normalized = raw.lower()
    return int(normalized) if normalized.isdigit() else _DE_NUMBERS[normalized]


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


def extract_parser143_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 143."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_NAME_AND_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_and_origin_changed.v1",
            match.group("name"),
            extra={
                "action": "name_and_origin_changed",
                "previous_name": match.group("previous_name").strip(),
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_MANAGER_TRANSFER_AND_PRESIDENCY.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.manager_transfer_and_presidency_no_prefix.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_elected_president",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_BRANCH_REMOVED_NESTED_LABEL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_removed_nested_label.v1",
            {
                "action": "removed", "place": match.group("place").strip(),
                "previous_branch_id": match.group("registry_id"),
                "register_canton": match.group("register_canton").upper(),
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_UNSIGNED.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.associate_transfer_unsigned.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "new_associate": True, "without_signature": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_MISSING_LEGACY_COMPANY_NUMBER_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.missing_legacy_company_number_supplement.v1",
            {
                "kind": "previous_text_company_number", "action": "supplemented",
                "issue_number": match.group("issue_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "company": match.group("company").strip().rstrip(","),
                "registry_id": match.group("registry_id"),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspensive_effect.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "decision_date": _iso_date(match.group("decision_date")),
                "appeal_date": _iso_date(match.group("appeal_date")),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_DEED_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.deed_date.v1",
            {"kind": "deed_date", "date": _iso_date(match.group("date"))},
        ))

    match = _FR_EXACT_PERSON_NAME_CORRECTED_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.exact_name_corrected_notice.v1",
            match.group("name"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TRANSLATIONS_AND_MANAGER_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.translations_and_manager_liquidator.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id,
                {
                    "action": "translations_added",
                    "translations": {
                        "de": match.group("german").strip(),
                        "it": match.group("italian").strip(),
                        "en": match.group("english").strip(),
                    },
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="associé-gérant et liquidateur",
                extra={"action": "elected_liquidator"},
            ),
        ])

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_from_date.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "duration_months": _duration(match.group("duration")),
                "effective_from": _iso_date(match.group("effective_from")),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_duration_months": _duration(match.group("previous_duration")),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        ))

    match = _DE_ASSET_TRANSFER_WITHOUT_LIABILITIES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_contract_inventory_combined_dates.v1",
            {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"), "liabilities": None,
                "liabilities_transferred": False, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_currency": "CHF",
            },
        ))

    match = _DE_AUDITOR_PREVIOUS_TEXT_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_previous_text_completed.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="Revisionsstelle",
            extra={
                "action": "previous_text_completed",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
                "issue_number": match.group("issue_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
            },
        ))

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_asset_transfer_no_consideration.v1",
            {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "business_unit": match.group("business_unit").strip(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "liabilities_transferred": True, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": None,
            },
        ))

    match = _DE_BRANCH_SEAT_CHANGED_WITHOUT_IDENTIFIER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_seat_changed_without_identifier.v1",
            {
                "action": "seat_changed",
                "from": match.group("from").strip(),
                "to": match.group("to").strip(),
            },
        ))

    match = _DE_LLC_TO_CORPORATION_TRANSFORMATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "legal_form_changed", "de.text.llc_to_corporation_transformation_single_owner.v1",
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
        ))

    match = _DE_QUALIFIED_FACTS_CORRECTION_REMAINDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.qualified_facts_correction_remainder.v1",
            {
                "kind": "contribution_in_kind_and_acquisition",
                "action": "corrected_text_completed",
                "business": match.group("business").strip(),
                "business_place": match.group("place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_sheet_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "shares_issued": _count(match.group("shares")),
                "share_kind": "Namenaktien",
                "share_nominal": match.group("share_nominal"),
                "receivable_credited": match.group("receivable"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
