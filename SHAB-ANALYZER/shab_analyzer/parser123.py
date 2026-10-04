from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_COMMITTEE_FOUR_MEMBERS_RESTRICTED_SIGNING = re.compile(
    r"^Nouveaux membres du comité toutefois avec le président:\s*"
    r"(?P<name1>[^,.;]+),\s*à\s+(?P<place1>[^,.;()]+)\s*\((?P<country1>[^)]+)\),\s*"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*tous deux du\s+"
    r"(?P<common_country>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*et\s+"
    r"(?P<name4>[^,.;]+),\s*des\s+(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;()]+)\s*\((?P<country4>[^)]+)\)$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_AND_SECOND_MANAGER_APPOINTED = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+au gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"nouvel associé;\s*continue à signer collectivement à deux\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.\s*L['’]associée\s+"
    r"(?P<manager>[^,.;]+),\s*désormais à\s+(?P<manager_place>[^,.;]+),\s*"
    r"est nommée gérante$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE_POSTFIX = re.compile(
    r"^Nouveau membre du conseil de fondation:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;()]+?)(?:\s*\((?P<country>[^)]+)\))?,\s*sans signature$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_BRANCH_FRAGMENT = re.compile(
    r"^(?P<place>[^,.;()]+)\s*\((?P<uid>CHE-\d{3}[.-]\d{3}[.-]\d{3})\)$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_START = re.compile(
    r"^Beginn:\s*(?P<date>\d{2}\.\d{2}\.\d{4})$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_ART_260_CLAIMS = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte Gesellschaft "
    r"wird auf Grund des\s+(?P<document>Urteils)\s+des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zwecks Geltendmachung der "
    r"Ansprüche nach\s+(?P<legal_basis>Art\.\s*260 SchKG)\s+wieder in das "
    r"Handelsregister eingetragen und besteht entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>.+)\]$",
    re.I | re.UNICODE,
)
_DE_DOMICILE_CORRECTED_REGISTER_NOTICE = re.compile(
    r"^Tagesregister TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}):\s*Der bisherige Wohnsitz von\s+"
    r"(?P<name>.+?)\s+war nicht\s+(?P<previous_place>.+?),\s*sondern\s+"
    r"(?P<place>.+)$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant président\s+(?P<seller1>[^,.;]+)\s+cède\s+"
    r"(?P<transferred1>[\d']+)\s+de ses\s+(?P<before1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*et l['’]associé-gérant\s+(?P<seller2>[^,.;]+)\s+"
    r"(?P<transferred2>[\d']+)\s+de ses\s+(?P<before2>[\d']+)\s+parts de CHF\s+"
    r"(?P=nominal),\s*à\s+(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P=nominal),\s*gérant\s*;\s*(?P=seller1)\s+et\s+"
    r"(?P=seller2)\s+reste chacun titulaire de\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P=nominal)$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_ONLY_WITH_MANAGEMENT = re.compile(
    r"^Signature collective à deux,\s*toutefois uniquement avec un membre de la "
    r"direction est conférée à\s+(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?),\s*à\s+(?P<authority_place>[^,.;]+),\s*a suspendue la "
    r"procédure de faillite ouverte le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})$",
    re.I | re.UNICODE,
)
_IT_PREVIOUS_BRANCH_IDENTIFIER_FRAGMENT = re.compile(
    r"^\[finora:\s*(?P<place>[^()\]]+)\s*\((?P<registry_id>CH-[\d.-]+)\)\]$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_NEW_SOLE_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P=nominal);\s*lequel associé "
    r"est un outre nommé gérant unique\s+(?P=seller),\s*jusqu['’]ici gérant,\s*"
    r"est maintenant titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P=nominal)\s+et continue de signer individuellement$",
    re.I | re.UNICODE,
)
_FR_VICE_PRESIDENT_APPOINTED_COLLECTIVE = re.compile(
    r"^(?P<name>[^,.;]+),\s*nommé(?:e)?\s+(?P<role>vice-président(?:e)?),\s*"
    r"signe désormais collectivement à deux$",
    re.I | re.UNICODE,
)
_DE_PENSION_FOUNDATION_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung\s*\(Vorsorgeeinrichtung\)\s*überträgt "
    r"gemäss Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s*auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\(CHE-\s*(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_AND_TWO_MANAGERS = re.compile(
    r"^(?P<president>[^,.;]+),\s*gérant,\s*nommé président,\s*signe désormais "
    r"collectivement à deux\.\s*(?P<name1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*des\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*sont gérants$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_REMOVED = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\]\s*"
    r"\[gestrichen:\s*(?P<previous>Für die Verbindlichkeiten der Genossenschaft "
    r"haftet nur deren Vermögen\.)\]$",
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


def extract_parser123_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 123."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_COMMITTEE_FOUR_MEMBERS_RESTRICTED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.committee_four_members_restricted_signing.v1"
        for index in range(1, 5):
            country = match.group("common_country") if index in (1, 2) else match.group(f"origin{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "origin": country.strip(),
                    "signing_restriction": "toutefois avec le président",
                    **({"country": match.group(f"country{index}").strip()} if index in (1, 4) else {}),
                },
            ))

    match = _FR_MANAGER_TRANSFER_AND_SECOND_MANAGER_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_and_second_manager_appointed.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé",
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
                place=match.group("buyer_place"), role="gérant et associé",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    **common, "action": "shares_received_and_became_associate",
                    "shares_received": _count(match.group("transferred")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("manager_place"), role="gérante",
                signing="Kollektivunterschrift zu zweien", extra={"action": "appointed"},
            ),
        ])

    match = _FR_FOUNDATION_MEMBER_WITHOUT_SIGNATURE_POSTFIX.search(leftover)
    if match:
        consume(match)
        extra = {"action": "appointed", "origin": match.group("origin").strip(), "without_signature": True}
        if match.group("country"):
            extra["country"] = match.group("country").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_without_signature_postfix.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation", signing="ohne Zeichnungsberechtigung",
            extra=extra,
        ))

    match = _DE_ADDITIONAL_BRANCH_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.additional_branch_fragment.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": "CHE-" + match.group("uid")[4:].replace("-", "."),
            },
        ))

    match = _DE_BUSINESS_START.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.business_start_date.v1",
            {"kind": "business_start_date", "date": _iso_date(match.group("date"))},
        ))

    match = _DE_COMPANY_REINSTATED_FOR_ART_260_CLAIMS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_for_art260_claims.v1",
            {
                "kind": "registration_reinstated", "reason": "claims_under_art_260_schkg",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": match.group("legal_basis"),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _DE_DOMICILE_CORRECTED_REGISTER_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.domicile_corrected_register_notice.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected", "previous_place": match.group("previous_place").strip(),
                "entry_number": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_transfer_to_new_manager.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant" + (" président" if index == 1 else ""),
                extra={
                    **common, "action": "shares_transferred",
                    "previous_shares_count": _count(match.group(f"before{index}")),
                    "shares_transferred": _count(match.group(f"transferred{index}")),
                    "shares_count": _count(match.group("remaining")),
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"), place=match.group("place"),
            role="associé-gérant", signing="Kollektivunterschrift zu zweien",
            extra={
                **common, "action": "appointed_and_shares_received",
                "origin": match.group("origin").strip(),
                "shares_received": _count(match.group("buyer_count")),
                "shares_count": _count(match.group("buyer_count")),
            },
        ))

    match = _FR_SIGNING_GRANTED_ONLY_WITH_MANAGEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.collective_signing_only_with_management.v1",
            match.group("name"), place=match.group("place"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "granted", "origin": match.group("origin").strip(),
                "with_role": "membre de la direction",
            },
        ))

    match = _FR_BANKRUPTCY_PROCEEDINGS_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_proceedings_suspended.v1",
            {
                "kind": "bankruptcy_proceedings_suspended",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "authority_place": match.group("authority_place").strip(),
            },
        ))

    match = _IT_PREVIOUS_BRANCH_IDENTIFIER_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.previous_branch_identifier_fragment.v1",
            {
                "action": "identifier_replaced", "place": match.group("place").strip(),
                "previous_branch_id": match.group("registry_id"),
            },
        ))

    match = _FR_SHARE_TRANSFER_TO_NEW_SOLE_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_new_sole_manager.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="ancien gérant et associé",
                signing="Einzelunterschrift",
                extra={
                    **common, "action": "shares_transferred",
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"), place=match.group("place"),
                role="associé-gérant unique", signing="Einzelunterschrift",
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "origin": match.group("origin").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])

    match = _FR_VICE_PRESIDENT_APPOINTED_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.vice_president_appointed_collective.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_and_signing_changed"},
        ))

    match = _DE_PENSION_FOUNDATION_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.pension_foundation_asset_transfer.v1",
            {
                "date": _iso_date(match.group("date")), "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "currency": "CHF",
                "consideration": "none",
            },
        ))

    match = _FR_PRESIDENT_AND_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_president_and_two_managers.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="gérant président", signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed_president_and_signing_changed"},
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "origin": match.group(f"origin{index}").strip()},
            ))

    match = _DE_COOPERATIVE_LIABILITY_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.cooperative_liability_removed_assets_only.v1",
            {
                "kind": "member_liability", "action": "entry_removed",
                "reason": "changed_registration_rules", "previous": match.group("previous"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
