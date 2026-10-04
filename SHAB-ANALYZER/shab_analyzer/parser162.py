from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_REGISTERED_SHARE_STRUCTURE_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"capital-actions est divisé en\s+(?P<count>[\d']+)\s+"
    r"(?P<share_kind>actions nominatives) de CHF\s+(?P<nominal>[\d'.]+),?\s*"
    r"\(et non de\s+(?P<previous_count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+avec restrictions quant à la "
    r"transmissibilité selon statuts comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_DOTTED_LOCALITY = re.compile(
    r"^Weitere Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>St\.\s+Moritz)\.?$",
    re.I | re.UNICODE,
)
_DE_DOCUMENT_LIST_UPDATED = re.compile(
    r"^Aktualisierte Liste der Belege\.?$", re.I | re.UNICODE
)
_FR_UNLIMITED_PARTNER_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*de et à\s+(?P<place>[^,.;]+),\s*"
    r"est membre de l['’]administration et associé indéfiniment responsable$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_INCREASE_ADJUSTED_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung und Anpassung des "
    r"genehmigten Kapitals gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.\s*\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung und Anpassung "
    r"des genehmigten Kapitals gemäss näherer Umschreibung in den Statuten "
    r"beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_AND_DIRECTOR_SIGNING_CHANGED = re.compile(
    r"^L['’]administrateur\s+(?P<administrator>[^,.;]+)\s+et le directeur\s+"
    r"(?P<director>[^,.;]+),\s*signent désormais collectivement à deux avec\s+"
    r"(?P<with_person>[^,.;]+);\s*leurs pouvoirs sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_DATE_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}[-.]\d{2}[-.]\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les nouveaux "
    r"statuts sont du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non pas\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+),\s*"
    r"(?P<seller2>[^,.;]+)\s+et\s+(?P<seller3>[^,.;]+),\s*"
    r"cèdent chacun respectivement\s+(?P<count1>[\d']+),\s*"
    r"(?P<count2>[\d']+)\s+et\s+(?P<count3>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant\s*;\s*(?P=seller1),\s*(?P=seller2)\s+et\s+(?P=seller3)\s+"
    r"restent chacun titulaires de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FULL_ADDRESS_AND_NEW_CEO = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.\s*"
    r"Neu eingetragene Person:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<nationality>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>Vorsitzender der Geschäftsleitung\s*\(CEO\)),\s*"
    r"Kollektivunterschrift zu zweien\.?$",
    re.I | re.UNICODE,
)
_DE_PARTIAL_ASSET_TRANSFER_SHARES_AND_CREDIT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+Teilaktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Teilpassiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<share_nominal>[\d'.]+)\s+und "
    r"Gutschrift einer Forderung von CHF\s+(?P<credit>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_MODIFIED = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine Änderung des genehmigten Kapitals "
    r"gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_MANAGER_AND_SELLER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"lequel associé est en outre nommé gérant\s+L['’]associée-gérante\s+"
    r"(?P=seller),\s*nommée présidente,\s*est désormais titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_ADDED_AFTER_PREVIOUS_PLACE_FRAGMENT = re.compile(
    r"^\[finora:\s*(?P<previous_place>[^\]]+)\]\.\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ROLE_CORRECTED_AND_LIQUIDATOR_APPOINTED = re.compile(
    r"^L['’]inscription no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<manager>[^,.;]+)\s+est gérant\s*\(et non pas gérant liquidateur\)\s+"
    r"et que la liquidatrice est\s+(?P<liquidator>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_ORGANIZATION_RENAMED_FOREIGN_ID = re.compile(
    r"^L['’]associée\s+(?P<previous_name>.+?)\s*"
    r"\((?P<foreign_id>[^)]+)\)\s+porte désormais le nom de\s+"
    r"(?P<name>.+?)\s*\((?P<new_foreign_id>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_ERRONEOUS_DELETION_REINSTATED_IN_LIQUIDATION = re.compile(
    r"^La cancellazione della società pubblicata nel FUSC no\.\s*"
    r"(?P<issue>\d+)\s+del\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"è avvenuta erroneamente\.\s*La società rimane iscritta in liquidazione "
    r"come in precedenza\.\s*\[finora:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = re.split(r"[.-]", raw)
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


def extract_parser162_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 162."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_REGISTERED_SHARE_STRUCTURE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_structure_corrected.v1",
            {
                "kind": "share_structure", "action": "corrected",
                "currency": "CHF", "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": match.group("share_kind").lower(),
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
                "previous_transfer_restrictions": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _DE_ADDITIONAL_ADDRESS_DOTTED_LOCALITY.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.additional_address_dotted_locality.v1",
            {
                "kind": "additional_address", "action": "added",
                "address": address,
                "street": f"{match.group('street').strip()} {match.group('house')}",
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _DE_DOCUMENT_LIST_UPDATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.document_list_updated.v1",
            {"kind": "documents_updated", "action": "updated"},
        ))

    match = _FR_UNLIMITED_PARTNER_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.unlimited_partner_administrator.v1",
            match.group("name"), place=match.group("place"),
            role="membre de l'administration et associé indéfiniment responsable",
            signing="Einzelunterschrift",
            extra={
                "action": "appointed", "origin": match.group("place").strip(),
                "origin_same_as_place": True,
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_INCREASE_ADJUSTED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_increase_adjusted_with_history.v1",
            {
                "kind": "authorized_capital", "action": "increased_and_adjusted",
                "decision_date": _iso_date(match.group("date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_ADMINISTRATOR_AND_DIRECTOR_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrator_and_director_signing_changed.v1"
        for name_group, role in (
            ("administrator", "administrateur"),
            ("director", "directeur"),
        ):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_group),
                role=role, signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "signing_changed",
                    "co_signs_with": match.group("with_person").strip(),
                },
            ))

    match = _FR_STATUTES_DATE_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.statutes_date_corrected_with_notice.v1",
            {
                "kind": "statutes_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_THREE_MANAGERS_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers_transfer_to_new_manager.v1"
        buyer = match.group("buyer").strip()
        for index in range(1, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group(f"count{index}")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé-gérant", signing="Einzelunterschrift",
            extra={
                "action": "appointed_manager_and_shares_received",
                "origin": match.group("origin").strip(),
                "new_associate": True,
                "shares_received": sum(
                    _count(match.group(f"count{index}")) for index in range(1, 4)
                ),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF",
            },
        ))

    match = _DE_FULL_ADDRESS_AND_NEW_CEO.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.full_address_and_new_ceo.v1"
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "action": "completed", "address": address,
                    "street": f"{match.group('street').strip()} {match.group('house')}",
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role=match.group("role").strip(),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "nationality": match.group("nationality").strip(),
                },
            ),
        ])

    match = _DE_PARTIAL_ASSET_TRANSFER_SHARES_AND_CREDIT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.partial_asset_transfer_shares_and_credit.v1",
            {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "assets_kind": "partial_assets",
                "liabilities_kind": "partial_third_party_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "currency": "CHF",
                "consideration_share_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_credit": match.group("credit"),
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_MODIFIED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_modified.v1",
            {
                "kind": "authorized_capital", "action": "modified",
                "decision_date": _iso_date(match.group("date")),
                "details_in_statutes": True,
            },
        ))

    match = _FR_TRANSFER_TO_NEW_MANAGER_AND_SELLER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.transfer_to_new_manager_and_seller_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associée-gérante, présidente",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_manager_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _IT_BRANCH_ADDED_AFTER_PREVIOUS_PLACE_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_added_after_previous_place_fragment.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_place_marker": match.group("previous_place").strip(),
            },
        ))

    match = _FR_MANAGER_ROLE_CORRECTED_AND_LIQUIDATOR_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_role_corrected_and_liquidator_appointed.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"), role="gérant",
                extra={
                    **reference, "action": "role_corrected",
                    "previous_role": "gérant liquidateur",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("liquidator"),
                place=match.group("place"), uid=match.group("uid"),
                role="liquidatrice",
                extra={**reference, "action": "appointed"},
            ),
        ])

    match = _FR_ASSOCIATE_ORGANIZATION_RENAMED_FOREIGN_ID.search(leftover)
    if match and match.group("foreign_id") == match.group("new_foreign_id"):
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.persons.associate_organization_renamed_foreign_id.v1",
            match.group("name"), role="associée",
            extra={
                "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
                "foreign_registry_id": match.group("foreign_id").strip(),
            },
        ))

    match = _IT_ERRONEOUS_DELETION_REINSTATED_IN_LIQUIDATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.erroneous_deletion_reinstated_in_liquidation.v1",
            {
                "kind": "registration_reinstated",
                "action": "reinstated_in_liquidation",
                "reason": "erroneous_deletion",
                "notice_issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "registry_reinstated": True,
                "liquidation_continued": True,
                "previous": match.group("previous").strip(),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
