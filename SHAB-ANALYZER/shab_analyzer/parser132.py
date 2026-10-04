from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SINGLE_DOMICILE_CHANGED = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est désormais domiciliée? à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_AUTHORIZED_CAPITAL_CHANGE = re.compile(
    r"^\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<change_date>\d{2}\.\d{2}\.\d{4})\s+die anlässlich der "
    r"Generalversammlung vom\s+(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eingeführte genehmigte Kapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_VOLUNTARY_DELETION = re.compile(
    r"^Der Vorstand hat am\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"beschlossen,\s*auf den Eintrag des Vereins im Handelsregister per\s+"
    r"(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+zu verzichten\.\s*"
    r"Da dieser Verein kein nach kaufmännischer Art geführtes Gewerbe betreibt "
    r"und somit nicht eintragungspflichtig ist,\s*wird der auf ihn bezügliche "
    r"Eintrag im Handelsregister gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_WITH_DOMICILE = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée-gérante\s+(?P<seller>[^,.;]+),\s*"
    r"maintenant domiciliée? à\s+(?P<seller_place>[^,.;]+),\s*détient\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"laquelle n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REMOVED_WITH_UID = re.compile(
    r"^(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"ist nicht mehr Revisionsstelle\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PAIR_ASYMMETRIC_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommée présidente,\s*et\s+"
    r"(?P<member>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.\s*"
    r"Signature individuelle de la présidente ou collective à deux de l['’]autre "
    r"membre du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_DE_HISTORICAL_FORMATION_AND_REGISTRATION = re.compile(
    r'^Die Gesellschaft wurde am\s+(?P<founding_date>\d{2}\.\d{2}\.\d{4})\s+unter '
    r'dem Namen\s+["“](?P<former_name>.+?)["”]\s+als\s+'
    r"(?P<legal_form>Aktiengesellschaft)\s+mit Sitz in\s+(?P<seat>[^,.;]+)\s+"
    r"gegründet,\s*aber erst mit den Statuten vom\s+"
    r"(?P<statutes_date>\d{2}\.\d{2}\.\d{4})\s+angemeldet und am\s+"
    r"(?P<registration_date>\d{2}\.\d{2}\.\d{4})\s+im Handelsregister "
    r"eingetragen\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDING_BUSINESS_ACQUISITION_FRAGMENT = re.compile(
    r"^eingetragenen Einzelunternehmens\s+(?P<source_name>.+?),\s*in\s+"
    r"(?P<source_place>[^()]+?)\s*\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"gemäss Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Übernahmebilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*wofür\s+(?P<share_count>[\d']+)\s+"
    r"(?P<share_kind>Namenaktien) zu CHF\s+(?P<share_nominal>[\d'.]+)\s+"
    r"ausgegeben und CHF\s+(?P<receivable>[\d'.]+)\s+als Forderung "
    r"gutgeschrieben werden\.?$",
    re.I | re.UNICODE,
)
_FR_OFFICER_SIGNING_CORRECTION = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\.\s*"
    r"(?P<notice_ref>\d+)\)\s+est rectifiée comme suit:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>administratrice),\s*"
    r"signature collective à deux\s*\(et non pas signature individuelle\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+),\s*associés-gérants,\s*"
    r"sont nommés liquidateurs?\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_RECEIVABLE_AND_RESERVES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Inventar per\s+(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von "
    r"CHF\s+(?P<assets>[\d'.]+)\s+und Fremdkapital von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<receivable>[\d'.]+)\s+werden in den Büchern "
    r"der Gesellschaft als Forderung gutgeschrieben und CHF\s+"
    r"(?P<reserves>[\d'.]+)\s+werden in den Büchern der Gesellschaft als "
    r"offene Reserven gutgeschrieben\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_AGREEMENT_DATE_CORRECTION = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>\d+)\)\s+est rectifiée en ce sens que la date du contrat "
    r"d['’]apports en nature est le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(et non\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLERS_TO_ONE_UNSIGNED_ASSOCIATE = re.compile(
    r"^(?P<seller1>[^,.;]+?)\s+et\s+(?P<seller2>[^,.;]+?)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^(),.;]+)\s*\((?P<country>[^)]+)\),\s*nouvel associé sans "
    r"signature,\s*avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller1)\s+et\s+(?P=seller2)\s+"
    r"restent titulaires de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_DE_NON_PUBLIC_STATUTES_CHANGED_TYPO = re.compile(
    r"^Statuten über nicht publikationspflichti(?:e|ge) Tatsachen geändert am\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_LIQUIDATION_ADDRESS = re.compile(
    r"^Liquidationsdomizil:\s*(?P<care_of>c/o\s+.+?),\s*"
    r"(?P<street>.+?),\s*(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATION_SHARE_TRANSFER = re.compile(
    r"^L['’]associée\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<seller_before>[\d']+)\s+parts de "
    r"CHF\s+(?P<nominal>[\d'.]+)\s+à l['’]associée\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
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


def extract_parser132_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 132."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SINGLE_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.single_domicile_changed.v1",
            match.group("name"), place=match.group("place"),
            extra={"action": "domicile_changed", "domicile_changed": True},
        ))

    match = _DE_PREVIOUS_AUTHORIZED_CAPITAL_CHANGE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.previous_authorized_capital_change.v1",
            {
                "kind": "authorized_increase",
                "action": "previous_clause_replaced",
                "change_date": _iso_date(match.group("change_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "historical_entry": True,
            },
        ))

    match = _DE_ASSOCIATION_VOLUNTARY_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "de.text.association_voluntary_deletion.v1",
            {
                "decision_date": _iso_date(match.group("decision_date")),
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_body": "board",
                "reason": "not_required_to_register",
                "commercial_business": False,
            },
        ))

    match = _FR_MANAGER_SHARE_TRANSFER_WITH_DOMICILE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_share_transfer_with_domicile.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associée-gérante",
                extra={
                    "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associée",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                    "new_associate": True,
                    "without_signature": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _DE_AUDITOR_REMOVED_WITH_UID.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "de.persons.auditor_removed_with_uid.v1",
            match.group("name"), role="Revisionsstelle", uid=match.group("uid"),
            extra={"action": "removed", "uid": match.group("uid")},
        ))

    match = _FR_BOARD_PAIR_ASYMMETRIC_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_pair_asymmetric_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="présidente", signing="Einzelunterschrift",
                extra={"action": "appointed_president"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"), place=match.group("place"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "heimat": match.group("origin").strip()},
            ),
        ])

    match = _DE_HISTORICAL_FORMATION_AND_REGISTRATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_registered", "de.text.historical_formation_registration.v1",
            {
                "founding_date": _iso_date(match.group("founding_date")),
                "former_name": match.group("former_name").strip(),
                "legal_form": match.group("legal_form"),
                "seat": match.group("seat").strip(),
                "statutes_date": _iso_date(match.group("statutes_date")),
                "registration_date": _iso_date(match.group("registration_date")),
                "historical_entry": True,
            },
        ))

    match = _DE_FOUNDING_BUSINESS_ACQUISITION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.founding_business_acquisition_fragment.v1",
            {
                "kind": "contribution_in_kind_and_asset_acquisition",
                "source": match.group("source_name").strip(),
                "source_place": match.group("source_place").strip(),
                "source_uid": match.group("source_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "shares_issued": _count(match.group("share_count")),
                "share_kind": match.group("share_kind"),
                "share_nominal": match.group("share_nominal"),
                "receivable": match.group("receivable"),
                "currency": "CHF",
            },
        ))

    match = _FR_OFFICER_SIGNING_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.officer_signing_correction.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_corrected",
                "previous_signing": "Einzelunterschrift",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_MANAGERS_APPOINTED_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.managers_appointed_liquidators.v1"
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role="associé-gérant et liquidateur",
                extra={"action": "appointed_liquidator", "remains_manager": True},
            ))

    match = _DE_ASSET_TRANSFER_RECEIVABLE_AND_RESERVES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_receivable_reserves.v1",
            {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_receivable": match.group("receivable"),
                "consideration_open_reserves": match.group("reserves"),
                "currency": "CHF",
            },
        ))

    match = _FR_CONTRIBUTION_AGREEMENT_DATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.contribution_agreement_date_corrected.v1",
            {
                "kind": "contribution_in_kind_agreement_date",
                "action": "date_corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_SELLERS_TO_ONE_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_sellers_to_one_unsigned_associate.v1"
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        for group in ("seller1", "seller2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role="associé",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"),
                    "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé",
            extra={
                "action": "shares_received",
                "counterparties": [match.group("seller1").strip(), match.group("seller2").strip()],
                "heimat": match.group("origin").strip(),
                "country": match.group("country").strip(),
                "new_associate": True,
                "without_signature": True,
                "shares_received": transferred * 2,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF",
            },
        ))

    match = _DE_NON_PUBLIC_STATUTES_CHANGED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.non_public_statutes_changed_typo.v1",
            {
                "date": _iso_date(match.group("date")),
                "scope": "non_public_facts",
                "publication_required": False,
            },
        ))

    match = _DE_LIQUIDATION_ADDRESS.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('care_of').strip()}, {match.group('street').strip()}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.liquidation_address_short.v1",
            {
                "kind": "liquidation_address",
                "action": "changed",
                "to": address,
                "care_of": match.group("care_of").strip(),
                "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_ORGANIZATION_SHARE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.organization_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée",
                uid=match.group("seller_uid"),
                extra={
                    "action": "shares_transferred",
                    "uid": match.group("seller_uid"),
                    "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                    "shares_before": _count(match.group("seller_before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associée",
                uid=match.group("buyer_uid"),
                extra={
                    "action": "shares_received",
                    "uid": match.group("buyer_uid"),
                    "counterparty": seller,
                    "counterparty_uid": match.group("seller_uid"),
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
