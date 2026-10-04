from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_CAPITAL_BAND_DECISION = re.compile(
    r"^Die Gesellschaft hat mit Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"ein Kapitalband gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_DE_UID_CORRECTION = re.compile(
    r"^Berichtigung der Eintragung Nr\.\s*(?P<entry>[\d']+) vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s*(?P<notice_id>\d+)\):\s*"
    r"Die richtige UID-Nummer lautet:\s*(?P<to>CHE-\d{3}\.\d{3}\.\d{3})\s*"
    r"\(und nicht:\s*(?P<from>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_SIGNING_REVOKED = re.compile(
    r"^L['’](?P<role>administratrice secrétaire)\s+(?P<name>[^,.;]+)\s+"
    r"n['’]exerce plus la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_BECOMES_LIQUIDATOR = re.compile(
    r"^L['’](?P<previous_role>administratrice)\s+(?P<name>[^,.;]+)\s+"
    r"est désormais\s+(?P<role>liquidatrice)\s+et signe\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDITIONAL_ADDRESSES = re.compile(
    r"^(?:\[gestrichen:\s*Weitere Adresse:\s*[^\]]+\]\.?(?:\s*|$))+$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDITIONAL_ADDRESS_ITEM = re.compile(
    r"\[gestrichen:\s*Weitere Adresse:\s*(?P<address>[^\]]+?)\]\.?(?:\s*|$)",
    re.I | re.UNICODE,
)
_FR_CHAINED_ASSOCIATE_TRANSFER = re.compile(
    r"^(?P<seller_org>.+?)\s*\((?P<seller_registry>\d{4}\.\d{3}\.\d{3})\)\s+et\s+"
    r"(?P<seller_person>[^,.;]+)\s+ne sont plus associés,\s*ils ont cédé leurs\s+"
    r"(?P<count>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<intermediary>.+?)\s*\((?P<intermediary_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<intermediary_place>[^,.;]+)\s+qui les a ensuite cédées à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*nouvel associé pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"lequel associé n['’]exerce pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESSES_WITH_HISTORY = re.compile(
    r"^(?:Weitere Adresse:\s*.+?(?:\.|$)(?:\s*\[bisher:[^\]]+\]\.?)?\s*)+$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_ADDRESS_WITH_HISTORY_ITEM = re.compile(
    r"Weitere Adresse:\s*(?P<address>.*?,\s*(?P<postal_code>\d{4})\s+"
    r"(?P<locality>[^.\[]+?))(?:\.|$)(?:\s*\[bisher:\s*(?P<previous>[^\]]+?)\]\.?)?"
    r"(?=\s*(?:Weitere Adresse:|$))",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_REVOKED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die provisorische Nachlassstundung widerrufen\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P=authority)\s+eine provisorische Nachlassstundung bis\s+"
    r"(?P<initial_until>\d{2}\.\d{2}\.\d{4})\s+gewährt\.\]\.?\s*"
    r"\[gestrichen:\s*Mit Entscheid vom\s+(?P<extension_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"hat\s+(?P=authority)\s+eine provisorische Nachlassstundung bis letztmals\s+"
    r"(?P<extended_until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_ADDRESS_REMOVED_TYPO = re.compile(
    r"^Autres? adresses? radiées?\s*:\s*(?P<address>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_DANGLING_HEAD_OFFICE_CONNECTOR = re.compile(r"^,?\s*mit\s*$", re.I | re.UNICODE)
_FR_ASSOCIATE_SHARE_TRANSFER_WITHOUT_SIGNING = re.compile(
    r"^(?P<seller>[^,.;]+),\s*associé-gérant,\s*cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>.+?),\s*nouvel associé avec\s+(?P<buyer_count>[\d']+) parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*sans signature\.\s*"
    r"(?P=seller) reste titulaire de\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_MANAGER_DOMICILE_CHANGED = re.compile(
    r"^L['’]associé\s+(?P<name>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role>président),\s*"
    r"est\s+(?P<role>seul gérant)\s+et continue à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_NOMINAL_CORRECTION = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*(?P<notice_id>\d+)\)\s+"
    r"est rectifiée en ce sens que\s+(?P<name>[^,.;]+)\s+est désormais titulaire de\s+"
    r"(?P<count>[\d']+) parts de CHF\s+(?P<nominal>[\d'.]+)\s+\(et non\s+"
    r"(?P<previous_count>[\d']+) parts de CHF\s+(?P<previous_nominal>[\d'.]+)\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_SHORT_NEW_COMPANY_NAME = re.compile(
    r"^Nouvelle raison sociale:\s*(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_PROMOTIONS_DIRECTION_TYPO = re.compile(
    r"^(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici membres de la\s+"
    r"directionm\s+ont été nommés\s+(?P<role>administrateurs)\s+et continuent à signer\s+"
    r"(?P<sign>individuellement|collectivement(?:\s+à\s+deux)?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGERS_TRANSFER_TRUNCATED = re.compile(
    r"^(?P<seller>[^,.;]+) a cédé\s+(?P<transferred>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) au nouvel associé\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+)\.\s*"
    r"Associés-gérants:\s*(?P=seller),\s*nommée présidente,\s*et\s*(?P=buyer),\s*"
    r"pour\s+(?P<count>[\d']+) parts de CHF\s+(?P<manager_nominal>[\d'.]+) chacun,\s*"
    r"tous deux\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{year}-{month}-{day}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _signing(raw: str) -> str:
    return (
        "Einzelunterschrift"
        if "individ" in raw.lower()
        else "Kollektivunterschrift zu zweien"
    )


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


def extract_parser81_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 81."""
    del language  # Historical publications can mix languages.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_CAPITAL_BAND_DECISION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.capital_band_decision.v2",
                {
                    "kind": "capital_band",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            )
        )

    match = _DE_UID_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed", "de.text.uid_correction.v1",
                {
                    "action": "corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                    "from": match.group("from"),
                    "to": match.group("to"),
                },
            )
        )

    match = _FR_ADMINISTRATOR_SIGNING_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.administrator_signing_revoked.v1",
                match.group("name"), role=match.group("role").lower(),
                extra={"action": "revoked", "signing_revoked": True},
            )
        )

    match = _FR_ADMINISTRATOR_BECOMES_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.administrator_became_liquidator.v1",
                match.group("name"), role=match.group("role").lower(),
                signing=_signing(match.group("sign")),
                extra={
                    "action": "role_changed",
                    "previous_role": match.group("previous_role").lower(),
                },
            )
        )

    match = _DE_REMOVED_ADDITIONAL_ADDRESSES.search(leftover)
    if match:
        address_matches = list(_DE_REMOVED_ADDITIONAL_ADDRESS_ITEM.finditer(match.group(0)))
        if address_matches:
            consume(match)
            for address_match in address_matches:
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "address_changed", "de.text.additional_addresses_removed_sequence.v1",
                        {
                            "kind": "additional_address",
                            "action": "removed",
                            "address": address_match.group("address").strip().rstrip("."),
                        },
                    )
                )

    match = _FR_CHAINED_ASSOCIATE_TRANSFER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.chained_associate_transfer.v1"
        count = _count(match.group("count"))
        nominal = match.group("nominal")
        intermediary = match.group("intermediary").strip()
        buyer = match.group("buyer").strip()
        for name, registry_id in (
            (match.group("seller_org"), match.group("seller_registry")),
            (match.group("seller_person"), None),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name, role="associé",
                    extra={
                        "action": "shares_transferred_and_removed",
                        "counterparty": intermediary,
                        "joint_shares_transferred": count,
                        "shares_nominal": nominal,
                        **({"registry_id": registry_id} if registry_id else {}),
                    },
                )
            )
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, intermediary,
                    place=match.group("intermediary_place"),
                    uid=match.group("intermediary_uid"), role="associée",
                    extra={
                        "action": "shares_received_and_retransferred",
                        "shares_received": count,
                        "shares_transferred": count,
                        "shares_nominal": nominal,
                        "counterparty": buyer,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "country": match.group("country"),
                        "shares_received": count,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "new_associate": True,
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _DE_ADDITIONAL_ADDRESSES_WITH_HISTORY.search(leftover)
    if match:
        address_matches = list(
            _DE_ADDITIONAL_ADDRESS_WITH_HISTORY_ITEM.finditer(match.group(0))
        )
        if address_matches:
            consume(match)
            for address_match in address_matches:
                previous = address_match.group("previous")
                events.append(
                    _event(
                        publication_id, published_at, org_uid, plz, canton,
                        "address_changed", "de.text.additional_addresses_with_history.v1",
                        {
                            "kind": "additional_address",
                            "action": "changed" if previous else "added",
                            "address": address_match.group("address").strip(),
                            "postal_code": address_match.group("postal_code"),
                            "locality": address_match.group("locality").strip(),
                            **({"previous": previous.strip().rstrip(".")} if previous else {}),
                        },
                    )
                )

    match = _DE_PROVISIONAL_MORATORIUM_REVOKED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.provisional_moratorium_revoked_with_history.v1",
                {
                    "kind": "composition_moratorium",
                    "action": "revoked",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authority": match.group("authority").strip(),
                    "grant_date": _iso_date(match.group("grant_date")),
                    "initial_until": _iso_date(match.group("initial_until")),
                    "extension_date": _iso_date(match.group("extension_date")),
                    "extended_until": _iso_date(match.group("extended_until")),
                    "provisional": True,
                },
            )
        )

    match = _FR_ADDITIONAL_ADDRESS_REMOVED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "fr.text.additional_address_removed_typo.v1",
                {
                    "kind": "additional_address",
                    "action": "removed",
                    "address": match.group("address").strip(),
                },
            )
        )

    match = _DE_DANGLING_HEAD_OFFICE_CONNECTOR.search(leftover)
    if match:
        # The preceding head-office identifier rule already emitted the fact. This
        # exact connector is syntactic residue from "mit Hauptsitz in" and carries
        # no independent business meaning.
        consume(match)

    match = _FR_ASSOCIATE_SHARE_TRANSFER_WITHOUT_SIGNING.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_share_transfer_without_signing.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                        "new_associate": True,
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _FR_SOLE_MANAGER_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.sole_manager_domicile_changed.v1",
                match.group("name"), place=match.group("place"),
                role=match.group("role").lower(), signing=_signing(match.group("sign")),
                extra={
                    "action": "role_and_domicile_changed",
                    "previous_role": match.group("previous_role").lower(),
                    "domicile_changed": True,
                    "signing_continues": True,
                },
            )
        )

    match = _FR_SHARE_NOMINAL_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.share_nominal_correction.v1",
                match.group("name"), role="associé",
                extra={
                    "action": "share_nominal_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                    "shares_count": _count(match.group("count")),
                    "shares_nominal": match.group("nominal"),
                    "previous_shares_count": _count(match.group("previous_count")),
                    "previous_shares_nominal": match.group("previous_nominal"),
                },
            )
        )

    match = _FR_SHORT_NEW_COMPANY_NAME.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", "fr.text.company_name_changed_short.v1",
                {"action": "changed", "to": match.group("name").strip()},
            )
        )

    match = _FR_BOARD_PROMOTIONS_DIRECTION_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.board_promotions_directionm_typo.v1"
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(group),
                    role="administrateur", signing=_signing(match.group("sign")),
                    extra={
                        "action": "role_changed",
                        "previous_role": "membre de la direction",
                        "signing_continues": True,
                    },
                )
            )

    match = _FR_ASSOCIATE_MANAGERS_TRANSFER_TRUNCATED.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        count = _count(match.group("count"))
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.associate_managers_transfer_split_signing.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associée-gérante présidente", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_transferred": transferred,
                        "shares_count": count,
                        "shares_nominal": match.group("manager_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("place"),
                    role="associé-gérant", signing="Einzelunterschrift",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": count,
                        "shares_nominal": match.group("manager_nominal"),
                        "new_associate": True,
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
