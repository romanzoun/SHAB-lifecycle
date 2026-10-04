from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_AUDITOR_LEGAL_NAME_CHANGED = re.compile(
    r"^La nouvelle raison sociale de l['’]organe de révision est\s*:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED = re.compile(
    r"^Das Statutendatum lautet richtig:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und nicht\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_APPEAL_ACCEPTED_DECISION_REVOKED = re.compile(
    r"^In Gutheissung der Beschwerde hat\s+(?P<authority>.+?)\s+mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s*den Entscheid der\s+"
    r"(?P<court>.+?)\s+vom\s+(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"aufgehoben\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CONTINUES_WITH_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+)\s+continue à signer collectivement à deux,\s*"
    r"désormais avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_DE_PARTICIPATION_CERTIFICATES_REMOVED = re.compile(
    r"^Genussscheine neu:\s*\[Die\s+(?P<count>[\d']+)\s+Genussscheine sind "
    r"aufgehoben worden\.\]\s*\[gestrichen:\s*(?P=count)\s+Genussscheine,\s*"
    r"(?P<rights>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*associée-gérante,\s*désormais à\s+"
    r"(?P<place>[^,.;]+),\s*est nommée liquidatrice\.?$",
    re.I | re.UNICODE,
)
_IT_ORGANIZATION_CLAUSE_REMOVED = re.compile(
    r"^Nuova organizzazione:\s*\[finora:\s*Organizzazione:\s*"
    r"(?P<previous>[^\]]+?)\]\.?\s*\[L['’]indicazione relativa l['’]organizzazione "
    r"è cancellata a seguito dell['’]abrogazione della disposizione di cui "
    r"all['’]art\.\s*(?P<article>\d+)\s+cpv\.\s*(?P<paragraph>\d+)\s+"
    r"lett\.\s*(?P<letter>[a-z])\s+ORC\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_HEAD_OFFICE_DISSOLVED_BANKRUPTCY = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Auflösung der Gesellschaft am "
    r"Hauptsitz infolge Konkurseröffnung\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE = re.compile(
    r"^Nouvel associé:\s*(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),?\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE = re.compile(
    r"^Mit Beschluss des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+ist der Beschwerde gegen das "
    r"Urteil des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung "
    r"betreffend Auflösung der Gesellschaft infolge Konkurses im Handelsregister "
    r"gestrichen\.\s*\[bisher:\s*Mit Urteil vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<previous_court>.+?)\s+über die Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<time>\d{1,2}[.:]\d{2})\s+Uhr,\s*den Konkurs eröffnet;\s*"
    r"demnach ist die Gesellschaft aufgelöst\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMMUNICATION_EXAMPLES_CONTINUATION = re.compile(
    r"^ex\.\s*courrier écrit,\s*télécopie,\s*courrier électronique\)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILIARY_ADDRESS_CHANGED = re.compile(
    r"^Nouvelle raison sociale de la domiciliataire:\s*"
    r"(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*c/o\s+"
    r"(?P<care_of>.+?),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_COMMITTEE_MEMBER = re.compile(
    r"^Nouveau membre du comité\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_TWO_LIQUIDATORS = re.compile(
    r"^Selon décision de son assemblée générale du\s+"
    r"(?P<day>\d{1,2})\s+(?P<month>[A-Za-zÀ-ÿ]+)\s+(?P<year>\d{4}),\s*"
    r"l['’]association a prononcé sa dissolution\.\s*"
    r"(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont nommés "
    r"liquidateurs\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETION_REVOKED = re.compile(
    r"^Die Löschung dieses Einzelunternehmens erfolgte irrtümlich und wird in "
    r"allen Teilen widerrufen\.\s*Das Einzelunternehmen besteht gemäss den "
    r"früheren Einträgen weiter\.\s*\[bisher:\s*Das Einzelunternehmen ist "
    r"infolge Aufgabe der Geschäftstätigkeit erloschen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_RESTITUTION_REFUSED = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a refusé d['’]entrer en matière sur la requête de "
    r"restitution de délai,\s*révoqué l['’]effet suspensif et dit que le "
    r"prononcé de faillite du\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"prend effet le\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*à\s*"
    r"(?P<time>\d{1,2})h(?P<minute>\d{2})\.\s*La raison de commerce devient\s+"
    r"(?P<name>.+?)\.?$",
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


def _fr_date(day: str, month: str, year: str) -> str:
    return f"{int(year):04d}-{_FR_MONTHS[month.lower()]:02d}-{int(day):02d}"


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
    uid: str | None = None,
    role: str | None = None,
    signing: str | None = None,
    extra: dict | None = None,
) -> Event:
    clean_name = name.strip()
    clean_place = place.strip() if place else None
    clean_uid = uid.strip() if uid else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place, uid=clean_uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser89_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 89."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_AUDITOR_LEGAL_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_legal_name_changed.v1",
                match.group("name"), place=match.group("place"), uid=match.group("uid"),
                role="organe de révision",
                extra={"action": "registered_name_changed", "uid": match.group("uid")},
            )
        )

    match = _DE_STATUTES_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.statutes_date_corrected.v1",
                {
                    "action": "date_corrected",
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _DE_APPEAL_ACCEPTED_DECISION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.appeal_accepted_decision_revoked_typo.v1",
                {
                    "kind": "court_decision_revoked",
                    "action": "revoked_on_appeal",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "original_date": _iso_date(match.group("original_date")),
                    "authority": match.group("authority").strip(),
                    "original_court": match.group("court").strip(),
                },
            )
        )

    match = _FR_SIGNING_CONTINUES_WITH_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_continues_with_administrator.v1",
                match.group("name"), signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "restriction_changed",
                    "signing_continues": True,
                    "signing_with_role": "administrateur",
                },
            )
        )

    match = _DE_PARTICIPATION_CERTIFICATES_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.participation_certificates_removed_counted.v2",
                {
                    "kind": "participation_certificates",
                    "action": "removed",
                    "count": _count(match.group("count")),
                    "previous_rights": match.group("rights").strip().rstrip("."),
                },
            )
        )

    match = _FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_manager_liquidator.v2",
                match.group("name"), place=match.group("place"),
                role="associée-gérante et liquidatrice", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "domicile_changed": True},
            )
        )

    match = _IT_ORGANIZATION_CLAUSE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "it.text.organization_clause_removed_orc.v1",
                {
                    "kind": "organization_clause",
                    "action": "removed",
                    "previous": match.group("previous").strip().rstrip("."),
                    "legal_basis": (
                        f"art. {match.group('article')} cpv. {match.group('paragraph')} "
                        f"lett. {match.group('letter')} ORC"
                    ),
                },
            )
        )

    match = _DE_BRANCH_HEAD_OFFICE_DISSOLVED_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.branch_head_office_bankruptcy.v1",
                {
                    "kind": "bankruptcy_opened",
                    "scope": "head_office",
                    "branch_affected": True,
                    "dissolved": True,
                },
            )
        )

    match = _FR_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.new_associate_trailing_comma.v1",
                match.group("name"), place=match.group("place"), role="associé",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            )
        )

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.bankruptcy_appeal_suspensive_dissolution_removed.v1",
                {
                    "kind": "bankruptcy",
                    "action": "suspended_on_appeal",
                    "dissolution_entry_removed": True,
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": match.group("time").replace(".", ":"),
                    "authority": match.group("authority").strip(),
                    "court": match.group("court").strip(),
                },
            )
        )

    match = _FR_COMMUNICATION_EXAMPLES_CONTINUATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.communications_examples_continuation.v1",
                {
                    "kind": "communications",
                    "action": "examples_specified",
                    "channels": ["courrier écrit", "télécopie", "courrier électronique"],
                },
            )
        )

    match = _FR_DOMICILIARY_ADDRESS_CHANGED.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"c/o {match.group('care_of').strip()}, {match.group('postal_code')} "
            f"{match.group('place').strip()}"
        )
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "fr.text.domiciliary_address_changed.v1",
                {
                    "kind": "domiciliary_address",
                    "action": "changed",
                    "address": address,
                    "street": match.group("street").strip(),
                    "house_number": match.group("house"),
                    "care_of": match.group("care_of").strip(),
                    "postal_code": match.group("postal_code"),
                    "place": match.group("place").strip(),
                },
            )
        )

    match = _FR_NEW_COMMITTEE_MEMBER.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.new_committee_member_signing.v1",
                match.group("name"), place=match.group("place"), role="membre du comité",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            )
        )

    match = _FR_ASSOCIATION_DISSOLVED_TWO_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.association_dissolved_two_liquidators.v1"
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution",
                    "action": "dissolved",
                    "decision_date": _fr_date(
                        match.group("day"), match.group("month"), match.group("year")
                    ),
                },
            )
        )
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(group), role="liquidateur",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed"},
                )
            )

    match = _DE_SOLE_PROPRIETOR_DELETION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.sole_proprietor_deletion_revoked.v1",
                {
                    "kind": "registration_reinstated",
                    "action": "deletion_revoked",
                    "scope": "sole_proprietor",
                    "previous_reason": "cessation_of_business",
                },
            )
        )

    match = _FR_BANKRUPTCY_RESTITUTION_REFUSED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_restitution_refused_effective.v1",
                {
                    "kind": "bankruptcy_opened",
                    "action": "suspensive_effect_revoked",
                    "restitution_request": "refused_without_consideration",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "effective_date": _iso_date(match.group("effective_date")),
                    "effective_time": f"{int(match.group('time')):02d}:{match.group('minute')}",
                    "authority": match.group("authority").strip(),
                    "company_name": match.group("name").strip(),
                    "in_liquidation": True,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
