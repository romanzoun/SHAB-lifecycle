from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_IT_SHARE_TRANSFER_STATUTORY_DEROGATION = re.compile(
    r"^Trasferimento quote sociali deroga a quanto previsto dalla legge "
    r"a norma di statuto\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_REPLACEMENT_SINGULAR = re.compile(
    r"^Gelöschte Person:\s*(?P<removed>[^,.;]+),\s*"
    r"(?P<removed_role>[^,.;]+),\s*"
    r"(?P<removed_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.\s*"
    r"Neu eingetragene Person:\s*(?P<added>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<added_role>[^,.;]+),\s*"
    r"(?P<added_sign>Einzelunterschrift|Kollektivunterschrift(?:\s+zu\s+zweien)?)\.?$",
    re.I | re.UNICODE,
)
_IT_STATUTES_DATE_CORRECTED_SHORT = re.compile(
    r"^Statuti corretti:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_CORRECTION_PAIR_TYPO = re.compile(
    r"^Recitificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>\d+)/(?P<notice_id>\d+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+)\s+sont à\s+"
    r"(?P<place>[^()]+?)\s+\(et non\s+(?P<previous_place>[^)]+)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROCURATIONS_REMOVED_PAIR = re.compile(
    r"^Les procurations de\s+(?P<name1>[^,.;]+)\s+et de\s+"
    r"(?P<name2>[^,.;]+)\s+sont radiées\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_MEMBERS_PAIR_WITH_COUNTRY = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<role1>président(?:e)?)\s+et\s+(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*"
    r"sont membres du conseil d['’]administration,\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_RENAMED_MIXED_LANGUAGE = re.compile(
    r"^Die eingetragene Revisionsstelle\s+(?P<old_name>.+?)\s+"
    r"\((?P<old_registry_id>CH-[\d.-]+-\d)\)\s+firmiert neu\s+"
    r"(?P<name>.+?)\s+\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_DISSOLUTION_DATE_CORRECTED = re.compile(
    r"^L['’]inscription n°\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que la "
    r"société a été dissoute le\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"\(et non pas le\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_PROXIES_REPLACED_WITH_SIGNING = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+)\s+et\s+"
    r"(?P<name3>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"engagent désormais la société par leur signature collective à deux,\s*"
    r"toutefois entre eux\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_EXEMPTION_REVOKED = re.compile(
    r"^Mit Verfügung der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde die Befreiung von der Pflicht,\s*"
    r"eine Revisionsstelle zu bezeichnen,\s*mit Wirkung ab dem Geschäftsjahr\s+"
    r"(?P<fiscal_year>\d{4})\s+widerrufen\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_ADDITIONAL_ADDRESS = re.compile(
    r"^\[bisher:\s*Weitere Adresse:\s*(?P<address>[^\]]+?)\.?\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_ELECTED_LIQUIDATOR = re.compile(
    r"^L['’]administrateur\s+(?P<name>[^,.;]+),\s*maintenant\s+"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_NOT_REGISTERABLE_DELETION = re.compile(
    r"^N['’]étant pas soumise à l['’]inscription\s*"
    r"\((?P<legal_basis>art\.\s*931,\s*al\.\s*1\s*CO)\),\s*"
    r"l['’]entreprise individuelle est radiée\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATEMENT_ORDERED = re.compile(
    r"^Selon ordonnance du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a ordonné la réinscription de la société "
    r"au registre du commerce\.?$",
    re.I | re.UNICODE,
)
_FR_SINGLE_SHARE_TRANSFER_UNSIGNED = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé une part de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé pour une part de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*lequel associé n['’]exerce pas la "
    r"signature sociale\.\s*Par conséquent,\s*(?P=seller)\s+est maintenant "
    r"titulaire de\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_WITH_BALANCE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) "
    r"von CHF\s+(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*Gutschrift im Kontokorrent von CHF\s*"
    r"(?P<consideration>[\d'.]+)\.?$",
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


def extract_parser68_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 68."""
    del language  # Historical records can contain a different language in this field.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _IT_SHARE_TRANSFER_STATUTORY_DEROGATION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", "it.text.share_transfer_statutory_derogation.v1",
                {
                    "kind": "share_transfer",
                    "action": "statutory_derogation",
                    "derogates_from_law": True,
                },
            )
        )

    match = _DE_PERSON_REPLACEMENT_SINGULAR.search(leftover)
    if match:
        consume(match)
        rule_id = "de.persons.replacement_singular.v1"
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, match.group("removed"),
                    role=match.group("removed_role").strip(),
                    signing=match.group("removed_sign").strip(),
                    extra={"action": "removed"},
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("added"),
                    place=match.group("place"), role=match.group("added_role").strip(),
                    signing=match.group("added_sign").strip(),
                    extra={
                        "action": "appointed",
                        "heimat": match.group("origin").strip(),
                    },
                ),
            ]
        )

    match = _IT_STATUTES_DATE_CORRECTED_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", "it.text.statutes_date_corrected_short.v1",
                {
                    "kind": "statutes_date",
                    "action": "corrected",
                    "date": _iso_date(match.group("date")),
                },
            )
        )

    match = _FR_DOMICILE_CORRECTION_PAIR_TYPO.search(leftover)
    if match:
        consume(match)
        common = {
            "action": "domicile_corrected",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_page": match.group("notice_page"),
            "notice_id": match.group("notice_id"),
            "previous_place": match.group("previous_place").strip(),
        }
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.domicile_correction_pair.v1",
                    match.group(group), place=match.group("place"), extra=common,
                )
            )

    match = _FR_PROCURATIONS_REMOVED_PAIR.search(leftover)
    if match:
        consume(match)
        for group in ("name1", "name2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", "fr.persons.procurations_removed_pair.v1",
                    match.group(group),
                    extra={"action": "revoked", "previous_signing": "procuration"},
                )
            )

    match = _FR_BOARD_MEMBERS_PAIR_WITH_COUNTRY.search(leftover)
    if match:
        consume(match)
        people = (
            (
                match.group("name1"), match.group("place1"), match.group("role1"),
                {"heimat": match.group("origin1").strip()},
            ),
            (
                match.group("name2"), match.group("place2"), "administrateur",
                {
                    "heimat": match.group("origin2").strip(),
                    "country": match.group("country"),
                },
            ),
        )
        for name, place, role, extra in people:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.board_members_pair_country.v1",
                    name, place=place, role=role,
                    extra={"action": "appointed", **extra},
                )
            )

    match = _DE_AUDITOR_RENAMED_MIXED_LANGUAGE.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "de.persons.auditor_renamed_mixed_language.v1",
                match.group("name"), uid=match.group("uid"), role="Revisionsstelle",
                extra={
                    "action": "name_changed",
                    "previous": match.group("old_name").strip(),
                    "previous_registry_id": match.group("old_registry_id"),
                },
            )
        )

    match = _FR_DISSOLUTION_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.dissolution_date_corrected.v1",
                {
                    "kind": "dissolution_date_corrected",
                    "action": "corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "date": _iso_date(match.group("date")),
                    "previous_date": _iso_date(match.group("previous_date")),
                },
            )
        )

    match = _FR_THREE_PROXIES_REPLACED_WITH_SIGNING.search(leftover)
    if match:
        consume(match)
        names = [match.group(group).strip() for group in ("name1", "name2", "name3")]
        for name in names:
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed",
                    "fr.persons.three_proxies_replaced_with_signing.v1",
                    name, signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "signing_replaced",
                        "previous_signing": "procuration",
                        "previous_signing_revoked": True,
                        "only_among_themselves": True,
                        "signing_group": names,
                    },
                )
            )

    match = _DE_AUDIT_EXEMPTION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.audit_exemption_revoked.v1",
                {
                    "kind": "auditor_appointment_exemption",
                    "action": "revoked",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                    "effective_fiscal_year": int(match.group("fiscal_year")),
                },
            )
        )

    match = _DE_PREVIOUS_ADDITIONAL_ADDRESS.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", "de.text.additional_address_previous.v1",
                {
                    "kind": "additional_address",
                    "action": "removed",
                    "address": match.group("address").strip().rstrip("."),
                    "replaced": True,
                },
            )
        )

    match = _FR_ADMINISTRATOR_ELECTED_LIQUIDATOR.search(leftover)
    if match:
        consume(match)
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", "fr.persons.administrator_elected_liquidator.v1",
                match.group("name"), role="liquidateur",
                extra={
                    "action": "role_and_origin_changed",
                    "previous_role": "administrateur",
                    "heimat": match.group("origin").strip(),
                },
            )
        )

    match = _FR_SOLE_PROPRIETOR_NOT_REGISTERABLE_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", "fr.text.sole_proprietor_not_registerable_deletion.v1",
                {
                    "reason": "registration_not_required",
                    "scope": "sole_proprietorship",
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            )
        )

    match = _FR_COMPANY_REINSTATEMENT_ORDERED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "fr.text.company_reinstatement_ordered.v2",
                {
                    "kind": "registration_reinstated",
                    "action": "ordered",
                    "date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_SINGLE_SHARE_TRANSFER_UNSIGNED.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        seller_count = _count(match.group("seller_count"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.single_share_transfer_unsigned.v1",
                    seller, role="associé",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": seller_count + 1,
                        "shares_transferred": 1,
                        "shares_count": seller_count,
                        "shares_nominal": match.group("seller_nominal"),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", "fr.persons.single_share_transfer_unsigned.v1",
                    buyer, place=match.group("place"), role="associé",
                    extra={
                        "action": "shares_received",
                        "heimat": match.group("origin").strip(),
                        "counterparty": seller,
                        "shares_received": 1,
                        "shares_count": 1,
                        "shares_nominal": match.group("buyer_nominal"),
                        "without_signature": True,
                    },
                ),
            ]
        )

    match = _DE_ASSET_TRANSFER_WITH_BALANCE.search(leftover)
    if match:
        consume(match)
        consideration = match.group("consideration")
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "assets_transferred", "de.text.asset_transfer_with_balance.v1",
                {
                    "date": _iso_date(match.group("date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "recipient": match.group("recipient").strip(),
                    "recipient_place": match.group("place").strip(),
                    "recipient_uid": match.group("uid"),
                    "consideration": f"Gutschrift im Kontokorrent von CHF {consideration}",
                    "consideration_kind": "current_account_credit",
                    "consideration_amount": consideration,
                },
            )
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
