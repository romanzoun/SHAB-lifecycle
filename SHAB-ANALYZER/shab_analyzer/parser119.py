from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BOARD_THREE_WITH_CHANGED_SIGNING = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<role1>présidente),\s*"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<role2>vice-présidente),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*maintenant domicilié(?:e)?\s+à\s+"
    r"(?P<place3>[^,.;]+),\s*lesquels signent collectivement à deux\.\s*"
    r"Les pouvoirs de\s+(?P=name3)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_MALFORMED_SPACED_UID = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d[\s.]?\d{2}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_BOARD_AUDIT_WAIVER_WITHOUT_ARTICLE = re.compile(
    r"^Gemäss Erklärung des Verwaltungsrates vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_LIQUIDATORS_WITH_PREVIOUS_DIRECTOR = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*nommé\s+"
    r"(?P<role1>président),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"jusqu['’]ici\s+(?P<previous_role2>directeur),\s*tous deux gérants,\s*"
    r"lesquels continuent de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_FIRST_MOVED_AND_APPOINTED_PRESIDENT = re.compile(
    r"^Gérants:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié(?:e)?\s+à\s+"
    r"(?P<place1>[^,.;]+),\s*nommé(?:e)?\s+(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_INDIVIDUAL_PROXIES_SHARED_ORIGIN_AND_PLACE = re.compile(
    r"^Procuration individuelle est conférée à\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*tous deux de et à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_SUPPLEMENT_NO_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée? dans ce sens "
    r"que le capital-actions:\s*CHF\s+(?P<total>[\d'.]+),\s*divisé en\s+"
    r"(?P<count>[\d']+)\s+actions de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<share_kind>nominatives),?\s*,?\s*est entièrement libéré\.?$",
    re.I | re.UNICODE,
)
_FR_INTENDED_ASSET_ACQUISITION_COMPLETED = re.compile(
    r"^Reprise de biens:\s*La reprise de bien envisagée à la constitution "
    r"a été réalisée les\s+(?P<date1>\d{2}\.\d{2}\.\d{4})\s+et\s+"
    r"(?P<date2>\d{2}\.\d{2}\.\d{4})\s+pour le prix de CHF\s+"
    r"(?P<price>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_MOVED_APPOINTED_VICE_PRESIDENT = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant domicilié(?:e)?\s+à\s+"
    r"(?P<place>[^,.;]+),\s*membre du conseil de fondation,\s*nommé(?:e)?\s+"
    r"(?P<role>vice-président(?:e)?),\s*exerce désormais la signature sociale,\s*"
    r"collec?tivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_REPLACED_LEGACY_TO_UID = re.compile(
    r"^(?P<previous_name>.+?)\s*\((?P<previous_registry_id>CH-[\d-]+)\)\s+"
    r"n['’]est plus organe de révision\.\s*Nouvel organe de révision:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_THREE_WITH_SEPARATE_GROUP_SIGNING = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role1>président),\s*(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>président)\s+et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*tous trois\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_SIGNING_GRANTED_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux a été conférée à\s+"
    r"(?P<name>[^,.;]+),\s*nommé(?:e)?\s+(?P<role>directeur|directrice);\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND = re.compile(
    r"^Division des\s+(?P<from_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<from_nominal>[\d'.]+)\s+en\s+(?P<to_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<to_nominal>[\d'.]+)\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<capital_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<capital_nominal>[\d'.]+),\s*(?P<share_kind>nominatives)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_FOUR_INDIVIDUAL_SIGNATORIES = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]),\s*"
    r"(?P<role1>président),\s*(?P<name2>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role2>secrétaire),\s*(?P<name3>[^,.;]+),\s*de\s+"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]),\s*et\s+(?P<name4>[^,.;]+),\s*de\s+"
    r"(?P<origin4>[^,.;]+),\s*à\s+(?P<place4>[^,.;]+),\s*"
    r"(?P<country4>[A-Z]),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_COLLECTIVE_PROXIES_NOT_TOGETHER = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre eux,\s*est conférée "
    r"à\s+(?P<name1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*au\s+(?P<place2>[^,.;]+),\s*tous deux de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]"
    r"(?P<role>associé-gérant) se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous>[^()]+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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
    uid: str | None = None,
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


def extract_parser119_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 119."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BOARD_THREE_WITH_CHANGED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_three_with_changed_signing.v1"
        people = (
            ("name1", "place1", "administratrice présidente", "origin1"),
            ("name2", "place2", "administratrice vice-présidente", "origin2"),
            ("name3", "place3", "membre du conseil d'administration", None),
        )
        for name_key, place_key, role, origin_key in people:
            extra = {"action": "signing_changed"}
            if origin_key:
                extra["heimat"] = match.group(origin_key).strip()
            if name_key == "name3":
                extra["domicile_changed"] = True
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key), role=role,
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _DE_BRANCH_ADDED_MALFORMED_SPACED_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_added_malformed_spaced_uid.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": re.sub(r"\s+", "", match.group("uid")).upper(),
            },
        ))

    match = _DE_BOARD_AUDIT_WAIVER_WITHOUT_ARTICLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.board_audit_waiver_without_article.v1",
            {
                "kind": "limited_audit_waiver", "action": "declared",
                "declarant": "Verwaltungsrat", "date": _iso_date(match.group("date")),
            },
        ))

    match = _FR_MANAGER_LIQUIDATORS_WITH_PREVIOUS_DIRECTOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_liquidators_previous_director.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="gérant liquidateur président", signing="Einzelunterschrift",
                extra={"action": "appointed", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="gérant liquidateur", signing="Einzelunterschrift",
                extra={
                    "action": "role_changed", "previous_role": match.group("previous_role2"),
                    "signing_continues": True,
                },
            ),
        ])

    match = _FR_TWO_MANAGERS_FIRST_MOVED_AND_APPOINTED_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_first_moved_appointed_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="gérant président",
                signing="Einzelunterschrift",
                extra={"action": "moved_and_appointed", "domicile_changed": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="gérant", signing="Einzelunterschrift",
                extra={"action": "recorded", "heimat": match.group("origin2").strip()},
            ),
        ])

    match = _FR_TWO_INDIVIDUAL_PROXIES_SHARED_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_individual_proxies_shared_origin_place.v1"
        for name_key in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_key),
                place=match.group("place"), role="fondé de procuration",
                signing="Einzelprokura",
                extra={
                    "action": "proxy_granted", "heimat": match.group("place").strip(),
                },
            ))

    match = _FR_SHARE_CAPITAL_SUPPLEMENT_NO_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_supplement_no_notice.v1",
            {
                "kind": "share_capital", "action": "publication_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "total": match.group("total"), "currency": "CHF",
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "actions nominatives", "fully_paid": True,
            },
        ))

    match = _FR_INTENDED_ASSET_ACQUISITION_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.intended_asset_acquisition_completed.v1",
            {
                "kind": "intended_asset_acquisition", "action": "completed",
                "completion_dates": [
                    _iso_date(match.group("date1")), _iso_date(match.group("date2")),
                ],
                "price": match.group("price"), "currency": "CHF",
            },
        ))

    match = _FR_FOUNDATION_MEMBER_MOVED_APPOINTED_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_moved_vice_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation vice-président",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "moved_appointed_and_signing_granted", "domicile_changed": True,
            },
        ))

    match = _FR_AUDITOR_REPLACED_LEGACY_TO_UID.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.auditor_replaced_legacy_to_uid.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                role="organe de révision",
                extra={
                    "action": "removed",
                    "registry_id": match.group("previous_registry_id"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="organe de révision",
                uid=match.group("uid"),
                extra={"action": "appointed", "uid": match.group("uid")},
            ),
        ])

    match = _FR_BOARD_THREE_WITH_SEPARATE_GROUP_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_three_separate_group_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur président", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="administrateur", signing="Einzelunterschrift",
                extra={"action": "role_changed", "previous_role": "président"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                place=match.group("place3"), role="administrateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin3").strip()},
            ),
        ])

    match = _FR_DIRECTOR_SIGNING_GRANTED_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_signing_granted_proxy_revoked.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed_and_signing_changed",
                "previous_authority": "procuration", "previous_authority_revoked": True,
            },
        ))

    match = _FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_split_without_source_kind.v1",
            {
                "kind": "share_split", "currency": "CHF",
                "from_count": _count(match.group("from_count")),
                "from_nominal": match.group("from_nominal"),
                "to_count": _count(match.group("to_count")),
                "to_nominal": match.group("to_nominal"),
                "total": match.group("total"), "fully_paid": True,
                "share_kind": "actions nominatives",
            },
        ))

    match = _FR_BOARD_FOUR_INDIVIDUAL_SIGNATORIES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_four_individual_signatories.v1"
        people = (
            ("name1", "place1", "administrateur président", "origin1", "country1", "recorded"),
            ("name2", None, "administrateur secrétaire", None, None, "appointed_secretary"),
            ("name3", "place3", "administrateur", "origin3", "country3", "recorded"),
            ("name4", "place4", "administrateur", "origin4", "country4", "recorded"),
        )
        for name_key, place_key, role, origin_key, country_key, action in people:
            extra = {"action": action}
            if origin_key:
                extra["heimat"] = match.group(origin_key).strip()
            if country_key:
                extra["country"] = match.group(country_key)
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key) if place_key else None,
                role=role, signing="Einzelunterschrift", extra=extra,
            ))

    match = _FR_TWO_COLLECTIVE_PROXIES_NOT_TOGETHER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_collective_proxies_not_together.v1"
        for name_key, place_key in (("name1", "place1"), ("name2", "place2")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_key),
                place=match.group(place_key), role="fondé de procuration",
                signing="Kollektivprokura zu zweien",
                extra={
                    "action": "proxy_granted", "heimat": match.group("origin").strip(),
                    "not_with_each_other": True,
                },
            ))

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_name_corrected_notice.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "name_corrected", "previous": match.group("previous").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
