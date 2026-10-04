from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_IT_BRANCH_HEAD_OFFICE_DETAILS = re.compile(
    r"^,?\s*Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuova ditta o ragione sociale della succursale:\s*(?P<branch_name>[^.]+)\.\s*"
    r"Nuovo numero di identificazione della sede principale:\s*"
    r"(?P<head_office_uid>CHE-\d{3}\.\d{3}\.\d{3})\.\s*"
    r"Nuova iscrizione nel RC della sede principale:\s*(?P<registration>[^\[]+?)\s*"
    r"\[finora:\s*Iscrizione nel RC della sede principale:\s*"
    r"(?P<previous_registration>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_ORGANIZATION_REMOVED_AND_DEED_CHANGED = re.compile(
    r"^Nuova organizzazione:\s*\[Organizzazione:\s*(?P<organization>[^\]]+?)\]\.?\s*"
    r"\[L['’]indicazione relativa all['’]organizzazione è cancellata a seguito "
    r"dell['’]abrogazione della disposizione di cui all['’]"
    r"(?P<legal_basis>art\.\s*95 cpv\.\s*1 lett\.\s*h ORC)\.\]\.?\s*"
    r"Atto di fondazione modificato con decisione della\s+(?P<authority>.+?)\s*"
    r"\((?P<authority_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+in\s+"
    r"(?P<authority_place>[^,.;]+)\s+in data\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+anche su punti non soggetti a "
    r"pubblicazione\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BRANCH_LEGACY_ID = re.compile(
    r"^Zweigniederlassung neu:\s*\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CATEGORIES_CREATED = re.compile(
    r"^Création de deux catégories d['’]actions,\s*soit\s+"
    r"(?P<ordinary_count>[\d']+)\s+actions ordinaires de CHF\s+"
    r"(?P<ordinary_nominal>[\d'.]+),\s*et\s+"
    r"(?P<preferred_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*privilégiées quant au dividende,\s*"
    r"tous nominatives,\s*\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P=ordinary_count)\s+actions de CHF\s+(?P=ordinary_nominal)\s+et\s+"
    r"(?P=preferred_count)\s+actions de CHF\s+(?P=preferred_nominal),\s*"
    r"privilégiées quant au dividende,\s*tous nominatives,\s*"
    r"liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_DE_STANDALONE_BRANCH_UID = re.compile(
    r"^(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_IT_CAPITAL_FLUCTUATION_MARGIN = re.compile(
    r"^Margine di variazione del capitale;\s*per i dettagli si rinvia allo "
    r"statuto\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_NAME_CORRECTION_WITH_NOTICE = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans ce sens que le nom correct "
    r"est\s+(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_EXTENDED_WEEKS = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>das zuständige Einzelgericht)\s+der Gesellschaft die "
    r"provisorische Nachlassstundung für die Dauer von\s+"
    r"(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+Wochen,\s*"
    r"d\.h\.\s*bis am\s+(?P<until>\d{2}\.\d{2}\.\d{4}),\s*verlängert\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_DEED_CHANGED_SUPERVISORY_AUTHORITY = re.compile(
    r"^Atto di fondazione modificato con decisione del\s+(?P<authority>.+?),\s*"
    r"in\s+(?P<authority_place>[^,.;]+),\s*quale autorità di vigilanza,\s*"
    r"in data\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+anche su punti non soggetti "
    r"a pubblicazione\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENDED_AND_NAME_RESTORED = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé le\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la faillite\.\s*"
    r"La raison de commerce redevient\s*:?[ ]*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat de transfert de patrimoine du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*le titulaire a transféré certains "
    r"actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et certains passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+)\s+à la société anonyme\s+"
    r"(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"(?P<shares_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal>[\d'.]+),\s*,\s*entièrement libérées et une créance "
    r"de CHF\s+(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_COLLECTIVE_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés-gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*lesquels continuent à signer collectivement à "
    r"deux\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE = re.compile(
    r"^(?P<newly_restricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<newly_restricted_nominal>[\d'.]+),\s*nominatives,\s*sont maintenant\s*"
    r"\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<unrestricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<unrestricted_nominal>[\d'.]+),\s*nominatives et\s+"
    r"(?P<restricted_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<restricted_nominal>[\d'.]+),\s*nominatives,\s*liées selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_CORRECT_DATE_AFTER_CONSUMPTION = re.compile(
    r"^\[non:\s*\]\.\s*Selon déclaration du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*(?:il\s+)?est renoncé à un contrôle "
    r"restreint\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_MEMBER_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<member>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*lesquels "
    r"signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_BRANCHES_PAIR_SHARED_NOTICE = re.compile(
    r"^Neue Zweigniederlassungen:\s*(?P<place1>[^(),]+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+und\s+"
    r"(?P<place2>[^(),]+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"Eintragung Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+),\s*bei der\s+(?P<related_company>.+?)\s*"
    r"\((?P<related_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+in\s+"
    r"(?P<related_place>[^.]+)\.?$",
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


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _number(raw: str) -> int:
    return int(raw) if raw.isdigit() else _DE_NUMBERS[raw.lower()]


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


def extract_parser108_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 108."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _IT_BRANCH_HEAD_OFFICE_DETAILS.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.branch_head_office_details.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", rule_id,
                {
                    "scope": "head_office", "action": "set",
                    "head_office": match.group("head_office").strip(),
                    "to": match.group("head_office_uid"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "head_office_details_changed",
                    "head_office": match.group("head_office").strip(),
                    "head_office_uid": match.group("head_office_uid"),
                    "branch_name": match.group("branch_name").strip(),
                    "head_office_registration": match.group("registration").strip(),
                    "previous_head_office_registration": (
                        match.group("previous_registration").strip()
                    ),
                },
            ),
        ])

    match = _IT_FOUNDATION_ORGANIZATION_REMOVED_AND_DEED_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.foundation_organization_removed_and_deed_changed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "kind": "foundation_organization", "action": "entry_removed",
                    "previous": match.group("organization").strip(" ."),
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "foundation_deed_non_public_changes",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "authority_uid": match.group("authority_uid"),
                    "authority_place": match.group("authority_place").strip(),
                    "non_public_changes": True,
                },
            ),
        ])

    match = _DE_REMOVED_BRANCH_LEGACY_ID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_removed_legacy_id.v1",
            {
                "action": "removed", "place": match.group("place").strip(),
                "legacy_registry_id": match.group("registry_id"),
            },
        ))

    match = _FR_SHARE_CATEGORIES_CREATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_categories_created.v1",
            {
                "kind": "share_categories_created", "currency": "CHF",
                "total": match.group("total"), "fully_paid": True,
                "registered": True, "transfer_restricted": True,
                "classes": [
                    {
                        "kind": "ordinary", "count": _count(match.group("ordinary_count")),
                        "nominal": match.group("ordinary_nominal"),
                    },
                    {
                        "kind": "dividend_preferred",
                        "count": _count(match.group("preferred_count")),
                        "nominal": match.group("preferred_nominal"),
                    },
                ],
            },
        ))

    match = _DE_STANDALONE_BRANCH_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.standalone_branch_uid.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
            },
        ))

    match = _IT_CAPITAL_FLUCTUATION_MARGIN.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "it.text.capital_fluctuation_margin.v1",
            {
                "kind": "capital_band", "action": "introduced",
                "details_in_statutes": True,
            },
        ))

    match = _FR_PERSON_NAME_CORRECTION_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.name_correction_with_notice.v3",
            match.group("name"),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_PROVISIONAL_MORATORIUM_EXTENDED_WEEKS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.provisional_moratorium_extended_weeks.v1",
            {
                "kind": "composition_moratorium_extended", "provisional": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "duration": _number(match.group("duration")),
                "duration_unit": "weeks",
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority"),
            },
        ))

    match = _IT_FOUNDATION_DEED_CHANGED_SUPERVISORY_AUTHORITY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.foundation_deed_supervisory_authority.v1",
            {
                "kind": "foundation_deed_non_public_changes",
                "date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "authority_place": match.group("authority_place").strip(),
                "authority_role": "supervisory_authority",
                "non_public_changes": True,
            },
        ))

    match = _FR_BANKRUPTCY_SUSPENDED_AND_NAME_RESTORED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_suspended_name_restored.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "action": "suspended_on_appeal",
                "decision_date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "company_name_restored": match.group("name").strip(),
            },
        ))

    match = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_asset_transfer.v1",
            {
                "transferor_kind": "sole_proprietor",
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_claim",
                "shares_count": _count(match.group("shares_count")),
                "share_nominal": match.group("share_nominal"),
                "shares_fully_paid": True,
                "claim": match.group("claim"),
            },
        ))

    match = _FR_ASSOCIATE_MANAGERS_COLLECTIVE_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_managers_collective_liquidators.v1"
        for name_group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                role="associé-gérant et liquidateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ))

    match = _FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_restriction_structure.v1",
            {
                "kind": "share_structure_and_transfer_restriction",
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True,
                "newly_restricted_count": _count(match.group("newly_restricted_count")),
                "newly_restricted_nominal": match.group("newly_restricted_nominal"),
                "classes": [
                    {
                        "count": _count(match.group("unrestricted_count")),
                        "nominal": match.group("unrestricted_nominal"),
                        "registered": True, "transfer_restricted": False,
                    },
                    {
                        "count": _count(match.group("restricted_count")),
                        "nominal": match.group("restricted_nominal"),
                        "registered": True, "transfer_restricted": True,
                    },
                ],
            },
        ))

    match = _FR_AUDIT_WAIVER_CORRECT_DATE_AFTER_CONSUMPTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.audit_waiver_correct_date.v2",
            {
                "kind": "limited_audit_waiver",
                "action": "declaration_date_corrected",
                "date": _iso_date(match.group("date")),
            },
        ))

    match = _FR_ADMINISTRATION_PRESIDENT_AND_MEMBER_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_president_member_individual.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="membre de l'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed", "heimat": match.group("place").strip(),
                },
            ),
        ])

    match = _DE_NEW_BRANCHES_PAIR_SHARED_NOTICE.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.new_branches_pair_shared_notice.v1"
        for index in (1, 2):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "registered",
                    "place": match.group(f"place{index}").strip(),
                    "branch_uid": match.group(f"uid{index}"),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                    "related_company": match.group("related_company").strip(),
                    "related_company_uid": match.group("related_uid"),
                    "related_company_place": match.group("related_place").strip(),
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
