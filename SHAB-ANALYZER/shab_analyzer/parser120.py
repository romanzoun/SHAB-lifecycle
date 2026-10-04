from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SINGLE_NOTICE_DELETION_BLOCKED = re.compile(
    r"^Auf die durch das Handelsregisteramt gestützt auf\s+"
    r"(?P<legal_basis>Art\.\s*934 Abs\.\s*2 OR sowie Art\.\s*152 Abs\.\s*1 HRegV)\s+"
    r"veranlasste und im SHAB mit Meldungsnummer\s+(?P<issue>[A-Z]{2}\d{2}-\d+)\s+"
    r"publizierten Aufforderung haben sich keine weiteren Betroffenen gemeldet\.\s*"
    r"Das amtliche Verfahren zur Löschung der Rechtseinheit ist damit abgeschlossen\.\s*"
    r"Sie kann mangels Zustimmungen der Eidgenössischen Steuerverwaltung und des "
    r"kantonalen Steueramtes jedoch noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation conditionnelle du capital par décision du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_POST_CONVERSION_CAPITAL_COVERED = re.compile(
    r"^Im Nachgang zur Umwandlung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurden Zuschüsse in der Höhe von CHF\s+(?P<amount>[\d'.]+)\s+geleistet,\s*"
    r"wodurch das Kapital nun voll gedeckt ist\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR = re.compile(
    r"^L['’]associée-gérante\s+(?P<name>[^,.;]+)\s+est élue liquidatrice\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED = re.compile(
    r"^La commandite de l['’]associé commanditaire de\s+(?P<name>[^,.;]+)\s+"
    r"a été diminuée de CHF\s+(?P<from>[\d'.]+)\s+à CHF\s+(?P<to>[\d'.]+)\.\s*"
    r"Nouvelle associée commanditaire\s*:\s*(?P<organization>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"avec une commandite de CHF\s+(?P<contribution>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),?\s*cède\s+"
    r"(?P<transferred>[\d']+) parts de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé sans signature\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+) parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_EXISTING_MOVED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé\s+(?P<buyer>[^,.;]+),\s*"
    r"maintenant à\s+(?P<place>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+) parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_FOUR_INDIVIDUAL_SIGNATORIES = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommée\s+présidente,\s*"
    r"(?P<name2>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*et\s+(?P<name4>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin4>[^,.;]+),\s*"
    r"à\s+(?P<place4>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_INDIVIDUAL_SIGNATORIES = re.compile(
    r"^Nouveaux gérants:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{2,3}),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’]\s*)"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s*"
    r"(?P<name3>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’]\s*)"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la raison de "
    r"commerce exacte de l['’]associée est\s+(?P<name>.+?)\s*"
    r"\(et non\s+(?P<previous>.+?),\s*comme publié\)\s+et que son siège est à\s+"
    r"(?P<seat>[^()]+?)\s*\((?P<country>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BRANCHES_ADDED = re.compile(
    r"^Nouvelles succursales:\s*(?P<place1>[^(),.;]+?)\s*"
    r"\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+et\s+"
    r"(?P<place2>[^(),.;]+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_SHARE_CLASSES_CONSOLIDATED = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<name>.+?)\s*"
    r"\((?P<registry_id>[^)]+)\),\s*Gesellschafterin,\s*"
    r"(?P<class_a_count>[\d']+) privilegierte Stammanteile Klasse A zu CHF\s+"
    r"(?P<class_a_nominal>[\d'.]+)\s+und\s+(?P<class_b_count>[\d']+) ordentliche "
    r"Stammanteile Klasse B zu CHF\s+(?P<class_b_nominal>[\d'.]+),\s*neu "
    r"Gesellschafterin,\s*(?P<count>[\d']+) Stammanteile zu CHF\s+"
    r"(?P<nominal>[\d'.]+)\.\s*Statuten geändert am\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le nom exact de "
    r"la directrice est\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS = re.compile(
    r"^Nouveaux membres du conseil de fondation\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:(?:du|de la|des|de)\s+|d['’]\s*)(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_CERTIFICATE_NOMINAL_REDUCTION = re.compile(
    r"^und CHF\s+(?P<new2>[\d.]+)\s*\[bisher:\s*CHF\s+(?P<old1>[\d.-]+)\s+"
    r"und CHF\s+(?P<old2>[\d.-]+)\]\.\s*Mit Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wird der Nennwert der Anteilscheine zu CHF\s+"
    r"(?P<before1>[\d.]+)\s+bzw\.\s+zu CHF\s+(?P<before2>[\d.]+)\s+im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*735 i\.V\.m\.\s*Art\.\s*874 Abs\.\s*2 OR)\s+"
    r"zur Beseitigung einer Unterbilanz auf CHF\s+(?P<new1>[\d.]+)\s+bzw\.\s+"
    r"CHF\s+(?P<after2>[\d.]+)\s+herabgesetzt\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_SIGNING_WITH_EXCLUSIONS_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux,\s*sauf avec\s+(?P<excluded1>[^,.;]+),\s*"
    r"(?P<excluded2>[^,.;]+),\s*(?P<excluded3>[^,.;]+)\s+et\s+"
    r"(?P<excluded4>[^,.;]+),\s*a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"(?P<role>directeur|directrice);\s*sa procuration est radiée\.?$",
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
    day, month, year = raw.lower().replace("1er", "1").split()
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


def extract_parser120_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 120."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_SINGLE_NOTICE_DELETION_BLOCKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.single_notice_deletion_blocked.v1",
            {
                "kind": "deletion_blocked",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "procedure_completed": True,
                "issues": [match.group("issue")],
                "affected_parties_responded": False,
                "tax_authority_consent_missing": True,
                "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
            },
        ))

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_INTRODUCED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_introduced.v2",
            {
                "kind": "conditional_capital_clause", "action": "introduced",
                "date": _french_date(match.group("date")), "details_in_statutes": True,
            },
        ))

    match = _DE_POST_CONVERSION_CAPITAL_COVERED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.post_conversion_capital_covered.v1",
            {
                "kind": "capital_coverage_after_conversion", "action": "contribution_made",
                "conversion_date": _iso_date(match.group("date")),
                "contribution": match.group("amount"), "currency": "CHF",
                "fully_covered": True,
            },
        ))

    match = _FR_ASSOCIATE_MANAGER_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_appointed_liquidator.v1",
            match.group("name"), role="associée-gérante et liquidatrice",
            signing="Einzelunterschrift",
            extra={"action": "appointed_liquidator", "previous_role": "associée-gérante"},
        ))

    match = _FR_LIMITED_PARTNER_REDUCED_AND_ORGANIZATION_ADDED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.limited_partner_reduced_and_organization_added.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="associé commanditaire",
                extra={
                    "action": "limited_partnership_contribution_changed",
                    "previous_limited_partnership_contribution": match.group("from"),
                    "limited_partnership_contribution": match.group("to"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("organization"),
                place=match.group("place"), role="associée commanditaire",
                uid=match.group("uid"),
                extra={
                    "action": "appointed", "uid": match.group("uid"),
                    "limited_partnership_contribution": match.group("contribution"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_MANAGER_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_to_new_unsigned_associate.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred",
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé", signing="ohne Zeichnungsberechtigung",
                extra={
                    **common, "action": "appointed", "heimat": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")),
                },
            ),
        ])

    match = _FR_MANAGER_TRANSFER_TO_EXISTING_MOVED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_to_existing_moved_associate.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller"), role="associé-gérant",
                extra={
                    "action": "shares_transferred",
                    "previous_shares_count": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé",
                extra={
                    "action": "shares_received_and_moved", "domicile_changed": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_BOARD_FOUR_INDIVIDUAL_SIGNATORIES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_four_first_appointed_president.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("name1"),
            role="administratrice présidente", signing="Einzelunterschrift",
            extra={"action": "appointed_president"},
        ))
        for index in (2, 3, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="administrateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group(f"origin{index}").strip()},
            ))

    match = _FR_THREE_MANAGERS_INDIVIDUAL_SIGNATORIES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers_individual_signatories.v1"
        for index in (1, 2, 3):
            extra = {"action": "appointed", "origin": match.group(f"origin{index}").strip()}
            if index == 1:
                extra["country"] = match.group("country1")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérant",
                signing="Einzelunterschrift", extra=extra,
            ))

    match = _FR_ASSOCIATE_ORGANIZATION_NAME_AND_SEAT_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_organization_name_seat_corrected.v1",
            match.group("name"), place=match.group("seat"), role="associée",
            extra={
                "action": "name_and_seat_corrected", "previous_name": match.group("previous").strip(),
                "country": match.group("country").strip(), "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_BRANCHES_ADDED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.two_branches_added.v1"
        for index in (1, 2):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id,
                {
                    "action": "added", "place": match.group(f"place{index}").strip(),
                    "branch_uid": match.group(f"uid{index}"),
                },
            ))

    match = _DE_ORGANIZATION_SHARE_CLASSES_CONSOLIDATED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.organization_share_classes_consolidated.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), role="Gesellschafterin",
                extra={
                    "action": "share_classes_consolidated",
                    "registry_id": match.group("registry_id"),
                    "previous_share_classes": [
                        {
                            "class": "A", "kind": "privilegierte Stammanteile",
                            "count": _count(match.group("class_a_count")),
                            "nominal": match.group("class_a_nominal"),
                        },
                        {
                            "class": "B", "kind": "ordentliche Stammanteile",
                            "count": _count(match.group("class_b_count")),
                            "nominal": match.group("class_b_nominal"),
                        },
                    ],
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {"action": "changed", "date": _iso_date(match.group("date"))},
            ),
        ])

    match = _FR_DIRECTOR_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected_notice.v1",
            match.group("name"), role="directrice",
            extra={
                "action": "name_corrected", "previous_name": match.group("previous").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_FOUNDATION_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_foundation_members_with_collective_signing.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group(f"origin{index}").strip()},
            ))

    match = _DE_COOPERATIVE_CERTIFICATE_NOMINAL_REDUCTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.cooperative_certificate_nominal_reduction.v1",
            {
                "kind": "cooperative_share_certificate_nominal_reduction",
                "action": "reduced", "date": _iso_date(match.group("date")),
                "currency": "CHF", "from_nominals": [match.group("before1"), match.group("before2")],
                "to_nominals": [match.group("new1"), match.group("after2")],
                "reason": "elimination_of_balance_sheet_deficit",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_DIRECTOR_SIGNING_WITH_EXCLUSIONS_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_signing_exclusions_proxy_revoked.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_changed", "previous_authority": "procuration",
                "previous_authority_revoked": True,
                "excluded_with": [match.group(f"excluded{index}").strip() for index in range(1, 5)],
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
