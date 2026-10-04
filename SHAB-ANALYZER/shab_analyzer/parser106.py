from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_REGISTRATION_CONTINUED_LEGAL_BASIS = re.compile(
    r"^\((?P<legal_basis>art\.\s*159a\s+al\.\s*2\s+lit\.\s*b\s+ORC)\)\.?$",
    re.I | re.UNICODE,
)
_IT_OWNER_CONTINUES = re.compile(
    r"^Il titolare continua la propria attività,\s*l['’]iscrizione sussiste\.?$",
    re.I | re.UNICODE,
)
_FR_VICE_PRESIDENT_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que "
    r"l['’]administratrice\s+(?P<name>[^,.;]+?)\s+est vice-présidente\.?$",
    re.I | re.UNICODE,
)
_FR_ORDINARY_PARTICIPATION_CAPITAL_INCREASE = re.compile(
    r"^Augmentation ordinaire du capital-participation porté de CHF\s+"
    r"(?P<previous_total>[\d'.]+)\s+à CHF\s+(?P<total>[\d'.]+),\s*par "
    r"l['’]émission de\s+(?P<issued>[\d']+)\s+bons de CHF\s+"
    r"(?P<issued_nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<reported_total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<count>[\d']+)\s+bons de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ALL_SHARES_TO_NEW_ASSOCIATE = re.compile(
    r"^La gérante\s+(?P<seller>[^,.;]+?)\s+a cédé ses\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*Gérants:\s*"
    r"l['’]associé\s+(?P=buyer),\s*président et\s+(?P=seller),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_SHARED_DETAILS = re.compile(
    r"^L['’]administrateur\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;()]+)\s*\((?P<place_canton>[A-Z]{2})\),\s*"
    r"sont élus liquidateurs\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"l['’]assemblée générale a modifié la clause statutaire relative à une "
    r"augmentation conditionnelle du capital-actions introduite par décision du\s+"
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4})\s+et modifiée précédemment le\s+"
    r"(?P<previous_change_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(pour les détails:\s*voir les statuts\)\.?$",
    re.I | re.UNICODE,
)
_FR_DISSOLUTION_SUSPENDED_NAME_RESTORED = re.compile(
    r"^Le président du\s+(?P<authority>Tribunal de l['’]arrondissement de\s+"
    r"[^.]+?)\s+a prononcé le\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+"
    r"\d{4})\s+l['’]effet suspensif de la dissolution prononcée le\s+"
    r"(?P<dissolution_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"La raison de commerce redevient\s+(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_NEW_MANAGER_AND_PRESIDENT = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*désormais à\s+"
    r"(?P<seller_place>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant\s+(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+);\s*"
    r"est élu président\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_APPOINTED_WITH_DOMICILE = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui est maintenant à\s+(?P<place>[^,.;]+),\s*"
    r"est nommé gérant\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_MIXED_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<administrator>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REPLACED_WITH_UIDS = re.compile(
    r"^\[gestrichen:\s*(?P<previous_place>[^\]]+)\]\.\s*"
    r"(?P<new_place>[^().]+?)\s*\((?P<new_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"(?P<context_place>[^().]+?)\s*"
    r"\((?P<context_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Genossenschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<recipient_canton>[A-Z]{2})\)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_OWNER_ORIGIN_CORRECTION = re.compile(
    r"^Bei TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+und SHAB-Nr\.\s*"
    r"(?P<notice>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"der Mutation des Heimatortes vom Inhaber wurde der Bisher-Text nicht "
    r"korrekt erfasst\.\s*Es sollte korrekt:\s*\[bisher:\s*"
    r"(?P<correct>[^\]]+)\]\s+statt\s+\[bisher:\s*(?P<incorrect>[^\]]+)\]\s+"
    r"lauten\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_ENTRY_OMITTED = re.compile(
    r"^\[die Aufführung des bisher-Eintrages ging vergessen\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_DELETED_AFTER_CESSATION = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuove disposizioni per la succursale:\s*Questa succursale è cancellata "
    r"a seguito di cessazione dell['’]esercizio\.?$",
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


def extract_parser106_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 106."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_REGISTRATION_CONTINUED_LEGAL_BASIS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.registration_continued_legal_basis.v1",
            {
                "kind": "registration_continued",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _IT_OWNER_CONTINUES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.owner_continues_registration.v1",
            {"kind": "registration_continued", "business_continues": True},
        ))

    match = _FR_VICE_PRESIDENT_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.vice_president_supplement.v1",
            match.group("name"), role="vice-présidente",
            extra={
                "action": "role_supplemented",
                "previous_role": "administratrice",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ORDINARY_PARTICIPATION_CAPITAL_INCREASE.search(leftover)
    if match and match.group("total") == match.group("reported_total"):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.ordinary_participation_capital_increase.v1",
            {
                "kind": "ordinary_participation_capital_increase",
                "currency": "CHF",
                "previous_total": match.group("previous_total"),
                "total": match.group("total"),
                "issued_participation_certificates": _count(match.group("issued")),
                "issued_participation_certificate_nominal": match.group("issued_nominal"),
                "participation_certificates_count": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "registered": True,
                "transfer_restricted": True,
                "fully_paid": True,
            },
        ))

    match = _FR_MANAGER_ALL_SHARES_TO_NEW_ASSOCIATE.search(leftover)
    if match and match.group("nominal") == match.group("buyer_nominal"):
        consume(match)
        rule_id = "fr.persons.manager_all_shares_to_new_associate.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="gérante",
                extra={
                    "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_before": _count(match.group("transferred")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": 0,
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé-gérant président",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                    "heimat": match.group("origin").strip(),
                    "new_associate": True,
                },
            ),
        ])

    match = _FR_TWO_LIQUIDATORS_SHARED_DETAILS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_liquidators_shared_details.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"), role="liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "role_changed", "previous_role": "administrateur"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place"), role="liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "place_canton": match.group("place_canton").upper(),
                },
            ),
        ])

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.conditional_capital_clause_changed_history.v1",
            {
                "kind": "conditional_share_capital_clause",
                "action": "changed",
                "decision_date": _iso_date(match.group("decision_date")),
                "introduced_date": _iso_date(match.group("introduced_date")),
                "previous_change_date": _iso_date(match.group("previous_change_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_DISSOLUTION_SUSPENDED_NAME_RESTORED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.dissolution_suspended_name_restored.v1",
            {
                "kind": "dissolution_suspended",
                "action": "suspended",
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
                "dissolution_date": _french_date(match.group("dissolution_date")),
                "company_name_restored": match.group("name").strip(),
            },
        ))

    match = _FR_MANAGER_TRANSFER_NEW_MANAGER_AND_PRESIDENT.search(leftover)
    if match and match.group("nominal") == match.group("remaining_nominal"):
        consume(match)
        rule_id = "fr.persons.manager_transfer_new_manager_and_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"),
                place=match.group("seller_place"), role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": match.group("buyer").strip(),
                    "domicile_changed": True,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("buyer_place"), role="associé-gérant",
                extra={
                    "action": "appointed_and_shares_received",
                    "counterparty": match.group("seller").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                    "heimat": match.group("origin").strip(),
                    "new_associate": True,
                },
            ),
        ])

    match = _FR_MANAGER_APPOINTED_WITH_DOMICILE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_appointed_with_domicile.v1",
            match.group("name"), place=match.group("place"), role="gérant",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed", "domicile_changed": True},
        ))

    match = _FR_TWO_ADMINISTRATORS_MIXED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_administrators_mixed_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"), role="président",
                signing="Einzelunterschrift", extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                },
            ),
        ])

    match = _DE_BRANCH_REPLACED_WITH_UIDS.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.branch_replaced_with_uids.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {"action": "removed", "place": match.group("previous_place").strip()},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "added",
                    "place": match.group("new_place").strip(),
                    "branch_uid": match.group("new_uid"),
                    "context_branch_place": match.group("context_place").strip(),
                    "context_branch_uid": match.group("context_uid"),
                },
            ),
        ])

    match = _DE_COOPERATIVE_ASSET_TRANSFER_NO_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.cooperative_asset_transfer_no_consideration.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "liabilities_kind": "third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_canton": match.group("recipient_canton").upper(),
                "recipient_uid": match.group("uid"),
                "consideration": "keine",
                "consideration_kind": "none",
            },
        ))

    match = _DE_OWNER_ORIGIN_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.owner_origin_previous_text_corrected.v1",
            {
                "action": "corrected",
                "kind": "owner_origin_previous_text",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice": match.group("notice"),
                "notice_date": _iso_date(match.group("notice_date")),
                "correct_previous_text": match.group("correct").strip(),
                "incorrect_previous_text": match.group("incorrect").strip(),
            },
        ))

    match = _DE_PREVIOUS_ENTRY_OMITTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.previous_entry_omitted.v1",
            {
                "action": "supplemented",
                "kind": "previous_entry",
                "previous_entry_omitted": True,
            },
        ))

    match = _IT_BRANCH_DELETED_AFTER_CESSATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_deleted_after_cessation.v1",
            {
                "action": "removed",
                "reason": "business_ceased",
                "head_office": match.group("head_office").strip(),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
