from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_NON_PUBLIC_REMAINING_CHANGES = re.compile(
    r"^\[Die übrigen Änderungen betreffen die publikationspflichtigen "
    r"Tatsachen nicht\.\]$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_JUDGMENT = re.compile(
    r"^Mit Urteil vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<authority>.+?)\s+die gewährte definitive Nachlassstundung um\s+"
    r"(?P<duration>\w+)\s+Monate bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Urteil vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat das\s+"
    r"(?P<previous_authority>.+?)\s+eine definitive Nachlassstundung von\s+"
    r"(?P<previous_duration>\w+)\s+Monaten bis zum\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_FROM_PROCURATION = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]une "
    r"signature collective à deux est conférée à\s+(?P<name>[^()]+?)\s*"
    r"\(et non une procuration collective à deux comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_FOUNDATION_BOARD_ROLE_CHANGES = re.compile(
    r"^Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*von\s+"
    r"(?P<origin1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>[^,;\[]+),\s*mit\s+(?P<signing1>[^;\[]+)\s*"
    r"\[bisher:\s*(?P<previous_role1>[^,;\]]+),\s*mit\s+"
    r"(?P<previous_signing1>[^;\]]+)\];\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*von\s+"
    r"(?P<origin2>[^,;]+),\s*in\s+(?P<place2>[^,;]+),\s*"
    r"(?P<role2>[^,;\[]+),\s*mit\s+(?P<signing2>[^;\[]+)\s*"
    r"\[bisher:\s*(?P<previous_role2>[^,;\]]+),\s*mit\s+"
    r"(?P<previous_signing2>[^;\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_NON_ENFORCEABLE_JUDGMENT_ENTRY_CANCELLED = re.compile(
    r"^Le jugement du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<judgment_date>\d{2}\.\d{2}\.\d{4})\s+n['’]étant pas exécutoire,\s*"
    r"l['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est radiée\.\s*"
    r"Par conséquent,\s*la raison sociale de la société redevient:\s*"
    r"(?P<name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_DIRECTOR_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"directeur de la succursale\s+(?P<name>[^()]+?)\s+signe collectivement "
    r"à deux\s*\(et non individuellement\)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_TWO_LIQUIDATORS_ADDRESS = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*"
    r"Die Liquidation wird unter der Firma:\s*(?P<name>.+? in Liquidation)\s+"
    r"durchgeführt\.\s*Eingetragene Personen geändert:\s*"
    r"(?P<person1>[^,;]+),\s*(?P<previous_role1>.+?),\s*"
    r"(?P<previous_signing1>Kollektivunterschrift zu zweien),\s*neu\s+"
    r"(?P<role1>.+?),\s*(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<person2>[^,;]+),\s*(?P<previous_role2>.+?),\s*"
    r"(?P<previous_signing2>Kollektivunterschrift zu zweien),\s*neu\s+"
    r"(?P<role2>.+?),\s*(?P<signing2>Kollektivunterschrift zu zweien)\.\s*"
    r"Liquidationsadresse:\s*(?P<street>[^,]+),\s*"
    r"(?P<care_of>c/o\s+[^,]+),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>.+?)(?:\s+(?P<address_canton>[A-Z]{2}))?\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_COLLECTIVE_SIGNING = re.compile(
    r"^(?P<name1>[^,;]+),\s*de\s+(?P<origin1>[^,;]+),\s*à\s+"
    r"(?P<place1>[^,;]+)\s+et\s+(?P<name2>[^,;]+),\s*de\s+"
    r"(?P<origin2>[^,;]+),\s*à\s+(?P<place2>[^,;]+),\s*"
    r"sont membres du conseil d['’]administration avec signature collective "
    r"à deux\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_PREVIOUS_REGISTRY_COMPLETED = re.compile(
    r"^Bei den Eingetragenen Personen neu oder mutierend wurde bei der\s+"
    r"(?P<name>.+?)\s+der bisher Text nicht vollständig aufgeführt\.\s*"
    r"Korrekt sollte die Eintragung lauten:\s*\[bisher:\s*"
    r"(?P<previous_name>.+?)\s*\((?P<registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveaux membres du conseil de fondation sans signature:\s*"
    r"(?P<name1>[^,;]+),\s*de et à\s+(?P<place1>[^,;]+),\s*et\s+"
    r"(?P<name2>[^,;]+),\s*de\s+(?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FIVE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président,\s*"
    r"(?P<name2>[^,;]+),\s*de\s+(?P<origin2>[^,;]+),\s*à\s+"
    r"(?P<place2>[^,;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<name3>[^,;]+),\s*des\s+(?P<origin3>[^,;]+),\s*à\s+"
    r"(?P<place3>[^,;]+),\s*(?P<name4>[^,;]+),\s*d['’]"
    r"(?P<origin4>[^,;]+),\s*à\s+(?P<place4>[^,;]+)\s+et\s+"
    r"(?P<name5>[^,;]+),\s*de\s+(?P<origin5>[^,;]+),\s*à\s+"
    r"(?P<place5>[^,;]+),\s*(?P<country5>[A-Z]{1,3}),\s*tous avec "
    r"signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_COUNCIL_MEMBERS_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,;]+),\s*de et à\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>vice-président),\s*(?P<name2>[^,;]+),\s*de\s+"
    r"(?P<origin2>[^,;]+),\s*à\s+(?P<place2>[^,;]+),\s*"
    r"(?P<name3>[^,;]+),\s*de et à\s+(?P<place3>[^,;]+),\s*"
    r"(?P<name4>[^,;]+),\s*de et à\s+(?P<place4>[^,;]+),\s*et\s+"
    r"(?P<name5>[^,;]+),\s*de et à\s+(?P<place5>[^,;]+),\s*"
    r"sont membres du conseil avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_SIGNING_NOW_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,;]+),\s*(?P<name2>[^,;]+)\s+et\s+"
    r"(?P<name3>[^,;]+),\s*signent désormais collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_COLLECTIVE_SIGNING_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que le "
    r"gérant\s+(?P<name>[^,;]+?)\s+a maintenant la signature collective à "
    r"deux;\s*ses pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FOUR_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président,\s*"
    r"(?P<previous_president>[^,;]+),\s*jusqu['’]ici président,\s*"
    r"(?P<name3>[^,;]+),\s*de\s+(?P<origin3>[^,;]+),\s*à\s+"
    r"(?P<place3>[^,;]+),\s*(?P<country3>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name4>[^,;]+),\s*de\s+(?P<origin4>[^,;]+),\s*à\s+"
    r"(?P<place4>[^,;]+),\s*tous quatre avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_PRESIDENT_INDIVIDUAL = re.compile(
    r"^(?P<name>[^,;]+),\s*du et au\s+(?P<place>[^,;]+),\s*"
    r"est membre et président du conseil d['’]administration avec signature "
    r"individuelle\.?$",
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


def _duration_months(raw: str) -> int | None:
    token = raw.strip().lower()
    return int(token) if token.isdigit() else _GERMAN_NUMBERS.get(token)


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
        role=role.strip() if role else None,
        signing=signing.strip() if signing else None,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser216_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 216."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    if _DE_NON_PUBLIC_REMAINING_CHANGES.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.non_public_remaining_changes.v1", {
                "kind": "non_public_changes", "action": "noted",
                "registerable_facts_changed": False,
            },
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_JUDGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_judgment.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _duration_months(match.group("duration")),
                "until": _iso_date(match.group("until")),
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_authority": match.group("previous_authority").strip(),
                "previous_duration_months": _duration_months(
                    match.group("previous_duration")
                ),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        )], ""

    match = _FR_SIGNING_CORRECTED_FROM_PROCURATION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.signing_corrected_from_procuration.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "publication_corrected",
                "previous_signing": "Kollektivprokura zu zweien",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_TWO_FOUNDATION_BOARD_ROLE_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_foundation_board_role_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id,
                f"{match.group(f'surname{index}')}, {match.group(f'given{index}')}",
                place=match.group(f"place{index}"),
                role=match.group(f"role{index}"),
                signing=match.group(f"signing{index}"), extra={
                    "action": "role_changed",
                    "origin": match.group(f"origin{index}").strip(),
                    "previous_role": match.group(f"previous_role{index}").strip(),
                    "previous_signing": match.group(
                        f"previous_signing{index}"
                    ).strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_NON_ENFORCEABLE_JUDGMENT_ENTRY_CANCELLED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.non_enforceable_judgment_entry_cancelled.v1", {
                "kind": "registry_entry_cancelled",
                "action": "cancelled_as_judgment_not_enforceable",
                "authority": match.group("authority").strip(),
                "judgment_date": _iso_date(match.group("judgment_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "restored_name": match.group("name").strip(),
            },
        )], ""

    match = _FR_BRANCH_DIRECTOR_SIGNING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.branch_director_signing_corrected.v1",
            match.group("name"), role="directeur de la succursale",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "publication_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_DISSOLUTION_TWO_LIQUIDATORS_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_two_liquidators_address.v1"
        full_address = ", ".join((
            match.group("street").strip(),
            match.group("care_of").strip(),
            f"{match.group('postal_code')} {match.group('locality').strip()}"
            + (
                f" {match.group('address_canton')}"
                if match.group("address_canton") else ""
            ),
        ))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "new_name": match.group("name").strip(),
                    "liquidation": True,
                },
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"person{index}"),
                    role=match.group(f"role{index}"),
                    signing=match.group(f"signing{index}"), extra={
                        "action": "appointed_liquidator",
                        "previous_role": match.group(
                            f"previous_role{index}"
                        ).strip(),
                        "previous_signing": match.group(
                            f"previous_signing{index}"
                        ).strip(),
                    },
                )
                for index in (1, 2)
            ],
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "changed",
                    "street": match.group("street").strip(),
                    "care_of": match.group("care_of").strip(),
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                    "canton": match.group("address_canton"),
                    "full_address": full_address,
                },
            ),
        ], ""

    match = _FR_TWO_BOARD_MEMBERS_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_collective_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _DE_ORGANIZATION_PREVIOUS_REGISTRY_COMPLETED.fullmatch(leftover)
    if match and match.group("name").strip() == match.group("previous_name").strip():
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "de.persons.organization_previous_registry_completed.v1",
            match.group("name"), extra={
                "action": "previous_text_completed",
                "previous_registry_id": match.group("registry_id"),
                "organization": True,
            },
        )], ""

    match = _FR_TWO_FOUNDATION_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_without_signature.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation", extra={
                    "action": "appointed", "without_signature": True,
                    "origin": (
                        match.group("place1").strip()
                        if index == 1 else match.group("origin2").strip()
                    ),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_ADMINISTRATION_FIVE_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_five_individual.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président", signing="Einzelunterschrift",
            extra={"action": "appointed_president"},
        )]
        for index in range(2, 6):
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift", extra=extra,
            ))
        return events, ""

    match = _FR_FIVE_COUNCIL_MEMBERS_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.five_council_members_collective.v1"
        events = []
        for index in range(1, 6):
            place = match.group(f"place{index}")
            extra = {
                "action": "appointed",
                "origin": (
                    match.group("origin2").strip() if index == 2 else place.strip()
                ),
            }
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place,
                role=(match.group("role1") if index == 1 else "membre du conseil"),
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        return events, ""

    match = _FR_THREE_SIGNING_NOW_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_signing_now_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id,
                match.group(f"name{index}"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "modified"},
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_MANAGER_COLLECTIVE_SIGNING_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.manager_collective_signing_supplement.v1",
            match.group("name"), role="gérant",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "supplemented_and_modified",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "powers_modified": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_FOUR_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_four_individual.v1"
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("previous_president"),
                role="administrateur", signing="Einzelunterschrift", extra={
                    "action": "role_changed", "previous_role": "président",
                },
            ),
        ]
        for index in (3, 4):
            extra = {
                "action": "appointed",
                "origin": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift", extra=extra,
            ))
        return events, ""

    match = _FR_BOARD_MEMBER_PRESIDENT_INDIVIDUAL.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_president_individual.v1",
            match.group("name"), place=match.group("place"),
            role="membre et président du conseil d'administration",
            signing="Einzelunterschrift", extra={
                "action": "appointed", "origin": match.group("place").strip(),
            },
        )], ""

    return [], leftover
