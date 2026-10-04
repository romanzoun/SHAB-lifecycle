from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_FOUNDER_PURPOSE_RESERVATION_REMOVED = re.compile(
    r"^Radiation de la mention d['’]une réserve de modification du but en faveur "
    r"de la fondatrice selon l['’](?P<legal_basis>article\s+86a CC)$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_BECOMES_DIRECTOR = re.compile(
    r"^(?P<name>.+?)\s+jusqu['’]ici administrateur sans signature est dorénavant "
    r"administrateur directeur avec une signature collective à deux$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_FOR_INVESTMENT_CLAIMS = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"(?P<recipient_place>[^()]+?)\s*\((?P<recipient_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?);\s*der Gesamtwert der Ansprüche "
    r"entspricht dem Wert der übertragenen Aktiven,\s*welche per\s+"
    r"(?P<book_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+einen Buchwert von "
    r"CHF\s+(?P<book_value>[\d'.]+)\s+aufweisen$",
    re.I | re.UNICODE,
)
_DE_CORRECTED_FOUNDATION_VICE_PRESIDENT = re.compile(
    r"^Mit dem im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde der bisherige Text nicht richtig publiziert\.\s*Korrekt wäre:\s*"
    r"(?P<name>[^,.;]+,\s*[^,.;]+),\s*von\s+(?P<origin>.+?),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*(?P<role>Vizepräsident des Stiftungsrates),\s*"
    r"mit\s+(?P<signing>Kollektivunterschrift zu zweien)\s*"
    r"\[bisher:\s*(?P<previous_role>Mitglied des Stiftungsrates),\s*mit\s+"
    r"(?P<previous_signing>.+?),\s*in\s+(?P<previous_place>[^\]]+)\]$",
    re.I | re.UNICODE,
)
_IT_COMPANY_NAME_CASE_CORRECTED = re.compile(
    r"^Nuova ragione sociale:\s*(?P<name>.+?)\.\s*La ditta è stata erroneamente "
    r"pubblicata con la lettera\s+[\"“](?P<wrong_letter>[^\"”]+)[\"”]\s+minuscola "
    r"invece che correttamente con la lettera\s+[\"“](?P<correct_letter>[^\"”]+)"
    r"[\"”]\s+maiuscola$",
    re.I | re.UNICODE,
)
_FR_SHARE_NOMINAL_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le capital-actions "
    r"est composé de\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),?\s*\(et non de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+comme publié\)$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_GENDER_CORRECTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>.+?)\s+est\s+(?P<role>associé)\s*\(et non pas\s+"
    r"(?P<previous_role>associée)\)$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_SHARE_RESTRICTION_WITH_PARTICIPATION = re.compile(
    r"^\[bisher:\s*Die Übertragbarkeit der Namenaktien und der "
    r"Namenpartizipationsscheine ist nach Massgabe der Statuten beschränkt\.\]$",
    re.I | re.UNICODE,
)
_DE_EMPTY_TRANSACTION_TEXT_SUPPLEMENT = re.compile(
    r"^Nachtrag zu SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"folgender TR-Text\s*\[\s*\]$",
    re.I | re.UNICODE,
)
_FR_MERGER_SAME_SHAREHOLDER = re.compile(
    r"^Fusion:\s*reprise des actifs de CHF\s+(?P<assets>[\d'.]+)\s+et des "
    r"passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+de la "
    r"(?P<absorbed_legal_form>société anonyme)\s+(?P<absorbed_name>.+?),\s*à\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"selon contrat de fusion du\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et "
    r"bilan(?: intermédiaire)? au\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"La société reprenante détenant l['’]ensemble des actions de la société "
    r"transférante,\s*la fusion ne donne pas lieu à une augmentation du capital,\s*"
    r"ni à une attribution d['’]actions$",
    re.I | re.UNICODE,
)
_FR_BOARD_DELEGATION_AND_EXECUTIVE_ROLE_CORRECTED = re.compile(
    r"^Les administrateurs\s+(?P<president>.+?),\s*président,\s*et\s+"
    r"(?P<vice_president>.+?),\s*vice-président,\s*jusqu['’]ici délégués,\s*"
    r"continuent à signer collectivement à deux\.\s*"
    r"(?P<secretary>.+?)\s+n['’]est pas membre du conseil d['’]administration,\s*"
    r"mais bien secrétaire hors conseil et directrice générale\s*;\s*"
    r"l['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens$",
    re.I | re.UNICODE,
)
_IT_ARBITRATION_CLAUSE = re.compile(
    r"^Clausola arbitrale;\s*per i dettagli si rinvia allo statuto$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATE = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital par décision du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}):\s*pour les détails,\s*voir les statuts$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription no\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]associée gérante se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)$",
    re.I | re.UNICODE,
)
_DE_REGISTERED_PERSON_RENAMED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"(?P<role1>Gesellschafterin),\s*(?P<role2>Geschäftsführerin),\s*"
    r"(?P<signing>Einzelunterschrift),\s*heisst neu\s+(?P<name>.+)$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_TWO_NEW_UNSIGNED = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé,\s*a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+),\s*dont\s+(?P<count1>[\d']+)\s+à\s+"
    r"(?P<buyer1>[^,.;]+),\s*d['’](?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<count2>[\d']+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*nouveaux associés,\s*lesquels n['’]exercent pas "
    r"la signature sociale$",
    re.I | re.UNICODE,
)


_DE_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.lower().replace(".", "", 1).split()
    return f"{int(year):04d}-{_DE_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser125_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 125."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_FOUNDER_PURPOSE_RESERVATION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.founder_purpose_reservation_removed.v1",
            {
                "kind": "founder_purpose_change_reservation",
                "action": "removed",
                "beneficiary": "fondatrice",
                "legal_basis": match.group("legal_basis"),
            },
        ))

    match = _FR_ADMINISTRATOR_BECOMES_DIRECTOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_becomes_director.v1",
            match.group("name"), role="administrateur directeur",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "role_and_signing_changed",
                "previous_role": "administrateur",
                "previous_signing": "ohne Zeichnungsberechtigung",
            },
        ))

    match = _DE_ASSET_TRANSFER_FOR_INVESTMENT_CLAIMS.search(leftover)
    if match:
        consume(match)
        claims = [
            {"count": _count(count), "investment_group": group}
            for count, group in re.findall(
                r"sämtliche\s+([\d']+)\s+Ansprüche an der Anlagegruppe\s+[\"“]([^\"”]+)[\"”]",
                match.group("consideration"),
                re.I | re.UNICODE,
            )
        ]
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_for_investment_claims.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("recipient_place").strip(),
                "recipient_uid": match.group("recipient_uid"),
                "consideration_kind": "investment_group_claims",
                "consideration_claims": claims,
                "book_date": _german_date(match.group("book_date")),
                "book_value": match.group("book_value"),
            },
        ))

    match = _DE_CORRECTED_FOUNDATION_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.foundation_vice_president_corrected.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), signing=match.group("signing"),
            extra={
                "action": "role_signing_and_place_corrected",
                "origin": match.group("origin").strip(),
                "previous_role": match.group("previous_role"),
                "previous_signing": match.group("previous_signing").strip(),
                "previous_place": match.group("previous_place").strip(),
                "reference": {
                    "issue": match.group("issue"),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            },
        ))

    match = _IT_COMPANY_NAME_CASE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.company_name_letter_case_corrected.v1",
            {
                "action": "corrected",
                "to": match.group("name").strip(),
                "incorrect_letter": match.group("wrong_letter"),
                "correct_letter": match.group("correct_letter"),
                "correction_kind": "letter_case",
            },
        ))

    match = _FR_SHARE_NOMINAL_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_nominal_corrected.v1",
            {
                "kind": "share_structure_correction",
                "currency": "CHF",
                "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "nominal": match.group("nominal"),
                "previous_nominal": match.group("previous_nominal"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ASSOCIATE_GENDER_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_gender_corrected.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "role_label_corrected",
                "previous_role": match.group("previous_role"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_PREVIOUS_SHARE_RESTRICTION_WITH_PARTICIPATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.previous_share_restriction_with_participation.v1",
            {
                "kind": "share_transfer_restriction",
                "scope": ["Namenaktien", "Namenpartizipationsscheine"],
                "basis": "Statuten",
                "history_marker": "bisher",
            },
        ))

    match = _DE_EMPTY_TRANSACTION_TEXT_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.empty_transaction_text_supplement.v1",
            {
                "kind": "transaction_text_supplement",
                "action": "empty_supplement_recorded",
                "transaction_text": "",
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_MERGER_SAME_SHAREHOLDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.merger_same_shareholder.v1",
            {
                "kind": "absorption",
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_legal_form": match.group("absorbed_legal_form"),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "same_shareholder": True,
                "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _FR_BOARD_DELEGATION_AND_EXECUTIVE_ROLE_CORRECTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_delegation_and_executive_role_corrected.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        for group, role in (("president", "président"), ("vice_president", "vice-président")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role=role,
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "delegation_removed_signing_continued",
                    "previous_role": "administrateur délégué",
                    **reference,
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("secretary"),
            role="secrétaire hors conseil et directrice générale",
            extra={
                "action": "role_corrected",
                "previous_role": "membre du conseil d'administration",
                **reference,
            },
        ))

    match = _IT_ARBITRATION_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.arbitration_clause.v1",
            {
                "kind": "arbitration_clause",
                "action": "recorded",
                "details_in_statutes": True,
            },
        ))

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_NUMERIC_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_numeric_date.v1",
            {
                "kind": "conditional_capital_clause",
                "action": "introduced",
                "date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_name_corrected.v1",
            match.group("name"), role="associée-gérante",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_REGISTERED_PERSON_RENAMED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.registered_person_renamed.v1",
            match.group("name"),
            role=f"{match.group('role1')}; {match.group('role2')}",
            signing=match.group("signing"),
            extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
                "roles": [match.group("role1"), match.group("role2")],
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_TO_TWO_NEW_UNSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_to_two_new_unsigned.v1"
        seller = match.group("seller").strip()
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé",
            extra={
                **common,
                "action": "shares_transferred",
                "shares_transferred": transferred,
                "previous_shares_count": before,
                "shares_count": before - transferred,
                "counterparties": [
                    match.group("buyer1").strip(), match.group("buyer2").strip(),
                ],
            },
        ))
        for index in (1, 2):
            received = _count(match.group(f"count{index}"))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé",
                signing="ohne Zeichnungsberechtigung",
                extra={
                    **common,
                    "action": "appointed_and_shares_received",
                    "origin": match.group(f"origin{index}").strip(),
                    "counterparty": seller,
                    "new_associate": True,
                    "shares_received": received,
                    "shares_count": received,
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
