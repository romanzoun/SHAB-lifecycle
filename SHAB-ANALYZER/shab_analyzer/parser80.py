from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_THREE_NEW_FOUNDATION_MEMBERS = re.compile(
    r"^Nouveaux membres du conseil de fondation\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s*(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s*(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*de et à\s*(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_PARTICIPATION_CAPITAL = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eine bedingte Erhöhung des Partizipationskapitals gemäss näherer Umschreibung "
    r"in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée comme suit\.\s*"
    r"Administration:\s*(?P<name>[^,.;]+),\s*de et à\s*(?P<place>[^,.;]+),\s*"
    r"(?P<role>administrateur unique)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS_COLLECTIVE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s*(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s*(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s*(?P<place3>[^,.;]+),\s*sont membres du conseil d['’]administration\s*"
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_MUTATION_PREVIOUS_TEXT_COMPLETED = re.compile(
    r"^Bei der Mutation von\s+(?P<previous_name>.+?),\s*von\s+(?P<origin>[^,.;]+),\s*"
    r"in\s+(?P<previous_place>[^,.;]+),\s*(?P<previous_role>[^,.;]+?)\s+mit\s+"
    r"(?P<previous_sign>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?),\s*"
    r"wurde bei der Mutation in\s+(?P<name>.+?),\s*von\s+(?P<new_origin>[^,.;]+),\s*"
    r"in\s+(?P<place>[^,.;]+),\s*(?P<role>[^,.;]+?)\s+mit\s+"
    r"(?P<sign>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?),\s*"
    r"der Bishertext\s*\((?P<omitted>.+)\)\s*nicht vollständig wiedergegeben\.?$",
    re.I | re.UNICODE,
)
_FR_SUPERVISORY_AUDIT_WAIVER_REVOKED_WRITTEN_DATE = re.compile(
    r"^L['’]autorité de surveillance a révoqué la dispense d['’]organe de révision "
    r"octroyée à la Fondation par décision du\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_LEGACY_BRANCH_REMOVED_NO_UID = re.compile(
    r"^Zweigniederlassung neu:\s*\[Folgende Zweigniederlassung ist aufgehoben worden:\]\s*"
    r"\[bisher:\s*(?P<place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLER_SPLIT_SHARE_TRANSFERS = re.compile(
    r"^(?P<seller1>[^,.;]+),?\s*cède\s+(?P<seller1_transferred>[\d']+) de ses\s+"
    r"(?P<seller1_before>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<org_received1>[\d']+) parts de CHF\s+(?P<org_nominal1>[\d'.]+) à\s+"
    r"(?P<org1>.+?)\s*\((?P<org_uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<org_place1>[^,.;]+),\s*nouvelle associée,\s*titulaire de\s+"
    r"(?P<org_count1>[\d']+) parts de CHF\s+(?P<org_count_nominal1>[\d'.]+),\s*et par\s+"
    r"(?P<buyer1_received>[\d']+) parts de CHF\s+(?P<buyer1_nominal>[\d'.]+) à\s+"
    r"(?P<buyer1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<buyer1_origin>[^,.;]+),\s*"
    r"à\s*(?P<buyer1_place>[^,.;]+),\s*nouvel associé-gérant titulaire de\s+"
    r"(?P<buyer1_count>[\d']+) parts de CHF\s+(?P<buyer1_count_nominal>[\d'.]+)\.\s*"
    r"(?P<seller2>[^,.;]+)\s+cède\s+(?P<seller2_transferred>[\d']+) de ses\s+"
    r"(?P<seller2_before>[\d']+) parts de CHF\s+(?P<nominal2>[\d'.]+),\s*par\s+"
    r"(?P<org_received2>[\d']+) parts de CHF\s+(?P<org_nominal2>[\d'.]+) à\s+"
    r"(?P<org2>.+?)\s*\((?P<org_uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*désormais "
    r"titulaire de\s+(?P<org_count2>[\d']+) parts de CHF\s+(?P<org_count_nominal2>[\d'.]+),\s*"
    r"et par\s+(?P<buyer2_received>[\d']+) parts de CHF\s+(?P<buyer2_nominal>[\d'.]+) à\s+"
    r"(?P<buyer2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<buyer2_origin>[^,.;]+),\s*"
    r"à\s*(?P<buyer2_place>[^,.;]+),\s*avec\s+(?P<buyer2_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer2_count_nominal>[\d'.]+),\s*nouvelle associée-gérante avec signature "
    r"individuelle,\s*titulaire de\s+(?P<buyer2_final_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer2_final_nominal>[\d'.]+)\.\s*(?P=seller1) a maintenant\s+"
    r"(?P<seller1_count>[\d']+) parts de CHF\s+(?P<seller1_final_nominal>[\d'.]+) et\s+"
    r"(?P=seller2)\s+(?P<seller2_count>[\d']+) parts de CHF\s+"
    r"(?P<seller2_final_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_SIGNING_CHANGED = re.compile(
    r"^Les membres du comité\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*maintenant à\s*(?P<place2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*maintenant à\s*(?P<place3>[^,.;]+),\s*et\s*"
    r"(?P<name4>[^,.;]+),\s*maintenant à\s*(?P<place4>[^,.;]+),\s*"
    r"signent désormais collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^Nouveau membre du comité sans signature:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_SUSPENDED_DATE_MIDDLE = re.compile(
    r"^(?P<authority>La présidente du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé le\s+(?P<date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+l['’]effet suspensif de la faillite\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_THIRD_PARTY_CAPITAL_UID_BEFORE_PLACE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Fremdkapital von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NAME_AND_ARTICLE_176_REMOVED = re.compile(
    r"^Raison sociale:\s*(?P<name>.+?)\.\s*Radiation de la mention relative à\s+"
    r"l['’](?P<article>art\.\s*176 ORC)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_LOCATION = re.compile(
    r"^\[bisher:\s*(?P<previous_place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PREVIOUS_DOMICILE_CORRECTED = re.compile(
    r"^(?P<name>.+?),\s*von\s+(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>[^,.;]+),\s*mit\s+(?P<sign>Einzelunterschrift|"
    r"Kollektivunterschrift(?: zu zweien)?)\s*\[bisher:\s*in\s+"
    r"(?P<incorrect_previous_place>[^\]]+)\]\s*richtig sollte der Eintrag lauten:\s*"
    r"(?P<correct_name>.+?),\s*von\s+(?P<correct_origin>[^,.;]+),\s*in\s+"
    r"(?P<correct_place>[^,.;]+),\s*(?P<correct_role>[^,.;]+),\s*mit\s+"
    r"(?P<correct_sign>Einzelunterschrift|Kollektivunterschrift(?: zu zweien)?)\s*"
    r"\[bisher:\s*in\s+(?P<previous_place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_INTENDED_ASSET_ACQUISITION_PROVISION_REMOVED = re.compile(
    r"^Suppression de la disposition relative à la reprise de biens envisagée "
    r"suite à l['’]abrogation de l['’](?P<legal_basis>art\.\s*628 aCO)\.?$",
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


def _french_date(raw: str) -> str:
    day, month, year = raw.strip().lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser80_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 80."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_THREE_NEW_FOUNDATION_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_new_foundation_members.v1"
        for index in (1, 2, 3):
            extra = {"action": "appointed"}
            origin = match.groupdict().get(f"origin{index}")
            if origin:
                extra["heimat"] = origin.strip()
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra=extra,
                )
            )

    match = _DE_CONDITIONAL_PARTICIPATION_CAPITAL.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.conditional_participation_capital.v1",
                {
                    "kind": "conditional_participation_capital",
                    "action": "increase_authorized",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_SOLE_ADMINISTRATOR_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.sole_administrator_name_corrected.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"), signing="Einzelunterschrift",
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _FR_THREE_BOARD_MEMBERS_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_board_members_collective.v1"
        for index in (1, 2, 3):
            extra = {"action": "appointed", "heimat": match.group(f"origin{index}").strip()}
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"name{index}"),
                    place=match.group(f"place{index}"),
                    role="membre du conseil d'administration",
                    signing="Kollektivunterschrift zu zweien", extra=extra,
                )
            )

    match = _DE_PERSON_MUTATION_PREVIOUS_TEXT_COMPLETED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.mutation_previous_text_completed.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role"), signing=match.group("sign"),
                extra={
                    "action": "mutation_completed",
                    "heimat": match.group("new_origin").strip(),
                    "previous_place": match.group("previous_place").strip(),
                    "previous_role": match.group("previous_role").strip(),
                    "previous_signing": match.group("previous_sign"),
                    "omitted_previous_text": match.group("omitted").strip(),
                },
            )
        )

    match = _FR_SUPERVISORY_AUDIT_WAIVER_REVOKED_WRITTEN_DATE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed",
                "fr.text.supervisory_audit_waiver_revoked_written_date.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "revoked",
                    "decision_date": _french_date(match.group("date")),
                    "authority": "supervisory_authority",
                },
            )
        )

    match = _DE_LEGACY_BRANCH_REMOVED_NO_UID.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.legacy_branch_removed_no_uid.v1",
                {"action": "removed", "place": match.group("place").strip()},
            )
        )

    match = _FR_TWO_SELLER_SPLIT_SHARE_TRANSFERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_seller_split_share_transfers.v1"
        seller1 = match.group("seller1").strip()
        seller2 = match.group("seller2").strip()
        org_name = match.group("org2").strip()
        associate_uid = match.group("org_uid2")
        buyer1 = match.group("buyer1").strip()
        buyer2 = match.group("buyer2").strip()
        for seller, before_group, transferred_group, count_group, counterparties in (
            (seller1, "seller1_before", "seller1_transferred", "seller1_count", [org_name, buyer1]),
            (seller2, "seller2_before", "seller2_transferred", "seller2_count", [org_name, buyer2]),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparties": counterparties,
                        "shares_before": _count(match.group(before_group)),
                        "shares_transferred": _count(match.group(transferred_group)),
                        "shares_count": _count(match.group(count_group)),
                        "shares_nominal": match.group("nominal"),
                    },
                )
            )
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, org_name,
                    place=match.group("org_place1"), uid=associate_uid, role="associée",
                    extra={
                        "action": "shares_received",
                        "shares_received": _count(match.group("org_received1"))
                        + _count(match.group("org_received2")),
                        "shares_count": _count(match.group("org_count2")),
                        "shares_nominal": match.group("org_count_nominal2"),
                        "transferors": [seller1, seller2],
                        "new_associate": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer1, place=match.group("buyer1_place"),
                    role="associé-gérant", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("buyer1_origin").strip(),
                        "counterparty": seller1,
                        "shares_received": _count(match.group("buyer1_received")),
                        "shares_count": _count(match.group("buyer1_count")),
                        "shares_nominal": match.group("buyer1_count_nominal"),
                        "new_associate": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer2, place=match.group("buyer2_place"),
                    role="associée-gérante", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("buyer2_origin").strip(),
                        "counterparty": seller2,
                        "shares_received": _count(match.group("buyer2_received")),
                        "shares_count": _count(match.group("buyer2_final_count")),
                        "shares_nominal": match.group("buyer2_final_nominal"),
                        "new_associate": True,
                    },
                ),
            ]
        )

    match = _FR_COMMITTEE_MEMBERS_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.committee_members_signing_changed.v1"
        for index in (1, 2, 3, 4):
            place = match.groupdict().get(f"place{index}")
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(f"name{index}"),
                    place=place, role="membre du comité",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "signing_changed",
                        **({"domicile_changed": True} if place else {}),
                    },
                )
            )

    match = _FR_NEW_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.new_committee_member_without_signature.v1",
                match.group("name"), place=match.group("place"), role="membre du comité",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "without_signature": True,
                },
            )
        )

    match = _FR_BANKRUPTCY_SUSPENDED_DATE_MIDDLE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.bankruptcy_effect_suspended_female_president.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "decision_date": _french_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _DE_ASSET_TRANSFER_THIRD_PARTY_CAPITAL_UID_BEFORE_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred",
                "de.text.asset_transfer_third_party_capital_uid_before_place.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "liabilities_kind": "third_party_capital",
                    "currency": "CHF",
                    "recipient": match.group("recipient").strip(),
                    "recipient_uid": match.group("uid"),
                    "recipient_place": match.group("place").strip(),
                    "consideration": f"CHF {match.group('consideration')}",
                    "consideration_kind": "cash",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _FR_NAME_AND_ARTICLE_176_REMOVED.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "organization_changed", "fr.text.company_name_confirmed_short.v1",
                    {
                        "kind": "company_name_confirmation",
                        "name": match.group("name").strip(),
                        "changed": False,
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", "fr.text.article_176_mention_removed_short.v1",
                    {
                        "kind": "legal_mention",
                        "action": "removed",
                        "legal_basis": re.sub(r"\s+", " ", match.group("article")),
                    },
                ),
            ]
        )

    match = _DE_BRANCH_PREVIOUS_LOCATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.branch_previous_location.v1",
                {
                    "action": "moved",
                    "previous_place": match.group("previous_place").strip(),
                    "branch_uid": match.group("uid"),
                },
            )
        )

    match = _DE_PERSON_PREVIOUS_DOMICILE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.previous_domicile_correction.v1",
                match.group("correct_name"), place=match.group("correct_place"),
                role=match.group("correct_role"), signing=match.group("correct_sign"),
                extra={
                    "action": "publication_corrected",
                    "heimat": match.group("correct_origin").strip(),
                    "previous_place": match.group("previous_place").strip(),
                    "incorrectly_reported_previous_place": match.group(
                        "incorrect_previous_place"
                    ).strip(),
                },
            )
        )

    match = _FR_INTENDED_ASSET_ACQUISITION_PROVISION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed",
                "fr.text.intended_asset_acquisition_provision_removed.v1",
                {
                    "kind": "intended_asset_acquisition_provision",
                    "action": "removed",
                    "reason": "legal_basis_repealed",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
