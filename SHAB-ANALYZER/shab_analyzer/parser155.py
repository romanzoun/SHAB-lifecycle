from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_STATUTES_CHANGE_DATE_CORRECTED = re.compile(
    r"^Das Statutenänderungsdatum lautet korrekt\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)(?:\s*\((?P<place_canton>[A-Z]{2})\))?\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_BRANCH_REGISTER_NAMED = re.compile(
    r"^\[bisher:\s*(?P<place>[^()\]]+?)\s*"
    r"\(HR\s+(?P<register>[^)\]]+)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_CONTRIBUTION_AND_ACQUISITION_CORRECTED = re.compile(
    r"^Rectification:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\.\s*"
    r"(?P<notice_id>\d+)\)\s+est modifiée dans ce sens:\s*"
    r"Apport en nature et reprise de biens:\s*Selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*est fait apport à la société de\s+"
    r"(?P<assets>.+?)\s+pour la valeur de CHF\s+(?P<value>[\d'.]+)\s+et accepté "
    r"pour ce prix\.\s*En contrepartie de cet apport et d['’]un montant de CHF\s+"
    r"(?P<cash>[\d'.]+)\s+en espèces,\s*a été remis\s+"
    r"(?P<shares>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+aux apporteurs\.\s*"
    r"Le solde de CHF\s+(?P<credit>[\d'.]+)\s+correspond à une créance en leur "
    r"faveur\s*\(et non pas Apport en nature et reprise de biens:\s*Selon contrat du\s+"
    r"(?P=agreement_date),\s*est fait apport à la société de\s+(?P=assets)\s+"
    r"pour la valeur de CHF\s+(?P=value)\s+et accepté pour ce prix\.\s*"
    r"En contrepartie de cet apport et d['’]un montant de CHF\s+(?P=cash)\s+"
    r"en espèces,\s*a été remis\s+(?P=shares)\s+parts de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+aux apporteurs\.\s*Le solde de CHF\s+"
    r"(?P=credit)\s+correspond à une créance en leur faveur\.\)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ADMINISTRATOR_MISSPELLED = re.compile(
    r"^Nouvel administateur\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:(?:du|des|de la|de)\s+|d['’]\s*)(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_BRANCHES_DOTTED = re.compile(
    r"^Zweigniederlassungen neu:\s*(?P<items>"
    r"[^().;]+\s*\(CHE-\d{3}\.\d{3}\.\d{3}\)"
    r"(?:\s*\.\s*[^().;]+\s*\(CHE-\d{3}\.\d{3}\.\d{3}\))+"
    r")\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ITEM = re.compile(
    r"(?P<place>[^().;]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_PROXY = re.compile(
    r"^L['’]associé-gérant et président\s+(?P<seller1>[^,.;]+?)\s+et "
    r"l['’]associé-gérant\s+(?P<seller2>[^,.;]+?)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+au fondé de pouvoir\s+(?P<buyer>[^,.;]+),\s*"
    r"maintenant à\s+(?P<place>[^,.;]+?)(?:\s*\((?P<place_canton>[A-Z]{2})\))?,\s*"
    r"nouvel associé,\s*titulaire de\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1)\s+et\s+(?P=seller2)\s+"
    r"restent titulaires de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+chacun\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_SOLE_SHAREHOLDER = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und "
    r"Fremdkapital von CHF\s+(?P<liabilities>[\d'.]+)\s+der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Da die übernehmende Gesellschaft "
    r"einzige Gesellschafterin der übertragenden Gesellschaft ist,\s*findet weder "
    r"eine Kapitalerhöhung noch eine Zuteilung von Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CORRECTED_WITH_ENTRY = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est en réalité originaire\s+"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_TWO_DIFFERENT_SIGNINGS = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"lequel continue à signer individuellement\s+et\s+"
    r"(?P<member>[^,.;]+),\s*lequel continue à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_MOVED_APPOINTED_LIQUIDATOR = re.compile(
    r"^L['’]administrateur\s+(?P<name>[^,.;]+),\s*maintenant à\s+"
    r"(?P<place>[^,.;]+),\s*est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_FEMALE_MANAGER_TRANSFER_NEW_FEMALE_MANAGER = re.compile(
    r"^L['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*nouvelle associée-gérante "
    r"pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_ASSOCIATE_SAME_ORIGIN_AND_PLACE = re.compile(
    r"^Nouvelle associée:\s*(?P<name>[^,.;]+),\s*de et à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOREIGN_BOARD_MEMBERS_SHARED_DETAILS = re.compile(
    r"^(?P<president>[^,.;]+),\s*président,\s*et\s+(?P<member>[^,.;]+),\s*"
    r"tous deux de\s+(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[^,.;]+),\s*sont membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_FIVE_CHANGES = re.compile(
    r"^Administration:\s*(?P<name1>[^,.;]+),\s*jusqu['’]ici vice-président,\s*"
    r"nommé président,\s*(?P<name2>[^,.;]+),\s*nommé secrétaire,\s*"
    r"(?P<name3>[^,.;]+),\s*maintenant domicilié à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<name4>[^,.;]+),\s*jusqu['’]ici président,\s*et\s+"
    r"(?P<name5>[^,.;]+),\s*lesquels continuent de signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_ALL_SHARES_TO_CORPORATE_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+),\s*maintenant originaire\s+"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*a cédé ses\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
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


def extract_parser155_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 155."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_STATUTES_CHANGE_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.statutes_change_date_corrected.v1",
            {
                "kind": "statutes_change_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
            },
        ))

    match = _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.company_asset_transfer_with_inventory.v1",
            {
                "source_kind": "gesellschaft",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_canton": match.group("place_canton"),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
            },
        ))

    match = _DE_PREVIOUS_BRANCH_REGISTER_NAMED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.previous_branch_register_named.v1",
            {
                "action": "previous_registration_recorded",
                "previous_place": match.group("place").strip(),
                "previous_register": match.group("register").strip(),
            },
        ))

    match = _FR_CONTRIBUTION_AND_ACQUISITION_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "fr.text.contribution_and_acquisition_nominal_corrected.v1",
            {
                "kind": "contribution_in_kind_and_asset_acquisition",
                "action": "share_nominal_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets").strip(),
                "contributed_value": match.group("value"),
                "cash_contribution": match.group("cash"),
                "shares_count": _count(match.group("shares")),
                "share_nominal": match.group("nominal"),
                "previous_incorrect_share_nominal": match.group("previous_nominal"),
                "credit_balance": match.group("credit"), "currency": "CHF",
            },
        ))

    match = _FR_NEW_ADMINISTRATOR_MISSPELLED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_administrator_misspelled.v1",
            match.group("name"), place=match.group("place"), role="administrateur",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "published_role": "administateur",
            },
        ))

    match = _DE_NEW_BRANCHES_DOTTED.search(leftover)
    if match:
        items = list(_DE_BRANCH_ITEM.finditer(match.group("items")))
        if len(items) >= 2:
            consume(match)
            for item in items:
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "branch_changed", "de.text.new_branches_dotted.v1",
                    {
                        "action": "added", "place": item.group("place").strip(),
                        "branch_uid": item.group("uid"),
                    },
                ))

    match = _FR_TWO_MANAGERS_TRANSFER_TO_PROXY.search(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            before == remaining + transferred
            and buyer_count == 2 * transferred
            and len({
                match.group("nominal"), match.group("buyer_nominal"),
                match.group("remaining_nominal"),
            }) == 1
        ):
            consume(match)
            rule_id = "fr.persons.two_managers_transfer_to_proxy.v1"
            buyer = match.group("buyer").strip()
            for index, role in ((1, "associé-gérant président"), (2, "associé-gérant")):
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"seller{index}"), role=role,
                    extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_transferred": transferred,
                        "shares_count": remaining, "share_nominal": match.group("nominal"),
                        "currency": "CHF",
                    },
                ))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé et fondé de pouvoir",
                extra={
                    "action": "shares_received", "new_associate": True,
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    "place_canton": match.group("place_canton"),
                    "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip(),
                    ],
                },
            ))

    match = _DE_MERGER_SOLE_SHAREHOLDER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_sole_shareholder_social_shares.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("place").strip(),
                "absorbed_uid": match.group("uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "liabilities_kind": "third_party_capital",
                "sole_shareholder": True, "capital_increase": False,
                "share_allocation": False, "transferred_interest_kind": "Stammanteile",
            },
        ))

    match = _FR_ORIGIN_CORRECTED_WITH_ENTRY.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.origin_corrected_with_entry.v1",
            match.group("name"),
            extra={
                "action": "origin_corrected", "heimat": match.group("origin").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_ADMINISTRATION_TWO_DIFFERENT_SIGNINGS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_two_different_signings.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"), role="président",
                signing="Einzelunterschrift",
                extra={"action": "appointed_president", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "confirmed", "signing_continues": True},
            ),
        ])

    match = _FR_ADMINISTRATOR_MOVED_APPOINTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_moved_appointed_liquidator.v1",
            match.group("name"), place=match.group("place"),
            role="administrateur et liquidateur",
            extra={
                "action": "domicile_changed_and_appointed_liquidator",
                "previous_role": "administrateur", "domicile_changed": True,
            },
        ))

    match = _FR_FEMALE_MANAGER_TRANSFER_NEW_FEMALE_MANAGER.search(leftover)
    if match:
        seller_count = _count(match.group("seller_count"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if (
            transferred == buyer_count
            and len({
                match.group("nominal"), match.group("transfer_nominal"),
                match.group("buyer_nominal"),
            }) == 1
        ):
            consume(match)
            rule_id = "fr.persons.female_manager_transfer_new_female_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associée-gérante",
                    extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred, "shares_count": seller_count,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associée-gérante",
                    extra={
                        "action": "shares_received_and_appointed_manager",
                        "counterparty": seller, "new_associate": True,
                        "shares_received": buyer_count, "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                        "origin": match.group("origin").strip(),
                        "country": match.group("country").upper(),
                    },
                ),
            ])

    match = _FR_NEW_ASSOCIATE_SAME_ORIGIN_AND_PLACE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_associate_same_origin_and_place.v1",
            match.group("name"), place=match.group("place"), role="associée",
            extra={
                "action": "appointed", "new_associate": True,
                "heimat": match.group("place").strip(),
            },
        ))

    match = _FR_TWO_FOREIGN_BOARD_MEMBERS_SHARED_DETAILS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_foreign_board_members_shared_details.v1"
        common = {
            "action": "appointed", "origin": match.group("origin").strip(),
            "country": match.group("country").strip(),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"),
                role="président du conseil d'administration", extra=common,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"),
                role="membre du conseil d'administration", extra=common,
            ),
        ])

    match = _FR_ADMINISTRATION_FIVE_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_five_changes.v1"
        signing = "Kollektivunterschrift zu zweien"
        details = (
            ("name1", "président", None, "appointed_president", "vice-président"),
            ("name2", "secrétaire", None, "appointed_secretary", None),
            ("name3", "administrateur", match.group("place"), "domicile_changed", None),
            ("name4", "administrateur", None, "role_changed", "président"),
            ("name5", "administrateur", None, "confirmed", None),
        )
        for group, role, place, action, previous_role in details:
            extra = {"action": action, "signing_continues": True}
            if previous_role:
                extra["previous_role"] = previous_role
            if place:
                extra["domicile_changed"] = True
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), place=place,
                role=role, signing=signing, extra=extra,
            ))

    match = _FR_MANAGER_ALL_SHARES_TO_CORPORATE_ASSOCIATE.search(leftover)
    if match:
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        if transferred == buyer_count and match.group("nominal") == match.group("buyer_nominal"):
            consume(match)
            rule_id = "fr.persons.manager_all_shares_to_corporate_associate.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="gérant",
                    extra={
                        "action": "all_shares_transferred", "counterparty": buyer,
                        "shares_before": transferred, "shares_transferred": transferred,
                        "shares_count": 0, "share_nominal": match.group("nominal"),
                        "currency": "CHF", "heimat": match.group("origin").strip(),
                        "origin_changed": True, "previous_role": "associé-gérant",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    uid=match.group("uid"), role="associée",
                    extra={
                        "action": "shares_received", "counterparty": seller,
                        "new_associate": True, "shares_received": buyer_count,
                        "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    },
                ),
            ])

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
