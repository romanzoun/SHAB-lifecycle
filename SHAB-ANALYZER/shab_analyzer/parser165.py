from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_CORPORATE_ASSOCIATE_TRANSFER_AND_PRESIDENT = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_registry>[^)]+)\)\s+associée,\s*"
    r"désormais pour\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*"
    r"gérant-associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*"
    r"(?:avec signature individuelle\.\s*)?Le gérant\s+"
    r"(?P<president>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<president_place>[^,.;]+),\s*(?P<president_country>[A-Z]{2,3})\s+"
    r"est désormais président\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_BOARD_PRESIDENT = re.compile(
    r"^Neu eingetragene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role1>Verwaltungsratsmitglied),\s*(?P<role2>Präsident),\s*"
    r"(?P<signing>Einzelunterschrift)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_SIGN_INDIVIDUALLY = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>président),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>secrétaire),\s*membres du conseil "
    r"d['’]administration,\s*signent désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_RETROACTIVE_SINCE = re.compile(
    r"^\[seit\s+(?P<month>Januar|Februar|März|April|Mai|Juni|Juli|August|"
    r"September|Oktober|November|Dezember)\s+(?P<year>\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_INCREASE_WITH_HISTORY = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des bedingten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\s*"
    r"\[bisher:\s*Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eine Erhöhung des bedingten "
    r"Kapitals gemäss näherer Umschreibung in den Statuten beschlossen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_MANAGER_PRESIDENCY_ENDED = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici président,\s*reste seul gérant et "
    r"continue de signer individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_PERSON_AND_ADDRESS = re.compile(
    r"^Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*Die Liquidation wird unter "
    r"der Firma:\s*(?P<liquidation_name>.+?)\s+durchgeführt\.\s*"
    r"Eingetragene Person geändert:\s*(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role1>Gesellschafter),\s*(?P<previous_count>[\d']+)\s+"
    r"Stammanteil(?:e)? zu CHF\s+(?P<previous_nominal>[\d'.]+),\s*"
    r"(?P<previous_role2>Geschäftsführer),\s*(?P<previous_signing>Einzelunterschrift),\s*"
    r"neu\s+(?P<role1>Gesellschafter),\s*(?P<count>[\d']+)\s+"
    r"Stammanteil(?:e)? zu CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<role2>Geschäftsführer),\s*(?P<role3>Liquidator),\s*"
    r"(?P<signing>Einzelunterschrift)\.\s*Liquidationsadresse:\s*"
    r"(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:No|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens "
    r"qu['’]une administratrice porte le nom de\s+(?P<name>[^()]+?)\s*"
    r"\(et non pas de\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_CONTRIBUTION_IN_KIND_HISTORY_FRAGMENT = re.compile(
    r'^eingetragenen Einzelunternehmens\s+["“](?P<source>.+?)["”],\s*in\s+'
    r"(?P<source_place>[^,.;]+),\s*gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d']+(?:\.\d+|\.--)?)[ ]+und Passiven\s+\(Fremdkapital\)\s+"
    r"von CHF\s+(?P<liabilities>[\d']+(?:\.\d+|\.--)?),\s*wofür\s+"
    r"(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien) zu CHF\s+"
    r"(?P<nominal>[\d']+(?:\.\d+|\.--)?)[ ]+ausgegeben werden\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_BUSINESS_ASSET_TRANSFER = re.compile(
    r"\s*Vermögensübertragung:\s*Die Gesellschaft\s*überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+den Geschäftsbereich\s+"
    r"(?P<business_area>.+?)\s+mit Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+"
    r"und Fremdkapital von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+?)\.\s*Gegenleistung:\s*Forderung von CHF\s+"
    r"(?P<claim>[\d'.]+)\.?(?=\s*(?:Vermögensübertragung:|$))",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS = re.compile(
    r"^(?P<members>.+?),\s*sont membres du conseil d['’]administration"
    r"(?:,?\s*avec signature collective à deux)?"
    r"(?:,?\s*(?P<restriction>avec le président ou le directeur))?\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_ITEM = re.compile(
    r"(?:,\s*)?(?:et\s+)?(?P<name>[^,]+),\s*"
    r"(?:(?:de et à)\s+(?P<same_place>[^,]+)|"
    r"(?:(?:de la|de l['’]|du|des|de|d['’])\s*)"
    r"(?P<origin>[^,]+),\s*à\s+(?P<place>[^,]+))",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED = re.compile(
    r"^Mit Datum vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde unter "
    r"TR-Nr\.\s*(?P<entry>[\d']+)\s+als Datum der Statutenänderung irrtümlich\s+"
    r"(?P<wrong_date>\d{2}\.\d{2}\.\d{4})\s+eingetragen\.\s*Richtig wäre:\s*"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ADMINISTRATORS_MOVED_PRESIDENCY_CHANGED = re.compile(
    r"^Les administrateurs\s+(?P<new_president>[^,.;]+),\s*maintenant domicilié "
    r"à\s+(?P<new_place>[^,.;]+),\s*nommé président et\s+"
    r"(?P<old_president>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<old_place>[^,.;]+),\s*jusqu['’]ici président,\s*continuent à signer "
    r"collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_MISSING_DATE = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die mit Beschluss vom\s+"
    r"eingeführte Bestimmung betreffend bedingter Kapitalerhöhung gemäss näherer "
    r"Umschreibung in den Statuten geändert\.\s*\[bisher:\s*Die Gesellschaft hat "
    r"mit Beschluss vom\s+(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"die mit Beschluss vom\s+(?P<introduction_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"eingeführte Bestimmung betreffend bedingter Erhöhung des "
    r"Partizipationskapitals gemäss näherer Umschreibung in den Statuten geändert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_ROLE_CHANGES_AND_NEW_MEMBERS = re.compile(
    r"^Les membres du comité\s+(?P<old_president>[^,.;]+),\s*jusqu['’]ici "
    r"président,\s*et\s+(?P<old_vice>[^,.;]+),\s*jusqu['’]ici vice-président,\s*"
    r"continuent à signer collective à deux\.\s*(?P<president>[^,.;]+),\s*"
    r"de\s+(?P<president_origin>[^,.;]+),\s*à\s+(?P<president_place>[^,.;]+),\s*"
    r"(?P<president_country>[A-Z]),\s*présidente,\s*et\s+"
    r"(?P<vice>[^,.;]+),\s*de\s+(?P<vice_origin>[^,.;]+),\s*à\s+"
    r"(?P<vice_place>[^,.;]+),\s*vice-président,\s*sont membres du comité "
    r"signature collective à deux\.?$",
    re.I | re.UNICODE,
)


_DE_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


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


def _french_board_members(raw: str) -> list[dict[str, str | None]] | None:
    members: list[dict[str, str | None]] = []
    position = 0
    while position < len(raw):
        match = _FR_BOARD_MEMBER_ITEM.match(raw, position)
        if not match:
            return None
        same_place = match.group("same_place")
        members.append({
            "name": match.group("name").strip(),
            "origin": (same_place or match.group("origin")).strip(),
            "place": (same_place or match.group("place")).strip(),
        })
        position = match.end()
    return members if len(members) >= 2 else None


def _business_asset_transfers(raw: str) -> list[re.Match[str]] | None:
    matches: list[re.Match[str]] = []
    position = 0
    while position < len(raw):
        match = _DE_BUSINESS_ASSET_TRANSFER.match(raw, position)
        if not match:
            return None
        matches.append(match)
        position = match.end()
    return matches or None


def extract_parser165_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 165."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    events: list[Event] = []

    match = _FR_CORPORATE_ASSOCIATE_TRANSFER_AND_PRESIDENT.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.corporate_associate_transfer_and_president.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id,
                {
                    "kind": "shareholding", "action": "shareholding_changed",
                    "name": match.group("seller").strip(),
                    "registry_id": match.group("seller_registry").strip(),
                    "shares_count": _count(match.group("seller_count")),
                    "shares_nominal": match.group("nominal"), "currency": "CHF",
                    "transferred_shares": _count(match.group("transferred")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="gérant-associé",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shareholding_changed",
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"),
                    "shares_count": _count(match.group("buyer_count")),
                    "shares_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="gérant président",
                extra={
                    "action": "appointed_president_and_domicile_changed",
                    "country": match.group("president_country"),
                },
            ),
        ])
        return events, ""

    match = _DE_NEW_BOARD_PRESIDENT.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.new_board_president.v1",
            match.group("name"), place=match.group("place"),
            role=f'{match.group("role1")}, {match.group("role2")}',
            signing=match.group("signing"), extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        ))
        return events, ""

    match = _FR_TWO_BOARD_MEMBERS_SIGN_INDIVIDUALLY.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_board_members_sign_individually.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                role=f'membre du conseil d\'administration, {match.group(f"role{index}")}',
                signing="Einzelunterschrift", extra={"action": "signing_changed"},
            ))
        return events, ""

    match = _DE_BRANCH_RETROACTIVE_SINCE.fullmatch(leftover)
    if match:
        month = _DE_MONTHS[match.group("month").casefold()]
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_retroactive_since.v1",
            {
                "action": "effective_date_noted",
                "effective_since": f'{int(match.group("year")):04d}-{month:02d}',
            },
        ))
        return events, ""

    match = _DE_CONDITIONAL_CAPITAL_INCREASE_WITH_HISTORY.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_increase_with_history.v1",
            {
                "kind": "conditional_capital", "action": "increase_resolved",
                "decision_date": _iso_date(match.group("decision_date")),
                "previous_decision_date": _iso_date(match.group("previous_date")),
                "details_in_statutes": True,
            },
        ))
        return events, ""

    match = _FR_SOLE_MANAGER_PRESIDENCY_ENDED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_manager_presidency_ended.v1",
            match.group("name"), role="seul gérant", signing="Einzelunterschrift",
            extra={
                "action": "presidency_ended", "previous_role": "président",
                "management_continues": True, "signing_continues": True,
            },
        ))
        return events, ""

    match = _DE_DISSOLUTION_PERSON_AND_ADDRESS.fullmatch(leftover)
    if match:
        rule_id = "de.text.dissolution_person_and_address.v1"
        roles = ", ".join(match.group(key) for key in ("role1", "role2", "role3"))
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "dissolution", "action": "dissolved",
                    "date": _iso_date(match.group("date")),
                    "deciding_body": "Gesellschafterversammlung",
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role=roles, signing=match.group("signing"), extra={
                    "action": "appointed_liquidator",
                    "previous_role": ", ".join(
                        match.group(key) for key in ("previous_role1", "previous_role2")
                    ),
                    "shares_count": _count(match.group("count")),
                    "shares_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "kind": "liquidation_address", "action": "changed",
                    "to": match.group("address").strip(),
                },
            ),
        ])
        return events, ""

    match = _FR_ADMINISTRATOR_NAME_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_name_corrected.v1",
            match.group("name"), role="administratrice", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))
        return events, ""

    match = _DE_REMOVED_CONTRIBUTION_IN_KIND_HISTORY_FRAGMENT.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.removed_contribution_in_kind_history_fragment.v1",
            {
                "kind": "qualified_fact_contribution_in_kind", "action": "removed",
                "source_kind": "sole_proprietorship",
                "source": match.group("source").strip(),
                "source_place": match.group("source_place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "consideration_shares": {
                    "count": _count(match.group("count")),
                    "kind": match.group("share_kind"),
                    "nominal": match.group("nominal"), "currency": "CHF",
                },
            },
        ))
        return events, ""

    transfer_matches = _business_asset_transfers(leftover)
    if transfer_matches:
        rule_id = "de.text.business_area_asset_transfers.v1"
        for transfer in transfer_matches:
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", rule_id,
                {
                    "source_kind": "company",
                    "business_area": transfer.group("business_area").strip(),
                    "agreement_date": _iso_date(transfer.group("agreement_date")),
                    "inventory_date": _iso_date(transfer.group("inventory_date")),
                    "assets": transfer.group("assets"),
                    "liabilities": transfer.group("liabilities"), "currency": "CHF",
                    "recipient": transfer.group("recipient").strip(),
                    "recipient_uid": transfer.group("uid"),
                    "recipient_place": transfer.group("place").strip(),
                    "consideration_claim": transfer.group("claim").rstrip("."),
                },
            ))
        return events, ""

    match = _FR_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        members = _french_board_members(match.group("members"))
        if members:
            rule_id = "fr.persons.board_members_list.v1"
            restriction = match.group("restriction")
            for member in members:
                extra: dict = {
                    "action": "appointed", "origin": member["origin"],
                }
                if restriction:
                    extra["co_signs_with_roles"] = ["président", "directeur"]
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, member["name"] or "",
                    place=member["place"], role="membre du conseil d'administration",
                    signing="Kollektivunterschrift zu zweien", extra=extra,
                ))
            return events, ""

    match = _DE_STATUTES_DATE_CORRECTED.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.statutes_date_corrected_with_entry.v1",
            {
                "kind": "statutes_date", "action": "date_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "previous_date": _iso_date(match.group("wrong_date")),
                "date": _iso_date(match.group("date")),
            },
        ))
        return events, ""

    match = _FR_TWO_ADMINISTRATORS_MOVED_PRESIDENCY_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_administrators_moved_presidency_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("new_president"),
                place=match.group("new_place"), role="administrateur président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_domicile_changed",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("old_president"),
                place=match.group("old_place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended_and_domicile_changed",
                    "previous_role": "président", "signing_continues": True,
                },
            ),
        ])
        return events, ""

    match = _DE_CONDITIONAL_CAPITAL_CLAUSE_CHANGED_MISSING_DATE.fullmatch(leftover)
    if match:
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.conditional_capital_clause_changed_missing_date.v1",
            {
                "kind": "conditional_capital_clause", "action": "modified",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date_missing_in_source": True,
                "previous_decision_date": _iso_date(
                    match.group("previous_decision_date")
                ),
                "previous_introduction_date": _iso_date(match.group("introduction_date")),
                "previous_kind": "conditional_participation_capital_clause",
                "details_in_statutes": True,
            },
        ))
        return events, ""

    match = _FR_COMMITTEE_ROLE_CHANGES_AND_NEW_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.committee_role_changes_and_new_members.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("old_president"),
                role="membre du comité", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("old_vice"),
                role="membre du comité", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "vice_presidency_ended",
                    "previous_role": "vice-président", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="présidente du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("president_origin"),
                    "country": match.group("president_country"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                place=match.group("vice_place"), role="vice-président du comité",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("vice_origin"),
                },
            ),
        ])
        return events, ""

    return [], text
