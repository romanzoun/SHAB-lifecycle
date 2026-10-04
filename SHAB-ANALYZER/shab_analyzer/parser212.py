from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_MIXED_THREE_REMOVED_OFFICERS = re.compile(
    r"^Gelöschte Personen:\s*(?P<name1>[^,;]+),\s*"
    r"(?P<role1>[^,;]+),\s*(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<name2>[^,;]+),\s*(?P<signing2>Kollektivprokura zu zweien);\s*"
    r"(?P<name3>[^,;]+),\s*(?P<signing3>Kollektivprokura zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ADDRESS_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]adresse de la fondation est sise\s+(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_ADMINISTRATORS_SHARED_ORIGIN_PLACE = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommée?\s+"
    r"(?P<role1>présidente?),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+),\s*tous deux de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_VICE_PRESIDENT_AND_THREE_COMMITTEE_MEMBERS = re.compile(
    r"^(?P<vice_president>[^,.;]+)\s+est nommé\s+vice-président\.\s*"
    r"Nouveaux membres du comité(?:\s+avec signature collective à deux)?\s*"
    r":\s*(?P<name1>[^,.;]+),\s*"
    r"du\s+(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>.+?),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*"
    r"de et à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_AND_FIVE_SIGNATURES_REVOKED = re.compile(
    r"^(?:Les\s+(?P<share_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+ne sont désormais plus restreintes quant "
    r"à la transmissibilité\s*\(art\.\s*685a,\s*al\.\s*3\s*CO\)\.\s*)?"
    r"(?P<liquidator>[^,.;]+),\s*administrateur dont la signature est "
    r"radiée,\s*est nommé liquidateur(?:\s+avec signature individuelle)?\.\s*"
    r"La signature des administrateurs\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*(?P<name4>[^,.;]+)\s+et\s+"
    r"(?P<name5>[^,.;]+)\s+est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_PROCURATION_RESTRICTION_CHANGES = re.compile(
    r"^(?P<name1>[^,.;]+)\s+continue de signer par procuration,\s*"
    r"collectivement à deux,\s*mais désormais sans autre restriction\.\s*"
    r"(?P<name2>[^,.;]+)\s+et\s+(?P<name3>[^,.;]+)\s+continuent de "
    r"signer par procuration,\s*collectivement à deux,\s*mais désormais "
    r"sauf entre eux et sauf avec\s+(?P<name4>[^,.;]+)\.\s*"
    r"(?P=name4)\s+contin(?:u)?e de signer collectivement à deux,\s*"
    r"mais désormais par procuration et sauf avec\s+(?P=name2)\s+et\s+"
    r"(?P=name3)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_STORE_MENTIONS_REMOVED = re.compile(
    r"^Radiation de la mention relative à de l['’]exploitation d['’]un "
    r"magasin à l['’]enseigne\s+[\"“](?P<store1>.+?)[\"”]\s+et à "
    r"l['’]exploitation d['’]un magasin à l['’]enseigne\s+"
    r"[\"“](?P<store2>.+?)[\"”]\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_LIQUIDATOR_FRAGMENT = re.compile(
    r"^\((?P<translated_name>.+? in liquidation)\),\s*par\s+"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*liquidatrice\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_SIGNING_GRANTED = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?P<role>membre du conseil de fondation),\s*"
    r"exerce désormais la signature sociale,\s*collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_DUPLICATE_DOMICILE_ENTRY_CORRECTED = re.compile(
    r"^Mit der mit TR vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eingetragenen Domiziländerung wurde das bereits eingetragene Domizil "
    r"der Gesellschaft irrtümlich erneut eingetragen\.\s*Da das Domizil "
    r"nach wie vor gültig ist,\s*bleibt der Eintrag bestehen\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_LIST_TO_BE_SUPPLEMENTED = re.compile(
    r"^Die Liste der Belege ist nachzutragen\.?$", re.I | re.UNICODE
)
_DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive "
    r"Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Als Sachwalterin "
    r"wird die\s+(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"Patentträger\s+(?P<representative1>.+?)\s+und/oder\s+"
    r"(?P<representative2>.+?),\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^,.;]+),\s*eingesetzt\.?$",
    re.I | re.UNICODE,
)
_FR_VOTING_PRIVILEGE_SHARE_RESTRICTION = re.compile(
    r"^Les\s+(?P<count1>[\d']+)\s+actions de CHF\s+"
    r"(?P<nominal1>[\d'.]+),\s*à droit de vote privilégié,\s*et\s+"
    r"(?P<count2>[\d']+)\s+actions ordinaires de CHF\s+"
    r"(?P<nominal2>[\d'.]+),\s*toutes nominatives,\s*sont liées selon "
    r"status\.\s*Capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P=count1)\s+actions de CHF\s+"
    r"(?P=nominal1),\s*à droit de vote privilégié et\s+"
    r"(?P=count2)\s+actions ordinaires de CHF\s+(?P=nominal2),\s*"
    r"toutes nominatives,\s*liées selon status\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_CREATED = re.compile(
    r"^Création d['’]un capital-participation,\s*fondée sur la clause "
    r"d['’]augmentation conditionnelle relative à l['’]octroi de droits "
    r"adoptée le\s+(?P<clause_date>\d{2}\.\d{2}\.\d{4}),\s*par "
    r"l['’]émission de\s+(?P<issued>[\d']+)\s+bons de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*nominatifs,\s*liés selon statuts\.\s*"
    r"Capital-participation:\s*CHF\s+(?P<total>[\d'.]+),\s*entièrement "
    r"libéré,\s*divisé en\s+(?P<count>[\d']+)\s+bons de CHF\s+"
    r"(?P=nominal),\s*nominatifs,\s*liés selon statuts\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_JUDGMENT_EXECUTION_SUSPENDED = re.compile(
    r"^Par ordonnance du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+le\s+"
    r"(?P<authority>.+?)\s+a suspendu l['’]exécution du jugement de "
    r"faillite rendu le\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PETITION_LIFTED_COMPANY_CONTINUES = re.compile(
    r"^Mit Verfügung des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde das Konkursbegehren "
    r"aufgehoben\.\s*Infolgedessen besteht die Firma entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*Mit Verfügung des\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+ist über diese "
    r"Gesellschaft mit Wirkung ab dem\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}[.:]\d{2})\s+Uhr,\s*der Konkurs eröffnet "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)


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


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    normalized = raw.lower()
    return int(normalized) if normalized.isdigit() else _DE_NUMBERS[normalized]


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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser212_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 212."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _MIXED_THREE_REMOVED_OFFICERS.fullmatch(leftover)
    if match:
        rule_id = "mixed.persons.three_removed_officers.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"name{index}"),
                role=match.group("role1").strip() if index == 1 else None,
                signing=match.group(f"signing{index}"),
                extra={"action": "removed"},
            )
            for index in (1, 2, 3)
        ], ""

    match = _FR_FOUNDATION_ADDRESS_CORRECTED.fullmatch(leftover)
    if match:
        address = f"{match.group('address').strip()}, {match.group('postal_code')} {match.group('locality').strip()}"
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.foundation_address_corrected.v1", {
                "kind": "registered_address", "action": "corrected",
                "address": address, "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_THREE_ADMINISTRATORS_SHARED_ORIGIN_PLACE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_administrators_shared_origin_place.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").lower(), signing="Einzelunterschrift",
                extra={"action": "appointed"},
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group("place"), role="administrateur",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed", "origin": match.group("origin").strip(),
                    },
                )
                for index in (2, 3)
            ],
        ], ""

    match = _FR_VICE_PRESIDENT_AND_THREE_COMMITTEE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.vice_president_and_three_committee_members.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("vice_president"),
            role="vice-président", extra={"action": "appointed"},
        )]
        for index in (1, 2, 3):
            place = match.group(f"place{index}")
            origin = place if index == 3 else match.group(f"origin{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="membre du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": origin.strip(),
                },
            ))
        return events, ""

    match = _FR_LIQUIDATOR_AND_FIVE_SIGNATURES_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.liquidator_and_five_signatures_revoked.v1"
        events = []
        if match.group("share_count"):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.share_transfer_restriction_removed.v5", {
                    "kind": "share_transfer_restriction", "action": "removed",
                    "shares_count": _count(match.group("share_count")),
                    "share_nominal": match.group("share_nominal"),
                    "currency": "CHF", "legal_basis": "Art. 685a Abs. 3 OR",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("liquidator"),
            role="liquidateur", signing="Einzelunterschrift", extra={
                "action": "appointed_liquidator", "previous_role": "administrateur",
                "previous_signing_revoked": True,
            },
        ))
        events.extend(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                role="administrateur", extra={"action": "revoked"},
            )
            for index in range(1, 6)
        )
        return events, ""

    match = _FR_FOUR_PROCURATION_RESTRICTION_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_procuration_restriction_changes.v1"
        names = [match.group(f"name{index}").strip() for index in range(1, 5)]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name,
                signing="Kollektivprokura zu zweien", extra={
                    "action": "restriction_changed", "continued": True,
                    "restriction": (
                        None if index == 0 else
                        [other for other in names[1:] if other != name]
                    ),
                },
            )
            for index, name in enumerate(names)
        ], ""

    match = _FR_TWO_STORE_MENTIONS_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.two_store_mentions_removed.v1", {
                "kind": "store_operation_mentions", "action": "removed",
                "store_names": [match.group("store1"), match.group("store2")],
            },
        )], ""

    match = _FR_CORPORATE_LIQUIDATOR_FRAGMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.corporate_liquidator_fragment.v1",
            match.group("name"), uid=match.group("uid"),
            place=match.group("place"), role="liquidatrice", extra={
                "action": "appointed_liquidator",
                "translated_liquidation_name": match.group("translated_name").strip(),
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_SIGNING_GRANTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.foundation_member_signing_granted.v2",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien", extra={"action": "granted"},
        )], ""

    match = _DE_DUPLICATE_DOMICILE_ENTRY_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.duplicate_domicile_entry_corrected.v1", {
                "kind": "registered_address", "action": "duplicate_entry_corrected",
                "entry_date": _iso_date(match.group("entry_date")),
                "address_remains_valid": True,
            },
        )], ""

    match = _DE_DOCUMENT_LIST_TO_BE_SUPPLEMENTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.document_list_to_be_supplemented.v1",
            {"kind": "document_list", "action": "to_be_supplemented"},
        )], ""

    match = _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "de.text.definitive_moratorium_with_commissioner.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium", "action": "granted",
                    "moratorium_type": "definitive",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "duration_months": _duration(match.group("duration")),
                    "until": _iso_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                uid=match.group("uid"), place=match.group("place"),
                role="Sachwalterin", extra={
                    "action": "appointed",
                    "representatives": [
                        match.group("representative1").strip(),
                        match.group("representative2").strip(),
                    ],
                    "address": match.group("address").strip(),
                    "postal_code": match.group("postal_code"),
                },
            ),
        ], ""

    match = _FR_VOTING_PRIVILEGE_SHARE_RESTRICTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.voting_privilege_share_restriction.v1", {
                "kind": "share_structure", "action": "transfer_restricted",
                "currency": "CHF", "total": match.group("total"),
                "fully_paid": True, "share_kind": "registered",
                "transfer_restricted_by_statutes": True,
                "classes": [
                    {
                        "shares_count": _count(match.group("count1")),
                        "share_nominal": match.group("nominal1"),
                        "voting_privilege": True,
                    },
                    {
                        "shares_count": _count(match.group("count2")),
                        "share_nominal": match.group("nominal2"),
                        "voting_privilege": False,
                    },
                ],
            },
        )], ""

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_CREATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_created.v1", {
                "kind": "conditional_participation_capital", "action": "created",
                "clause_date": _iso_date(match.group("clause_date")),
                "issued_participation_certificates": _count(match.group("issued")),
                "participation_certificates": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "total": match.group("total"), "currency": "CHF",
                "fully_paid": True, "participation_certificate_kind": "registered",
                "transfer_restricted_by_statutes": True,
            },
        )], ""

    match = _FR_BANKRUPTCY_JUDGMENT_EXECUTION_SUSPENDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_judgment_execution_suspended.v1", {
                "kind": "bankruptcy", "action": "execution_suspended",
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "authority": match.group("authority").strip(),
                "suspensive_effect": True,
            },
        )], ""

    match = _DE_BANKRUPTCY_PETITION_LIFTED_COMPANY_CONTINUES.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_petition_lifted_company_continues.v1", {
                "kind": "bankruptcy", "action": "lifted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "company_continues": True,
                "previous_authority": match.group("previous_authority").strip(),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_effective_date": _iso_date(match.group("effective_date")),
                "previous_effective_time": match.group("effective_time").replace(".", ":"),
            },
        )], ""

    return [], leftover
