from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ORIGIN = r"(?:du|de la|des|de|d['’])\s*"

_FR_STATUTES_ADAPTED_NEW_LAW = re.compile(
    r"^Statuts adaptés au nouveau droit\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_EXTENDED_DOTTED = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a prolongé le sursis concordataire définitif "
    r"accordé à la société jusqu['’]au\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_NEW_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+?)"
    r"(?:,\s*maintenant originaire de\s+(?P<seller_origin>[^,.;]+),\s*|\s+)"
    r"a cédé\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"nouvel associé,\s*lequel est en outre nommé gérant"
    r"(?:\s+avec signature individuelle)?\.?"
    r"(?:\s+(?P=seller)\s+est désormais titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+))?\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_SEAT_REGISTRY_ITEM = re.compile(
    r"\s*\[Sitz\]\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+HR\s+"
    r"(?P<register_canton>[A-Z]{2})\.?",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{2,3}),\s*sont membres du conseil "
    r"d['’]administration,\s*sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_APPOINTED_SIGNATURE_REVOKED = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la signature est radiée,\s*"
    r"est nommé liquidateur(?:\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_ALSO_DIRECTOR_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?:n°|no)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que "
    r"l['’]administrateur\s+(?P<name>[^,.;]+)\s+est aussi directeur\.?$",
    re.I | re.UNICODE,
)
_FR_SIX_DOMICILES_CORRECTED = re.compile(
    r"^(?P<name1>[^,]+?)\s+est en réalité domicilié à\s+"
    r"(?P<place1>[^,]+),\s*(?P<region1>[^,]+),\s*(?P<country1>[A-Z]{3}),\s*"
    r"(?P<name2>[^,]+?)\s+à\s+(?P<place2>[^,]+),\s*"
    r"(?P<region2>[^,]+),\s*(?P<country2>[A-Z]{3}),\s*"
    r"(?P<name3>[^,]+?)\s+à\s+(?P<place3>[^,]+),\s*"
    r"(?P<region3>[^,]+),\s*(?P<country3>[A-Z]{3}),\s*"
    r"(?P<name4>[^,]+?)\s+à\s+(?P<place4>[^,]+),\s*"
    r"(?P<region4>[^,]+),\s*(?P<country4>[A-Z]{3}),\s*"
    r"(?P<name5>[^,]+?)\s+à\s+(?P<place5>[^,]+),\s*"
    r"(?P<region5>[^,]+),\s*(?P<country5>[A-Z]{3}),\s*et\s*"
    r"(?P<name6>[^,]+?)\s+à\s+(?P<place6>[^,]+),\s*"
    r"(?P<country6>[A-Z]{3})\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_ROLE_CHANGES_AND_NEW_MEMBERS = re.compile(
    r"^Les membres du conseil\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role1>secrétaire),\s*nommé\s+(?P<role1>président),\s*"
    r"(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>président),\s*maintenant\s+"
    r"(?P<role2>secrétaire)\s+et\s+(?P<name3>[^,.;]+),\s*nommé\s+"
    r"(?P<role3>trésorier),\s*continuent à signer collectivement à deux\.\s*"
    r"(?P<name4>[^,.;]+),\s*de et à\s+(?P<place4>[^,.;]+)\s+et\s+"
    r"(?P<name5>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin5>[^,.;]+),\s*à\s+(?P<place5>[^,.;]+),\s*"
    r"sont membres du conseil,\s*tous deux"
    r"(?:\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTION_THREE_OFFICERS = re.compile(
    r"^L['’]inscription au journal\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée et complétée "
    r"en ce sens que signature collective à deux a été conférée à\s+"
    r"(?P<name1>[^,]+),\s*\(et non pas\s+(?P<previous_name1>[^)]+)\),\s*"
    + _FR_ORIGIN
    + r"(?P<origin1>[^,]+),\s*à\s+(?P<place1>[^,]+),\s*"
    r"(?P<role1>directeur adjoint)\.\s*Signature collective à deux,\s*"
    r"limitée à l['’]établissement principal a été conférée\s+(?:à\s+)?"
    r"(?P<name2>[^,]+)\s*\(et non pas\s+(?P<previous_name2>[^)]+)\),\s*"
    r"(?P<role2>directeur),\s*et à\s+(?P<name3>[^,]+),\s*de et à\s+"
    r"(?P<place3>[^,]+),\s*(?P<role3>directrice adjointe)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_FOREIGN_ORGANIZATION = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<foreign_registry_id>[^)]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{2,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*" + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé "
    r"avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant président"
    r"(?:\s+avec signature individuelle)?\.?\s+"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+"
    r"parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTED_NESTED_COUNTRY = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est à\s+(?P<place>[^()]+?)\s*"
    r"\(et non à\s+(?P<previous_place>[^()]+\([^)]+\))\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT_VP_SECRETARY = re.compile(
    r"^Nouveau membre du conseil de fondation"
    r"(?:\s+avec signature collective à deux)?\s+avec le président,\s*le "
    r"vice-président ou le secrétaire:\s*(?P<name>[^,.;]+),\s*"
    + _FR_ORIGIN
    + r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def _branch_events(
    text: str,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> list[Event] | None:
    matches: list[re.Match[str]] = []
    position = 0
    while position < len(text):
        match = _DE_BRANCH_SEAT_REGISTRY_ITEM.match(text, position)
        if not match or match.end() == position:
            return None
        matches.append(match)
        position = match.end()
    if not matches:
        return None
    return [
        _event(
            publication_id,
            published_at,
            org_uid,
            plz,
            canton,
            "branch_changed",
            "de.text.branch_seat_registry_sequence.v1",
            {
                "action": "added",
                "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "register_canton": match.group("register_canton").upper(),
            },
        )
        for match in matches
    ]


def extract_parser215_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 215."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    if _FR_STATUTES_ADAPTED_NEW_LAW.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_adapted_new_law.v1", {
                "kind": "statutes", "action": "adapted",
                "legal_framework": "new_law",
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_EXTENDED_DOTTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.definitive_moratorium_extended_dotted.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _FR_ASSOCIATE_TRANSFER_NEW_MANAGER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = (
            _count(match.group("remaining"))
            if match.group("remaining") else before - transferred
        )
        valid = (
            before - transferred == remaining
            and (
                not match.group("remaining_nominal")
                or match.group("remaining_nominal") == match.group("nominal")
            )
        )
        if valid:
            rule_id = "fr.persons.associate_transfer_new_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
            seller_extra = {
                **common, "action": "shares_transferred", "counterparty": buyer,
                "shares_before": before, "shares_transferred": transferred,
                "shares_count": remaining,
            }
            if match.group("seller_origin"):
                seller_extra["origin"] = match.group("seller_origin").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra=seller_extra,
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift", extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "origin": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": transferred,
                        "new_associate": True,
                    },
                ),
            ], ""

    branches = _branch_events(
        leftover, publication_id, published_at, org_uid, plz, canton
    )
    if branches:
        return branches, ""

    match = _FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_without_signature.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                    **(
                        {"country": match.group("country2")}
                        if index == 2 else {}
                    ),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_LIQUIDATOR_APPOINTED_SIGNATURE_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.liquidator_appointed_signature_revoked.v1",
            match.group("name"), role="liquidateur",
            signing="Einzelunterschrift", extra={
                "action": "appointed_liquidator",
                "previous_signing_revoked": True,
            },
        )], ""

    match = _FR_ADMINISTRATOR_ALSO_DIRECTOR_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_also_director_supplement.v1",
            match.group("name"), role="administrateur et directeur", extra={
                "action": "additional_role_added", "additional_role": "directeur",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_SIX_DOMICILES_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.six_domiciles_corrected.v1"
        events = []
        for index in range(1, 7):
            extra = {
                "action": "domicile_corrected",
                "country": match.group(f"country{index}"),
            }
            region = match.groupdict().get(f"region{index}")
            if region:
                extra["region"] = region.strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), extra=extra,
            ))
        return events, ""

    match = _FR_FOUNDATION_BOARD_ROLE_CHANGES_AND_NEW_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_board_role_changes_new_members.v1"
        events = []
        for index in (1, 2, 3):
            extra = {"action": "role_changed" if index < 3 else "role_added"}
            if index < 3:
                extra["previous_role"] = match.group(f"previous_role{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}"),
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name4"),
                place=match.group("place4"), role="membre du conseil",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("place4").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name5"),
                place=match.group("place5"), role="membre du conseil",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin5").strip(),
                },
            ),
        ])
        return events, ""

    match = _FR_SIGNING_CORRECTION_THREE_OFFICERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.signing_correction_three_officers.v1"
        common = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id, {
                    "kind": "officer_names_and_signing", "action": "corrected",
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role=match.group("role1"),
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "action": "name_corrected_and_signing_granted",
                    "previous_name": match.group("previous_name1").strip(),
                    "origin": match.group("origin1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role=match.group("role2"),
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "action": "name_corrected_and_signing_granted",
                    "previous_name": match.group("previous_name2").strip(),
                    "signing_scope": "principal_establishment",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                place=match.group("place3"), role=match.group("role3"),
                signing="Kollektivunterschrift zu zweien", extra={
                    **common, "action": "signing_granted",
                    "origin": match.group("place3").strip(),
                    "signing_scope": "principal_establishment",
                },
            ),
        ], ""

    match = _FR_MANAGER_TRANSFER_TO_FOREIGN_ORGANIZATION.fullmatch(leftover)
    if match and (
        match.group("nominal") == match.group("transfer_nominal")
        == match.group("buyer_nominal")
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
    ):
        rule_id = "fr.persons.manager_transfer_foreign_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": remaining + transferred,
                    "shares_transferred": transferred, "shares_count": remaining,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "foreign_registry_id": match.group("foreign_registry_id"),
                    "country": match.group("country"), "new_associate": True,
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.share_transfer_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président", signing="Einzelunterschrift", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True,
                },
            ),
        ], ""

    match = _FR_DOMICILE_CORRECTED_NESTED_COUNTRY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_nested_country.v1",
            match.group("name"), place=match.group("place"), extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT_VP_SECRETARY.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_three_signers_secretary.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "required_with": ["président", "vice-président", "secrétaire"],
            },
        )], ""

    return [], leftover
