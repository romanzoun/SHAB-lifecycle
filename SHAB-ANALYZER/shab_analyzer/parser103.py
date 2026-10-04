from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SUPERVISORY_AUTHORITY_PLAIN = re.compile(
    r"^(?P<authority>Autorité de surveillance .+?)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_SPLIT_FULLY_PAID = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives,\s*(?:,\s*)?en\s+"
    r"(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d'.]+)\.\s*"
    r"Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*"
    r"divisé en\s+(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*nominatives(?:,\s*liées selon statuts)?\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]"
    r"(?P<role>[^,.;]+?)\s+(?P<name>[^,.;]+?)\s+est originaire de\s+"
    r"(?P<origin>[^()]+?)\s*\((?:et|en) non de\s+(?P<previous_origin>.+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_GRANTED = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde gegen das "
    r"Urteil des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend "
    r"Konkurseröffnung aufschiebende Wirkung erteilt worden\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTION_COMMA = re.compile(
    r"^Die Statuten datieren vom\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"nicht vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_BRANCH_REGISTERED_AT = re.compile(
    r"^Inscription de la nouvelle succursale à\s+(?P<place>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+au registre du commerce du canton "
    r"de\s+(?P<register_canton>.+?)\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>[\d/]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_REMOVED_OBLIGATIONS_AND_SHARE_TRANSFER_RESTRICTION = re.compile(
    r"^\[biffé:\s*Obligations:\s*\]\.?\s*Nouvelle restriction à la "
    r"transmissibilité:\s*Les statuts dérogent à la loi quant aux modalités du "
    r"transfert des parts sociales:\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_ORGANIZATION_AND_DEED_CHANGED = re.compile(
    r"^Nuova organizzazione:\s*\[Nuova organizzazione:\s*"
    r"(?P<organization>[^\]]+?)\]\.?\s*"
    r"\[L['’]indicazione relativa all['’]organizzazione è cancellata a seguito "
    r"dell['’]abrogazione della disposizione di cui all['’]"
    r"(?P<law>art\.\s*95 cpv\.\s*1 lett\.\s*h ORC)\.\]\.?\s*"
    r"Atto di fondazione modificato con decisione del\s+(?P<authority>.+?),\s*"
    r"in\s+(?P<authority_place>[^,.;]+),\s*quale autorità di vigilanza,\s*"
    r"in data\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+anche su punti non soggetti "
    r"a pubblicazione\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+),\s*désormais à\s+"
    r"(?P<place>[^,.;]+),\s*est nommé gérant et président\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_CORRECTION_AND_CHANGE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la raison de "
    r"commerce exacte est\s+(?P<corrected_name>.+?)\.\s*Nouvelle raison de "
    r"commerce:\s*(?P<new_name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_APPOINTMENT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+est nommée?\s+(?P<role>administratrice?)\s*"
    r"\(et non pas avec signature individuelle\)\.?$",
    re.I | re.UNICODE,
)
_DE_PENSION_ASSET_TRANSFER_WITH_CLAIMS_AND_CASH = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss Vertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<claims_count>[\d']+)\s+Ansprüche zu CHF\s+"
    r"(?P<claim_nominal>[\d'.]+)\s+der Anlagegruppe\s+(?P<investment_group>.+?)\s+"
    r"des übernehmenden Rechtsträgers sowie eine Barzahlung von CHF\s*"
    r"(?P<cash>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_SUPPLEMENT_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée comme suit:\s*Capital-actions:\s*"
    r"CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<share_kind>nominatives)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_RESTRICTION_REMOVED_PAIR = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+continuent à signer "
    r"collectivement à deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_MULTIPLE_PLAN_DATES = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss Spaltungsplan "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+bzw\.\s+"
    r"(?P<additional_dates>[\d./]+)\s+auf die\s+"
    r"(?P<newly_founded>neu gegründete\s+)?(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),?\s*über\.?$",
    re.I | re.UNICODE,
)
_FR_COMPOSITION_MORATORIUM_EXTENDED_UNTIL = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4}),\s*(?P<authority>.+?)\s+a prolongé le "
    r"sursis concordataire jusqu['’]au\s+(?P<until>\d{1,2}(?:er)?\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
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
    day, month, year = re.sub(r"(?<=\d)er\b", "", raw.strip().lower()).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _expanded_compact_dates(raw: str, primary: str) -> list[str]:
    _, primary_month, primary_year = primary.split(".")
    parts = raw.split("/")
    final_values = [value for value in parts[-1].split(".") if value]
    month = final_values[1] if len(final_values) == 3 else primary_month
    year = final_values[2] if len(final_values) == 3 else primary_year
    dates: list[str] = []
    for part in parts:
        values = [value for value in part.split(".") if value]
        day = values[0]
        dates.append(_iso_date(f"{day}.{month}.{year}"))
    return dates


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


def extract_parser103_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 103."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SUPERVISORY_AUTHORITY_PLAIN.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "supervisor_changed", "fr.text.supervisory_authority_plain.v1",
            {"to": match.group("authority").strip(), "action": "recorded"},
        ))

    match = _FR_REGISTERED_SHARE_SPLIT_FULLY_PAID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_split_fully_paid.v1",
            {
                "kind": "share_split", "currency": "CHF",
                "from_count": _count(match.group("from_count")),
                "from_nominal": match.group("from_nominal"),
                "to_count": _count(match.group("to_count")),
                "to_nominal": match.group("to_nominal"),
                "total": match.group("total"), "fully_paid": True,
                "share_kind": "actions nominatives",
                "transfer_restricted": True,
            },
        ))

    match = _FR_ORIGIN_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "origin_corrected", "heimat": match.group("origin").strip(),
                "previous_heimat": match.group("previous_origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspensive_effect_granted.v1",
            {
                "kind": "bankruptcy_effect_suspended", "action": "suspended_on_appeal",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
            },
        ))

    match = _DE_STATUTES_DATE_CORRECTION_COMMA.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_corrected_comma.v1",
            {
                "action": "date_corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_NEW_BRANCH_REGISTERED_AT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.new_branch_registered_at.v1",
            {
                "action": "registered", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "register_canton": match.group("register_canton").strip(),
                "source_notice_date": _iso_date(match.group("notice_date")),
                "source_notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_REMOVED_OBLIGATIONS_AND_SHARE_TRANSFER_RESTRICTION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.removed_obligations_and_share_transfer_restriction.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {"kind": "obligations", "action": "removed"},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "share_transfer_rules", "action": "introduced",
                    "share_transfer_rules": "statutory_derogation",
                    "details_in_statutes": True,
                },
            ),
        ])

    match = _IT_FOUNDATION_ORGANIZATION_AND_DEED_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.foundation_organization_and_deed_changed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "kind": "foundation_organization", "action": "changed",
                    "to": match.group("organization").strip(" ."),
                    "obsolete_organization_indication_removed": True,
                    "legal_basis": re.sub(r"\s+", " ", match.group("law")).strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "foundation_deed_non_public_changes",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "authority_place": match.group("authority_place").strip(),
                },
            ),
        ])

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president.v1",
            match.group("name"), place=match.group("place"),
            role="associé, gérant et président",
            extra={"action": "appointed", "domicile_changed": True},
        ))

    match = _FR_COMPANY_NAME_CORRECTION_AND_CHANGE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.company_name_correction_and_change.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {
                    "kind": "company_name", "action": "corrected",
                    "corrected_name": match.group("corrected_name").strip(),
                    **reference,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id,
                {
                    "from": match.group("corrected_name").strip(),
                    "to": match.group("new_name").strip(),
                },
            ),
        ])

    match = _FR_ADMINISTRATOR_APPOINTMENT_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_appointment_corrected.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "appointment_corrected", "without_signature": True,
                "previous_erroneous_attribute": "signature individuelle",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_PENSION_ASSET_TRANSFER_WITH_CLAIMS_AND_CASH.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.pension_asset_transfer_claims_and_cash.v1",
            {
                "source": match.group("source").strip(),
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": None,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "investment_claims_and_cash",
                "claims_count": _count(match.group("claims_count")),
                "claim_nominal": match.group("claim_nominal"),
                "investment_group": match.group("investment_group").strip(),
                "cash_consideration": match.group("cash"), "currency": "CHF",
            },
        ))

    match = _FR_CAPITAL_SUPPLEMENT_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_supplement_with_notice.v1",
            {
                "kind": "share_structure", "action": "publication_supplemented",
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True, "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": match.group("share_kind").lower(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_SIGNING_RESTRICTION_REMOVED_PAIR.search(leftover)
    if match:
        consume(match)
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_restriction_removed_pair.v1",
                match.group(f"name{index}"), signing="Kollektivunterschrift zu zweien",
                extra={"action": "restriction_removed", "signing_continues": True},
            ))

    match = _DE_OUTGOING_SPIN_OFF_MULTIPLE_PLAN_DATES.search(leftover)
    if match:
        consume(match)
        primary_date = match.group("date")
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.outgoing_spin_off_multiple_plan_dates.v1",
            {
                "kind": "spin_off_distribution",
                "date": _iso_date(primary_date),
                "additional_plan_dates": _expanded_compact_dates(
                    match.group("additional_dates"), primary_date
                ),
                "document": "spaltungsplan", "scope": "part_of_assets_and_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_newly_founded": bool(match.group("newly_founded")),
            },
        ))

    match = _FR_COMPOSITION_MORATORIUM_EXTENDED_UNTIL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.composition_moratorium_extended_until.v1",
            {
                "kind": "composition_moratorium_extended",
                "decision_date": _french_date(match.group("decision_date")),
                "until": _french_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
