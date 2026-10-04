from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_PROVISIONAL_MORATORIUM_WITH_CORPORATE_COMMISSIONER = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine provisorische "
    r"Nachlassstundung für die Dauer von\s+(?P<duration>\w+)\s+Monaten bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\s*"
    r"Als provisorische Sachwalterin wird die\s+(?P<commissioner>[^,.;]+),\s*"
    r"Herr\s+(?P<leader1>[^,.;]+),\s*Frau\s+(?P<leader2>[^,.;]+),\s*"
    r"(?P<street>[^,.;]+),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<place>[^,.;]+),\s*eingesetzt\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETION_REVOKED_BY_OWNER = re.compile(
    r"^Die Eintragung der Löschung des Einzelunternehmens erfolgte irrtümlich "
    r"auf Antrag der Inhaberin und wird von ihr widerrufen\.\s*"
    r"Da der Geschäftsbetrieb nicht aufgehört hat,\s*besteht der ursprüngliche "
    r"Eintrag mit den eingetragenen Tatsachen,\s*wie sie vor der Löschung "
    r"registriert waren,\s*unverändert weiter\.\s*"
    r"\[bisher:\s*(?P<previous>Löschung infolge Geschäftsaufgabe\.)\]\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_PEOPLE_COLLECTIVE_SIGNING_GRANTED = re.compile(
    r"^Signature collective à deux a été conférée à\s+(?P<name1>[^,.;]+),\s*"
    r"à\s+(?P<name2>[^,.;]+),\s*toutes deux de\s+(?P<origin12>[^,.;]+),\s*"
    r"ainsi qu['’]à\s+(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*"
    r"tous les trois à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_REGISTERED_PERSON_CHANGES = re.compile(
    r"^Eingetragene Personen geändert:\s*(?P<name1>[^,.;]+),\s*"
    r"(?P<previous_role1>[^,.;]+),\s*(?P<previous_signing1>[^,.;]+),\s*"
    r"neu\s+(?P<role11>[^,.;]+),\s*(?P<count1>[\d']+)\s+Stammanteile zu "
    r"CHF\s+(?P<nominal1>[\d'.]+),\s*(?P<role12>[^,.;]+),\s*"
    r"(?P<signing1>[^,.;]+)\.\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<previous_role21>[^,.;]+),\s*"
    r"(?P<previous_count2>[\d']+)\s+Stammanteile zu CHF\s+"
    r"(?P<previous_nominal2>[\d'.]+),\s*(?P<previous_role22>[^,.;]+),\s*"
    r"(?P<previous_signing2>[^,.;]+),\s*neu ohne Funktion und ohne "
    r"Stammanteile,\s*mit\s+(?P<signing2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_DOMICILE_CORRECTED = re.compile(
    r"^Der Eintrag Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+ist wie folgt berichtigt:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\(und nicht in\s+(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENING_REVOKED_AFTER_DISMISSAL = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat der\s+"
    r"(?P<authority>.+?)\s+das Konkursbegehren gegen die Gesellschaft infolge "
    r"Tilgung der Schuld abgewiesen\.\s*Die vom\s+(?P=authority)\s+verfügte "
    r"Konkurseröffnung vom\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"erfolgte dementsprechend fälschlicherweise\.\s*Die Publikation der "
    r"Konkurseröffnung vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<issue_date>\d{2}\.\d{2}\.\d{4}),\s*Publ\.\s*"
    r"(?P<publication_ref>\d+)\)\s+wird widerrufen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_DOMICILE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est domicilié(?:e)? à\s+(?P<place>[^,();]+),\s*"
    r"(?P<country>[A-Z]{1,3})\s*\(et non à\s+(?P<previous_place>[^,()]+),\s*"
    r"(?P<previous_country>[A-Z]{1,3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_DISSOLVED_BY_GENERAL_ASSEMBLY = re.compile(
    r"^Der Verein wurde mit Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.?$",
    re.I | re.UNICODE,
)
_DE_UID_PUBLISHED_INSTEAD_OF_ADMINISTRATION_NUMBER = re.compile(
    r"^Unter TR-Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+im SHAB Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+wurde "
    r"fälschlicherweise die Administrations-Nr\.\s*(?P<previous>ADM-[\d.]+)\s+"
    r"anstelle der korrekten UID-Nr\.\s*(?P<uid>CHE-[\d.]+)\s+publiziert\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_REMOVED_POWERS_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+)\s+n['’]est plus administrateur;\s*"
    r"ses pouvoirs sont radiés\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_WITH_PROXY_REMOVED = re.compile(
    r"^Ausgeschiedene Personen und erloschene Unterschriften:\s*"
    r"(?P<last>[^,.;]+),\s*(?P<first>[^,.;]+),\s*"
    r"(?P<nationality>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*mit\s+"
    r"(?P<signing>Kollektivprokura zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*sont membres du "
    r"conseil d['’]administration,\s*tous deux avec signature collective à "
    r"deux\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_AND_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif de\s+(?P<duration>\w+)\s+mois,\s*échéant le\s+"
    r"(?P<until>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<name>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*est désigné commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_SEAT_TAIL = re.compile(
    r"^\[bisher:\s*(?P<previous_place>Vufflens-la-Ville)\]\.?$",
    re.I | re.UNICODE,
)
_FR_DELEGATE_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+)\s+est nommé(?:e)?\s+(?P<role>délégué(?:e)?)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGEMENT_MEMBER_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est membre de la direction avec signature collective à deux\.?$",
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
_NUMBER_WORDS = {
    "un": 1,
    "une": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration_months(raw: str) -> int | None:
    normalized = raw.casefold()
    return int(normalized) if normalized.isdigit() else _NUMBER_WORDS.get(normalized)


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


def extract_parser240_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 240."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _DE_PROVISIONAL_MORATORIUM_WITH_CORPORATE_COMMISSIONER.fullmatch(leftover)
    if match:
        duration = _duration_months(match.group("duration"))
        if duration is None:
            return [], leftover
        rule_id = "de.text.provisional_moratorium_corporate_commissioner.v1"
        common = {
            "decision_date": _iso_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    **common,
                    "kind": "composition_moratorium_granted",
                    "action": "granted",
                    "moratorium_type": "provisional",
                    "duration_months": duration,
                    "until": _iso_date(match.group("until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("commissioner"),
                place=match.group("place"), role="provisorische Sachwalterin",
                extra={
                    **common,
                    "action": "appointed",
                    "mandate_leaders": [
                        match.group("leader1").strip(),
                        match.group("leader2").strip(),
                    ],
                    "address": (
                        f"{match.group('street').strip()}, "
                        f"{match.group('postal_code')} {match.group('place').strip()}"
                    ),
                    "postal_code": match.group("postal_code"),
                },
            ),
        ], ""

    match = _DE_SOLE_PROPRIETOR_DELETION_REVOKED_BY_OWNER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_deletion_revoked_by_owner.v1", {
                "kind": "registration_reinstated",
                "action": "deletion_revoked",
                "reason": "erroneous_deletion",
                "business_continues": True,
                "removed_fact": match.group("previous").strip(),
            },
        )], ""

    match = _FR_THREE_PEOPLE_COLLECTIVE_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_collective_signatures_granted.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted",
                    "origin": match.group("origin12" if index < 3 else "origin3").strip(),
                },
            )
            for index in (1, 2, 3)
        ], ""

    match = _DE_TWO_REGISTERED_PERSON_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_registered_person_changes.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=f"{match.group('role11').strip()}; {match.group('role12').strip()}",
                signing=match.group("signing1").strip(), extra={
                    "action": "roles_and_shares_changed",
                    "previous_role": match.group("previous_role1").strip(),
                    "previous_signing": match.group("previous_signing1").strip(),
                    "shares_count": _count(match.group("count1")),
                    "share_nominal": match.group("nominal1"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                signing=match.group("signing2").strip(), extra={
                    "action": "roles_and_shares_removed",
                    "previous_roles": [
                        match.group("previous_role21").strip(),
                        match.group("previous_role22").strip(),
                    ],
                    "previous_signing": match.group("previous_signing2").strip(),
                    "previous_shares_count": _count(match.group("previous_count2")),
                    "previous_share_nominal": match.group("previous_nominal2"),
                    "shares_count": 0,
                    "currency": "CHF",
                },
            ),
        ], ""

    match = _DE_PERSON_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.domicile_corrected_notice.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").strip(), extra={
                "action": "domicile_corrected",
                "origin": match.group("origin").strip(),
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _DE_BANKRUPTCY_OPENING_REVOKED_AFTER_DISMISSAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_opening_revoked_after_dismissal.v1", {
                "kind": "bankruptcy_revoked",
                "action": "revoked",
                "reason": "debt_settled",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "issue": match.group("issue"),
                "issue_date": _iso_date(match.group("issue_date")),
                "publication_ref": match.group("publication_ref"),
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_PERSON_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_corrected",
                "country": match.group("country").upper(),
                "previous_place": match.group("previous_place").strip(),
                "previous_country": match.group("previous_country").upper(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_ASSOCIATION_DISSOLVED_BY_GENERAL_ASSEMBLY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.association_dissolved_by_general_assembly.v2", {
                "kind": "dissolution",
                "action": "dissolved",
                "entity_type": "association",
                "decision_date": _iso_date(match.group("decision_date")),
                "decision_body": "Generalversammlung",
            },
        )], ""

    match = _DE_UID_PUBLISHED_INSTEAD_OF_ADMINISTRATION_NUMBER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_identifier_changed", "de.text.uid_instead_of_administration_number.v1", {
                "kind": "identifier_correction",
                "action": "corrected",
                "from": match.group("previous"),
                "to": match.group("uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
            },
        )], ""

    match = _FR_ADMINISTRATOR_REMOVED_POWERS_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.administrator_removed_powers_revoked.v1",
            match.group("name"), role="administrateur", extra={
                "action": "removed",
                "powers_revoked": True,
            },
        )], ""

    match = _DE_PERSON_WITH_PROXY_REMOVED.fullmatch(leftover)
    if match:
        signing = match.group("signing").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.proxy_holder_removed.v1",
            f"{match.group('last').strip()} {match.group('first').strip()}",
            place=match.group("place"), role="Prokurist", extra={
                "action": "removed",
                "nationality": match.group("nationality").strip(),
                "previous_signing": signing,
                "signing_revoked": True,
            },
        )], ""

    match = _FR_TWO_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_collective_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_AND_COMMISSIONER.fullmatch(leftover)
    if match:
        duration = _duration_months(match.group("duration"))
        if duration is None:
            return [], leftover
        rule_id = "fr.text.definitive_moratorium_expiring_and_commissioner.v2"
        common = {
            "decision_date": _french_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    **common,
                    "kind": "composition_moratorium_granted",
                    "action": "granted",
                    "moratorium_type": "definitive",
                    "duration_months": duration,
                    "until": _french_date(match.group("until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    **common,
                    "action": "appointed",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _DE_BRANCH_PREVIOUS_SEAT_TAIL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_previous_seat_tail.v1", {
                "action": "previous_seat_recorded",
                "from": match.group("previous_place").strip(),
            },
        )], ""

    match = _FR_DELEGATE_APPOINTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.delegate_appointed.v1",
            match.group("name"), role=match.group("role").strip(),
            extra={"action": "appointed"},
        )], ""

    match = _FR_MANAGEMENT_MEMBER_APPOINTED.fullmatch(leftover)
    if match:
        place = match.group("place").strip()
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.management_member_appointed.v1",
            match.group("name"), place=place, role="membre de la direction",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed", "origin": place},
        )], ""

    return [], leftover
