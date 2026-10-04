from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_TWO_MANAGERS_REMOVED_SHARES_TO_EXISTING_MANAGER = re.compile(
    r"^(?P<removed1>[^,.;]+?)\s+et,?\s+(?P<removed2>[^,.;]+?)\s+"
    r"ne sont plus associés ni gérants,\s*leurs pouvoirs étant radiés;\s*"
    r"les\s+(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+"
    r"du premier et les\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+du second ont été cédées à l['’]associé-gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*jusqu['’]ici président et directeur,\s*lequel "
    r"détient ainsi les\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+formant le capital de CHF\s+"
    r"(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_INTRODUCED = re.compile(
    r"^Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte Kapitalerhöhung "
    r"gemäss näherer Umschreibung in den Statuten eingeführt\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_APPOINTED_LIQUIDATOR = re.compile(
    r"^L['’]administrateur unique\s+(?P<name>[^,.;]+?)\s+est désormais "
    r"liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’](?P<seller_role>associé(?:e)?-gérant(?:e)?)\s+"
    r"(?P<seller>[^,.;]+),\s*(?:lequel|laquelle) est "
    r"élu(?:e)?\s+(?P<president_role>président(?:e)?),\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<buyer_role>nouvel(?:le)? associée?)\s+avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"(?P<manager_role>gérant(?:e)?)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTORS_AND_PROXY_SIGNING_RESTRICTED = re.compile(
    r"^Le directeur\s+(?P<director1>[^,.;]+?)\s+et\s+"
    r"(?P<director2>[^,.;]+?)\s+continuent à signer collectivement à deux,\s*"
    r"désormais avec un administrateur\.\s*"
    r"(?P<proxy>[^,.;]+),\s*maintenant à\s+(?P<place>[^,.;]+),\s*continue à "
    r"engager la société par sa procuration collective à deux,\s*désormais avec "
    r"un administ(?:r)?ateur\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_ELECTED_VICE_PRESIDENT = re.compile(
    r"^(?P<name>[^,.;]+),\s*membre du conseil de fondation,\s*est élu "
    r"vice-président\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_SECOND_PRESIDENT_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<member>[^,.;]+?)\s+et\s+"
    r"(?P<president>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*président,\s*"
    r"lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_REMARK_REMOVED_AFTER_CONVERSION = re.compile(
    r"^\[Im Zuge der Umwandlung der Genossenschaft in eine Aktiengesellschaft "
    r"ging die Streichung der Bemerkung betreffend persönliche Haftbarkeit der "
    r"Genossenschafter vergessen\]\s*\[gestrichen:\s*Persönliche Haftbarkeit "
    r"der Genossenschafter ausgeschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_DEPUTY_DIRECTOR_SAME_ORIGIN_PLACE = re.compile(
    r"^Signature collective à deux est conférée à\s+(?P<name>[^,.;]+),\s*"
    r"du et au\s+(?P<place>[^,.;]+),\s*directeur adjoint\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CHANGED_TO_COLLECTIVE_PROXY = re.compile(
    r"^(?P<name>[^,.;]+),\s*continue de signer collectivement à deux,\s*"
    r"mais désormais par procuration\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_RESUMED_BY_COURT = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+den am\s+"
    r"(?P<opened_date>\d{2}\.\d{2}\.\d{4})\s+eröffneten und mit Entscheid "
    r"vom\s+(?P<suspended_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven "
    r"eingestellten Konkurs wieder aufgenommen\.\s*"
    r"\[bisher:\s*Das Konkursverfahren ist mit Entscheid des\s+"
    r"(?P<previous_authority>.+?)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven eingestellt "
    r"worden\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_TWO_SIGNING_FIVE_UNSIGNED = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<president_origin>[^,.;]+),\s*à\s+"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{1,3}),\s*"
    r"président,\s*(?P<secretary>[^,.;]+),\s*secrétaire,\s*tous deux\s+"
    r"(?P<member1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*(?P<member2>[^,;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<member3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3}),\s*(?P<member4>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+),\s*(?P<country4>[A-Z]{1,3}),\s*et\s*"
    r"(?P<member5>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin5>[^,.;]+),\s*à\s+(?P<place5>[^,.;]+),\s*"
    r"(?P<country5>[A-Z]{1,3}),\s*tous cinq sans signature\.?$",
    re.I | re.UNICODE,
)
_IT_SHARE_TRANSFER_RESTRICTION_CANCELLED = re.compile(
    r"^Nuova limitazione della trasferibilità:\s*\[La limitazione della "
    r"trasferibilità delle azioni nominative è cancellata\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTRATION_NOTICE_SHORT_CANTON = re.compile(
    r"^Eintragung der Zweigniederlassung von\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+im Handelsregister\s+"
    r"(?P<registry_canton>[^()]+?)\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+(?P<notice_id>\d+)\)\.?$",
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
    day, month, year = raw.lower().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").split(".", 1)[0])


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


def extract_parser141_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 141."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_TWO_MANAGERS_REMOVED_SHARES_TO_EXISTING_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_removed_shares_to_existing_manager.v1"
        buyer = match.group("buyer").strip()
        common = {"currency": "CHF", "counterparty": buyer}
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"removed{index}"),
                role="associé-gérant",
                extra={
                    **common,
                    "action": "removed_and_shares_transferred",
                    "powers_revoked": True,
                    "shares_transferred": _count(match.group(f"count{index}")),
                    "share_nominal": match.group(f"nominal{index}"),
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, role="associé-gérant",
            extra={
                "action": "shares_received",
                "previous_roles": ["président", "directeur"],
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "capital": match.group("capital"),
                "currency": "CHF",
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_introduced.v2",
            {
                "kind": "authorized_capital_clause", "action": "introduced",
                "date": _iso_date(match.group("date")), "basis": "statutes",
            },
        ))

    match = _FR_SOLE_ADMINISTRATOR_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_liquidator.v1",
            match.group("name"), role="administrateur unique et liquidateur",
            extra={"action": "appointed_liquidator", "previous_role": "administrateur unique"},
        ))

    match = _FR_MANAGER_PRESIDENT_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_president_transfer_to_new_manager.v2"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        seller_role = f"{match.group('seller_role')} et {match.group('president_role')}"
        buyer_role = f"{match.group('buyer_role').split()[-1]} et {match.group('manager_role')}"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role=seller_role,
                extra={
                    "action": "appointed_president_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("before")) - transferred,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role=buyer_role,
                extra={
                    "action": "appointed_manager_and_shares_received",
                    "counterparty": seller, "heimat": match.group("origin").strip(),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.authorized_capital_clause_introduced.v2",
            {
                "kind": "authorized_capital_clause", "action": "introduced",
                "date": _french_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_DIRECTORS_AND_PROXY_SIGNING_RESTRICTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.directors_and_proxy_signing_restricted.v1"
        for group in ("director1", "director2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(group),
                role="directeur", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "signing_restriction_changed",
                    "signing_continues": True, "must_sign_with_role": "administrateur",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("proxy"),
            place=match.group("place"), signing="Kollektivprokura zu zweien",
            extra={
                "action": "domicile_and_signing_restriction_changed",
                "signing_continues": True, "must_sign_with_role": "administrateur",
            },
        ))

    match = _FR_FOUNDATION_MEMBER_ELECTED_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_elected_vice_president.v1",
            match.group("name"), role="membre du conseil de fondation et vice-président",
            extra={"action": "appointed_vice_president", "previous_role": "membre du conseil de fondation"},
        ))

    match = _FR_ADMINISTRATION_PAIR_SECOND_PRESIDENT_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_second_president_collective.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="administrateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        ])

    match = _DE_COOPERATIVE_LIABILITY_REMARK_REMOVED_AFTER_CONVERSION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.cooperative_liability_remark_removed.v1",
            {
                "kind": "member_personal_liability_remark", "action": "removed",
                "previous_value": "personal_liability_excluded",
                "reason": "conversion_to_stock_corporation",
            },
        ))

    match = _FR_SIGNING_GRANTED_DEPUTY_DIRECTOR_SAME_ORIGIN_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.signing_granted_deputy_director.v1",
            match.group("name"), place=match.group("place"), role="directeur adjoint",
            signing="Kollektivunterschrift zu zweien",
            extra={"action": "appointed", "heimat": match.group("place").strip()},
        ))

    match = _FR_SIGNING_CHANGED_TO_COLLECTIVE_PROXY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_changed_to_collective_proxy.v1",
            match.group("name"), signing="Kollektivprokura zu zweien",
            extra={
                "action": "signing_type_changed",
                "previous_signing": "Kollektivunterschrift zu zweien",
            },
        ))

    match = _DE_BANKRUPTCY_RESUMED_BY_COURT.search(leftover)
    if match and match.group("suspended_date") == match.group("previous_date"):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_resumed_by_court.v1",
            {
                "kind": "bankruptcy_proceedings_resumed",
                "action": "resumed", "authority": match.group("authority").strip(),
                "previous_authority": match.group("previous_authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_opened_date": _iso_date(match.group("opened_date")),
                "previous_status": "suspended_lack_of_assets",
                "previous_decision_date": _iso_date(match.group("suspended_date")),
            },
        ))

    match = _FR_ADMINISTRATION_TWO_SIGNING_FIVE_UNSIGNED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_two_signing_five_unsigned.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"),
                role="président du conseil d'administration",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed", "heimat": match.group("president_origin").strip(),
                    "country": match.group("president_country").upper(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire du conseil d'administration",
                signing="Einzelunterschrift", extra={"action": "appointed"},
            ),
        ])
        for index in range(1, 6):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"member{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                extra={
                    "action": "appointed", "heimat": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").upper(),
                    "without_signature": True,
                },
            ))

    match = _IT_SHARE_TRANSFER_RESTRICTION_CANCELLED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "it.text.share_transfer_restriction_cancelled.v1",
            {
                "kind": "share_transfer_restricted", "action": "removed",
                "share_kind": "azioni nominative",
            },
        ))

    match = _DE_BRANCH_REGISTRATION_NOTICE_SHORT_CANTON.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_registration_notice_short_canton.v1",
            {
                "action": "registered", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "registry_canton": match.group("registry_canton").strip(),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
