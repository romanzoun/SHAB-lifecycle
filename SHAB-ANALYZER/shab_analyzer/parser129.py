from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BUSINESS_START_DATE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),?\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la date de "
    r"commencement de la société est le\s+(?P<date>\d{1,2}(?:er)?\s+"
    r"[A-Za-zÀ-ÿ]+\s+\d{4})\s*\(et non le\s+"
    r"(?P<previous_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SECOND_ADDRESS_REMOVED = re.compile(
    r"^Radiation de la seconde adresse:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_WITH_LABEL = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<to_capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?:(?P<to_paid_currency>[A-Z]{3})\s+)?(?P<to_paid>[\d'.]+)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*(?P<from_currency>[A-Z]{3})\s+"
    r"(?P<from_capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?:(?P<from_paid_currency>[A-Z]{3})\s+)?(?P<from_paid>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PETITION_WITHDRAWN = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde das Konkursbegehren "
    r"widerrufen\.\s*Infolgedessen besteht die Firma entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*Mit Verfügung des\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+ist über den Inhaber dieses "
    r"Einzelunternehmens mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_FULL_PERSON_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"nom exact de\s+(?P<previous_name>[^,.;]+?)\s+est\s+"
    r"(?P<name>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_CIVIL_STATUS_NAMES_CHANGED = re.compile(
    r"^Par suite de changement d['’]état civil,\s*"
    r"(?P<previous_name1>[^,.;]+?)\s+porte désormais le nom de\s+"
    r"(?P<name1>[^,.;]+?),\s*"
    r"(?P<previous_name2>[^,.;]+?)\s+le nom de\s+"
    r"(?P<name2>[^,.;]+?)\s+et\s+"
    r"(?P<previous_name3>[^,.;]+?)\s+le nom de\s+"
    r"(?P<name3>[^,.;]+?)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_OPTIONAL_LIABILITIES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)"
    r"(?:\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+))?\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"(?:\(vormals:\s*(?P<previous_recipient>[^)]+)\)\s*)?"
    r"\((?P<uid>CHE-\d{3}[.-]\d{3}[.-]\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ABOLISHED_DELETION_PENDING = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Aufhebung der Zweigniederlassung "
    r"von Amtes wegen infolge Löschung der Gesellschaft am Hauptsitz vom\s+"
    r"(?P<head_office_deletion_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"\[Die Löschung erfolgt,\s*sobald die Zustimmungen der Steuerverwaltungen "
    r"vorliegen\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+?)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérante\s*;\s*"
    r"(?P=seller),\s*lequel est élu président,\s*reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED_FUTURE_TENSE = re.compile(
    r"^Zweigniederlassung neu:\s*\[Folgende Zweigniederlassung wird gelöscht\]\s*"
    r"\[gestrichen:\s*(?P<place>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_OFFICE_ADDED = re.compile(
    r"^Geschäftsstelle:\s*(?P<street>[^,]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die gewährte provisorische Nachlassstundung um\s+"
    r"(?P<duration>.+?)\s+bis\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<previous_authority>.+?)\s+eine provisorische Nachlassstundung von\s+"
    r"(?P<previous_duration>.+?)\s+bis\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NON_PUBLIC_STATUTES_CHANGE = re.compile(
    r"^\[Modification des statuts sur un point/des points non soumis à publication\]\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_ORGANIZATION_COMMISSIONER = re.compile(
    r"^Mit Entscheid der\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive "
    r"Nachlassstundung von\s+(?P<duration>.+?)\s+bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Als Sachwalterin wird die\s+"
    r"(?P<commissioner>.+?),\s*in\s+(?P<commissioner_place>[^()]+?)\s*"
    r"\((?P<commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*ernannt\.\s*"
    r"\[bisher:\s*Mit Entscheid der\s+(?P<previous_authority>.+?),\s*vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde die am\s+"
    r"(?P<previous_grant_date>\d{2}\.\d{2}\.\d{4})\s+bewilligte provisorische "
    r"Nachlassstundung verlängert bis zum\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\.\s*Sachwalterin ist die\s+"
    r"(?P<previous_commissioner>.+?),\s*in\s+"
    r"(?P<previous_commissioner_place>[^()]+?)\s*"
    r"\((?P<previous_commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_LIMITED_PARTNER_WITH_PROXY = re.compile(
    r"^Nouvel associé commanditaire:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*avec une commandite "
    r"de CHF\s+(?P<contribution>[\d'.]+),\s*lequel signe par procuration "
    r"collective à deux\.?$",
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
    token = raw.strip().split()[0].lower()
    if token.isdigit():
        return int(token)
    return _GERMAN_NUMBERS.get(token)


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


def extract_parser129_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 129."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BUSINESS_START_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.business_start_date_corrected.v2",
            {
                "kind": "business_start_date", "action": "corrected",
                "date": _french_date(match.group("date")),
                "previous_date": _french_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_SECOND_ADDRESS_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.second_address_removed.v1",
            {
                "kind": "additional_address", "action": "removed",
                "address": match.group("address").strip(),
            },
        ))

    match = _DE_HEAD_OFFICE_CAPITAL_WITH_LABEL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_capital_with_label.v1",
            {
                "scope": "head_office", "currency": match.group("currency"),
                "from_nominal": match.group("from_capital"),
                "to_nominal": match.group("to_capital"),
                "from_paid": match.group("from_paid"),
                "to_paid": match.group("to_paid"),
            },
        ))

    match = _DE_BANKRUPTCY_PETITION_WITHDRAWN.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_petition_withdrawn.v1",
            {
                "kind": "bankruptcy_revoked", "scope": "owner",
                "action": "petition_withdrawn", "previous_status_restored": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "previous_authority": match.group("previous_authority").strip(),
            },
        ))

    match = _FR_FULL_PERSON_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.full_name_corrected.v1",
            match.group("name"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_THREE_CIVIL_STATUS_NAMES_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_civil_status_names_changed.v1"
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                extra={
                    "action": "name_changed", "reason": "civil_status_change",
                    "previous_name": match.group(f"previous_name{index}").strip(),
                },
            ))

    match = _DE_ASSET_TRANSFER_OPTIONAL_LIABILITIES.search(leftover)
    if match:
        consume(match)
        raw_recipient_uid = match.group("uid")
        recipient_uid = "CHE-" + raw_recipient_uid[4:].replace("-", ".")
        payload = {
            "date": _iso_date(match.group("date")),
            "assets": match.group("assets"),
            "liabilities": match.group("liabilities"),
            "liabilities_kind": (
                "third_party_capital" if match.group("liabilities") else None
            ),
            "liabilities_transferred": bool(match.group("liabilities")),
            "currency": "CHF", "recipient": match.group("recipient").strip(),
            "recipient_place": match.group("place").strip(),
            "recipient_uid": recipient_uid,
            "consideration": match.group("consideration"),
        }
        if match.group("previous_recipient"):
            payload["previous_recipient"] = match.group("previous_recipient").strip()
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_optional_liabilities.v1",
            payload,
        ))

    match = _DE_BRANCH_ABOLISHED_DELETION_PENDING.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_abolished_deletion_pending.v1",
            {
                "action": "abolished", "reason": "head_office_deleted",
                "head_office_deletion_date": _iso_date(
                    match.group("head_office_deletion_date")
                ),
                "registry_deletion_pending": True,
                "pending_tax_authority_consent": True,
            },
        ))

    match = _FR_MANAGER_TRANSFER_AND_PRESIDENCY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_and_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_elected_president",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": seller, "heimat": match.group("origin").strip(),
                    "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_LEGACY_BRANCH_REMOVED_FUTURE_TENSE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.legacy_branch_removed_future_tense.v1",
            {"action": "removed", "place": match.group("place").strip()},
        ))

    match = _DE_BUSINESS_OFFICE_ADDED.search(leftover)
    if match:
        consume(match)
        street = match.group("street").strip()
        postal_code = match.group("postal_code")
        locality = match.group("locality").strip()
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.business_office_added.v1",
            {
                "kind": "business_office", "action": "added",
                "address": f"{street}, {postal_code} {locality}",
                "street": street, "postal_code": postal_code, "locality": locality,
            },
        ))

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_history.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "provisional",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration": match.group("duration").strip(),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_duration": match.group("previous_duration").strip(),
                "previous_duration_months": _duration_months(
                    match.group("previous_duration")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        ))

    match = _FR_NON_PUBLIC_STATUTES_CHANGE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.non_public_statutes_change.v1",
            {
                "kind": "non_public_points", "action": "modified",
                "details_published": False,
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_ORGANIZATION_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.definitive_moratorium_organization_commissioner.v1"
        commissioner = match.group("commissioner").strip()
        commissioner_place = match.group("commissioner_place").strip()
        commissioner_uid = match.group("commissioner_uid")
        common = {
            "commissioner": commissioner,
            "commissioner_place": commissioner_place,
            "commissioner_uid": commissioner_uid,
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "composition_moratorium_granted",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration": match.group("duration").strip(),
                    "duration_months": _duration_months(match.group("duration")),
                    "until": _iso_date(match.group("until")),
                    "previous_moratorium_type": "provisional",
                    "previous_decision_date": _iso_date(
                        match.group("previous_decision_date")
                    ),
                    "previous_grant_date": _iso_date(
                        match.group("previous_grant_date")
                    ),
                    "previous_until": _iso_date(match.group("previous_until")),
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner,
                place=commissioner_place, uid=commissioner_uid, role="Sachwalterin",
                extra={"action": "appointed", "uid": commissioner_uid},
            ),
        ])

    match = _FR_NEW_LIMITED_PARTNER_WITH_PROXY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_limited_partner_with_proxy.v1",
            match.group("name"), place=match.group("place"),
            role="associé commanditaire", signing="Kollektivprokura zu zweien",
            extra={
                "action": "appointed", "new_partner": True,
                "heimat": match.group("origin").strip(),
                "country": match.group("country").upper(),
                "limited_partnership_contribution": match.group("contribution"),
                "currency": "CHF",
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
