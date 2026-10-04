from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATION_THREE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place1>[^,.;]+),\s*nommé président,\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*secrétaire,\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{1,3}),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^L['’]effet suspensif a été accordé au recours,\s*à l['’]encontre du "
    r"jugement de faillite du\s+(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"selon prononcé du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DOMICILES_SIGNING_CHANGED_PROXY_REVOKED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*désormais à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*désormais(?: à)?\s+(?P<place2>[^,.;]+),\s*"
    r"dont la procuration est éteinte,\s*signent maintenant individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXPIRING_AND_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif de\s+(?P<duration>\d+)\s+mois,\s*échéant\s+"
    r"(?P<until>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<name>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;()]+?)\s*\((?P<canton>[A-Z]{2})\),\s*"
    r"est désigné commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_FR_OTHER_ADDRESS_POSTAL_DISTRIBUTION_OFFICE = re.compile(
    r"^L['’]office de distribution postale de l['’]autre adresse est désormais\s+"
    r"(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+(?P<town>[^.]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_ROLE_SWAP = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici secrétaire et "
    r"nommé président,\s*et\s+(?P<name2>[^,.;]+),\s*nommé secrétaire,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NAME_CORRECTED_NO_UID = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"raison sociale du réviseur est\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_PREFIX_UID = re.compile(
    r"^Nouvelle raison sociale de l['’]organe de révision\s+"
    r"(?P<previous_name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\):\s*"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_PERSON_DOMICILE_REMARK_REMOVED = re.compile(
    r"^\[Die Bemerkung betreffend\s+(?P<remark>vertretungsberechtigte Person "
    r"mit Wohnsitz in der Schweiz und Rechtsdomizil)\s+wird gestrichen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_COMPENSATION_NOMINAL_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens qu['’]\s*a été remis\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+en contrepartie de la compensation de créance de "
    r"CHF\s+(?P<claim>[\d'.]+)\s*\(et non\s+(?P<previous_count>[\d']+)\s+"
    r"actions nominatives de CHF\s+(?P<previous_nominal>[\d'.]+),\s*"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_THREE_ROLES_POWERS_CHANGED = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<role1>président),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>vice-président),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*jusqu['’]ici président,\s*nommé\s+"
    r"(?P<role3>secrétaire),\s*lesquels signent collectivement à deux\.\s*"
    r"Les pouvoirs du vice-président et du secrétaire sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_FOREIGN_NEW_ASSOCIATE = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+"
    r"détient\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+qui n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_PRESIDENCY_CHANGED = re.compile(
    r"^Les administrateurs\s+(?P<name1>[^,.;]+),\s*nommée présidente et\s+"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici président directeur général,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_RESTRICTED_PROXY_FOUR = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre eux ni avec\s+"
    r"(?P<excluded1>[^,.;]+)\s+et\s+(?P<excluded2>[^,.;]+)\s+est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*et\s+(?P<name4>[^,.;]+),\s*de\s+"
    r"(?P<origin4>[^,.;]+),\s*les trois à\s+(?P<place234>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SHARE_TRANSFER_FOREIGN_BUYER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*maintenant associée pour\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*du\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)"
    r"(?:,\s*avec\s+(?P<buyer_signing>signature individuelle))?\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_ASSOCIATE_TRANSFER_TWO_MANAGERS = re.compile(
    r"^L['’]associée\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvelle associée\.\s*"
    r"Gérantes:\s*(?P=seller),\s*nommée présidente,\s*et\s+"
    r"(?P=buyer),\s*nommée secrétaire,\s*lesquelles signent individuellement\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser228_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 228."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ADMINISTRATION_THREE_INDIVIDUAL.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_three_individual.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="président du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_president_and_domicile_changed",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="secrétaire du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                place=match.group("place3"), role="membre du conseil d'administration",
                signing="Einzelunterschrift", extra={
                    "action": "appointed", "origin": match.group("origin3").strip(),
                    "country": match.group("country3"),
                },
            ),
        ], ""

    match = _FR_BANKRUPTCY_APPEAL_SUSPENSIVE_EFFECT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_appeal_suspensive_effect_granted.v1", {
                "kind": "bankruptcy", "action": "appeal_suspensive_effect_granted",
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_TWO_DOMICILES_SIGNING_CHANGED_PROXY_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_domiciles_individual_signing_proxy_revoked.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), signing="Einzelunterschrift", extra={
                    "action": "domicile_and_signing_changed",
                    "previous_procuration_revoked": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_EXPIRING_AND_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_expiring_and_commissioner.v1"
        common = {
            "decision_date": _french_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    **common, "kind": "composition_moratorium_granted",
                    "action": "granted", "moratorium_type": "definitive",
                    "duration_months": int(match.group("duration")),
                    "until": _french_date(match.group("until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    **common, "action": "appointed", "origin": match.group("origin").strip(),
                    "place_canton": match.group("canton"),
                },
            ),
        ], ""

    match = _FR_OTHER_ADDRESS_POSTAL_DISTRIBUTION_OFFICE.fullmatch(leftover)
    if match:
        street = match.group("street").strip()
        postal_code = match.group("postal_code")
        town = match.group("town").strip()
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.other_address_postal_distribution_office.v1", {
                "kind": "other_address", "action": "postal_distribution_office_changed",
                "street": street, "postal_code": postal_code, "town": town,
                "address": f"{street}, {postal_code} {town}",
            },
        )], ""

    match = _FR_TWO_ADMINISTRATORS_ROLE_SWAP.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_role_swap_collective.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed", "previous_role": "secrétaire",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="secrétaire du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed", "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_AUDITOR_NAME_CORRECTED_NO_UID.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_name_corrected_no_uid.v1",
            match.group("name"), role="organe de révision", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_AUDITOR_RENAMED_PREFIX_UID.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_renamed_prefix_uid.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision", extra={
                "action": "renamed", "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _DE_AUTHORIZED_PERSON_DOMICILE_REMARK_REMOVED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.authorized_person_domicile_remark_removed.v1", {
                "kind": "registry_remark", "action": "removed",
                "remark": match.group("remark").strip(),
            },
        )], ""

    match = _FR_CAPITAL_COMPENSATION_NOMINAL_CORRECTED.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        previous_count = _count(match.group("previous_count"))
        nominal = _amount(match.group("nominal"))
        claim = _amount(match.group("claim"))
        if count == previous_count and count * nominal == claim:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.capital_compensation_nominal_corrected.v1", {
                    "kind": "share_issue_by_claim_offset", "action": "corrected",
                    "shares_count": count, "share_kind": "actions nominatives",
                    "share_nominal": match.group("nominal"),
                    "previous_incorrect_share_nominal": match.group("previous_nominal"),
                    "claim_offset": match.group("claim"), "currency": "CHF",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_ref": match.group("notice_ref"),
                },
            )], ""

    match = _FR_BOARD_THREE_ROLES_POWERS_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_three_roles_powers_changed.v1"
        specs = (
            ("name1", "place1", "président du conseil d'administration", False),
            ("name2", None, "vice-président du conseil d'administration", True),
            ("name3", None, "secrétaire du conseil d'administration", True),
        )
        events = []
        for name_group, place_group, role, powers_modified in specs:
            extra = {"action": "role_and_signing_recorded"}
            if powers_modified:
                extra["powers_modified"] = True
            if name_group == "name1":
                extra["origin"] = match.group("origin1").strip()
            if name_group == "name3":
                extra["previous_role"] = "président"
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                place=match.group(place_group) if place_group else None,
                role=role, signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        return events, ""

    match = _FR_MANAGER_SHARE_TRANSFER_FOREIGN_NEW_ASSOCIATE.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before == remaining + transferred
            and transferred == buyer_count
            and len({
                match.group("nominal"), match.group("remaining_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.manager_share_transfer_foreign_new_associate.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associé-gérant",
                    extra={
                        "action": "shares_transferred", "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country"), "signing_authority": False,
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_TWO_ADMINISTRATORS_PRESIDENCY_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_presidency_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="présidente du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "role_changed", "previous_role": "président directeur général",
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_RESTRICTED_PROXY_FOUR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.restricted_proxy_four.v1"
        excluded = [match.group("excluded1").strip(), match.group("excluded2").strip()]
        events = []
        for index in range(1, 5):
            place = match.group("place1") if index == 1 else match.group("place234")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role="fondé de procuration",
                signing="Kollektivprokura zu zweien", extra={
                    "action": "proxy_granted", "origin": match.group(f"origin{index}").strip(),
                    "not_with_each_other": True, "excluded_signatories": excluded,
                },
            ))
        return events, ""

    match = _FR_ASSOCIATE_SHARE_TRANSFER_FOREIGN_BUYER.fullmatch(leftover)
    if match:
        remaining = _count(match.group("remaining"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            transferred == buyer_count
            and len({
                match.group("nominal"), match.group("transfer_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            rule_id = "fr.persons.associate_share_transfer_foreign_buyer.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"), role="associée", extra={
                        "action": "shares_transferred", "shares_before": remaining + transferred,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé",
                    signing="Einzelunterschrift" if match.group("buyer_signing") else None,
                    extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": buyer_count,
                        "origin": match.group("origin").strip(),
                        "country": match.group("country"),
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    match = _FR_FEMALE_ASSOCIATE_TRANSFER_TWO_MANAGERS.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if before >= transferred:
            rule_id = "fr.persons.female_associate_transfer_two_managers.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associée-gérante présidente", signing="Einzelunterschrift", extra={
                        "action": "shares_transferred_and_appointed_president",
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": before - transferred,
                        "counterparty": match.group("buyer").strip(), **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associée-gérante secrétaire",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received",
                        "shares_received": transferred, "shares_count": transferred,
                        "origin": match.group("origin").strip(),
                        "counterparty": match.group("seller").strip(), **common,
                    },
                ),
            ], ""

    return [], leftover
