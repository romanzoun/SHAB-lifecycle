from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_AUTHORIZED_CAPITAL_EXPIRED_WITH_PREVIOUS = re.compile(
    r"^Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+beschlossene genehmigte Kapitalerhöhung "
    r"infolge Fristablaufs\.\s*\[bisher:\s*Die Gründerversammlung hat mit "
    r"Beschluss vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]associé[ -]gérant porte le nom de\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_REPLACED_AND_CONDITIONAL = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit den Beschlüssen vom\s+"
    r"(?P<authorization_date1>\d{2}\.\d{2}\.\d{4})\s+und vom\s+"
    r"(?P<authorization_date2>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung ersetzt und eine neue genehmigte Kapitalerhöhung gemäss "
    r"näherer Umschreibung in\s+(?P<authorized_article>Art\.\s*\w+)\s+der Statuten "
    r"beschlossen\.\s*\[bisher:\s*(?P<previous>Die Gesellschaft hat mit den "
    r"Beschlüssen .+? beschlossen\.)\]\.?\s*Die Gesellschaft hat mit Beschluss "
    r"vom\s+(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in\s+"
    r"(?P<conditional_article>Art\.\s*\w+)\s+der Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_IT_NEW_BRANCH_BARE_UID = re.compile(
    r"^Nuova succursale:\s*(?P<place>.+?)\s+"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.?$",
    re.I | re.UNICODE,
)
_DE_FAILED_CONTRIBUTION_REPLACED_BY_CASH = re.compile(
    r"^\[gestrichen:\s*Infolge Unmöglichkeit konnte das\s+(?P<asset>.+?)\s+"
    r"im Wert und zum Preis von CHF\s+(?P<value>[\d'.]+)\s+gemäss "
    r"Sacheinlage-/Sachübernahmevertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+nicht übertragen werden\.\s*"
    r"Das Kapital wurde nicht vollständig liberiert\.\]\.?\s*Im Nachgang zur "
    r"Sacheinlage- und Sachübernahmegründung vom\s+"
    r"(?P<founding_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine Bareinlage in der "
    r"Höhe von CHF\s+(?P<cash>[\d'.]+)\s+geleistet,\s*wodurch das Aktienkapital "
    r"nun vollständig liberiert ist\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_UNIT_ASSET_TRANSFER_RECIPIENT_PLACE_UID = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+den Betriebsteil\s+"
    r"(?P<business_unit>.+?)\s+mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und "
    r"Passiven\s*\(Fremdkapital\)\s+von CHF\s+(?P<liabilities>[\d'.]+)\s+auf "
    r"die\s+(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<consideration>keine)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_TWO_CONTRACT_DATES_SHARE_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<first_day>\d{2})\./(?P<second_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven "
    r"von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von "
    r"CHF\s+(?P<liabilities>[\d'.]+)\s+auf die neu eingetragene\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Gegenleistung:\s*"
    r"(?P<share_count>[\d'.]+)\s+(?P<share_kind>Namenaktien) zu CHF\s+"
    r"(?P<share_nominal>[\d'.]+)\s+der\s+(?P<consideration_issuer>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_RESTRICTION_REMOVED_AND_THREE_APPOINTED = re.compile(
    r"^(?P<existing>[^,.;]+),\s*maintenant à\s+(?P<existing_place>[^,.;]+),\s*"
    r"continue à engager la société par sa procuration collective à deux,\s*"
    r"désormais sans restriction\.\s*Procuration collective à deux est conférée "
    r"à\s+(?P<name1>[^,.;]+),\s*(?:de|du|des|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:de|du|des|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:de|du|des|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_SHARE_CONSIDERATION = re.compile(
    r'^Transfert de patrimoine:\s*selon contrat du\s+'
    r'(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour '
    r'CHF\s+(?P<assets>[\d\'.]+)\s+et des passifs envers les tiers pour CHF\s+'
    r'(?P<liabilities>[\d\'.]+)\s+à la société\s+["“](?P<recipient>.+?)["”],\s*'
    r'à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*'
    r'Contre-prestation:\s*(?P<share_count>[\d\']+)\s+'
    r'(?P<share_kind>action nominative|actions nominatives) de CHF\s+'
    r'(?P<share_nominal>[\d\'.]+)\s+de la société\s+["“]'
    r'(?P<consideration_issuer>.+?)["”]\.?$',
    re.I | re.UNICODE,
)
_DE_ART_748_FULFILLED_DELETION_PENDING_TAX = re.compile(
    r"^Die Vorschriften von\s+(?P<legal_basis>Art\.\s*748 aOR)\s+sind "
    r"eingehalten\.\s*\[Die Löschung erfolgt sobald die Zustimmungen der "
    r"Steuerverwaltungen vorliegen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_REAL_ESTATE_ASSET_TRANSFER_AMOUNTED = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+die Liegenschaften\s+"
    r"(?P<properties>.+?)\s+im Wert von gesamthaft CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung\s*:?[ ]*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORDINARY_SHARES_RECLASSIFIED_AS_DIVIDEND_PREFERRED = re.compile(
    r"^(?P<reclassified_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<reclassified_nominal>[\d'.]+),\s*jusqu['’]ici ordinaires,\s*sont "
    r"maintenant privilégiées quant au dividende\.\s*Capital-actions:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*entièrement libéré,\s*divisé en\s+"
    r"(?P<preferred_count>[\d']+)\s+actions de CHF\s+"
    r"(?P<preferred_nominal>[\d'.]+),\s*privilégiées quant au dividende et\s+"
    r"(?P<ordinary_count>[\d']+)\s+actions ordinaires de CHF\s+"
    r"(?P<ordinary_nominal>[\d'.]+),\s*toutes nominatives\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_SHARE_COUNT_CORRECTED = re.compile(
    r"^L['’]inscription (?:no\.|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la nouvelle "
    r"associée\s+(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*détient\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s*\(et non\s+(?P<previous_count>[\d']+)\s+parts "
    r"de CHF\s+(?P<previous_nominal>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts sociales "
    r"de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?P<role>gérant),\s*nouvel associé\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_TWO_ASSOCIATES = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+)\s+est désormais titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*suite à "
    r"la cession de\s+(?P<transferred1>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal1>[\d'.]+)\s+à\s+(?P<buyer1>[^,.;]+)\s+et de\s+"
    r"(?P<transferred2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+à\s+"
    r"(?P<buyer2>[^,.;]+),\s*(?:de|du|des|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*laquelle n['’]exerce pas la signature "
    r"sociale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_NEW_MANAGERS = re.compile(
    r"^Nouvelles gérantes:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:de|du|des|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+?)(?:\s+avec\s+"
    r"(?P<signing>signature collective à deux))?\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _date_with_day(day: str, full_date: str) -> str:
    _, month, year = full_date.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    value = Decimal(raw.replace("'", ""))
    if value != value.to_integral_value():
        raise ValueError(f"non-integral count: {raw}")
    return int(value)


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


def extract_parser244_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 244."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_WITH_PREVIOUS.fullmatch(leftover)
    if match and match.group("date") == match.group("previous_date"):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_expired_previous.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_expired", "previous_entry_removed": True,
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.persons.associate_manager_name_corrected.v1",
            match.group("name"), role="associé-gérant", extra={
                "action": "name_corrected", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_REPLACED_AND_CONDITIONAL.fullmatch(leftover)
    if match and match.group("decision_date") == match.group("conditional_date"):
        rule_id = "de.text.authorized_capital_replaced_and_conditional_created.v1"
        decision_date = _iso_date(match.group("decision_date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "replaced",
                    "decision_date": decision_date,
                    "replaced_authorization_dates": [
                        _iso_date(match.group("authorization_date1")),
                        _iso_date(match.group("authorization_date2")),
                    ],
                    "statutes_article": re.sub(
                        r"\s+", " ", match.group("authorized_article")
                    ),
                    "previous": match.group("previous").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "created",
                    "decision_date": decision_date,
                    "statutes_article": re.sub(
                        r"\s+", " ", match.group("conditional_article")
                    ),
                },
            ),
        ], ""

    match = _IT_NEW_BRANCH_BARE_UID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.new_branch_bare_uid.v1", {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
            },
        )], ""

    match = _DE_FAILED_CONTRIBUTION_REPLACED_BY_CASH.fullmatch(leftover)
    if match and match.group("agreement_date") == match.group("founding_date"):
        rule_id = "de.text.failed_contribution_replaced_by_cash.v1"
        common = {
            "agreement_date": _iso_date(match.group("agreement_date")),
            "asset": match.group("asset").strip(), "value": match.group("value"),
            "currency": "CHF", "reason": "transfer_impossible",
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    **common, "kind": "contribution_in_kind", "action": "removed",
                    "not_transferred": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "capital_payment", "action": "cash_paid_in",
                    "agreement_date": _iso_date(match.group("founding_date")),
                    "cash_contribution": match.group("cash"), "currency": "CHF",
                    "capital_fully_paid": True,
                },
            ),
        ], ""

    match = _DE_BUSINESS_UNIT_ASSET_TRANSFER_RECIPIENT_PLACE_UID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.business_unit_transfer_place_uid.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "business_unit": match.group("business_unit").strip(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "liabilities_transferred": True, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "consideration": None,
                "consideration_kind": "none",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_TWO_CONTRACT_DATES_SHARE_CONSIDERATION.fullmatch(
        leftover
    )
    if match and match.group("recipient").casefold() == match.group(
        "consideration_issuer"
    ).casefold():
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_two_dates_shares.v1", {
                "agreement_dates": [
                    _date_with_day(match.group("first_day"), match.group("second_date")),
                    _iso_date(match.group("second_date")),
                ],
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "liabilities_transferred": True, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"), "recipient_newly_registered": True,
                "consideration_kind": "shares",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_issuer": match.group("consideration_issuer").strip(),
            },
        )], ""

    match = _FR_PROXY_RESTRICTION_REMOVED_AND_THREE_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.proxy_restriction_removed_and_three_appointed.v1"
        events = [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", rule_id, match.group("existing"),
            place=match.group("existing_place"), signing="Kollektivprokura zu zweien",
            extra={
                "action": "restriction_removed", "signing_continues": True,
                "domicile_changed": True,
            },
        )]
        for index in (1, 2, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivprokura zu zweien", extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            ))
        return events, ""

    match = _FR_ASSET_TRANSFER_SHARE_CONSIDERATION.fullmatch(leftover)
    if match and match.group("recipient").casefold() == match.group(
        "consideration_issuer"
    ).casefold():
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_share_consideration.v1", {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "liabilities_transferred": True, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "shares",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_kind": match.group("share_kind"),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_issuer": match.group("consideration_issuer").strip(),
            },
        )], ""

    match = _DE_ART_748_FULFILLED_DELETION_PENDING_TAX.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.art748_fulfilled_deletion_pending_tax.v1", {
                "kind": "deletion_pending", "legal_basis": re.sub(
                    r"\s+", " ", match.group("legal_basis")
                ),
                "legal_requirements_fulfilled": True,
                "pending_tax_authority_consents": True,
            },
        )], ""

    match = _DE_REAL_ESTATE_ASSET_TRANSFER_AMOUNTED.fullmatch(leftover)
    if match and _amount(match.group("assets")) == _amount(
        match.group("consideration")
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.real_estate_transfer_amounted.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "asset_kind": "real_estate",
                "properties": match.group("properties").strip(),
                "assets": match.group("assets"), "liabilities_transferred": False,
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    match = _FR_ORDINARY_SHARES_RECLASSIFIED_AS_DIVIDEND_PREFERRED.fullmatch(
        leftover
    )
    if match:
        preferred_count = _count(match.group("preferred_count"))
        ordinary_count = _count(match.group("ordinary_count"))
        nominal_values = {
            _amount(match.group("reclassified_nominal")),
            _amount(match.group("preferred_nominal")),
            _amount(match.group("ordinary_nominal")),
        }
        if (
            _count(match.group("reclassified_count")) > preferred_count
            or len(nominal_values) != 1
            or (preferred_count + ordinary_count) * nominal_values.pop()
            != _amount(match.group("total"))
        ):
            return [], leftover
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.shares_reclassified_dividend_preferred.v1", {
                "kind": "share_class_reclassification", "currency": "CHF",
                "total": match.group("total"), "fully_paid": True,
                "registered": True,
                "reclassified_count": _count(match.group("reclassified_count")),
                "reclassified_from": "ordinary",
                "reclassified_to": "dividend_preferred",
                "classes": [
                    {
                        "kind": "dividend_preferred", "count": preferred_count,
                        "nominal": match.group("preferred_nominal"),
                    },
                    {
                        "kind": "ordinary", "count": ordinary_count,
                        "nominal": match.group("ordinary_nominal"),
                    },
                ],
            },
        )], ""

    match = _FR_CORPORATE_ASSOCIATE_SHARE_COUNT_CORRECTED.fullmatch(leftover)
    if match and _amount(match.group("nominal")) == _amount(
        match.group("previous_nominal")
    ):
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "fr.persons.corporate_associate_share_count_corrected.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="associée", extra={
                "action": "shareholding_corrected", "uid": match.group("uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "shares_count": _count(match.group("count")),
                "previous_shares_count": _count(match.group("previous_count")),
                "share_nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_NEW_MANAGER.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if transferred >= before:
            return [], leftover
        rule_id = "fr.persons.associate_transfer_to_new_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "previous_shares_count": before,
                    "shares_transferred": transferred,
                    "shares_count": before - transferred, **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant", extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "shares_received": transferred, "shares_count": transferred,
                    **common,
                },
            ),
        ], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_TWO_ASSOCIATES.fullmatch(leftover)
    if match and len({
        _amount(match.group("nominal")), _amount(match.group("nominal1")),
        _amount(match.group("nominal2")),
    }) == 1:
        rule_id = "fr.persons.associate_transfer_to_two_associates.v1"
        seller = match.group("seller").strip()
        transferred1 = _count(match.group("transferred1"))
        transferred2 = _count(match.group("transferred2"))
        remaining = _count(match.group("remaining"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    "action": "shares_transferred",
                    "counterparties": [
                        match.group("buyer1").strip(), match.group("buyer2").strip()
                    ],
                    "previous_shares_count": remaining + transferred1 + transferred2,
                    "shares_transferred": transferred1 + transferred2,
                    "shares_count": remaining, **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer1"), role="associée",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "shares_received": transferred1, "shares_count": transferred1,
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer2"),
                place=match.group("place2"), role="associée", extra={
                    "action": "shares_received", "counterparty": seller,
                    "origin": match.group("origin2").strip(),
                    "shares_received": transferred2, "shares_count": transferred2,
                    "without_signature": True, **common,
                },
            ),
        ], ""

    match = _FR_TWO_NEW_MANAGERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_new_managers.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="gérante",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing") else None
                ), extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    return [], leftover
