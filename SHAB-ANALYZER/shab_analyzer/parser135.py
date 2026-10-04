from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SHARE_TRANSFER_RESTRICTION_STATUTORY_DEROGATION = re.compile(
    r"^Nouvelle restriction à la transmissibilité:\s*Les statuts dérogent à la "
    r"loi quant aux modalités du transfert des parts sociales:\s*"
    r"(?P<reference>pour les détails,\s*voir les statuts)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS = re.compile(
    r"^Selon décision de l['’](?P<authority>.+?)\s+du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la fondation est dissoute\.\s*"
    r"Liquidateurs:\s*les membres du conseil\s+(?P<name1>[^,.;]+),\s*"
    r"(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*"
    r"(?P<name4>[^,.;]+)\s+et\s+(?P<name5>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_SIGNING_GRANTED = re.compile(
    r"^Signature collective à deux a été conférée au membre du conseil de "
    r"fondation\s+(?P<name>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_REPLACED_FOUR_MEMBERS = re.compile(
    r"^(?P<removed1>[^,.;]+),\s*(?P<removed2>[^,.;]+)\s+ne sont plus membres "
    r"du conseil;\s*leurs pouvoirs sont radiés\.\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+),\s*président,\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+)\s+et\s+"
    r"(?P<name4>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,.;]+),\s*"
    r"à\s+(?P<place4>[^,.;]+),\s*sont membres du conseil\.?$",
    re.I | re.UNICODE,
)
_DE_ART_938A_DELETION_POSTPONED = re.compile(
    r"^Das Löschungsverfahren gemäss\s+(?P<legal_basis>Art\.\s*938a OR)\s+"
    r"ist abgeschlossen,\s*Löschung aufgeschoben mangels Zustimmungen der "
    r"Steuerverwaltungen\.?$",
    re.I | re.UNICODE,
)
_FR_INCORRECT_BOARD_MEMBERSHIP = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+),\s*qui signe individuellement,\s*n['’]est pas membre "
    r"du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_RESTRICTED_PROCURATIONS = re.compile(
    r"^Procuration collective à deux,\s*toutefois pas entre eux ni avec\s+"
    r"(?P<excluded1>[^,.;]+),\s*(?P<excluded2>[^,.;]+)\s+et\s+"
    r"(?P<excluded3>[^,.;]+),\s*est conférée à\s+"
    r"(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*(?P<name3>[^,.;]+),\s*"
    r"les trois\s+(?:du|de la|des|de|d['’])\s*(?P<origin123>[^,.;]+),\s*"
    r"à\s+(?P<place123>[^,.;]+),\s*et\s+(?P<name4>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin4>[^,.;]+),\s*"
    r"à\s+(?P<place4>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_NEW_MANAGER_SELLER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvell?e? associé(?:e)?-gérant(?:e)? avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller),\s*qui reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de "
    r"CHF\s+(?P<remaining_nominal>[\d'.]+),\s*est nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_NAME_CHANGED = re.compile(
    r"^Nouvelle raison de commerce de la succursale:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_UNLABELED_PAID_IN = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<to_capital>[\d'.]+);\s*Liberierung\s+"
    r"(?:(?P<to_paid_currency>[A-Z]{3})\s+)?(?P<to_paid>[\d'.]+)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*(?P<from_currency>[A-Z]{3})\s+"
    r"(?P<from_capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?:(?P<from_paid_currency>[A-Z]{3})\s+)?(?P<from_paid>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_MIXED_NOMINAL_TRANSFER = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*gérant à trois;\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining_other>[\d']+)\s+parts de "
    r"CHF\s+(?P<remaining_other_nominal>[\d'.]+)\s+et\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_SIGNERS_ONE_DOMICILE_CHANGED = re.compile(
    r"^Signature collective à deux est conférée à\s+(?P<name1>[^,;]+),\s*"
    r"(?P<name2>[^,;]+),\s*(?P<name3>[^,;]+),\s*qui est maintenant à\s+"
    r"(?P<place3>[^,.;]+),\s*(?P<name4>[^,.;]+)\s+et\s+"
    r"(?P<name5>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_APPOINTED_LIQUIDATOR_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*qui reste gérante sans signature,\s*"
    r"est nommée liquidatrice\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTORS_APPOINTED_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici "
    r"directeurs,\s*sont nommés membres du conseil d['’]administration et "
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_MANAGER_PRESIDENT_NO_SELLER_DOMICILE = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé-gérant président avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_ONE_MANAGER = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+)\s+et\s+"
    r"(?P<seller2>[^,.;]+)\s+cèdent chacun\s+(?P<transferred>[\d']+)\s+de leurs\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"gérant\s+(?P=seller1)\s+et\s+(?P=seller2)\s+restent titulaires,\s*chacun,\s*"
    r"de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
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


def extract_parser135_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 135."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SHARE_TRANSFER_RESTRICTION_STATUTORY_DEROGATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.share_transfer_restriction_statutory_derogation.v1",
            {
                "kind": "share_transfer_restriction", "action": "added",
                "basis": "statutes", "statutory_derogation": True,
                "scope": "parts sociales",
                "statutes_reference": match.group("reference").strip(),
            },
        ))

    match = _FR_FOUNDATION_DISSOLVED_FIVE_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.foundation_dissolved_five_liquidators.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id,
            {
                "kind": "dissolution", "action": "dissolved",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))
        for index in range(1, 6):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du conseil et liquidateur",
                extra={"action": "appointed_liquidator", "remains_board_member": True},
            ))

    match = _FR_FOUNDATION_MEMBER_SIGNING_GRANTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.foundation_member_signing_granted.v1",
            match.group("name"), role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien", extra={"action": "granted"},
        ))

    match = _FR_BOARD_REPLACED_FOUR_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_replaced_four_members.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"removed{index}"),
                role="membre du conseil",
                extra={"action": "removed", "signing_revoked": True},
            ))
        for index in range(1, 5):
            is_president = index == 1
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="président du conseil" if is_president else "membre du conseil",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_president" if is_president else "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _DE_ART_938A_DELETION_POSTPONED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.art_938a_deletion_postponed.v1",
            {
                "kind": "deletion_postponed", "action": "postponed",
                "procedure_completed": True,
                "reason": "missing_tax_authority_consents",
                "legal_basis": match.group("legal_basis"),
            },
        ))

    match = _FR_INCORRECT_BOARD_MEMBERSHIP.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.incorrect_board_membership_corrected.v1",
            match.group("name"), signing="Einzelunterschrift",
            extra={
                "action": "role_corrected", "incorrect_role": "membre du conseil d'administration",
                "role_applies": False, "signing_continues": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_FOUR_RESTRICTED_PROCURATIONS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_restricted_procurations.v1"
        excluded = [match.group(f"excluded{index}").strip() for index in range(1, 4)]
        for index in range(1, 5):
            common_group = index < 4
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place123" if common_group else "place4"),
                signing="Kollektivprokura zu zweien",
                extra={
                    "action": "procuration_granted",
                    "heimat": match.group("origin123" if common_group else "origin4").strip(),
                    "cannot_sign_with_each_other": True,
                    "cannot_sign_with": excluded,
                },
            ))

    match = _FR_ASSOCIATE_TRANSFER_NEW_MANAGER_SELLER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_new_manager_seller_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant président",
                extra={
                    "action": "shares_transferred_and_appointed_president",
                    "counterparty": buyer, "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_BRANCH_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.branch_name_changed.v1",
            {"scope": "branch", "action": "changed", "to": match.group("name").strip()},
        ))

    match = _DE_HEAD_OFFICE_CAPITAL_UNLABELED_PAID_IN.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_capital_unlabeled_paid_in.v1",
            {
                "scope": "head_office", "currency": match.group("currency"),
                "from_nominal": match.group("from_capital"),
                "to_nominal": match.group("to_capital"),
                "from_paid": match.group("from_paid"), "to_paid": match.group("to_paid"),
            },
        ))

    match = _FR_MANAGER_MIXED_NOMINAL_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_mixed_nominal_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                    "remaining_shareholdings": [
                        {
                            "shares_count": _count(match.group("remaining_other")),
                            "share_nominal": match.group("remaining_other_nominal"),
                        },
                        {
                            "shares_count": _count(match.group("remaining")),
                            "share_nominal": match.group("remaining_nominal"),
                        },
                    ],
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant", signing="Kollektivunterschrift zu dreien",
                extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_FIVE_SIGNERS_ONE_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.five_signers_one_domicile_changed.v1"
        for index in range(1, 6):
            moved = index == 3
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place3") if moved else None,
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "domicile_changed_and_granted" if moved else "granted",
                       "domicile_changed": moved},
            ))

    match = _FR_MANAGER_APPOINTED_LIQUIDATOR_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_appointed_liquidator_without_signature.v1",
            match.group("name"), role="gérante et liquidatrice",
            signing="Einzelunterschrift",
            extra={
                "action": "appointed_liquidator", "remains_manager": True,
                "previously_without_signature": True,
            },
        ))

    match = _FR_DIRECTORS_APPOINTED_BOARD_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.directors_appointed_board_members.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed", "previous_role": "directeur",
                    "signing_continues": True,
                },
            ))

    match = _FR_SHARE_TRANSFER_TO_MANAGER_PRESIDENT_NO_SELLER_DOMICILE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_manager_president_no_seller_domicile.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_TWO_MANAGERS_TRANSFER_TO_ONE_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_transfer_to_one_manager.v1"
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
        for seller in sellers:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            role="associé-gérant", signing="Einzelunterschrift",
            extra={
                "action": "appointed_and_shares_received", "counterparties": sellers,
                "heimat": match.group("origin").strip(), "new_associate": True,
                "shares_received": transferred * 2,
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
