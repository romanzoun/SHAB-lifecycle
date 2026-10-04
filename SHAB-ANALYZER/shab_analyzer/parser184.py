from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_DE_REMOVED_BRANCH_LEGACY_REGISTER = re.compile(
    r"^Zweigniederlassung neu:\s*"
    r"(?:\[Folgende Zweigniederlassungen sind aufgehoben worden:\]\s*)?"
    r"\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\((?P<registry_id>CH-[\d.]+-\d)\)\s*\(HR\s+(?P<register_canton>[A-Z]{2})\)\]\.?$",
    re.I | re.UNICODE,
)
_IT_OBLIGATIONS_HEADING = re.compile(r"^Obblighi:\s*$", re.I | re.UNICODE)
_DE_BONDHOLDER_DEEDS_FILED = re.compile(
    r"^Die öffentlichen Urkunden der Versammlungen der Anleihensgläubiger vom\s+"
    r"(?P<meeting_date>\d{2}\.\d{2}\.\d{4})\s+betreffend CHF\s+"
    r"(?P<amount1>[\d'.]+)\s+(?P<class1>Class\s+[A-Z])\s+Anleihen\s*"
    r"\(ISIN\s+(?P<isin1>[A-Z0-9]+),\s*Common Code\s+(?P<code1>\d+)\),\s*"
    r"fällig am\s+(?P<due1>\d{2}\.\d{2}\.\d{4}),\s*betreffend CHF\s+"
    r"(?P<amount2>[\d'.]+)\s+(?P<class2>Class\s+[A-Z])\s+Anleihen\s*"
    r"\(ISIN\s+(?P<isin2>[A-Z0-9]+),\s*Common Code\s+(?P<code2>\d+)\),\s*"
    r"fällig am\s+(?P<due2>\d{2}\.\d{2}\.\d{4})\s+und betreffend CHF\s+"
    r"(?P<amount3>[\d'.]+)\s+(?P<class3>Class\s+[A-Z])\s+Anleihen\s*"
    r"\(ISIN\s+(?P<isin3>[A-Z0-9]+),\s*Common Code\s+(?P<code3>\d+)\),\s*"
    r"fällig am\s+(?P<due3>\d{2}\.\d{2}\.\d{4}),\s*sind am\s+"
    r"(?P<filing_date>\d{2}\.\d{2}\.\d{4})\s+beim\s+"
    r"(?P<office>Handelsregisteramt des Kantons [^.]+?)\s+eingereicht worden und werden "
    r"gemäss\s+(?P<legal_basis>Art\.\s*151 HRegV)\s+bei den Handelsregisterakten "
    r"der Schuldnerin aufbewahrt\.?$",
    re.I | re.UNICODE,
)
_FR_CAPITAL_ENTRY_SUPPLEMENTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée? en ce sens que le Capital "
    r"est de:\s*CHF\s+(?P<capital>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_INVENTORY_RECEIVABLE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Fremdkapital von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*Forderung von CHF\s+(?P<receivable>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_OFFICIAL_DELETION_PROCEDURE_COMPLETED = re.compile(
    r"^Das amtliche Verfahren gemäss\s+(?P<legal_basis>Art\.\s*934 OR)\s+zur "
    r"Löschung der Gesellschaft wurde durchgeführt,\s*weil die Gesellschaft "
    r"keine Geschäftstätigkeit mehr aufweist,\s*keine verwertbaren Aktiven mehr "
    r"hat und kein Interesse an der Aufrechterhaltung der Eintragung innert "
    r"angesetzter Frist geltend gemacht wurde\.?$",
    re.I | re.UNICODE,
)
_DE_REAL_ESTATE_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträg(?:t)? gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s*\(inkl\.\s*(?P<asset_details>.+?)\)\s+und "
    r"Passiven\s*\(Fremdkapital\)\s*von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"auf die\s+(?:&quot;|[\"“])(?P<recipient>.+?)(?:&quot;|[\"”])\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY_CASH = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>[^,]+?)\s+in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_HEAD_OFFICE_TYPO_FRAGMENT = re.compile(
    r"^Siège princiapl:\s*(?P<head_office>[^.]+)\.\s*La succursale\s*$",
    re.I | re.UNICODE,
)
_FR_PROXY_RESTRICTION_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+est rectifiée en ce sens que "
    r"la procuration conférée à\s+(?P<name>[^,.;]+)\s+est limitée avec un "
    r"administrateur,\s*un directeur ou un sous-directeur\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_DIRECTOR_SIGNING_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]associé "
    r"et directeur\s+(?P<name>[^,.;]+)\s+dispose de la signature collective à "
    r"2\s*\(et non de la signature individuelle\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_LIQUIDATORS_MOVED = re.compile(
    r"^Liquidateurs:\s*les associés[- ]gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*maintenant domiciliés à\s+(?P<place>[^,.;]+),\s*"
    r"lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_NEW_NAME = re.compile(
    r"^Nouvelle raison sociale de l['’]associée:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_INVENTORY_CASH = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et inventaire au\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des "
    r"actifs pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers "
    r"pour CHF\s+(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGER_SIGNINGS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que les "
    r"associés-gérants\s+(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+)\s+signent les trois collectivement à deux\s*"
    r"\(et non individuellement,\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_COPY_FILED_SUPPLEMENT = re.compile(
    r"^En complément de l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*dépôt d['’]un nouvel exemplaire "
    r"des statuts\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser184_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 184."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_REMOVED_BRANCH_LEGACY_REGISTER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_removed_legacy_register.v1", {
                "action": "removed", "place": match.group("place").strip(),
                "legacy_registry_id": match.group("registry_id"),
                "register_canton": match.group("register_canton").upper(),
            },
        )], ""

    if _IT_OBLIGATIONS_HEADING.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.obligations_heading_residue.v1", {
                "kind": "ancillary_obligations",
                "action": "details_parsed_separately",
                "heading": "Obblighi",
            },
        )], ""

    match = _DE_BONDHOLDER_DEEDS_FILED.fullmatch(leftover)
    if match:
        bonds = [
            {
                "class": match.group(f"class{index}"),
                "currency": "CHF",
                "nominal": match.group(f"amount{index}"),
                "isin": match.group(f"isin{index}"),
                "common_code": match.group(f"code{index}"),
                "due_date": _iso_date(match.group(f"due{index}")),
            }
            for index in range(1, 4)
        ]
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "de.text.bondholder_deeds_filed.v1", {
                "kind": "bondholder_meeting_deeds",
                "action": "filed",
                "meeting_date": _iso_date(match.group("meeting_date")),
                "filing_date": _iso_date(match.group("filing_date")),
                "filing_office": match.group("office").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "bonds": bonds,
                "kept_with_commercial_register_files": True,
            },
        )], ""

    match = _FR_CAPITAL_ENTRY_SUPPLEMENTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.capital_entry_supplemented.v1", {
                "action": "entry_supplemented",
                "kind": "share_capital",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "capital": match.group("capital"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_INVENTORY_RECEIVABLE.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("receivable"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_inventory_receivable.v2", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "borrowed_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "receivable",
                "consideration_receivable": match.group("receivable"),
                "currency": "CHF",
            },
        )], ""

    match = _DE_OFFICIAL_DELETION_PROCEDURE_COMPLETED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.official_deletion_procedure_completed.v1", {
                "kind": "official_deletion_procedure",
                "action": "completed",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "business_activity": False,
                "realisable_assets": False,
                "maintenance_interest_asserted": False,
                "company_deleted": False,
            },
        )], ""

    match = _DE_REAL_ESTATE_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.real_estate_asset_transfer_no_consideration.v2", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "assets_include_real_estate": True,
                "asset_details": match.group("asset_details").strip(),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "borrowed_capital",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration").lower(),
                "consideration_kind": "none",
                "gratuitous": True,
                "currency": "CHF",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY_CASH.fullmatch(leftover)
    if match and _amount(match.group("assets")) == _amount(match.group("consideration")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_assets_only_cash.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
                "currency": "CHF",
            },
        )], ""

    match = _FR_BRANCH_HEAD_OFFICE_TYPO_FRAGMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_head_office_typo_fragment.v1", {
                "action": "head_office_recorded",
                "head_office": match.group("head_office").strip(),
                "source_label": "Siège princiapl",
                "source_label_typo": True,
            },
        )], ""

    match = _FR_PROXY_RESTRICTION_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.proxy_restriction_corrected.v1",
            match.group("name"), role="fondé de procuration",
            signing="Kollektivprokura zu zweien", extra={
                "action": "signing_restriction_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "co_signer_roles": ["administrateur", "directeur", "sous-directeur"],
            },
        )], ""

    match = _FR_ASSOCIATE_DIRECTOR_SIGNING_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.associate_director_signing_corrected.v1",
            match.group("name"), role="associé et directeur",
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGERS_LIQUIDATORS_MOVED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_managers_liquidators_moved.v1"
        events = []
        for name_group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                place=match.group("place"), role="associé-gérant et liquidateur",
                signing="Einzelunterschrift", extra={
                    "action": "appointed_liquidator_and_domicile_changed",
                    "signing_continues": True,
                },
            ))
        return events, ""

    match = _FR_CORPORATE_ASSOCIATE_NEW_NAME.fullmatch(leftover)
    if match and not re.search(
        r"\((?:RSIN\s+)?\d+\)\s*$|,\s*à\s+",
        match.group("name"),
        re.I | re.UNICODE,
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.corporate_associate_new_name_without_id.v1", {
                "kind": "corporate_associate",
                "action": "name_changed",
                "name": match.group("name").strip(),
            },
        )], ""

    match = _FR_ASSET_TRANSFER_INVENTORY_CASH.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_inventory_cash.v2", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
                "currency": "CHF",
            },
        )], ""

    match = _FR_THREE_MANAGER_SIGNINGS_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_manager_signings_corrected.v1"
        reference = {
            "action": "signing_corrected",
            "previous_signing": "Einzelunterschrift",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_group),
                role="associé-gérant", signing="Kollektivunterschrift zu zweien",
                extra=reference,
            )
            for name_group in ("name1", "name2", "name3")
        ], ""

    match = _FR_STATUTES_COPY_FILED_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.statutes_copy_filed_supplement.v1", {
                "action": "entry_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "document": "statutes",
                "document_action": "new_copy_filed",
            },
        )], ""

    return [], text
