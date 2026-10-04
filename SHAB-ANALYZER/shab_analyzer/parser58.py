from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_SPLIT = re.compile(
    r"Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+),\s*nominatives,\s*en\s+"
    r"(?P<to_count>[\d']+)\s+actions de CHF\s+(?P<to_nominal>[\d'.]+),\s*"
    r"nominatives\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"libéré à concurrence de CHF\s+(?P<paid>[\d'.]+),\s*divisé en\s+"
    r"(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*(?P<kind>nominatives)\.?,?",
    re.I | re.UNICODE,
)
_FR_GENERAL_PARTNER = re.compile(
    r"Nouvel associé indéfiniment responsable\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?,?",
    re.I | re.UNICODE,
)
_FR_DELEGATED_BOARD_MEMBER = re.compile(
    r"(?P<name>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*"
    r"est\s+(?P<role>membre délégué(?:e)? du conseil d['’]administration)\.?,?",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL = re.compile(
    r"Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+(?P<to>[\d'.]+);\s*"
    r"Liberierung:\s*(?:(?P<paid_currency>[A-Z]{3})\s+)?(?P<to_paid>[\d'.]+)\s*"
    r"\[bisher:\s*(?P<from_currency>[A-Z]{3})\s+(?P<from>[\d'.]+);\s*"
    r"Liberierung:\s*(?P<from_paid_currency>[A-Z]{3})\s+"
    r"(?P<from_paid>[\d'.]+)\]\.?,?",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_SUPPRESSED = re.compile(
    r"Mediante decisione della\s+(?P<authority>.+?),\s*"
    r"(?P<authority_place>[^,.;]+),\s*del\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"la fondazione è stata soppressa\.\s*La cancellazione non può tuttavia essere "
    r"effettuata mancando il consenso delle autorità fiscali federali e cantonali\.?,?",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR = re.compile(
    r"Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<role2>[^,.;]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_OPENED = re.compile(
    r"La faillite de la société a été prononcée par jugement du\s+"
    r"(?P<authority>.+?)\s+du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"avec effet à partir du\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"à\s+(?P<time>\d{1,2}:\d{2})\.\s*Par conséquent,\s*sa raison sociale "
    r"devient:\s*(?P<name>[^.]+)\.?,?",
    re.I | re.UNICODE,
)
_DE_BRANCH_REMOVAL_HEADING = re.compile(
    r"\[Folgende Zweigniederlassungen sind aufgehoben worden:\]", re.I
)
_FR_AUDITOR_RENAMED_FEDERAL_ID = re.compile(
    r"Nouvelle raison sociale de l['’]organe de révision\s+"
    r"[\"“](?P<old_name>.+?)[\"”],\s*dont le numéro fédéral d['’]identification\s+"
    r"(?P<registry_id>CH-[\d.-]+-\d)\s+est remplacé par le numéro\s+"
    r"IDE\s*/?\s*UID\s+(?P<uid>CHE-\d{3}\.\d{3}\.\d{3}):\s*"
    r"[\"“](?P<name>.+?)[\"”]\.?,?",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR = re.compile(
    r"(?P<name1>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*(?:avec signature "
    r"(?:individuelle|collective(?:\s+à\s+deux)?),\s*)?et\s+"
    r"(?P<name2>[A-ZÀ-Ÿ][^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*avec signature\s+"
    r"(?P<sign>individuelle|collective(?:\s+à\s+deux)?),\s*sont membres du "
    r"conseil d['’]administration\.?,?",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_NEW_NAME = re.compile(
    r"Nouvelle raison sociale de l['’]associée\s*:\s*(?P<name>.+?)\s+"
    r"\((?P<registry_id>\d+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3})\.?,?",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_WITH_ASSIGNED_UID = re.compile(
    r"(?P<old_name>[A-ZÀ-Ÿ][^()]+?)\s+\((?P<registry_id>CH-[\d.-]+-\d)\),\s*"
    r"dont le numéro d['’]identification est\s+\((?P<assigned_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"a modifié sa raison de commerce en\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?,?",
    re.I | re.UNICODE,
)
_FR_LEGAL_CONVERSION_ADAPTED = re.compile(
    r"Le\s+(?P<day>\d{1,2})(?:er)?\s+(?P<month>janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+(?P<year>\d{4}),\s*"
    r"les actions au porteur ont été converties de par la loi en actions nominatives\.\s*"
    r"Par décision de l['’]assemblée générale du\s+"
    r"(?P<adaptation_date>\d{2}\.\d{2}\.\d{4})\s+les statuts de la société ont été "
    r"adaptés à la conversion\.?,?",
    re.I | re.UNICODE,
)
_FR_MANAGERS_PAIR = re.compile(
    r"Gérants:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié(?:e)? à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*nommé(?:e)?\s+"
    r"(?P<role1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*lesquels signent\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?,?",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_REWORDING = re.compile(
    r"Die Umschreibung der mit Beschluss der Generalversammlung vom\s+"
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+eingeführten Bestimmung über das "
    r"genehmigte Kapital wurde mit Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.?,?",
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
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser58_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 58."""
    events: list[Event] = []
    leftover = text

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SHARE_SPLIT.search(leftover)
    if match:
        consume(match)
        total = match.group("total")
        paid = match.group("paid")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_split.v1",
                {
                    "kind": "share_split",
                    "split_from": {
                        "count": _count(match.group("from_count")),
                        "nominal": match.group("from_nominal"),
                    },
                    "split_to": {
                        "count": _count(match.group("to_count")),
                        "nominal": match.group("to_nominal"),
                    },
                    "capital_total": total,
                    "paid": paid,
                    "paid_in_full": paid == total,
                    "capital_count": _count(match.group("capital_count")),
                    "capital_nominal": match.group("capital_nominal"),
                    "share_kind": match.group("kind"),
                },
            )
        )

    match = _FR_GENERAL_PARTNER.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.general_partner.v2",
                match.group("name"), place=match.group("place"),
                role="associé indéfiniment responsable",
                extra={"heimat": match.group("origin").strip()},
            )
        )

    match = _FR_DELEGATED_BOARD_MEMBER.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.delegated_board_member.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role").strip(),
                extra={
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                },
            )
        )

    match = _DE_HEAD_OFFICE_CAPITAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.head_office_capital.v2",
                {
                    "scope": "head_office",
                    "currency": match.group("currency"),
                    "from": match.group("from"),
                    "to": match.group("to"),
                    "from_paid": match.group("from_paid"),
                    "to_paid": match.group("to_paid"),
                },
            )
        )

    match = _IT_FOUNDATION_SUPPRESSED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.foundation_suppressed_deletion_blocked.v2",
                {
                    "kind": "deletion_blocked",
                    "entity": "foundation",
                    "action": "suppressed",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "authority_place": match.group("authority_place").strip(),
                    "tax_authority_consent_missing": True,
                },
            )
        )

    match = _FR_ADMINISTRATION_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (match.group("name1"), None, match.group("role1"), {}),
            (
                match.group("name2"), match.group("place2"), match.group("role2"),
                {"heimat": match.group("origin2").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.administration_pair_roles.v2"),
                ("signing_authority_changed", "fr.persons.administration_pair_roles_signing.v2"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role.strip(),
                        signing=signing, extra=extra,
                    )
                )

    match = _FR_BANKRUPTCY_OPENED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_opened.v2",
                {
                    "kind": "bankruptcy_opened",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                    "company_name": match.group("name").strip(),
                    "in_liquidation": True,
                },
            )
        )

    if language == "de" and _DE_BRANCH_REMOVAL_HEADING.search(leftover):
        leftover = _DE_BRANCH_REMOVAL_HEADING.sub(" ", leftover)

    match = _FR_AUDITOR_RENAMED_FEDERAL_ID.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_renamed.v9",
                match.group("name"), uid=match.group("uid"), role="organe de révision",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("registry_id"),
                },
            )
        )

    match = _FR_BOARD_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_pair.v2",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role="membre du conseil d'administration", signing=signing,
                    extra={"heimat": match.group(f"origin{index}").strip()},
                )
            )

    match = _FR_ASSOCIATE_NEW_NAME.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_new_name.v1",
                match.group("name"), place=match.group("place"), role="associée",
                extra={
                    "action": "registered_name_changed",
                    "registry_id": match.group("registry_id"),
                    "country": match.group("country"),
                },
            )
        )

    match = _FR_AUDITOR_RENAMED_WITH_ASSIGNED_UID.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_renamed.v10",
                match.group("name"), uid=match.group("uid"), role="organe de révision",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("registry_id"),
                    "assigned_uid": match.group("assigned_uid"),
                },
            )
        )

    match = _FR_LEGAL_CONVERSION_ADAPTED.search(leftover)
    if match:
        consume(match)
        month = _FR_MONTHS[match.group("month").lower()]
        conversion_date = f"{match.group('year')}-{month:02d}-{int(match.group('day')):02d}"
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.legal_bearer_conversion_adapted.v2",
                {
                    "kind": "bearer_to_registered_conversion",
                    "legal_basis": "by_operation_of_law",
                    "conversion_date": conversion_date,
                    "adaptation_date": _iso_date(match.group("adaptation_date")),
                    "from_kind": "au porteur",
                    "to_kind": "nominatives",
                    "statutes_adapted": True,
                },
            )
        )

    match = _FR_MANAGERS_PAIR.search(leftover)
    if match:
        consume(match)
        signing = _signing(match.group("sign"))
        people = (
            (
                match.group("name1"), match.group("place1"), match.group("role1"),
                {"country": match.group("country1"), "domicile_changed": True},
            ),
            (
                match.group("name2"), match.group("place2"), "gérant",
                {"heimat": match.group("origin2").strip()},
            ),
        )
        for name, place, role, extra in people:
            for event_type, rule_id in (
                ("officer_changed", "fr.persons.managers_pair.v1"),
                ("signing_authority_changed", "fr.persons.managers_pair_signing.v1"),
            ):
                events.append(
                    _person_event(
                        publication_id, published_at, org_uid, plz, canton,
                        event_type, rule_id, name, place=place, role=role.strip(),
                        signing=signing, extra=extra,
                    )
                )

    match = _DE_AUTHORIZED_CAPITAL_REWORDING.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_capital_clause_modified.v1",
                {
                    "kind": "authorized_capital_clause_modified",
                    "original_decision_date": _iso_date(match.group("original_date")),
                    "decision_date": _iso_date(match.group("decision_date")),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
