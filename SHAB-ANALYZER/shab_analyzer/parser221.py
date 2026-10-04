from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_FULL_ADDRESS_AND_ONE_ADDITIONAL_ADDRESS = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>[^,;.]+?)\s+"
    r"(?P<house>\d+[A-Za-z]?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^.;]+)\.\s*Neue zusätzliche Adressen:\s*"
    r"(?P<additional_street>[^,;.]+?)\s+"
    r"(?P<additional_house>\d+[A-Za-z]?),\s*"
    r"(?P<additional_postal_code>\d{4})\s+"
    r"(?P<additional_locality>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_REINSTATED_AFTER_SUMMARY_REOPENING = re.compile(
    r"^Diese infolge Konkurses im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*159 Abs\.\s*5 lit\.\s*a HRegV)\s+am\s+"
    r"(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+von Amtes wegen gelöschte "
    r"Gesellschaft wird wieder als durch Konkurs aufgelöst in das "
    r"Handelsregister eingetragen,\s*nachdem\s+(?P<authority>.+?)\s+mit\s+"
    r"(?P<decision_kind>Verfügung|Entscheid)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die am\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+angeordnete Einstellung "
    r"des Verfahrens mangels Aktiven widerrufen und die Wiedereröffnung "
    r"eines\s+(?P<procedure>summarischen Verfahrens)\s+angeordnet hat\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_TRANSFEROR_DELETED_AFTER_ACQUIRER_BANKRUPTCY = re.compile(
    r"^Die übernehmende Gesellschaft\s+[“\"](?P<acquirer>.+?)[”\"]\s+"
    r"wurde mit Tagebucheintrag Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+zufolge Konkurses im "
    r"Handelsregister des Kantons\s+(?P<register_canton>[^.]+)\s+gelöscht\.\s*"
    r"Demzufolge wird auch die übertragende Gesellschaft\s+"
    r"[“\"](?P<transferor>.+?)[”\"]\s+von Amtes wegen gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_REPLACED = re.compile(
    r"^(?P<previous_name>[^()“”\"]+?)\s+n['’]est plus organe de révision\.\s*"
    r"Nouvel organe de révision:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_TREASURER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom de la\s+"
    r"(?P<role>membre du comité et trésorière)\s+est\s+"
    r"(?P<name>[^()]+?)\s*\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ERRONEOUSLY_REMOVED_REINSTATED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce\s+"
    r"(?:sens|dens)\s+que l['’](?P<role>associée)\s+"
    r"(?P<name>.+?)\s+ayant été radiée par erreur;\s*elle est "
    r"réinscrite\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_PAIR_PROXY_REVOKED = re.compile(
    r"^Signature individuelle a été conférée à\s+"
    r"(?P<name1>[^,;]+?)\s+et à\s+(?P<name2>[^,;]+?);\s*"
    r"leur procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_CLOSED_BUSINESS_CONTINUES = re.compile(
    r"^La procédure de faillite,\s*suspendue faute d['’]actifs,\s*a été "
    r"clôturée le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*Le titulaire "
    r"continue l['’]exploitation de son entreprise\.\s*L['’]inscription "
    r"subsiste\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NAME_AND_IDENTIFIER_CHANGED = re.compile(
    r"^L['’]organe de révision\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.-]+)\)\s+a modifié sa raison sociale "
    r"en\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_PAIR_REPLACED = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+)\s+ne sont plus membres "
    r"du comité de Caisse;\s*leurs pouvoirs sont radiés\.\s*"
    r"(?P<name1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3})\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*sont membres du "
    r"comité de Caisse(?:,\s*avec\s+"
    r"(?P<signing>signature collective à deux))?\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_BRANCHES_REMOVED = re.compile(
    r"^Zweigniederlassung neu:\s*"
    r"(?:\[Folgende Zweigniederlassungen sind aufgehoben worden:\]\s*)?"
    r"\[gestrichen:\s*(?P<place1>[^()\]]+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+HR\s+"
    r"(?P<register_canton1>[A-Z]{2})\]\.\s*"
    r"\[gestrichen:\s*(?P<place2>[^()\]]+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+HR\s+"
    r"(?P<register_canton2>[A-Z]{2})\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_MALFORMED_RECIPIENT_UID_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss "
    r"Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})(?P<uid_error>\?)\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*du\s+"
    r"(?P<origin>[^,.;]+),\s*(?:au|à)\s+(?P<place>[^,.;]+),\s*"
    r"est membre du conseil d['’]administration(?:\s+avec\s+"
    r"(?P<signing>signature collective à deux))?\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_BANKRUPTCY_OPENED = re.compile(
    r"^Name neu:\s*(?P<name>.+? in Liquidation)\.\s*Mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+über die Stiftung mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*den Konkurs eröffnet,\s*"
    r"womit sie aufgehoben ist\.?$",
    re.I | re.UNICODE,
)
_IT_REMOVED_SOLE_PROPRIETOR_CONTRIBUTION = re.compile(
    r"^\[radiati:\s*Attivo e passivo della cancellata ditta individuale\s+"
    r"[“\"](?P<source>.+?)[”\"],\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Attivo:\s*(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.-]+)\.\s*"
    r"Passivo:\s*(?P=currency)\s+(?P<liabilities>[\d'.-]+)\.\s*"
    r"Attivo netto:\s*(?P=currency)\s+(?P<net_assets>[\d'.-]+)\s+accettato "
    r"per tale importo,\s*interamente computato sul capitale azionario\.\s*"
    r"Bilancio di ripresa:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid der\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine provisorische "
    r"Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Als Sachwalterin wird "
    r"die\s+(?P<commissioner>.+?),\s*Herr\s+(?P<representative>[^,]+),\s*"
    r"(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^,.;]+),\s*ernannt\.?$",
    re.I | re.UNICODE,
)


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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser221_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 221."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_FULL_ADDRESS_AND_ONE_ADDITIONAL_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.full_address_and_one_additional_address.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "registered_address", "action": "completed",
                    "address": (
                        f"{match.group('street').strip()} {match.group('house')}, "
                        f"{match.group('postal_code')} {match.group('locality').strip()}"
                    ),
                    "street": match.group("street").strip(),
                    "house_number": match.group("house"),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "additional_address", "action": "added",
                    "address": (
                        f"{match.group('additional_street').strip()} "
                        f"{match.group('additional_house')}, "
                        f"{match.group('additional_postal_code')} "
                        f"{match.group('additional_locality').strip()}"
                    ),
                    "street": match.group("additional_street").strip(),
                    "house_number": match.group("additional_house"),
                    "postal_code": match.group("additional_postal_code"),
                    "locality": match.group("additional_locality").strip(),
                },
            ),
        ], ""

    match = _DE_BANKRUPTCY_REINSTATED_AFTER_SUMMARY_REOPENING.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.bankruptcy_reinstated_after_summary_reopening.v1", {
                "kind": "bankruptcy", "action": "reopened_and_reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "suspension_date": _iso_date(match.group("suspension_date")),
                "authority": match.group("authority").strip(),
                "decision_kind": match.group("decision_kind").lower(),
                "procedure": match.group("procedure").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _DE_TRANSFEROR_DELETED_AFTER_ACQUIRER_BANKRUPTCY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted",
            "de.text.transferor_deleted_after_acquirer_bankruptcy.v1", {
                "action": "deleted_ex_officio",
                "reason": "acquiring_company_deleted_after_bankruptcy",
                "company_name": match.group("transferor").strip(),
                "acquiring_company": match.group("acquirer").strip(),
                "acquiring_company_entry": match.group("entry"),
                "acquiring_company_entry_date": _iso_date(match.group("entry_date")),
                "register_canton": match.group("register_canton").strip(),
            },
        )], ""

    match = _FR_AUDITOR_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.auditor_replaced.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                role="organe de révision", extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="organe de révision",
                uid=match.group("uid"), extra={"action": "appointed"},
            ),
        ], ""

    match = _FR_COMMITTEE_TREASURER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.committee_treasurer_name_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSOCIATE_ERRONEOUSLY_REMOVED_REINSTATED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.associate_erroneously_removed_reinstated.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "reinstated_after_erroneous_removal",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_INDIVIDUAL_SIGNING_PAIR_PROXY_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.individual_signing_pair_proxy_revoked.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                signing="Einzelunterschrift", extra={
                    "action": "signing_replaced",
                    "previous_signing": "procuration",
                    "previous_signing_revoked": True,
                },
            )
            for group in ("name1", "name2")
        ], ""

    match = _FR_BANKRUPTCY_CLOSED_BUSINESS_CONTINUES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_closed_business_continues.v1", {
                "kind": "bankruptcy", "scope": "owner", "action": "closed",
                "date": _iso_date(match.group("date")),
                "previously_suspended_for_lack_of_assets": True,
                "business_continues": True,
                "registration_remains": True,
            },
        )], ""

    match = _FR_AUDITOR_NAME_AND_IDENTIFIER_CHANGED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.auditor_name_and_identifier_changed.v1",
            match.group("name"), role="organe de révision",
            uid=match.group("uid"), extra={
                "action": "registered_name_and_identifier_changed",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
            },
        )], ""

    match = _FR_COMMITTEE_PAIR_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_pair_replaced.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group),
                role="membre du comité de Caisse", extra={
                    "action": "removed", "powers_revoked": True,
                },
            )
            for group in ("removed1", "removed2")
        ]
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du comité de Caisse",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing") else None
                ), extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").upper(),
                },
            ))
        return events, ""

    match = _DE_TWO_BRANCHES_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "de.text.two_branches_removed.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "removed", "place": match.group(f"place{index}").strip(),
                    "branch_uid": match.group(f"uid{index}"),
                    "register_canton": match.group(f"register_canton{index}").upper(),
                },
            )
            for index in (1, 2)
        ], ""

    match = (
        _DE_ASSET_TRANSFER_MALFORMED_RECIPIENT_UID_NO_CONSIDERATION
        .fullmatch(leftover)
    )
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.asset_transfer_malformed_recipient_uid_no_consideration.v1", {
                "date": _iso_date(match.group("date")),
                "source": match.group("source").strip(),
                "assets": match.group("assets"),
                "currency": match.group("currency").upper(),
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_uid_raw": match.group("uid") + match.group("uid_error"),
                "identifier_source_typo": True,
                "consideration": match.group("consideration").lower(),
                "gratuitous": True,
            },
        )], ""

    match = _FR_BOARD_MEMBER_APPOINTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_appointed.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration",
            signing=(
                "Kollektivunterschrift zu zweien"
                if match.group("signing") else None
            ), extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        )], ""

    match = _DE_FOUNDATION_BANKRUPTCY_OPENED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.foundation_bankruptcy_opened.v1", {
                "kind": "bankruptcy", "action": "opened",
                "organization_kind": "foundation",
                "company_name": match.group("name").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time").replace(".", ":"),
                "authority": match.group("authority").strip(),
                "organization_dissolved": True,
            },
        )], ""

    match = _IT_REMOVED_SOLE_PROPRIETOR_CONTRIBUTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed",
            "it.text.removed_sole_proprietor_contribution.v1", {
                "kind": "contribution_in_kind", "action": "removed",
                "source": match.group("source").strip(),
                "source_kind": "sole_proprietorship",
                "source_place": match.group("place").strip(),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "net_assets": match.group("net_assets"),
                "credited_to_share_capital": match.group("net_assets"),
                "balance_date": _iso_date(match.group("date")),
            },
        )], ""

    match = _DE_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        duration = match.group("duration").lower()
        if duration in _GERMAN_NUMBERS:
            address = (
                f"{match.group('street').strip()} {match.group('house')}, "
                f"{match.group('postal_code')} {match.group('place').strip()}"
            )
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed",
                "de.text.provisional_moratorium_with_commissioner.v1", {
                    "kind": "composition_moratorium_granted", "action": "granted",
                    "moratorium_type": "provisional",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "duration_months": _GERMAN_NUMBERS[duration],
                    "until": _iso_date(match.group("until")),
                    "commissioner": match.group("commissioner").strip(),
                    "commissioner_representative": match.group("representative").strip(),
                    "commissioner_address": address,
                    "commissioner_postal_code": match.group("postal_code"),
                    "commissioner_place": match.group("place").strip(),
                },
            )], ""

    return [], leftover
