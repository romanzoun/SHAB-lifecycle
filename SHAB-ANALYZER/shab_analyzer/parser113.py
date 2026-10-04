from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ORGANIZATION_CHANGED = re.compile(
    r"^Nouvelle organisation:\s*(?P<organization>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_DELETION_BLOCKED_CANTONAL_AND_FEDERAL = re.compile(
    r"^Die Gesellschaft kann aber mangels Zustimmung der\s+"
    r"(?P<authorities>Kantonalen und der Eidgenössischen Steuerverwaltungen)\s+"
    r"noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_PROCURATION_ENDED_APPOINTED_ADMINISTRATOR = re.compile(
    r"^(?P<name>[^,.;]+),\s*maintenant à\s+(?P<place>[^,.;]+),\s*"
    r"dont la procuration est éteinte,\s*est nommé administrateur\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<members>.+?),\s*sont membres du comité,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_ITEM = re.compile(
    r"(?:^|,\s*(?:et\s+)?)"
    r"(?P<name>[^,]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,]+),\s*à\s+(?P<place>[^,]+?)\s*$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_AND_MOVED = re.compile(
    r"^L['’]organe de révision inscrit\s+(?P<previous_name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+se nomme désormais\s+"
    r"(?P<name>.+?),\s*maintenant à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_RECEIVABLE = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour "
    r"CHF\s+(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*une créance de CHF\s+(?P<consideration>[\d'.]+)\s+"
    r"est inscrite en faveur de la société transférante\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BUSINESS_OFFICES_WITH_HEADING = re.compile(
    r"^\[Die folgenden weiteren Adressen werden gelöscht:\]\s*"
    r"(?P<items>(?:\[gestrichen:\s*Weitere Geschäftsstelle:\s*[^\]]+\]\.?(?:\s*|$))+)$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BUSINESS_OFFICE_ITEM = re.compile(
    r"\[gestrichen:\s*Weitere Geschäftsstelle:\s*(?P<address>[^\]]+?)\]\.?(?:\s*|$)",
    re.I | re.UNICODE,
)
_FR_REMOVED_QUALIFIED_FACT = re.compile(
    r"^Nouveaux faits qualifiés:\s*\[biffé:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE | re.DOTALL,
)
_FR_REMOVED_QUALIFIED_FACT_AMOUNTS = re.compile(
    r"accepté pour le prix de CHF\s+(?P<accepted>[\d'.-]+)\s+payable par remise "
    r"de CHF\s+(?P<shares>[\d'.-]+)\s+en actions de la société et CHF\s+"
    r"(?P<debt>[\d'.-]+)\s+par reprise de la dette hypothécaire",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED_COMMA = re.compile(
    r"^Das Statutendatum lautet richtig:\s*(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"nicht\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_NAME_AND_IDENTIFIER_CHANGED_WITH_PLACE = re.compile(
    r"^Nouvelle raison sociale et numéro d['’]i(?:dent|fent)ification IDE/UID de "
    r"l['’]organe de révision\s+[\"“](?P<previous_name>.+?)[\"”]\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\),\s*à\s+(?P<place>[^:]+):\s*"
    r"[\"“](?P<name>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_PREVIOUS_PLACE_CORRECTED = re.compile(
    r"^Bei den Eingetragenen Personen neu oder mutierend wurde bei\s+"
    r"(?P<name>.+?)\s+der bisher Text nicht korrekt aufgeführt\.\s*"
    r"Korrekt sollte es lauten:\s*\[bisher:\s*in\s+(?P<previous_place>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés-gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*lesquels continuent à signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_DECISION_REVOKED = re.compile(
    r"^\[gestrichen:\s*Mit Verfügung des Handelsgerichts vom\s+"
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+wurde diese Gesellschaft mit "
    r"Wirkung ab dem\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<effective_time>\d{1,2}\.\d{2})\s+Uhr,\s*nach\s+"
    r"(?P<legal_basis>Art\.\s*731b OR)\s+aufgelöst und ihre Liquidation nach den "
    r"Vorschriften über den Konkurs angeordnet\.\]\.?\s*Mit Verfügung des "
    r"Handelsgerichts vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird der "
    r"Entscheid vom\s+(?P=original_date)\s+aufgehoben\.\s*Infolgedessen besteht "
    r"die Gesellschaft entsprechend den früheren Eintragungen weiter\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Conformemente all['’]attestazione di un "
    r"perito revisore abilitato,\s*dei crediti per un ammontare almeno equivalente "
    r"all['’]ammontare dello scoperto e del sovraindebitamento della società "
    r"assuntrice sono stati postergati\.\s*La società assuntrice detiene tutte le "
    r"azioni della società trasferente,\s*per cui la fusione avviene senza aumento "
    r"di capitale e senza attribuzione di azioni\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller1>[^,.;]+)\s+détient\s+"
    r"(?P<seller_count1>[\d']+)\s+parts de CHF\s+(?P<nominal1>[\d'.]+)\s+et "
    r"l['’]associé-gérant\s+(?P<seller2>[^,.;]+)\s+détient\s+"
    r"(?P<seller_count2>[\d']+)\s+parts de CHF\s+(?P<nominal2>[\d'.]+)\s+par "
    r"suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+chacun\.\s*Cessionnaire et nouvel "
    r"associé-gérant:\s*(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]),\s*"
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),?\.?$",
    re.I | re.UNICODE,
)
_DE_INCOMING_SPIN_OFF_SAME_OWNERS = re.compile(
    r"^Abspaltung:\s*Die Gesellschaft übernimmt von der\s+(?P<source>.+?),\s*"
    r"in\s+(?P<source_place>[^()]+?)\s*"
    r"\((?P<source_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+einen Teil des Vermögens\s*"
    r"\((?P<business_units>[^)]+)\)\.\s*Die Gesellschaft übernimmt dabei gemäss "
    r"Spaltungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Da dieselben Gesellschafter bzw\. Aktionäre "
    r"sämtliche Stammanteile, bzw\. Aktien der an der Spaltung beteiligten "
    r"Gesellschaften halten,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Zuteilung von Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


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
    clean_uid = uid.strip() if uid else None
    return Event(
        publication_id=publication_id,
        published_at=published_at,
        event_type=event_type,
        rule_id=rule_id,
        org_uid=org_uid,
        person_key=person_key(name=clean_name, place=clean_place, uid=clean_uid),
        plz=plz,
        canton=canton,
        role=role,
        signing=signing,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser113_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 113."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ORGANIZATION_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.organization_changed_named.v1",
            {
                "kind": "organization", "action": "changed",
                "organization": match.group("organization").strip(),
            },
        ))

    match = _DE_DELETION_BLOCKED_CANTONAL_AND_FEDERAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.deletion_blocked_cantonal_federal.v1",
            {
                "kind": "deletion_blocked",
                "tax_authority_consent_missing": True,
                "tax_authorities": ["cantonal", "federal"],
            },
        ))

    match = _FR_PROCURATION_ENDED_APPOINTED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.procuration_ended_appointed_administrator.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            extra={
                "action": "appointed", "previous_authority": "procuration",
                "previous_authority_ended": True, "domicile_changed": True,
            },
        ))

    match = _FR_COMMITTEE_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        member_chunks = re.split(
            r",\s*(?:et\s+)?(?=[^,]+,\s*(?:du|de la|des|de|d['’])\s+)",
            match.group("members"),
        )
        members = []
        for chunk in member_chunks:
            item = _FR_COMMITTEE_MEMBER_ITEM.fullmatch(chunk.strip())
            if item:
                members.append(item)
        if members and len(members) == len(member_chunks):
            consume(match)
            for item in members:
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.committee_members_without_signature.v1",
                    item.group("name"), place=item.group("place"), role="membre du comité",
                    extra={
                        "action": "appointed", "heimat": item.group("origin").strip(),
                        "without_signature": True,
                    },
                ))

    match = _FR_AUDITOR_RENAMED_AND_MOVED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_renamed_and_moved.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="organe de révision",
            extra={
                "action": "name_and_domicile_changed",
                "previous": match.group("previous_name").strip(),
                "uid": match.group("uid"),
            },
        ))

    match = _FR_ASSET_TRANSFER_RECEIVABLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_receivable.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF", "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "receivable",
            },
        ))

    match = _DE_REMOVED_BUSINESS_OFFICES_WITH_HEADING.search(leftover)
    if match:
        items = list(_DE_REMOVED_BUSINESS_OFFICE_ITEM.finditer(match.group("items")))
        if items:
            consume(match)
            for item in items:
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", "de.text.business_offices_removed_with_heading.v1",
                    {
                        "kind": "additional_business_office", "action": "removed",
                        "address": item.group("address").strip().rstrip("."),
                    },
                ))

    match = _FR_REMOVED_QUALIFIED_FACT.search(leftover)
    if match:
        consume(match)
        previous = re.sub(r"\s+", " ", match.group("previous")).strip()
        payload = {
            "kind": "contribution_in_kind", "action": "removed",
            "previous": previous,
        }
        amounts = _FR_REMOVED_QUALIFIED_FACT_AMOUNTS.search(previous)
        if amounts:
            payload.update({
                "accepted_value": amounts.group("accepted").rstrip(".-"),
                "consideration_in_shares": amounts.group("shares").rstrip(".-"),
                "mortgage_debt_assumed": amounts.group("debt").rstrip(".-"),
                "currency": "CHF",
            })
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.qualified_fact_removed_legacy.v1", payload,
        ))

    match = _DE_STATUTES_DATE_CORRECTED_COMMA.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_corrected_comma.v1",
            {
                "action": "date_corrected", "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_AUDITOR_NAME_AND_IDENTIFIER_CHANGED_WITH_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_name_identifier_changed_with_place.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role="organe de révision",
            extra={
                "action": "name_and_identifier_changed",
                "previous": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
                "uid": match.group("uid"),
            },
        ))

    match = _DE_PERSON_PREVIOUS_PLACE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.previous_place_corrected.v1",
            match.group("name"),
            extra={
                "action": "previous_entry_corrected",
                "previous_place": match.group("previous_place").strip(),
            },
        ))

    match = _FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.two_managers_appointed_liquidators.v1",
                match.group(group), role="associé-gérant et liquidateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ))

    match = _DE_DISSOLUTION_DECISION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.dissolution_decision_revoked_company_continues.v1",
            {
                "kind": "dissolution_revoked", "action": "reinstated",
                "decision_date": _iso_date(match.group("decision_date")),
                "original_date": _iso_date(match.group("original_date")),
                "original_effective_date": _iso_date(match.group("effective_date")),
                "original_effective_time": match.group("effective_time").replace(".", ":"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "continues_under_previous_entries": True,
            },
        ))

    match = _IT_MERGER_DEFICIT_SUBORDINATED_CLAIMS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_deficit_subordinated_claims.v1",
            {
                "kind": "merger", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "deficit_coverage": "subordinated_claims",
                "same_owner": True, "capital_increase": False,
                "share_allocation": False,
            },
        ))

    match = _FR_TWO_MANAGERS_TRANSFER_TO_NEW_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_transfer_to_new_manager.v1"
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé-gérant",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group(f"seller_count{index}")),
                    "share_nominal": match.group(f"nominal{index}"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé-gérant",
            extra={
                "action": "appointed_and_shares_received", "new_associate": True,
                "counterparties": [
                    match.group("seller1").strip(), match.group("seller2").strip(),
                ],
                "shares_received": transferred * 2,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                "heimat": match.group("origin").strip(),
                "country_code": match.group("country"),
            },
        ))

    match = _DE_INCOMING_SPIN_OFF_SAME_OWNERS.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.spin_off_acquisition_same_owners.v1",
            {
                "kind": "spin_off_acquisition", "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "source_uid": match.group("source_uid"),
                "business_units": match.group("business_units").strip(),
                "date": _iso_date(match.group("date")), "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "same_owners": True, "capital_increase": False,
                "share_allocation": False, "share_kind": "Stammanteile",
            },
        ))

    return events, leftover.strip(" .,;")
