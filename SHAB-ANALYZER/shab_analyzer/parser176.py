from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_MERGER_ALL_SHARES = re.compile(
    r"^Fusion:\s*reprise des actifs et passifs de\s+(?P<absorbed_name>.+?)\s*"
    r"\((?P<absorbed_uid>CHE[.-]\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<absorbed_place>[^,.;]+),\s*selon contrat de fusion du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+et bilan au\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*présentant des actifs de CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers de CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*soit un actif net de CHF\s+"
    r"(?P<net_assets>[\d'.]+)\.\s*La société reprenante détenant l['’]ensemble "
    r"du capital-actions de la société transférante,\s*la fusion ne donne pas "
    r"lieu à une augmentation de capital,\s*ni à une attribution d['’]actions\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>.+?)\s+détient désormais\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+"
    r"par suite de cession de\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<transfer_nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"de et à\s+(?P<place>[^,.;]+),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_THREE_SIGNERS = re.compile(
    r"^Nouveaux membres du conseil de fondation avec le président,\s*le "
    r"secrétaire ou le trésorier:\s*(?P<name1>[^,.;]+),\s*de\s+"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_DELETED_WITH_HISTORY = re.compile(
    r"^\[Folgende Geschäftsstelle wird im Handelsregister gelöscht:\]\s*"
    r"\[gestrichen:\s*Geschäftsstelle:\s*(?P<branch>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^\].]+)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_DIRECTORS_SIGNING_UNRESTRICTED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<role1>directeur général)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*(?P<role2>directeur),\s*signent désormais "
    r"collectivement à deux sans autre restriction;\s*leurs pouvoirs sont "
    r"modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_SIGNING_DIRECTOR = re.compile(
    r"^Signature individuelle de\s+(?P<name>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*(?P<role>directeur)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_SUCCESSOR_DELETION_SPACED_UID = re.compile(
    r"^Aktiven und Passiven\s*\(Fremdkapital\)\s+gehen infolge Fusion auf die\s+"
    r"(?P<successor>.+?),\s*in\s+(?P<place>[^(),.;]+)\s*"
    r"\((?P<uid>CHE-\s*\d{3}\.\d{3}\.\d{3})\),\s*über\.\s*"
    r"Die Gesellschaft wird gelöscht\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBER_WITH_AU = re.compile(
    r"^(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*au\s+"
    r"(?P<place>[^,.;]+),\s*est membre du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_AND_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"définitif de\s+(?P<duration>\d+)\s+mois,\s*soit jusqu['’]au\s+"
    r"(?P<until>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*est désigné commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_CORRECTED_FROM_PROCURATION = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est r[ée]ctifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+a en réalité une signature collective à deux et "
    r"non pas une procuration collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_MERGER_CAPITAL_AMOUNT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"montant de l['’]augmentation du capital-actions,\s*par suite de fusion,\s*"
    r"s['’]élève à CHF\s+(?P<amount>[\d'.]+)\s*"
    r"\(et non à CHF\s+(?P<previous_amount>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\./\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+"
    r"(?P<place>[^.]+)\.\s*Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_CORRECTED_LIQUIDATOR_ADDRESS = re.compile(
    r"^Die Gesellschaft wird gemäss Beschluss der Gesellschafterversammlung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+aufgelöst\.\s*Die Liquidation wird unter "
    r"der Firma:\s*(?P<liquidation_name>.+?)\s+durchgeführt\.\s*"
    r"Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"korrekterweise\s+(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role1>Gesellschafterin),\s*(?P<previous_count>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<previous_nominal>[\d'.]+),\s*"
    r"(?P<previous_role2>Geschäftsführerin),\s*(?P<previous_signing>Einzelunterschrift),\s*"
    r"neu\s+(?P<role1>Gesellschafterin),\s*(?P<count>[\d']+)\s+"
    r"Stammanteile zu CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<role2>Geschäftsführerin),\s*(?P<role3>Liquidatorin),\s*"
    r"(?P<signing>Einzelunterschrift)\.\s*Liquidationsadresse:\s*"
    r"(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_FOREIGN_NEW_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé sans signature,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:no|n°)\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]administrateur-président se nomme\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPLEX_BOARD_CHANGES = re.compile(
    r"^(?P<president>[^,.;]+),\s*maintenant originaire de et domicilié à\s+"
    r"(?P<president_place>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<previous_president>[^,.;]+),\s*jusqu['’]ici président,\s*tous deux "
    r"membres du conseil d['’]administration,\s*continuent de signer "
    r"collectivement à deux,\s*mais désormais sauf entre eux\.\s*"
    r"(?P<name3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<name4>[^,.;]+),\s*à\s+(?P<place4>[^,.;]+),\s*tous deux de\s+"
    r"(?P<origin34>[^,.;]+),\s*(?P<name5>[^,.;]+),\s*et\s+"
    r"(?P<name6>[^,.;]+),\s*tous deux de\s+(?P<origin56>[^,.;]+),\s*à\s+"
    r"(?P<place56>[^,.;]+),\s*sont membres du conseil d['’]administration\.?\s*"
    r"(?P<name7>[^,.;]+),\s*de\s+(?P<origin7>[^,.;]+),\s*à\s+"
    r"(?P<place7>[^,.;]+),\s*et\s+(?P<name8>[^,.;]+),\s*de\s+"
    r"(?P<origin8>[^,.;]+),\s*à\s+(?P<place8>[^,.;]+),\s*sont membres du "
    r"conseil d['’]administration;\s*ils n['’]exercent pas la signature sociale\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1").split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _uid(raw: str) -> str:
    return raw.replace("CHE.", "CHE-").replace("CHE- ", "CHE-")


def _dual_date(raw: str) -> list[str]:
    first_day, second = raw.split("./", 1)
    second_date = _iso_date(second)
    return [f"{second_date[:8]}{int(first_day):02d}", second_date]


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


def extract_parser176_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 176."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_MERGER_ALL_SHARES.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("net_assets"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "fr.text.merger_all_shares_net_assets.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_uid": _uid(match.group("absorbed_uid")),
                "absorbed_place": match.group("absorbed_place").strip(),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "net_assets": match.group("net_assets"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF", "acquirer_owns_all_shares": True,
                "capital_increase": False, "share_allocation": False,
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_ASSOCIATE.fullmatch(leftover)
    if match and (
        _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("transfer_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_transfer_to_new_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller,
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "origin": match.group("place").strip(), "new_associate": True,
                },
            ),
        ], ""

    match = _FR_TWO_FOUNDATION_MEMBERS_THREE_SIGNERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_three_signer_options.v1"
        events = []
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "required_with": ["président", "secrétaire", "trésorier"],
                },
            ))
        return events, ""

    match = _DE_BRANCH_DELETED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_deleted_with_history.v1", {
                "action": "deleted", "branch": match.group("branch").strip(),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(), "previous_entry_removed": True,
            },
        )], ""

    match = _FR_TWO_DIRECTORS_SIGNING_UNRESTRICTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_directors_signing_unrestricted.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_changed", "restriction": None,
                    "without_other_restriction": True,
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_INDIVIDUAL_SIGNING_DIRECTOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.individual_signing_director.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            signing="Einzelunterschrift", extra={
                "action": "signing_granted", "origin": match.group("origin").strip(),
                "country": match.group("country"),
            },
        )], ""

    match = _DE_MERGER_SUCCESSOR_DELETION_SPACED_UID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_successor_deletion_spaced_uid.v1", {
                "kind": "merger", "direction": "outbound",
                "successor_name": match.group("successor").strip(),
                "successor_uid": _uid(match.group("uid")),
                "successor_place": match.group("place").strip(),
                "assets_transferred": True, "liabilities_transferred": True,
                "liabilities_kind": "third_party_capital", "company_deleted": True,
            },
        )], ""

    match = _FR_BOARD_MEMBER_WITH_AU.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.board_member_with_au.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil d'administration", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
            },
        )], ""

    match = _FR_DEFINITIVE_MORATORIUM_AND_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_and_commissioner.v1"
        common = {
            "decision_date": _french_date(match.group("decision_date")),
            "authority": match.group("authority").strip(),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    **common, "kind": "composition_moratorium_granted",
                    "action": "granted", "moratorium_type": "definitive",
                    "duration_months": int(match.group("duration")),
                    "until": _french_date(match.group("until")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    **common, "action": "appointed",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _FR_SIGNING_CORRECTED_FROM_PROCURATION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_corrected_from_procuration.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien", extra={
                "action": "signing_corrected",
                "previous_signing": "Kollektivprokura zu zweien",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MERGER_CAPITAL_AMOUNT_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.merger_capital_amount_corrected.v1", {
                "kind": "share_capital_increase", "action": "amount_corrected",
                "reason": "merger", "currency": "CHF",
                "amount": match.group("amount"),
                "previous_incorrect_amount": match.group("previous_amount"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        agreement_dates = _dual_date(match.group("agreement_date"))
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_assets_only_no_consideration.v1", {
                "source_kind": "company", "agreement_dates": agreement_dates,
                "agreement_date": agreement_dates[-1], "assets": match.group("assets"),
                "liabilities_transferred": False, "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _DE_DISSOLUTION_CORRECTED_LIQUIDATOR_ADDRESS.fullmatch(leftover)
    if match and (
        _count(match.group("previous_count")) == _count(match.group("count"))
        and match.group("previous_nominal") == match.group("nominal")
    ):
        rule_id = "de.text.dissolution_corrected_liquidator_address.v1"
        roles = ", ".join(match.group(key) for key in ("role1", "role2", "role3"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "date": _iso_date(match.group("date")),
                    "deciding_body": "Gesellschafterversammlung",
                    "liquidation_name": match.group("liquidation_name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"), role=roles,
                signing=match.group("signing"), extra={
                    "action": "name_corrected_and_appointed_liquidator",
                    "previous_name": match.group("previous_name").strip(),
                    "previous_role": ", ".join(
                        match.group(key) for key in ("previous_role1", "previous_role2")
                    ),
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    "kind": "liquidation_address", "action": "changed",
                    "to": match.group("address").strip(),
                },
            ),
        ], ""

    match = _FR_FOREIGN_NEW_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before"))
        == _count(match.group("transferred")) + _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.foreign_new_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé", extra={
                    **common, "action": "appointed_and_shares_received",
                    "counterparty": seller, "origin": match.group("origin").strip(),
                    "shares_received": _count(match.group("buyer_count")),
                    "shares_count": _count(match.group("buyer_count")),
                    "new_associate": True, "without_signature": True,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_PRESIDENT_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_president_name_corrected.v1",
            match.group("name"), role="administrateur-président", extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_COMPLEX_BOARD_CHANGES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.complex_board_changes_except_each_other.v1"
        president = match.group("president").strip()
        previous_president = match.group("previous_president").strip()
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, president,
                place=match.group("president_place"),
                role="président du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "origin_domicile_and_role_changed",
                    "origin": match.group("president_place").strip(),
                    "excluded_co_signers": [previous_president],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, previous_president,
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended", "previous_role": "président",
                    "excluded_co_signers": [president],
                },
            ),
        ]
        for index in (3, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration", extra={
                    "action": "appointed", "origin": match.group("origin34").strip(),
                },
            ))
        for index in (5, 6):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place56"),
                role="membre du conseil d'administration", extra={
                    "action": "appointed", "origin": match.group("origin56").strip(),
                },
            ))
        for index in (7, 8):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                },
            ))
        return events, ""

    return [], text
