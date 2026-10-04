from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+?)\s+est nommé\s+"
    r"(?P<role>gérant-président)"
    r"(?P<individual_signing>\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_FR_UNPUBLISHED_STATUTES_DATE_FRAGMENT = re.compile(
    r"^le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_ASSET_TRANSFER_INVENTORY_SUPERVISORY_ORDER = re.compile(
    r"^Vermögensübertragung:\s*Die Stiftung überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+mit Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+und Verfügung der "
    r"Aufsichtsbehörde vom\s+(?P<order_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*"
    r"\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont directeurs\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]|No)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]administrateur unique porte le nom\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_ACQUIRER_OWNS_ALL_QUOTAS = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?)"
    r"(?:\s*\((?P<uid_before>CHE-\d{3}\.\d{3}\.\d{3})\))?,\s*in\s+"
    r"(?P<absorbed_place>[^(),]+?)"
    r"(?:\s*\((?P<uid_after>CHE-\d{3}\.\d{3}\.\d{3})\))?,\s*"
    r"secondo il contratto di fusione del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s*,\s*che presenta attivi "
    r"per CHF\s+(?P<assets>[\d'.]+),?\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La società assuntrice detiene tutte le\s+"
    r"(?P<interests>quote(?: sociali)?)\s+della società trasferente,\s*per "
    r"cui la fusione avviene senza aumento di capitale e senza attribuzione "
    r"di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_PERSON_FULL_NAME_AND_ORIGIN_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]|No)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<previous_name>[^,.;]+?)\s+porte en réalité le nom\s+"
    r"(?P<name>[^,.;]+),\s*et est originaire de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY_DECISION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<agreement_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\s+et "
    r"selon décision de l['’]autorité de surveillance du\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"la fondation a transféré des actifs de CHF\s+(?P<assets>[\d'.]+)\s+"
    r"et des passifs envers les tiers de CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"à\s+(?P<recipient>.+?),\s*à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_SIGNATORIES_WITH_ADMINISTRATOR = re.compile(
    r"^Signature collective à deux avec un administrateur est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*à\s+(?P<place2>[^(),.;]+)\s*"
    r"\((?P<country2>[^)]+)\),\s*(?P<name3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^(),.;]+)\s*\((?P<country3>[^)]+)\),\s*"
    r"les trois de\s+(?P<shared_origin>[^,.;]+),\s*et\s+"
    r"(?P<name4>[^,.;]+),\s*d['’](?P<origin4>[^,.;]+),\s*à\s+"
    r"(?P<place4>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_FOR_COMPLETE_LIQUIDATION_WITH_ADDRESS = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte\s+"
    r"(?P<legal_form>Aktiengesellschaft)\s+wird auf Grund des Entscheides des\s+"
    r"(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+zum Zwecke der vollständigen "
    r"Liquidation gemäss\s+(?P<legal_basis>Art\.\s*164 HRegV)\s+wieder in "
    r"das Handelsregister eingetragen und besteht entsprechend den früheren "
    r"Eintragungen weiter\.\s*Liquidationsadresse:\s*(?P<organization>.+?),\s*"
    r"(?P<contact>[^,.;]+),\s*(?P<street>[^,.;]+),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_SHAREHOLDINGS_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]|No)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que,\s*"
    r"par suite de cession,\s*l['’]associée\s+(?P<name1>[^,.;]+)\s+est devenue "
    r"associée pour\s+(?P<count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+);\s*l['’]associé\s+(?P<name2>[^,.;]+)\s+reste "
    r"associé pour\s+(?P<count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal2>[\d'.]+)\s*\(et non pas pour\s+"
    r"(?P<previous_count2>[\d']+)\s+parts de CHF\s+"
    r"(?P<previous_nominal2>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_APPOINTED_DIRECTORS_PROXY_REVOKED = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont nommés "
    r"directeurs(?P<individual_signing>\s+avec signature individuelle)?\s*;\s*"
    r"leur procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_NOMINATIVE_SHARES_CORRECTED = re.compile(
    r"^Nouvelles actions:\s*(?P<count>[\d']+)\s+actions\s+"
    r"(?P<kind>nominatives)\s+de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"(?P<restriction>avec restriction de transmissibilité selon statuts)\s*"
    r"\[non:\s*(?P<previous_count>[\d']+)\s+actions\s+"
    r"(?P<previous_kind>nominatives)\s+de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+"
    r"(?P<previous_restriction>avec restriction de transmissibilité selon statuts)"
    r"\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFERS_TO_NEW_UNSIGNED_ASSOCIATE_WITH_DOMICILE = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associée-gérante,\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"d['’](?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"nouvelle associée avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*sans signature\.\s*"
    r"(?P=seller),\s*désormais à\s+(?P<seller_place>[^,.;]+),\s*reste "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_AND_NEW_COMPANY_NAME = re.compile(
    r"^Die Gesellschaft ist laut Beschluss der Generalversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*Neue Firma:\s*"
    r"(?P<name>.+? in Liquidation)\."
    r"(?:\s*(?P<remaining>Eingetragene Person geändert:.+))?$",
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


def extract_parser236_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 236."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_president.v1",
            match.group("name"), role=match.group("role"),
            signing=("Einzelunterschrift" if match.group("individual_signing") else None),
            extra={"action": "appointed"},
        )], ""

    match = _FR_UNPUBLISHED_STATUTES_DATE_FRAGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.unpublished_statutes_date_fragment.v1", {
                "date": _iso_date(match.group("date")),
                "publication_relevant_change": False,
            },
        )], ""

    match = _DE_FOUNDATION_ASSET_TRANSFER_INVENTORY_SUPERVISORY_ORDER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.foundation_asset_transfer_inventory_supervisory_order.v1", {
                "source_kind": "Stiftung",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "supervisory_order_date": _iso_date(match.group("order_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "Fremdkapital",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "none",
            },
        )], ""

    match = _FR_ENTRY_SUPPLEMENTED_TWO_DIRECTORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.entry_supplemented_two_directors.v1"
        common = {
            "action": "appointed", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "correction_kind": "supplement",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="directeur", extra=common,
            )
            for index in (1, 2)
        ], ""

    match = _FR_SOLE_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_name_corrected.v1",
            match.group("name"), role="administrateur unique", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _IT_MERGER_ACQUIRER_OWNS_ALL_QUOTAS.fullmatch(leftover)
    parser236_merger_variant = bool(
        match
        and (
            match.group("uid_before")
            or match.group("interests").casefold() == "quote sociali"
            or re.search(
                r"bilancio al\s+\d{2}\.\d{2}\.\d{4}\s+,",
                leftover,
                re.I | re.UNICODE,
            )
        )
    )
    if match and parser236_merger_variant:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_acquirer_owns_all_quotas.v2", {
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("uid_before") or match.group("uid_after"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "ownership_interests": match.group("interests"),
                "all_interests_held_by_acquirer": True,
                "capital_increase": False,
                "shares_allocated": False,
            },
        )], ""

    match = _FR_PERSON_FULL_NAME_AND_ORIGIN_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.full_name_and_origin_corrected.v1",
            match.group("name"), extra={
                "action": "name_and_origin_corrected",
                "previous_name": match.group("previous_name").strip(),
                "origin": match.group("origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_FOUNDATION_ASSET_TRANSFER_SUPERVISORY_DECISION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "fr.text.foundation_asset_transfer_supervisory_decision.v1", {
                "source_kind": "fondation",
                "agreement_date": _french_date(match.group("agreement_date")),
                "supervisory_decision_date": _french_date(match.group("decision_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "none",
            },
        )], ""

    match = _FR_FOUR_SIGNATORIES_WITH_ADMINISTRATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.four_signatories_with_administrator.v1"
        events: list[Event] = []
        for index in (1, 2, 3, 4):
            country = (
                match.group("shared_origin") if index == 1
                else match.group(f"country{index}") if index in (2, 3)
                else match.group("origin4")
            )
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted",
                    "with": "un administrateur",
                    "origin_country": country.strip(),
                },
            ))
        return events, ""

    match = _DE_COMPANY_REINSTATED_FOR_COMPLETE_LIQUIDATION_WITH_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.company_reinstated_complete_liquidation_address.v1"
        common = {
            "deletion_date": _iso_date(match.group("deletion_date")),
            "decision_date": _iso_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
            "legal_basis": match.group("legal_basis"),
        }
        address = {
            "organization": match.group("organization").strip(),
            "contact": match.group("contact").strip(),
            "street": match.group("street").strip(),
            "postal_code": match.group("postal_code"),
            "locality": match.group("locality").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "registration_reinstated", "action": "reinstated",
                    "purpose": "complete_liquidation",
                    "legal_form": match.group("legal_form"),
                    "liquidation_address": address, **common,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "address": address, **common,
                },
            ),
        ], ""

    match = _FR_TWO_ASSOCIATE_SHAREHOLDINGS_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associate_shareholdings_corrected.v1"
        common = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "currency": "CHF", "reason": "share_transfer",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"), role="associée",
                extra={
                    **common, "action": "shareholding_corrected",
                    "shares_count": _count(match.group("count1")),
                    "share_nominal": match.group("nominal1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"), role="associé",
                extra={
                    **common, "action": "shareholding_corrected",
                    "shares_count": _count(match.group("count2")),
                    "share_nominal": match.group("nominal2"),
                    "previous_shares_count": _count(match.group("previous_count2")),
                    "previous_share_nominal": match.group("previous_nominal2"),
                },
            ),
        ], ""

    match = _FR_TWO_APPOINTED_DIRECTORS_PROXY_REVOKED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_directors_appointed_proxy_revoked.v1"
        signing = "Einzelunterschrift" if match.group("individual_signing") else None
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="directeur", signing=signing, extra={
                    "action": "appointed", "previous_authority": "procuration",
                    "previous_authority_revoked": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_NOMINATIVE_SHARES_CORRECTED.fullmatch(leftover)
    if match:
        count = _count(match.group("count"))
        previous_count = _count(match.group("previous_count"))
        nominal = _amount(match.group("nominal"))
        previous_nominal = _amount(match.group("previous_nominal"))
        if count * nominal == previous_count * previous_nominal:
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "fr.text.nominative_shares_corrected.v1", {
                    "action": "share_structure_corrected",
                    "count": count, "nominal": match.group("nominal"),
                    "share_kind": match.group("kind"),
                    "transfer_restricted": True,
                    "previous_count": previous_count,
                    "previous_nominal": match.group("previous_nominal"),
                    "previous_share_kind": match.group("previous_kind"),
                    "currency": "CHF",
                },
            )], ""

    match = _FR_MANAGER_TRANSFERS_TO_NEW_UNSIGNED_ASSOCIATE_WITH_DOMICILE.fullmatch(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if before - transferred == remaining and transferred == buyer_count and len(nominals) == 1:
            rule_id = "fr.persons.manager_transfer_new_unsigned_associate_domicile.v1"
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    place=match.group("seller_place"), role="associée-gérante", extra={
                        **common, "action": "shares_transferred_and_domicile_changed",
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, "counterparty": match.group("buyer"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("buyer_place"), role="associée", extra={
                        **common, "action": "appointed_and_shares_received",
                        "origin": match.group("origin").strip(),
                        "shares_received": transferred, "shares_count": buyer_count,
                        "without_signature": True,
                        "counterparty": match.group("seller"),
                    },
                ),
            ], ""

    match = _DE_DISSOLUTION_AND_NEW_COMPANY_NAME.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.dissolution_resolution_new_name.v1", {
                "kind": "dissolution", "action": "dissolved",
                "date": _iso_date(match.group("date")),
                "decision_body": "Generalversammlung",
                "new_name": match.group("name").strip(),
            },
        )], (match.group("remaining") or "")

    return [], leftover
