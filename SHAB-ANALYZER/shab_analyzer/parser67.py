from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_AUDIT_WAIVER_DATE_CORRECTED = re.compile(
    r"^l['’]inscription n° (?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que la "
    r"déclaration selon laquelle (?:il )?est renoncé à un contrôle restreint est du "
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*et non "
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_RENAMED_AND_MOVED = re.compile(
    r"^(?P<old_name>.+?)\s+\((?P<old_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"organe de révision,\s*nouvelle raison sociale\s+(?P<name>.+?)\s+"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*maintenant à "
    r"(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PAIR_SAME_PLACE = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*nommé président et\s*"
    r"(?P<member>[^,;]+),\s*de et à\s+(?P<place>[^,;]+),\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_DE_COOPERATIVE_LIABILITY_REMOVED_WITH_ADDRESS_HEADING = re.compile(
    r"^Haftung/Nachschusspflicht neu:\s*"
    r"\[Streichung des Eintrags aufgrund geänderter Eintragungsvorschriften\.\]\s*"
    r"\[gestrichen:\s*(?P<previous>Keine persönliche Haftung der Mitglieder)\]"
    r"(?:\s*\.)*\s*"
    r"\[Folgende weitere Adresse wird im Handelsregister gelöscht:\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_MOVED_PRESIDENT_AND_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,;]+),\s*désormais domiciliée? à\s*"
    r"(?P<president_place>[^,;]+),\s*nommée? présidente?,\s*et\s*"
    r"(?P<member>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<nationality>[^,;]+),\s*à\s*(?P<member_place>[^,;]+),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_TRADE_NAME = re.compile(
    r"^L['’]établissement principal exerce son activité sous le nom commercial\s+"
    r"(?P<trade_name>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_STATUTES_DATE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_WITHOUT_SIGNING = re.compile(
    r"^(?P<name1>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,;]+),\s*à\s*(?P<place1>[^,;]+),\s*"
    r"(?P<role1>secrétaire),\s*et\s*(?P<name2>[^,;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,;]+),\s*à\s*"
    r"(?P<place2>[^,;]+),\s*sont membres du conseil de fondation;\s*"
    r"ils n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED = re.compile(
    r"^Con decreto del\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?)\s+ha accordato effetto sospensivo provvisorio al reclamo "
    r"inoltrato contro la decisione di apertura del fallimento della\s+"
    r"(?P<bankruptcy_court>.+?)\s+del\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]iscrizione nel registro di commercio relativa allo scioglimento della "
    r"società a seguito di fallimento viene pertanto cancellata\.\s*"
    r"\[finora:\s*(?P<previous>La società è sciolta in seguito a fallimento .+?"
    r"a far tempo dal\s+(?P<effective_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"alle ore\s+(?P<time>\d{1,2}:\d{2})\.)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_DUAL_APPOINTMENTS = re.compile(
    r"^(?P<seller>[^,.;]+) cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<seller_before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"qui est maintenant de\s+(?P<buyer_origin>[^,.;]+)\s+et nommée? gérante?\.\s*"
    r"(?P=seller),\s*qui reste titulaire de\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+),\s*est nommée? présidente?\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_PAIR_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux a été conférée à\s+"
    r"(?P<name1>[^,;]+)\s+et\s+(?P<name2>[^,;]+);\s*"
    r"leur procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_CREDIT_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs "
    r"pour CHF\s+(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+à la société\s+[\"“](?P<recipient>.+?)[\"”],\s*"
    r"à\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*une créance de CHF\s*(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSOCIATE_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller>.+?)\s+\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"associée,\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<seller_before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<buyer_origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant\s+"
    r"(?P=seller)\s+\((?P=seller_uid)\)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATORS_SIGN_INDIVIDUALLY = re.compile(
    r"^(?P<name1>[^,;]+)\s+et\s+(?P<name2>[^,;]+),\s*administrateurs,\s*"
    r"signent désormais individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_PAIR = re.compile(
    r"^(?P<name1>[^,;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,;]+),\s*à\s+(?P<place1>[^,;]+),\s*et\s*"
    r"(?P<name2>[^,;]+),\s*de et à\s+(?P<place2>[^,;]+),\s*"
    r"sont membres du conseil de fondation\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROCURATION = re.compile(
    r"^(?P<name>[^,;]+)\s+signe désormais avec une procuration individuelle\.?$",
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


def extract_parser67_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 67."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_AUDIT_WAIVER_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "fr.text.audit_waiver_date_corrected.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "declaration_date_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _FR_AUDITOR_RENAMED_AND_MOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.auditor_renamed_and_moved.v5",
                match.group("name"), place=match.group("place"), uid=match.group("uid"),
                role="organe de révision",
                extra={
                    "action": "name_and_seat_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_uid": match.group("old_uid"),
                },
            )
        )

    match = _FR_ADMINISTRATION_PAIR_SAME_PLACE.search(leftover)
    if match:
        consume(match)
        place = match.group("place").strip()
        for name, role, action in (
            (match.group("president"), "président", "role_changed"),
            (match.group("member"), "administrateur", "appointed"),
        ):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_pair_same_place.v1",
                    name, place=place if action == "appointed" else None, role=role,
                    signing="Einzelunterschrift",
                    extra={"action": action, **({"heimat": place} if action == "appointed" else {})},
                )
            )

    match = _DE_COOPERATIVE_LIABILITY_REMOVED_WITH_ADDRESS_HEADING.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.cooperative_liability_removed.v1",
                {
                    "kind": "member_liability",
                    "action": "removed",
                    "previous": match.group("previous"),
                    "reason": "changed_registration_rules",
                },
            )
        )

    match = _FR_ADMINISTRATION_MOVED_PRESIDENT_AND_MEMBER.search(leftover)
    if match:
        consume(match)
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_moved_president_pair.v1",
                    match.group("president"), place=match.group("president_place"),
                    role="présidente", signing="Einzelunterschrift",
                    extra={"action": "role_and_domicile_changed", "domicile_changed": True},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.administration_moved_president_pair.v1",
                    match.group("member"), place=match.group("member_place"),
                    role="administrateur", signing="Einzelunterschrift",
                    extra={"action": "appointed", "nationality": match.group("nationality").strip()},
                ),
            ]
        )

    match = _FR_HEAD_OFFICE_TRADE_NAME.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", "fr.text.head_office_trade_name.v1",
                {
                    "kind": "trade_name",
                    "scope": "head_office",
                    "trade_name": match.group("trade_name").strip(),
                },
            )
        )

    match = _DE_ADDITIONAL_STATUTES_DATE.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "de.text.additional_statutes_date.v1",
                {"date": _iso_date(match.group("date")), "action": "amended"},
            )
        )

    match = _FR_FOUNDATION_MEMBERS_WITHOUT_SIGNING.search(leftover)
    if match:
        consume(match)
        for index, role in ((1, "secrétaire"), (2, "membre du conseil de fondation")):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_without_signing.v1",
                    match.group(f"name{index}"), place=match.group(f"place{index}"),
                    role=role,
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "without_signature": True,
                    },
                )
            )

    match = _IT_COMPANY_BANKRUPTCY_EFFECT_SUSPENDED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_bankruptcy_effect_suspended.v1",
                {
                    "kind": "bankruptcy_effect_suspended",
                    "scope": "company",
                    "provisional": True,
                    "decision_date": _iso_date(match.group("decision_date")),
                    "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                    "bankruptcy_effective_date": _iso_date(match.group("effective_date")),
                    "bankruptcy_effective_time": match.group("time"),
                    "authority": match.group("authority").strip(),
                    "bankruptcy_court": match.group("bankruptcy_court").strip(),
                    "dissolution_entry_removed": True,
                    "previous": match.group("previous").strip(),
                },
            )
        )

    match = _FR_ASSOCIATE_TRANSFER_DUAL_APPOINTMENTS.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_dual_appointments.v1",
                    seller, role="président",
                    extra={
                        "action": "shares_transferred_and_appointed",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("seller_before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.associate_transfer_dual_appointments.v1",
                    buyer, role="gérante",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("buyer_origin").strip(),
                        "origin_changed": True,
                        "counterparty": seller,
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_SIGNING_GRANTED_PAIR_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.signing_granted_proxy_revoked_pair.v1",
                    match.group(group), signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "signing_replaced",
                        "previous_signing": "procuration",
                        "previous_signing_revoked": True,
                    },
                )
            )

    match = _FR_ASSET_TRANSFER_CREDIT_CONSIDERATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "fr.text.asset_transfer_credit_consideration.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": f"une créance de CHF {match.group('consideration')}",
                    "consideration_kind": "receivable",
                    "consideration_amount": match.group("consideration"),
                },
            )
        )

    match = _FR_COMPANY_ASSOCIATE_TRANSFER_TO_MANAGER.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.company_associate_transfer_to_manager.v1",
                    seller, uid=match.group("seller_uid"), role="associée",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": _count(match.group("seller_before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.company_associate_transfer_to_manager.v1",
                    buyer, place=match.group("buyer_place"), role="associé et gérant",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "shares_received_and_appointed",
                        "heimat": match.group("buyer_origin").strip(),
                        "counterparty": seller,
                        "counterparty_uid": match.group("seller_uid"),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "shares_nominal": match.group("buyer_nominal"),
                    },
                ),
            ]
        )

    match = _FR_ADMINISTRATORS_SIGN_INDIVIDUALLY.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.administrators_sign_individually.v1",
                    match.group(group), role="administrateur", signing="Einzelunterschrift",
                    extra={"action": "signing_changed"},
                )
            )

    match = _FR_FOUNDATION_MEMBERS_PAIR.search(leftover)
    if match:
        consume(match)
        people = (
            (match.group("name1"), match.group("place1"), match.group("origin1")),
            (match.group("name2"), match.group("place2"), match.group("place2")),
        )
        for name, place, origin in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.foundation_members_pair.v1",
                    name, place=place, role="membre du conseil de fondation",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed", "heimat": origin.strip()},
                )
            )

    match = _FR_INDIVIDUAL_PROCURATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", "fr.persons.individual_procuration.v1",
                match.group("name"), signing="Einzelprokura",
                extra={"action": "signing_changed"},
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
