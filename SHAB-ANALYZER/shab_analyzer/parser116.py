from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_BOARD_THREE_WITH_SIGNING_EXCLUSIONS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*(?P<role1>présidente),\s*"
    r"(?:avec signature collective à deux,\s*)?pas avec\s+(?P<excluded1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<role2>secrétaire),\s*"
    r"avec signature collective à deux,\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*avec signature collective à deux,\s*"
    r"pas avec\s+(?P<excluded3>[^,.;]+),\s*"
    r"sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE = re.compile(
    r"^Augmentation conditionnelle du capital-participation fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<rights_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Nouveau capital-participation:\s*CHF\s+(?P<total>[\d'.]+),\s*"
    r"entièrement libéré,\s*divisé en\s+(?P<count>[\d']+)\s+"
    r"bons nominatifs de CHF\s+(?P<nominal>[\d'.]+)\.\s*"
    r"Le conseil d['’]administration a modifié une clause statutaire relative à "
    r"une augmentation conditionnelle du capital-participation\s*"
    r"\(selon décision relative à l['’]octroi de droits de l['’]assemblée "
    r"générale du\s+(?P<clause_rights_date>\d{2}\.\d{2}\.\d{4})\),\s*"
    r"par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"pour le détail cf\. statuts\.?$",
    re.I | re.UNICODE,
)
_FR_PURPOSE_AND_STATUTES_NON_PUBLIC_CONNECTOR = re.compile(
    r"^But et$", re.I | re.UNICODE
)
_FR_MANAGER_TRANSFER_PRESIDENCY_AND_NAME_CORRECTION = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé-gérant,\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant(?:\s+avec signature individuelle\.)?\s*(?P=seller)\s+reste "
    r"titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+);\s*(?:il\s+)?est élu président\.\s*"
    r"Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les nom et "
    r"prénom d['’]un associé-gérant ont été inversés,\s*et qu['’]\s*"
    r"(?:il\s+)?se nomme\s+(?P<corrected_name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^,()]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_DIVISION_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le capital-actions "
    r"de CHF\s+(?P<total>[\d'.]+),\s*entièrement libéré,\s*est divisé en\s+"
    r"(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),?\s*(?:avec restrictions quant à la "
    r"transmissibilité selon statuts\s*)?\(et non en\s+"
    r"(?P<previous_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_WITH_COUNTRY = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{2,3}),\s*"
    r"(?P<role2>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_PENSION_ASSET_TRANSFER_INVESTMENT_CLAIMS = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss "
    r"Vertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<claims>[\d'.]+)\s+Ansprüche zu CHF\s+"
    r"(?P<claim_nominal>[\d'.]+)\s+der Anlagegruppe\s+"
    r"(?P<investment_group>.+?)\s+des übernehmenden Rechtsträgers\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCHES_TAKEN_OVER_AFTER_MERGER = re.compile(
    r"^Complément à l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_ref>[\d/]+)\):\s*Reprise des deux succursales de la société\s+"
    r"(?P<absorbed_name>.+?)\s*\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"absorbée par contrat de fusion du\s+(?P<merger_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"soit la succursale de\s+(?P<branch1_place>[^()]+?)\s*"
    r"\((?P<branch1_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+et de\s+"
    r"(?P<branch2_place>[^()]+?)\s*"
    r"\((?P<branch2_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_SHARE_SHIFT = re.compile(
    r"^L['’]associé-gérant et président\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par "
    r"suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+(?:,\s*usage\s+[^,.;]+)?),\s*"
    r"associée-gérante désormais pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_SIGNATORIES_EXCLUDED_AMONG_THEMSELVES = re.compile(
    r"^Signature collective à deux,\s*sauf entre eux,\s*a été conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name4>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,.;]+),\s*"
    r"à\s+(?P<place4>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^Le gérant\s+(?P<seller>[^,.;]+)\s+a cédé ses\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_AND_DIRECTOR_SIGNING_CHANGES = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*nommé(?:e)?\s+"
    r"(?P<role1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*tous deux\s*"
    r"(?:avec signature collective à deux)?\s*;\s*les pouvoirs de\s+"
    r"(?P<changed_name>[^,.;]+)\s+sont modifiés en ce sens\.\s*"
    r"(?P<director>[^,.;]+),\s*nommé(?:e)?\s+(?P<director_role>[^,.;]+),\s*"
    r"signe désormais collectivement à deux sans autre restriction;\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_VICE_PRESIDENT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*est membre "
    r"vice-président du comité,\s*sans signature\s*\(et non pas\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_NAME_RESIDUE = re.compile(r"^ch GmbH$", re.I | re.UNICODE)
_FR_COMPANY_REINSTATED_BANKRUPTCY_REOPENED = re.compile(
    r"^La société est réinscrite au registre du commerce conformément à la "
    r"décision du\s+(?P<authority>.+?)\s+du\s+(?P<decision_date>\d{1,2}\s+"
    r"(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|"
    r"novembre|décembre)\s+\d{4})\s+prononçant la réouverture de la faillite le\s+"
    r"(?P<bankruptcy_date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|"
    r"juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}),\s*"
    r"à\s+(?P<hour>\d{1,2})h(?P<minute>\d{2})\.?$",
    re.I | re.UNICODE,
)
_DE_CHANGED_AND_NEW_PERSON = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<changed_name>[^,.;]+),\s*"
    r"(?P<changed_role>[^,.;]+),\s*(?P<previous_signing>[^,.;]+),\s*neu\s+"
    r"(?P<changed_signing>[^,.;]+)\.\s*Neu eingetragene Person:\s*"
    r"(?P<new_name>[^,.;]+),\s*(?P<nationality>[^,.;]+),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<country>[A-Z]{2,3})\),\s*"
    r"(?P<new_signing>[^,.;]+)\.?$",
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
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    lowered = raw.lower()
    if "individ" in lowered or "einzel" in lowered:
        return "Einzelunterschrift"
    if "collect" in lowered or "kollektiv" in lowered:
        return "Kollektivunterschrift zu zweien"
    return raw.strip()


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


def extract_parser116_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 116."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_BOARD_THREE_WITH_SIGNING_EXCLUSIONS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_three_with_signing_exclusions.v1"
        people = (
            ("name1", "origin1", "place1", match.group("role1"), "excluded1"),
            ("name2", "origin2", "place2", match.group("role2"), None),
            ("name3", "origin3", "place3", "membre du conseil d'administration", "excluded3"),
        )
        for name_key, origin_key, place_key, role, excluded_key in people:
            extra = {"action": "appointed", "heimat": match.group(origin_key).strip()}
            if excluded_key:
                extra["not_with"] = match.group(excluded_key).strip()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key), role=role,
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_participation_capital_and_clause.v1",
            {
                "kind": "conditional_participation_capital_increase",
                "rights_decision_date": _iso_date(match.group("rights_date")),
                "total": match.group("total"), "currency": "CHF",
                "fully_paid": True,
                "participation_certificates_count": _count(match.group("count")),
                "participation_certificate_nominal": match.group("nominal"),
                "registered": True,
                "clause_action": "modified_by_board",
                "clause_decision_date": _iso_date(match.group("decision_date")),
                "clause_rights_decision_date": _iso_date(match.group("clause_rights_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_PURPOSE_AND_STATUTES_NON_PUBLIC_CONNECTOR.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "fr.text.purpose_and_statutes_non_public_change.v1",
            {
                "action": "changed", "details_published": False,
                "paired_with_statutes_change": True,
            },
        ))

    match = _FR_MANAGER_TRANSFER_PRESIDENCY_AND_NAME_CORRECTION.search(leftover)
    if match:
        consume(match)
        transfer_rule = "fr.persons.manager_transfer_presidency.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_transferred": _count(match.group("transferred")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", transfer_rule, seller,
                role="associé-gérant et président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer, "shares_before": _count(match.group("before")),
                    "shares_count": _count(match.group("seller_count")), **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", transfer_rule, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.associate_manager_name_order_corrected.v1",
                match.group("corrected_name"), role="associé-gérant",
                extra={
                    "action": "name_corrected",
                    "previous_name": match.group("previous_name").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_ref": match.group("notice_ref"),
                },
            ),
        ])

    match = _FR_SHARE_CAPITAL_DIVISION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_division_corrected.v1",
            {
                "kind": "share_structure", "action": "corrected",
                "total": match.group("total"), "fully_paid": True,
                "share_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": "nominatives", "currency": "CHF",
                "previous_published_share_count": _count(match.group("previous_count")),
                "previous_published_share_nominal": match.group("previous_nominal"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATION_PAIR_WITH_COUNTRY.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_individual_country.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").strip(), signing="Einzelunterschrift",
                extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role=match.group("role2").strip(),
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed", "heimat": match.group("origin2").strip(),
                    "country": match.group("country2"),
                },
            ),
        ])

    match = _DE_PENSION_ASSET_TRANSFER_INVESTMENT_CLAIMS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.pension_asset_transfer_investment_claims.v1",
            {
                "source": match.group("source").strip(),
                "source_kind": "pension_fund", "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "currency": "CHF",
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "investment_group_claims",
                "claims": match.group("claims"),
                "claim_nominal": match.group("claim_nominal"),
                "investment_group": match.group("investment_group").strip(),
            },
        ))

    match = _FR_BRANCHES_TAKEN_OVER_AFTER_MERGER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.branches_taken_over_after_merger.v1",
            {
                "kind": "branch_takeover", "action": "supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "merger_date": _iso_date(match.group("merger_date")),
                "branches": [
                    {"place": match.group("branch1_place").strip(), "uid": match.group("branch1_uid")},
                    {"place": match.group("branch2_place").strip(), "uid": match.group("branch2_uid")},
                ],
            },
        ))

    match = _FR_ASSOCIATE_MANAGERS_SHARE_SHIFT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_managers_share_shift.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant et président",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associée-gérante",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_FOUR_SIGNATORIES_EXCLUDED_AMONG_THEMSELVES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_signatories_excluded_among_themselves.v1"
        names = [match.group(f"name{index}").strip() for index in range(1, 5)]
        for index, name in enumerate(names, start=1):
            extra = {
                "action": "granted", "heimat": match.group(f"origin{index}").strip(),
                "not_with": [other for other in names if other != name],
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, name,
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _FR_MANAGER_TRANSFER_TO_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="gérant",
                extra={
                    "action": "all_shares_transferred", "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": 0, "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", uid=match.group("buyer_uid"),
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "uid": match.group("buyer_uid"), "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_ADMINISTRATION_AND_DIRECTOR_SIGNING_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_and_director_signing_changes.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1").strip(), signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "powers_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                role=match.group("director_role").strip(),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_and_signing_changed",
                    "signing_restrictions_removed": True,
                    "previous_signing": "procuration", "previous_signing_revoked": True,
                },
            ),
        ])

    match = _FR_COMMITTEE_VICE_PRESIDENT_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.committee_vice_president_corrected.v1",
            match.group("name"), place=match.group("place"),
            role="membre vice-président du comité",
            extra={
                "action": "person_corrected", "without_signature": True,
                "heimat": match.group("origin").strip(), "country": match.group("country"),
                "previous_published_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_COMPANY_NAME_RESIDUE.search(leftover)
    if match:
        # The generic company-name extractor consumed "Tomtek." at the dot in
        # the embedded domain-style name.  This bounded suffix is publication
        # header residue, not another business event.
        consume(match)

    match = _FR_COMPANY_REINSTATED_BANKRUPTCY_REOPENED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.company_reinstated_bankruptcy_reopened.v1",
            {
                "kind": "bankruptcy_reopened", "action": "registry_reinstated",
                "authority": match.group("authority").strip(),
                "decision_date": _french_date(match.group("decision_date")),
                "bankruptcy_reopened_date": _french_date(match.group("bankruptcy_date")),
                "bankruptcy_reopened_time": (
                    f"{int(match.group('hour')):02d}:{int(match.group('minute')):02d}"
                ),
                "registry_reinstated": True,
            },
        ))

    match = _DE_CHANGED_AND_NEW_PERSON.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.changed_and_new_person.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("changed_name"),
                role=match.group("changed_role").strip(),
                signing=_signing(match.group("changed_signing")),
                extra={
                    "action": "changed",
                    "previous_signing": _signing(match.group("previous_signing")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_name"),
                place=match.group("place"), signing=_signing(match.group("new_signing")),
                extra={
                    "action": "appointed", "nationality": match.group("nationality").strip(),
                    "country": match.group("country"),
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
