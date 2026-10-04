from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_PAIR_DOMICILE_CHANGED_TOGETHER = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont maintenant "
    r"tous deux domiciliés à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_PARTICIPATION_CAPITAL_INTRODUCED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Erhöhung des "
    r"Partizipationskapitals gemäss näherer Umschreibung in den Statuten "
    r"eingeführt\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_INTO_SUCCESSOR_AND_DELETION = re.compile(
    r"^Aktiven und Passiven\s*\(Fremdkapital\)\s+gehen infolge Fusion auf die\s+"
    r"[\"“](?P<successor>.+?)[\"”]\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*über\.\s*Die Gesellschaft wird gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_ORIGIN_CORRECTED = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est en réalité originaire de\s+"
    r"(?P<origin>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_SEAT_AND_IDENTIFIER = re.compile(
    r"^Nouveau siège de l['’]établissement principal à\s+(?P<place>[^,.;]+),\s*"
    r"inscrit au registre du commerce du canton de\s+(?P<register_canton>[^,.;]+)\s+"
    r"sous le numéro d['’]identification\s*\(IDE/UID\)\s*"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_FR_CORRECTION_WITH_ONLY_INCORRECT_DATE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s*"
    r"\(et non pas du\s+(?P<incorrect_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_DE_LIMITED_PARTNERSHIP_CAPITAL_CHANGED = re.compile(
    r"^Kommanditsumme neu:\s*(?P<to>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<from>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_MISSING_BOARD = re.compile(
    r"^Name neu:\s*(?P<name>.+? in Liquidation)\.\s*"
    r"Organisation neu:\s*\[Gestrichene Angaben über die Organisation aufgrund "
    r"geänderter Eintragungsvorschriften gemäss\s+"
    r"(?P<organization_basis>Art\.\s*92 HRegV)\.\]\.?\s*"
    r"Der Verein ist gemäss\s+(?P<dissolution_basis>Art\.\s*77 ZGB)\s+von "
    r"Gesetzes wegen aufgelöst,\s*weil der Vorstand nicht mehr "
    r"Statutengemäss bestellt werden kann\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_ROLE_CORRECTED = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\.\s*(?P<notice_id>\d+)\)\s+"
    r"est rectifiée dans ce sens:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role>membre du conseil de fondation),\s*"
    r"(?P<previous_signing>signature collective à deux),\s*maintenant\s+"
    r"(?P<role>présidente? de la commission exécutive),\s*"
    r"(?P<signing>signature collective à deux)\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_NOW = re.compile(
    r"^(?P<name>[^,.;]+?)\s+engage désormais la société par sa\s+"
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*administrateur et président,\s*"
    r"est nommé liquidateur\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_STATUTES_DATES = re.compile(
    r"^\[Die Statutendaten vom\s+(?P<date1>\d{2}\.\d{2}\.\d{4})\s*und vom\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+wurden irrtümlich eingetragen\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_DEFINITIVE_MORATORIUM_GRANTED = re.compile(
    r"^Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*alla società è stata concessa "
    r"una moratoria in via definitiva per un periodo di\s+"
    r"(?P<duration>\d+)\s+mesi a far tempo dal\s+"
    r"(?P<effective_from>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_CONDITIONAL_CAPITAL_INTRODUCED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine zusätzliche bedingte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DEED_DATE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_page>[\d/]+)\)\s+"
    r"est rectifiée en ce sens que l['’]acte de fondation est du\s+"
    r"(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s*"
    r"\(et non du\s+(?P<incorrect_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_IT_DELETION_PROCEDURE_BLOCKED_FEDERAL = re.compile(
    r"^La procedura ufficiale per la cancellazione dell['’]ente giuridico secondo\s+"
    r"(?P<legal_basis>l['’]art\.\s*934 CO in unione con l['’]art\.\s*153 ORC)\s+"
    r"è conclusa in base alla decisione del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+passata in giudicato\.\s*"
    r"L['’]ente giuridico non può ancora essere cancellato mancando il consenso "
    r"dell['’]autorità fiscale federale\.?$",
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


def extract_parser144_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 144."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_PAIR_DOMICILE_CHANGED_TOGETHER.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.pair_domicile_changed_together.v1",
                match.group(group), place=match.group("place"),
                extra={"action": "domicile_changed", "domicile_changed": True},
            ))

    match = _DE_AUTHORIZED_PARTICIPATION_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_participation_capital_introduced.v1",
            {
                "kind": "authorized_participation_capital_increase",
                "action": "introduced",
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _DE_MERGER_INTO_SUCCESSOR_AND_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_into_successor_and_deletion.v1",
            {
                "kind": "merger", "direction": "outbound",
                "successor_name": match.group("successor").strip(),
                "successor_uid": match.group("uid"),
                "successor_place": match.group("place").strip(),
                "assets_transferred": True, "liabilities_transferred": True,
                "liabilities_kind": "third_party_capital", "company_deleted": True,
            },
        ))

    match = _FR_PERSON_ORIGIN_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_corrected_reality.v1",
            match.group("name"),
            extra={
                "action": "origin_corrected",
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_HEAD_OFFICE_SEAT_AND_IDENTIFIER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.head_office_seat_and_identifier.v1",
            {
                "scope": "head_office", "action": "seat_and_identifier_changed",
                "head_office": match.group("place").strip(),
                "head_office_uid": match.group("uid"),
                "register_canton": match.group("register_canton").strip(),
            },
        ))

    match = _FR_CORRECTION_WITH_ONLY_INCORRECT_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.correction_incorrect_date_only.v1",
            {
                "kind": "date", "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "incorrect_published_date": _iso_date(match.group("incorrect_date")),
                "correct_value_omitted_in_source": True,
            },
        ))

    match = _DE_LIMITED_PARTNERSHIP_CAPITAL_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.limited_partnership_capital_changed.v1",
            {
                "kind": "limited_partnership_capital", "currency": "CHF",
                "from": match.group("from"), "to": match.group("to"),
            },
        ))

    match = _DE_ASSOCIATION_DISSOLVED_MISSING_BOARD.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.association_dissolved_missing_board.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "action": "organization_details_removed",
                    "legal_basis": re.sub(r"\s+", " ", match.group("organization_basis")),
                    "reason": "changed_registration_rules",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution", "action": "dissolved_by_law",
                    "legal_basis": re.sub(r"\s+", " ", match.group("dissolution_basis")),
                    "reason": "board_cannot_be_appointed_under_statutes",
                    "liquidation_name": match.group("name").strip(),
                },
            ),
        ])

    match = _FR_FOUNDATION_MEMBER_ROLE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_role_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").lower(),
                "signing_unchanged": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_COLLECTIVE_SIGNING_NOW.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.collective_signing_now.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien",
            extra={"action": "signing_changed"},
        ))

    match = _FR_ADMINISTRATOR_PRESIDENT_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_president_liquidator.v1",
            match.group("name"), role="administrateur, président et liquidateur",
            extra={
                "action": "appointed_liquidator",
                "previous_roles": ["administrateur", "président"],
            },
        ))

    match = _DE_ERRONEOUS_STATUTES_DATES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.erroneous_statutes_dates.v1",
            {
                "kind": "statutes_dates", "action": "erroneous_entries_removed",
                "erroneous_dates": [
                    _iso_date(match.group("date1")),
                    _iso_date(match.group("date2")),
                ],
            },
        ))

    match = _IT_DEFINITIVE_MORATORIUM_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.definitive_moratorium_granted.v1",
            {
                "kind": "composition_moratorium_granted",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_from": _iso_date(match.group("effective_from")),
                "duration_months": int(match.group("duration")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_ADDITIONAL_CONDITIONAL_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.additional_conditional_capital_introduced.v1",
            {
                "kind": "conditional_capital_increase", "action": "introduced",
                "additional": True,
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_FOUNDATION_DEED_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.foundation_deed_date_corrected.v1",
            {
                "kind": "foundation_deed_date", "action": "corrected",
                "date": _french_date(match.group("date")),
                "incorrect_published_date": _french_date(match.group("incorrect_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("notice_page"),
            },
        ))

    match = _IT_DELETION_PROCEDURE_BLOCKED_FEDERAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.deletion_procedure_blocked_federal.v1",
            {
                "kind": "deletion_blocked", "procedure_completed": True,
                "procedure_completed_at": _iso_date(match.group("date")),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "tax_authority": "federal",
                "tax_authority_consent_missing": True,
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip()
