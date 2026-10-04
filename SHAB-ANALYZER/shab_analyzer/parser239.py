from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED = re.compile(
    r"^En application de l['’]art\.\s*110,\s*al\.\s*1,\s*lit\.\s*e ORC,\s*"
    r"les personnes disposant d['’]un pouvoir de représentation selon l['’]inscription "
    r"de l['’]établissement principal sont radiées,\s*ainsi,?\s*les pouvoirs et les "
    r"signatures de\s+(?P<names>.+?)\s+sont radiés\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Beschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Fristablauf\.\]$",
    re.I | re.UNICODE,
)
_IT_ASSOCIATION_DISSOLVED = re.compile(
    r"^L['’]associazione è sciolta con decisione dell['’]assemblea dei soci del\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENSION_GRANTED = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde der "
    r"Gesellschaft ab\s+(?P<start_date>\d{2}\.\d{2}\.\d{4})\s+eine Verlängerung "
    r"der definitiven Nachlassstundung für die Dauer von\s+"
    r"(?P<duration>\w+)\s+Monaten bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde der Gesellschaft die "
    r"gewährte definitive Nachlassstundung um\s+(?P<duration>\w+)\s+Monate,\s*"
    r"d\.h\.\s*bis am\s+(?P<until>\d{2}\.\d{2}\.\d{4}),\s*verlängert\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_SIGNATURE_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la signature est radiée,\s*reste "
    r"administrateur\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_INDIVIDUAL_SIGNING = re.compile(
    r"^Les associés\s+(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+"
    r"ont désormais la signature individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_REGULATION_REMOVED = re.compile(
    r"^\[gestrichen:\s*Organisationsreglement vom\s+"
    r"(?P<regulation_date>\d{2}\.\d{2}\.\d{4})\]$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_RENAMED_SAME_UID = re.compile(
    r"^Die eingetragene Revisionsstelle\s+(?P<previous_name>.+?)\s+"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+firmiert neu\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_CHANGES = re.compile(
    r"^Les procurations de\s+(?P<removed1>[^,.;]+?)\s+et de\s+"
    r"(?P<removed2>[^,.;]+?)\s+sont radiées\.\s*"
    r"(?P<restricted>.+?)\s+continuent de signer par procuration "
    r"collectivement à deux,\s*mais désormais sauf entre eux\.\s*"
    r"(?P<moved>[^,.;]+),\s*maintenant domicilié à\s+(?P<place>[^,.;]+),\s*"
    r"continue de signer par procuration collectivement à deux,\s*mais désormais "
    r"sans autre restriction\.?$",
    re.I | re.UNICODE,
)
_FR_COURT_NOTICE_NOT_TO_BE_PUBLISHED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le délai fixé "
    r"dans la décision du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+"
    r"n['’]étant pas encore échu,\s*la décision ne doit pas être publiée\.?$",
    re.I | re.UNICODE,
)
_DE_DIRECTOR_WITH_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name>[^,.;]+),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+"
    r"(?P<place>[^,.;]+),\s*Direktor,\s*Kollektivunterschrift zu zweien\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS_CHANGED = re.compile(
    r"^Liquidationsadresse:\s*(?P<address>.+?,\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^.]+))\.\s*"
    r"\[bisher:\s*Liquidationsadresse:\s*(?P<previous_address>.+?,\s*"
    r"(?P<previous_postal_code>\d{4})\s+(?P<previous_place>[^.]+))\.\]$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]un "
    r"associé-gérant se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_BOARD_PERSON_SECTIONS = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<removed>.+?)\.\s*Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<incoming>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_BOARD_PERSON = re.compile(
    r"^(?P<last>[^,;]+),\s*(?P<first>[^,;]+),\s*"
    r"(?P<nationality>[^,;]+),\s*in\s+(?P<place>[^,;]+),\s*"
    r"(?P<role>[^,;]+),\s*mit\s+(?P<signing>[^,;]+)$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_SOLE_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+?)\s+est nommé gérant unique"
    r"(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
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
    "einem": 1,
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


def _duration_months(raw: str) -> int | None:
    normalized = raw.casefold()
    if normalized.isdigit():
        return int(normalized)
    return _GERMAN_NUMBERS.get(normalized)


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


def _split_names(raw: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", name).strip()
        for name in re.split(r",\s*|\s+et\s+", raw)
        if name.strip()
    ]


def extract_parser239_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 239."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_HEAD_OFFICE_REPRESENTATIVES_REMOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.head_office_representatives_powers_removed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, name,
                role="personne disposant d'un pouvoir de représentation",
                extra={
                    "action": "removed",
                    "powers_revoked": True,
                    "signing_revoked": True,
                    "legal_basis": "art. 110 al. 1 lit. e ORC",
                },
            )
            for name in _split_names(match.group("names"))
        ], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_EXPIRED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_expired_resolution.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("authorization_date")),
                "reason": "authorization_expired", "basis": "statutes",
            },
        )], ""

    match = _IT_ASSOCIATION_DISSOLVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.association_dissolved_by_members.v1", {
                "kind": "dissolution", "action": "dissolved",
                "decision_body": "assemblea dei soci",
                "decision_date": _iso_date(match.group("decision_date")),
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENSION_GRANTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extension_granted.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "start_date": _iso_date(match.group("start_date")),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_decision.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
            },
        )], ""

    match = _FR_ADMINISTRATOR_SIGNATURE_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.administrator_signature_revoked.v1",
            match.group("name"), role="administrateur", extra={
                "action": "signing_revoked", "role_retained": True,
            },
        )], ""

    match = _FR_TWO_ASSOCIATES_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associates_individual_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role="associé", signing="Einzelunterschrift",
                extra={"action": "signing_changed"},
            )
            for group in ("name1", "name2")
        ], ""

    match = _DE_ORGANIZATION_REGULATION_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_regulation_removed.v1", {
                "kind": "organization_regulation", "action": "removed",
                "regulation_date": _iso_date(match.group("regulation_date")),
            },
        )], ""

    match = _DE_AUDITOR_RENAMED_SAME_UID.fullmatch(leftover)
    if match and match.group("previous_uid") == match.group("uid"):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_renamed_same_uid.v1",
            match.group("name"), uid=match.group("uid"), role="Revisionsstelle",
            extra={
                "action": "renamed",
                "previous_name": match.group("previous_name").strip(),
                "uid": match.group("uid"),
            },
        )], ""

    match = _FR_PROXY_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.proxy_group_restrictions_changed.v1"
        removed = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(group),
                role="fondé de procuration", extra={
                    "action": "procuration_revoked", "signing_revoked": True,
                },
            )
            for group in ("removed1", "removed2")
        ]
        restricted_names = _split_names(match.group("restricted"))
        restricted = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name,
                role="fondé de procuration", signing="Kollektivprokura zu zweien",
                extra={
                    "action": "signing_restriction_changed",
                    "excluded_with": [
                        other for other in restricted_names if other != name
                    ],
                    "signing_continues": True,
                },
            )
            for name in restricted_names
        ]
        moved = _person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("moved"),
            place=match.group("place"), role="fondé de procuration",
            signing="Kollektivprokura zu zweien", extra={
                "action": "domicile_and_signing_restriction_changed",
                "signing_restriction": None, "signing_continues": True,
            },
        )
        return removed + restricted + [moved], ""

    match = _FR_COURT_NOTICE_NOT_TO_BE_PUBLISHED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.court_notice_not_to_be_published.v1", {
                "kind": "court_decision_publication", "action": "publication_cancelled",
                "reason": "deadline_not_expired", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
            },
        )], ""

    match = _DE_DIRECTOR_WITH_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.director_collective_signing.v1",
            match.group("name"), place=match.group("place"), role="Direktor",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        )], ""

    match = _DE_LIQUIDATION_ADDRESS_CHANGED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.liquidation_address_changed.v1", {
                "kind": "liquidation_address", "action": "changed",
                "address": match.group("address").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
                "previous_address": match.group("previous_address").strip(),
                "previous_postal_code": match.group("previous_postal_code"),
                "previous_place": match.group("previous_place").strip(),
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_name_corrected.v1",
            match.group("name"), role="associé-gérant", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_BOARD_PERSON_SECTIONS.fullmatch(leftover)
    if match:
        rule_id = "de.persons.board_members_removed_and_added.v1"
        events: list[Event] = []
        for section, event_type, action in (
            (match.group("removed"), "officer_removed", "removed"),
            (match.group("incoming"), "officer_changed", "appointed"),
        ):
            chunks = [chunk.strip() for chunk in section.split(";") if chunk.strip()]
            parsed: list[re.Match[str]] = []
            for chunk in chunks:
                person = _DE_BOARD_PERSON.fullmatch(chunk)
                if person is None:
                    parsed = []
                    break
                parsed.append(person)
            if not parsed:
                return [], leftover
            for person in parsed:
                name = f"{person.group('last').strip()} {person.group('first').strip()}"
                signing = person.group("signing").strip()
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    event_type, rule_id, name, place=person.group("place"),
                    role=person.group("role").strip(),
                    signing=signing if event_type == "officer_changed" else None,
                    extra={
                        "action": action,
                        "nationality": person.group("nationality").strip(),
                        "previous_signing": signing if event_type == "officer_removed" else None,
                        "signing_revoked": event_type == "officer_removed",
                    },
                ))
        return events, ""

    match = _FR_ASSOCIATE_APPOINTED_SOLE_MANAGER.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_sole_manager.v1",
            match.group("name"), role="associé-gérant unique",
            signing="Einzelunterschrift",
            extra={"action": "appointed_sole_manager"},
        )], ""

    return [], leftover
