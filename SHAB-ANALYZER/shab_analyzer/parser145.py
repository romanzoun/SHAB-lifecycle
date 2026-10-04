from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_COMPANY_REINSTATED_PUBLIC_REGISTER_CLEANUP = re.compile(
    r"^(?P<company>.+? in Liquidation),\s*in\s+(?P<seat>[^,.;]+),\s*"
    r"(?P<legacy_id>[A-Z]{2,4}-[\d.]+),\s*(?P<legal_form>[^()]+?)\s*"
    r"\(SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*S\.(?P<page>\d+)\)\.\s*"
    r"Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte Gesellschaft "
    r"wird auf Grund des Urteils des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zwecks Bereinigung eines "
    r"öffentlichen Registers wieder in das Handelsregister eingetragen und besteht "
    r"entsprechend den früheren Eintragungen weiter\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_ASSOCIATE_TRANSFER_TO_TWO = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<incorrect_id>\d+)\)\s+dont le numéro "
    r"d['’]immatricualtion exacte est\s+(?P<seller_id>[A-Z]\s?\d+)\s+a cédé\s+"
    r"(?P<count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+à\s+"
    r"(?P<buyer1>.+?)\s*\((?P<buyer1_id>[^)]+)\),\s*à\s+"
    r"(?P<buyer1_place>[^,.;]+),\s*(?P<buyer1_country>[A-Z]{2,3}),\s*"
    r"nouvelle associée pour\s+(?P<buyer1_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer1_nominal>[\d'.]+)\s+et\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s+à\s+(?P<buyer2>.+?)\s*"
    r"\((?P<buyer2_id>[^)]+)\),\s*à\s+(?P<buyer2_place>[^,.;]+),\s*"
    r"(?P<buyer2_country>[A-Z]{2,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer2_count>[\d']+)\s+parts de CHF\s+(?P<buyer2_nominal>[\d'.]+);\s*"
    r"par conséquent\s+(?P=seller)\s*\((?P<seller_id_again>[^)]+)\),\s*à\s+"
    r"(?P<seller_place>[^,.;]+),\s*(?P<seller_country>[A-Z]{2,3}),\s*est "
    r"maintenant associée pour\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_SEAT_CHANGED = re.compile(
    r"^L['’]associée\s+(?P<name>.+?)\s+a maintenant son siège à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3})\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_ADMINISTRATORS_AND_DOCTOR_TITLE = re.compile(
    r"^(?:Nouveaux administrateurs(?: avec signature collective à deux)?\s*:\s*)?"
    r"(?P<name1>[^,;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<role1>vice-président),\s*et\s+"
    r"(?P<name2>[^,;]+),\s*des\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^.]+)\.\s*(?P<name3>[^,.;]+),\s*"
    r"(?P<role3>administrateur),\s*porte le titre de\s+(?P<title>docteur)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_INDIVIDUAL_PROXIES_MIXED_ORIGINS = re.compile(
    r"^Procuration individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s*\((?P<country1>[^)]+)\),\s*"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*tous deux d['’](?P<origin12>[^,.;]+),\s*"
    r"et\s+(?P<name3>[^,.;]+),\s*d['’](?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+)\s*\((?P<country3>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_NAME_SUFFIX = re.compile(r"^in Liquidation\.?$", re.I | re.UNICODE)
_FR_ASSOCIATE_MANAGER_ROLE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est\s+(?P<role>associé-gérant)\s*"
    r"\(et non\s+(?P<previous_role>associé-gérant président),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_MOVED_AND_PRESIDENT = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*maintenant domicilié(?:e)? à\s+"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<role2>président),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_HEAD_OFFICE_EMPTY_PROVISIONS = re.compile(
    r"^Sede principale a:\s*(?P<head_office>[^.]+)\.\s*"
    r"Nuove disposizioni per la succursale:\s*$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_DELETION_REINSTATED = re.compile(
    r"^Berichtigung des im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrags Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4}):\s*"
    r"Die irrtümlich mit Tagesregistereintrag vom\s+"
    r"(?P<deletion_entry_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte Gesellschaft "
    r"wird zum Zwecke der Liquidation wieder in das Handelsregister eingetragen\.\s*"
    r"Die Publikation im SHAB Nr\.\s*(?P<revoked_issue>\d+)\s+vom\s+"
    r"(?P<revoked_notice_date>\d{2}\.\d{2}\.\d{4})\s+wird widerrufen\.\s*"
    r"\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_EFFECTIVE_DATE_CORRECTED = re.compile(
    r"^Par décision rectifiée du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"prononcée par\s+(?P<authority>.+?),\s*cette société a été déclarée en "
    r"faillite avec effet le\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<effective_time>\d{1,2}h\d{2})\s+et dissoute d['’]office\s*"
    r"\[précédemment:\s*Par décision du\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+prononcée par\s+"
    r"(?P<previous_authority>.+?),\s*cette société a été déclarée en faillite "
    r"avec effet le\s+(?P<previous_effective_date>\d{2}\.\d{2}\.\d{4})\s+à\s+"
    r"(?P<previous_effective_time>\d{1,2}h\d{2})\s+et dissoute d['’]office\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDITION_TAIL_WITH_PREVIOUS_REGISTER = re.compile(
    r"^\[bisher:\s*(?P<previous_place>[^()\]]+?)\s*\(HR\s+"
    r"(?P<previous_register>[A-Za-zÀ-ÿ]+)\)\]\.\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_NAME_CORRECTED_WITH_TRANSLATIONS = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la raison de "
    r"commerce exacte est:\s*(?P<name>[^()]+?)\s*\((?P<german>[^()]+)\)\s*"
    r"\((?P<english>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_TRANSFER_CATEGORIZED_SHARES = re.compile(
    r"^(?P<seller1>.+?)\s*\((?P<seller1_id>[^)]+)\)\s+et\s+"
    r"(?P<seller2>.+?)\s*\((?P<seller2_id>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"qui ne sont plus associées,\s*cèdent leurs\s+(?P<ordinary>[\d']+)\s+"
    r"parts ordinaires de CHF\s+(?P<ordinary_nominal>[\d'.]+),\s*respectivement\s+"
    r"(?P<class_a>[\d']+)\s+parts de catégorie A de CHF\s+"
    r"(?P<class_a_nominal>[\d'.]+)\s+et\s+(?P<class_c>[\d']+)\s+parts de "
    r"catégorie C de CHF\s+(?P<class_c_nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_class_a>[\d']+)\s+parts de catégorie A de CHF\s+"
    r"(?P<buyer_class_a_nominal>[\d'.]+),\s*(?P<buyer_class_c>[\d']+)\s+parts "
    r"de catégorie C de CHF\s+(?P<buyer_class_c_nominal>[\d'.]+)\s+et\s+"
    r"(?P<buyer_ordinary>[\d']+)\s+parts ordinaires de CHF\s+"
    r"(?P<buyer_ordinary_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_THREE_MANAGERS = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+par\s+"
    r"(?P<each>[\d']+)\s+parts chacune à\s+(?P<buyer1>.+?),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^()]+?)\s*"
    r"\((?P<country1>[^)]+)\),\s*nouvelle associée-gérante\s+"
    r"(?P<buyer2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^()]+?)\s*\((?P<country2>[^)]+)\),\s*"
    r"(?P<buyer3>[^,.;]+),\s*de\s+(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^()]+?)\s*\((?P<country3>[^)]+)\),\s*toutes deux nouvelles "
    r"associés-gérantes avec signature collective à deux,\s*chacune avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"est nommé(?:e)?\s+(?P<role>administratrice?)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser145_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 145."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_COMPANY_REINSTATED_PUBLIC_REGISTER_CLEANUP.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_public_register_cleanup.v1",
            {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "public_register_cleanup",
                "company_name": match.group("company").strip(),
                "seat": match.group("seat").strip(),
                "legacy_id": match.group("legacy_id"),
                "legal_form": match.group("legal_form").strip(),
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "notice_issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_page": match.group("page"),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _FR_FOREIGN_ASSOCIATE_TRANSFER_TO_TWO.search(leftover)
    if match and len({
        match.group("nominal1"), match.group("buyer1_nominal"),
        match.group("nominal2"), match.group("buyer2_nominal"),
        match.group("remaining_nominal"),
    }) == 1 and match.group("seller_id").replace(" ", "") == match.group(
        "seller_id_again"
    ).replace(" ", ""):
        consume(match)
        rule_id = "fr.persons.foreign_associate_transfer_to_two.v1"
        seller = match.group("seller").strip()
        buyer1 = match.group("buyer1").strip()
        buyer2 = match.group("buyer2").strip()
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("remaining_nominal"), "currency": "CHF"}
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, place=match.group("seller_place"),
            role="associée",
            extra={
                **common, "action": "shares_transferred",
                "registry_id": match.group("seller_id").replace(" ", ""),
                "incorrect_registry_id": match.group("incorrect_id"),
                "registry_id_corrected": True,
                "country": match.group("seller_country"),
                "shares_before": remaining + count1 + count2,
                "shares_transferred": count1 + count2,
                "shares_count": remaining,
                "counterparties": [buyer1, buyer2],
            },
        ))
        for index, buyer, transferred in ((1, buyer1, count1), (2, buyer2, count2)):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer,
                place=match.group(f"buyer{index}_place"), role="associée",
                extra={
                    **common, "action": "shares_received", "new_associate": True,
                    "registry_id": match.group(f"buyer{index}_id").strip(),
                    "country": match.group(f"buyer{index}_country"),
                    "counterparty": seller, "shares_received": transferred,
                    "shares_count": _count(match.group(f"buyer{index}_count")),
                },
            ))

    match = _FR_ASSOCIATE_ORGANIZATION_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_organization_seat_changed.v1",
            match.group("name"), place=match.group("place"), role="associée",
            extra={
                "action": "seat_changed", "organization": True,
                "country": match.group("country"),
            },
        ))

    match = _FR_TWO_NEW_ADMINISTRATORS_AND_DOCTOR_TITLE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_new_administrators_and_doctor_title.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role=match.group("role1"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("origin1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("origin2").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name3"),
                role=match.group("role3"),
                extra={"action": "title_added", "title": match.group("title").lower()},
            ),
        ])

    match = _FR_THREE_INDIVIDUAL_PROXIES_MIXED_ORIGINS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_individual_proxies_mixed_origins.v1"
        for index in (1, 2, 3):
            origin = match.group("origin12") if index < 3 else match.group("origin3")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Einzelprokura",
                extra={
                    "action": "proxy_granted", "heimat": origin.strip(),
                    "country": match.group(f"country{index}").strip(),
                },
            ))

    match = _DE_LIQUIDATION_NAME_SUFFIX.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.liquidation_name_suffix.v1",
            {"kind": "dissolution", "action": "liquidation_name_added"},
        ))

    match = _FR_ASSOCIATE_MANAGER_ROLE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_role_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").lower(),
                "entry": match.group("entry"),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ADMINISTRATION_PAIR_MOVED_AND_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_pair_moved_and_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="administrateur",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_changed", "domicile_changed": True,
                    "country": match.group("country1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role=match.group("role2"),
                signing="Einzelunterschrift",
                extra={"action": "appointed", "heimat": match.group("origin2").strip()},
            ),
        ])

    match = _IT_BRANCH_HEAD_OFFICE_EMPTY_PROVISIONS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_head_office_empty_provisions.v1",
            {
                "scope": "head_office", "action": "head_office_recorded",
                "head_office": match.group("head_office").strip(),
                "branch_provisions_heading_present": True,
                "branch_provisions_omitted_in_source": True,
            },
        ))

    match = _DE_ERRONEOUS_DELETION_REINSTATED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.erroneous_deletion_reinstated.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_issue": match.group("issue"),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "registration_reinstated", "action": "reinstated",
                    "reason": "erroneous_deletion", "purpose": "liquidation",
                    "deletion_entry_date": _iso_date(match.group("deletion_entry_date")),
                    "previous": match.group("previous").strip(), **reference,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {
                    "kind": "erroneous_deletion", "action": "notice_revoked",
                    "revoked_notice_issue": match.group("revoked_issue"),
                    "revoked_notice_date": _iso_date(match.group("revoked_notice_date")),
                    **reference,
                },
            ),
        ])

    match = _FR_BANKRUPTCY_EFFECTIVE_DATE_CORRECTED.search(leftover)
    if match and match.group("authority") == match.group("previous_authority"):
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_effective_date_corrected.v1",
            {
                "kind": "bankruptcy", "action": "effective_date_corrected",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time"),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_effective_date": _iso_date(match.group("previous_effective_date")),
                "previous_effective_time": match.group("previous_effective_time"),
                "dissolved_by_law": True,
            },
        ))

    match = _DE_BRANCH_ADDITION_TAIL_WITH_PREVIOUS_REGISTER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_addition_tail_with_previous_register.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_branch_place": match.group("previous_place").strip(),
                "previous_register_canton": match.group("previous_register").upper(),
            },
        ))

    match = _FR_COMPANY_NAME_CORRECTED_WITH_TRANSLATIONS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_name_corrected_with_translations.v1",
            {
                "action": "corrected", "name": match.group("name").strip(),
                "translations": {
                    "de": match.group("german").strip(),
                    "en": match.group("english").strip(),
                },
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_ASSOCIATES_TRANSFER_CATEGORIZED_SHARES.search(leftover)
    if match and (
        match.group("ordinary") == match.group("buyer_ordinary")
        and match.group("class_a") == match.group("buyer_class_a")
        and match.group("class_c") == match.group("buyer_class_c")
        and match.group("ordinary_nominal") == match.group("buyer_ordinary_nominal")
        and match.group("class_a_nominal") == match.group("buyer_class_a_nominal")
        and match.group("class_c_nominal") == match.group("buyer_class_c_nominal")
    ):
        consume(match)
        rule_id = "fr.persons.two_associates_transfer_categorized_shares.v1"
        buyer = match.group("buyer").strip()
        ordinary = {
            "count": _count(match.group("ordinary")), "category": "ordinary",
            "nominal": match.group("ordinary_nominal"), "currency": "CHF",
        }
        class_a = {
            "count": _count(match.group("class_a")), "category": "A",
            "nominal": match.group("class_a_nominal"), "currency": "CHF",
        }
        class_c = {
            "count": _count(match.group("class_c")), "category": "C",
            "nominal": match.group("class_c_nominal"), "currency": "CHF",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("seller1"), role="associée",
                extra={
                    "action": "shares_transferred_and_removed",
                    "registry_id": match.group("seller1_id").strip(),
                    "counterparty": buyer, "shares": [ordinary],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("seller2"),
                uid=match.group("seller2_id"), role="associée",
                extra={
                    "action": "shares_transferred_and_removed",
                    "counterparty": buyer, "shares": [class_a, class_c],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                uid=match.group("buyer_uid"), role="associée",
                extra={
                    "action": "shares_received", "new_associate": True,
                    "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip()
                    ],
                    "shares": [class_a, class_c, ordinary],
                },
            ),
        ])

    match = _FR_ASSOCIATE_TRANSFER_TO_THREE_MANAGERS.search(leftover)
    if match and (
        _count(match.group("transferred")) == 3 * _count(match.group("each"))
        and match.group("nominal") == match.group("buyer_nominal")
        and match.group("each") == match.group("buyer_count")
    ):
        consume(match)
        rule_id = "fr.persons.associate_transfer_to_three_managers.v1"
        seller = match.group("seller").strip()
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        each = _count(match.group("each"))
        common = {
            "shares_received": each, "shares_count": each,
            "share_nominal": match.group("nominal"), "currency": "CHF",
            "new_associate": True,
        }
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, seller, role="associé",
            extra={
                "action": "shares_transferred", "shares_before": before,
                "shares_transferred": transferred, "shares_count": before - transferred,
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "counterparties": [match.group(f"buyer{i}").strip() for i in (1, 2, 3)],
            },
        ))
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associée-gérante",
                signing=(
                    "Einzelunterschrift" if index == 1
                    else "Kollektivunterschrift zu zweien"
                ),
                extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "heimat": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}").strip(),
                },
            ))

    match = _FR_PROXY_REVOKED_APPOINTED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_administrator.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Einzelunterschrift",
            extra={
                "action": "appointed", "previous_role": "fondée de procuration",
                "proxy_revoked": True,
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip()
