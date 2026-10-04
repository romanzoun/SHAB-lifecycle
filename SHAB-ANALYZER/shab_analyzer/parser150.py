from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_FOUNDATION_ASSET_TRANSFER_BY_ORDER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Verfügung der "
    r"Aufsichtsbehörde vom\s+(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_TRANSFER_RESTRICTION_REMOVED = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"ne sont désormais plus restreintes quant à la transmissibilité\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_DOMICILE_CORRECTED_WITH_REFERENCE = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\):\s*(?P<name>[^,.;]+),\s*(?P<role>.+?),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien|Einzelunterschrift),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\(und nicht in\s+"
    r"(?P<previous_place>[^()]+?)\s*\((?P<previous_country>[A-Z]{2,3})\)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_INDIVIDUAL_SIGNING = re.compile(
    r"^Signature individuelle est conférée à\s+(?P<name1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^(),;]+)\s*\((?P<country1>[^()]+)\),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^(),;]+)\s*"
    r"\((?P<country2>[^()]+)\),\s*tous deux des\s+"
    r"(?P<nationality>[^,.;]+),\s*(?P<role>gérants)\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE = re.compile(
    r"^Der Eintrag Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+ist wie folgt berichtigt:\s*"
    r"(?P<surname>[^()]+?)\s*\(und nicht\s+(?P<previous_surname>[^)]+)\)\s+"
    r"(?P<given_names>[^,.;]+),\s*(?P<role>.+?),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien|Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_DE_ORGANIZATION_ENTRY_REMOVED_ART_95_DETAIL = re.compile(
    r"^Organisation neu:\s*\[Löschung aufgrund geänderter "
    r"Eintragungsvorschriften gemäss\s+"
    r"(?P<legal_basis>Art\.\s*95 Abs\.\s*1 lit\.\s*h HRegV)\]\.?$",
    re.I | re.UNICODE,
)
_FR_QUALIFIED_FACT_EXECUTED_SHARE_ACQUISITION = re.compile(
    r"^Nouveaux faits qualifiés:\s*Lors de la modification des statuts du\s+"
    r"(?P<statutes_date>\d{2}\.\d{2}\.\d{4}),\s*la société a complété les "
    r"statuts avec un nouvel article d['’]une reprise de biens envisagée,\s*"
    r"qui lors de la fondation de la société était déjà envisagée et entre-temps "
    r"par contrat du\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+exécutée:\s*"
    r"Reprise de\s+(?P<count>[\d']+)\s+parts sociales à CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de la société\s+(?P<company>.+?),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"pour le prix de CHF\s+(?P<price>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_PARTIAL_SHARE_TRANSFER_WITH_SIGNING = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associée,\s*a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé,\s*"
    r"lequel signe collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROXY_MODIFIED = re.compile(
    r"^Procuration individuelle a été conférée à\s+(?P<name>[^,.;]+);\s*"
    r"sa procuration est modifiée en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED = re.compile(
    r"^L['’]assemblée générale a modifié une clause statutaire relative à une "
    r"augmentation conditionnelle du capital\s*\(selon décision du\s+"
    r"(?P<original_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\)\s+par décision du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_COMPLEX_ASSOCIATE_SHARE_TRANSFERS = re.compile(
    r"^L['’]associé-gérant et président\s+(?P<seller1>[^,.;]+)\s+cède\s+"
    r"(?P<seller1_transferred>[\d']+)\s+de ses\s+(?P<seller1_before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+),\s*par\s+"
    r"(?P<buyer_received1>[\d']+)\s+à l['’]associé-gérant\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_after1>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal1>[\d'.]+),\s*"
    r"et par\s+(?P<new_received>[\d']+)\s+à\s+(?P<new_buyer>[^,.;]+),\s*de\s+"
    r"(?P<new_origin>[^,.;]+),\s*à\s+(?P<new_place>[^,.;]+),\s*"
    r"nouvel associé sans signature\.\s*(?P=seller1)\s+reste titulaire de\s+"
    r"(?P<seller1_remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller1_nominal>[\d'.]+)\.\s*L['’]associé-gérant\s+"
    r"(?P<seller2>[^,.;]+)\s+cède\s+(?P<seller2_transferred>[\d']+)\s+de ses\s+"
    r"(?P<seller2_before>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller2_nominal>[\d'.]+)\s+à l['’]associé-gérant\s+(?P=buyer)\s+"
    r"désormais titulaire de\s+(?P<buyer_after2>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal2>[\d'.]+)\.\s*(?P=seller2)\s+reste titulaire de\s+"
    r"(?P<seller2_remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller2_remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_DELETED_FROM_REGISTER = re.compile(
    r"^Das Einzelunternehmen wird im Handelsregister gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"^(?:Nouveaux faits qualifiés:\s*)?Transfert de patrimoine:\s*selon contrat "
    r"du\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des "
    r"actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+)\s+à la société\s+[\"“]"
    r"(?P<recipient>.+?)[\"”],\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*"
    r"CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_SUPPLEMENT_WITH_REFERENCE = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*n°\s+"
    r"(?P<notice_id>\d+)\)\s+est complétée en ce sens que le capital est de "
    r"CHF\s+(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_EXACT_NAME_CORRECTED = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+est rectifiée dans le sens que le nom précis de "
    r"l['’](?P<role>administrateur vice-président) est\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_APPOINTED_QUOTED = re.compile(
    r"^Organe de révision:\s*[\"“](?P<name>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
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
    day, month, year = raw.casefold().split()
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


def extract_parser150_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 150."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_FOUNDATION_ASSET_TRANSFER_BY_ORDER.search(leftover)
    if match:
        consume(match)
        consideration = match.group("consideration").strip()
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.foundation_asset_transfer_by_order.v1",
            {
                "source_kind": "foundation",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "supervisory_order_date": _iso_date(match.group("order_date")),
                "currency": "CHF", "assets": match.group("assets"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": consideration,
                "gratuitous": consideration.casefold() == "keine",
            },
        ))

    match = _FR_REGISTERED_SHARE_TRANSFER_RESTRICTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_transfer_restriction_removed.v1",
            {
                "kind": "share_transfer_restriction", "action": "removed",
                "registered": True, "entire_share_capital": True,
                "currency": "CHF", "share_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
            },
        ))

    match = _DE_PERSON_DOMICILE_CORRECTED_WITH_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.domicile_corrected_with_reference.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role").strip(), signing=match.group("signing"),
            extra={
                "action": "domicile_corrected",
                "previous_place": match.group("previous_place").strip(),
                "previous_country": match.group("previous_country").upper(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_TWO_MANAGERS_INDIVIDUAL_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_individual_signing_abroad.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role=match.group("role").lower(),
                signing="Einzelunterschrift",
                extra={
                    "action": "signing_granted",
                    "country": match.group(f"country{index}").strip(),
                    "nationality": match.group("nationality").strip(),
                },
            ))

    match = _DE_PERSON_SURNAME_CORRECTED_WITH_REFERENCE.search(leftover)
    if match:
        consume(match)
        given_names = match.group("given_names").strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.surname_corrected_with_reference.v1",
            f"{match.group('surname').strip()} {given_names}",
            role=match.group("role").strip(), signing=match.group("signing"),
            extra={
                "action": "name_corrected",
                "previous_name": f"{match.group('previous_surname').strip()} {given_names}",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_ORGANIZATION_ENTRY_REMOVED_ART_95_DETAIL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.organization_entry_removed_art_95_detail.v1",
            {
                "action": "entry_removed", "reason": "registration_rules_changed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _FR_QUALIFIED_FACT_EXECUTED_SHARE_ACQUISITION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.qualified_fact_executed_share_acquisition.v1",
            {
                "kind": "business_acquisition", "action": "executed",
                "previously_intended_at_foundation": True,
                "statutes_date": _iso_date(match.group("statutes_date")),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "asset_kind": "social_shares", "share_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "company": match.group("company").strip(),
                "company_place": match.group("place").strip(),
                "company_uid": match.group("uid"), "price": match.group("price"),
            },
        ))

    match = _FR_ASSOCIATE_PARTIAL_SHARE_TRANSFER_WITH_SIGNING.search(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if transferred <= before:
            consume(match)
            rule_id = "fr.persons.associate_partial_share_transfer_with_signing.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée",
                    extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "previous_shares_count": before, "shares_transferred": transferred,
                        "shares_count": before - transferred,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé", signing="Kollektivunterschrift zu zweien",
                    extra={
                        **common, "action": "appointed_and_shares_received",
                        "counterparty": seller, "shares_received": transferred,
                        "shares_count": transferred,
                        "origin": match.group("origin").strip(),
                    },
                ),
            ])

    match = _FR_INDIVIDUAL_PROXY_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_proxy_modified.v1",
            match.group("name"), signing="Einzelprokura",
            extra={"action": "proxy_changed", "proxy_granted": True},
        ))

    match = _FR_CONDITIONAL_CAPITAL_CLAUSE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.conditional_capital_clause_changed_dates.v1",
            {
                "kind": "conditional_capital_clause", "action": "changed",
                "original_decision_date": _french_date(match.group("original_date")),
                "decision_date": _french_date(match.group("decision_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_COMPLEX_ASSOCIATE_SHARE_TRANSFERS.search(leftover)
    if match:
        numeric = {
            key: _count(match.group(key))
            for key in (
                "seller1_transferred", "seller1_before", "buyer_received1",
                "buyer_after1", "new_received", "seller1_remaining",
                "seller2_transferred", "seller2_before", "buyer_after2",
                "seller2_remaining",
            )
        }
        nominals = {
            match.group(key)
            for key in (
                "nominal", "buyer_nominal1", "seller1_nominal", "seller2_nominal",
                "buyer_nominal2", "seller2_remaining_nominal",
            )
        }
        valid = (
            len(nominals) == 1
            and numeric["seller1_transferred"]
            == numeric["buyer_received1"] + numeric["new_received"]
            and numeric["seller1_before"] - numeric["seller1_transferred"]
            == numeric["seller1_remaining"]
            and numeric["seller2_before"] - numeric["seller2_transferred"]
            == numeric["seller2_remaining"]
            and numeric["buyer_after1"] + numeric["seller2_transferred"]
            == numeric["buyer_after2"]
        )
        if valid:
            consume(match)
            rule_id = "fr.persons.complex_associate_share_transfers.v1"
            seller1 = match.group("seller1").strip()
            seller2 = match.group("seller2").strip()
            buyer = match.group("buyer").strip()
            new_buyer = match.group("new_buyer").strip()
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller1,
                    role="associé-gérant président",
                    extra={
                        **common, "action": "shares_transferred",
                        "previous_shares_count": numeric["seller1_before"],
                        "shares_transferred": numeric["seller1_transferred"],
                        "shares_count": numeric["seller1_remaining"],
                        "transfers": [
                            {"to": buyer, "count": numeric["buyer_received1"]},
                            {"to": new_buyer, "count": numeric["new_received"]},
                        ],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé-gérant",
                    extra={
                        **common, "action": "shares_received",
                        "shares_received": (
                            numeric["buyer_received1"] + numeric["seller2_transferred"]
                        ),
                        "shares_count": numeric["buyer_after2"],
                        "transfers": [
                            {"from": seller1, "count": numeric["buyer_received1"]},
                            {"from": seller2, "count": numeric["seller2_transferred"]},
                        ],
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, new_buyer, place=match.group("new_place"),
                    role="associé", extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("new_origin").strip(),
                        "shares_received": numeric["new_received"],
                        "shares_count": numeric["new_received"], "without_signature": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller2, role="associé-gérant",
                    extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "previous_shares_count": numeric["seller2_before"],
                        "shares_transferred": numeric["seller2_transferred"],
                        "shares_count": numeric["seller2_remaining"],
                    },
                ),
            ])

    match = _DE_SOLE_PROPRIETOR_DELETED_FROM_REGISTER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.sole_proprietor_deleted_from_register.v1",
            {"scope": "sole_proprietor", "action": "deleted_from_register"},
        ))

    match = _FR_ASSET_TRANSFER_WITH_INVENTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_with_inventory.v1",
            {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "currency": "CHF", "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
            },
        ))

    match = _FR_CAPITAL_SUPPLEMENT_WITH_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.capital_supplement_with_reference.v1",
            {
                "kind": "share_capital", "action": "supplemented",
                "currency": "CHF", "total": match.group("capital"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_ADMINISTRATOR_EXACT_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_exact_name_corrected.v1",
            match.group("name"), role=match.group("role").lower(),
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_AUDITOR_APPOINTED_QUOTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_appointed_quoted.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="organe de révision", extra={"action": "appointed"},
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
