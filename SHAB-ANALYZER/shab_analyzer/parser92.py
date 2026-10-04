from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_COMMUNICATIONS_REGISTERED_SHAREHOLDERS_FRAGMENT = re.compile(
    r"^eingetragene Aktionäre\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<seller>[^,.;]+)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_SHARE_CAPITAL_AT_FOUNDING = re.compile(
    r"^Die Gesellschaft hat bei der Gründung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+genehmigte Kapitalerhöhungen betreffend "
    r"Aktienkapital gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_EXCLUSION_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_page>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+continue à signer collectivement à deux,\s*"
    r"toutefois pas avec\s+(?P<excluded>.+?)\s+\(et non\s+"
    r"(?P<previous_excluded>.+?)\s+comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_REINSTATED_CORRECTION = re.compile(
    r"^\[gestrichen:\s*\]\.?\s*\[Berichtigung:\]\s*Das irrtümlich unter "
    r"TR Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}),\s*SHAB Nr\.\s*"
    r"(?P<notice_number>\d+)\s+vom\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"gelöschte Einzelunternehmen wird wieder in das Handelsregister eingetragen\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine definitive "
    r"Nachlassstundung von\s+(?P<duration>\w+)\s+Monaten bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.\s*Als Sachwalter wird\s+"
    r"(?P<commissioner>[^,.;]+),\s*(?P<commissioner_org>.+?)\s*"
    r"\((?P<commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<commissioner_address>.+?),\s*(?P<commissioner_postal_code>\d{4})\s+"
    r"(?P<commissioner_place>[^,.;\]]+),\s*eingesetzt\.\s*"
    r"\[bisher:\s*Mit Entscheid des\s+(?P<previous_authority>.+?),\s*vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine provisorische "
    r"Nachlassstundung bis zum\s+(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+"
    r"bewilligt\.\s*Als Sachwalter wird\s+(?P<previous_commissioner>[^,.;]+),\s*"
    r"(?P<previous_commissioner_org>.+?)\s*"
    r"\((?P<previous_commissioner_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<previous_commissioner_address>.+?),\s*"
    r"(?P<previous_commissioner_postal_code>\d{4})\s+"
    r"(?P<previous_commissioner_place>[^,.;\]]+),\s*eingesetzt\.\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_INTENDED_ASSET_ACQUISITION_PRICE_CORRECTED = re.compile(
    r"^Nouveaux faits qualifiés:\s*Reprise de biens envisagée:\s*la société "
    r"envisage de reprendre\s+(?P<count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de la société à responsabilité limitée\s+"
    r"(?P<target>.+?)\s*\((?P<target_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<target_place>[^,.;]+),\s*pour le prix maximum de CHF\s+"
    r"(?P<price>[\d'.]+)\s*\[non:\s*Reprise de biens envisagée:\s*la société "
    r"envisage de reprendre\s+(?P<previous_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\s+de la société à responsabilité limitée\s+"
    r"(?P<previous_target>.+?)\s*"
    r"\((?P<previous_target_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<previous_target_place>[^,.;]+),\s*pour le montant minimum de CHF\s+"
    r"(?P<previous_price>[\d'.]+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_HEAD_OFFICE_LEGACY_IDENTIFIER_REMOVED = re.compile(
    r"^,?\s*mit Bemerkungen zum Hauptsitz neu:\s*\[gestrichen:\s*"
    r"Bemerkungen zum Hauptsitz:\s*Identifiktionsnummer:\s*"
    r"(?P<registry_id>CH-[\d.]+-\d)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_SUPPLEMENT_REFERENCE_SHORT = re.compile(
    r"^L['’]inscription\s+N°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est complétée comme suit\s*:\s*$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_BY_CANTONAL_COURT = re.compile(
    r"^Die Gesellschaft wird gemäss Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+wieder in das Handelsregister "
    r"eingetragen\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_ASSOCIATES_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’]associé-gérant\s+(?P<manager>[^,.;]+),\s*les associés\s+"
    r"(?P<associates>.+?)\s+cèdent chacun\s+(?P<transferred>[\d']+)\s+de leurs\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+chacun à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+(?:\s*\([^)]+\))?),\s*"
    r"nouvel associé sans signature,\s*avec\s+(?P<buyer_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P<remaining_people>.+?)\s+restent titulaires de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"chacun\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_DE_MANAGEMENT_AUDIT_WAIVER = re.compile(
    r"^Gemäss Erklärung der Geschäftsführung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft keiner "
    r"ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_REMOVED_AFTER_SEAT_TRANSFER = re.compile(
    r"^La succursale de\s+(?P<from_place>.+?)\s*"
    r"\((?P<registry_id>CH-[\d-]+)\)\s+est radiée suite à son transfert de siège "
    r"à\s+(?P<to_place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_EXISTING_AND_NEW_ADMINISTRATORS_SIGNING_RESTRICTED = re.compile(
    r"^(?P<existing1>[^,.;]+)\s+et\s+(?P<existing2>[^,.;]+)\s+continuent à "
    r"signer collectivement à deux,\s*désormais pas entre eux\.\s*"
    r"Nouveaux administrateurs toutefois pas entre eux:\s*"
    r"(?P<new1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<new2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_RELOCATION_FRAGMENT = re.compile(
    r"^\]\.?\s*(?P<to_place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+HR\s+"
    r"(?P<register_canton>[A-Z]{2})\.?$",
    re.I | re.UNICODE,
)
_DE_LLC_TO_CORPORATION_TRANSFORMATION = re.compile(
    r"^Umwandlung:\s*Die Gesellschaft mit beschränkter Haftung hat das "
    r"Stammkapital auf CHF\s+(?P<capital>[\d'.]+)\s+erhöht und wird gemäss "
    r"Umwandlungsplan vom\s+(?P<plan_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+in eine Aktiengesellschaft umgewandelt\.\s*"
    r"Die Gesellschafter erhalten für ihre bisherigen Stammanteile\s+"
    r"(?P<shares>[\d']+)\s+Namenaktien zu CHF\s+(?P<share_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)


_GERMAN_NUMBERS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
    "elf": 11,
    "zwölf": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _number(raw: str) -> int | None:
    normalized = raw.lower()
    if normalized.isdigit():
        return int(normalized)
    return _GERMAN_NUMBERS.get(normalized)


def _split_fr_names(raw: str) -> list[str]:
    normalized = re.sub(r"\s+et\s+", ", ", raw.strip(), flags=re.I)
    return [name.strip() for name in normalized.split(",") if name.strip()]


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


def extract_parser92_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 92."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_COMMUNICATIONS_REGISTERED_SHAREHOLDERS_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed",
                "de.text.communications_registered_shareholders_continuation.v1",
                {
                    "kind": "communications_recipient_completion",
                    "recipient": "registered_shareholders",
                    "raw": match.group(0).rstrip("."),
                },
            )
        )

    match = _FR_MANAGER_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.manager_transfer_new_unsigned_associate.v1"
        transferred = _count(match.group("transferred"))
        events.extend(
            [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("seller"),
                    role="associé-gérant",
                    extra={
                        "action": "shares_transferred",
                        "shares_before": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("seller_count")),
                        "share_nominal": match.group("seller_nominal"),
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("buyer"),
                    place=match.group("place"), role="associé",
                    extra={
                        "action": "appointed",
                        "new_associate": True,
                        "without_signature": True,
                        "heimat": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    match = _DE_AUTHORIZED_SHARE_CAPITAL_AT_FOUNDING.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.authorized_share_capital_at_foundation.v1",
                {
                    "kind": "authorized_capital",
                    "action": "introduced",
                    "foundation_date": _iso_date(match.group("date")),
                    "capital_scope": "share_capital",
                    "details_in_statutes": True,
                },
            )
        )

    match = _FR_SIGNING_EXCLUSION_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        excluded = _split_fr_names(match.group("excluded"))
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed",
                "fr.persons.signing_exclusion_name_corrected.v1",
                match.group("name"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "publication_corrected",
                    "excluded_cosignatories": excluded,
                    "corrected_name": excluded[-1],
                    "previous_name": match.group("previous_excluded").strip(),
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_page": match.group("notice_page"),
                },
            )
        )

    match = _DE_SOLE_PROPRIETOR_REINSTATED_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.sole_proprietor_reinstated_correction.v1",
                {
                    "kind": "registration_reinstated",
                    "scope": "sole_proprietor",
                    "reason": "erroneous_deletion",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_number": match.group("notice_number"),
                    "notice_date": _iso_date(match.group("notice_date")),
                },
            )
        )

    match = _DE_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.definitive_moratorium_with_commissioner.v1"
        common = {
            "commissioner": match.group("commissioner").strip(),
            "commissioner_organization": match.group("commissioner_org").strip(),
            "commissioner_organization_uid": match.group("commissioner_uid"),
            "commissioner_address": match.group("commissioner_address").strip(),
            "commissioner_postal_code": match.group("commissioner_postal_code"),
            "commissioner_place": match.group("commissioner_place").strip(),
        }
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", rule_id,
                    {
                        "kind": "composition_moratorium_granted",
                        "moratorium_type": "definitive",
                        "decision_date": _iso_date(match.group("decision_date")),
                        "until": _iso_date(match.group("until")),
                        "duration_months": _number(match.group("duration")),
                        "authority": match.group("authority").strip(),
                        "previous_moratorium_type": "provisional",
                        "previous_decision_date": _iso_date(
                            match.group("previous_decision_date")
                        ),
                        "previous_until": _iso_date(match.group("previous_until")),
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("commissioner"),
                    place=match.group("commissioner_place"), role="Sachwalter",
                    extra={
                        "action": "appointed",
                        "organization": match.group("commissioner_org").strip(),
                        "organization_uid": match.group("commissioner_uid"),
                        "address": match.group("commissioner_address").strip(),
                        "postal_code": match.group("commissioner_postal_code"),
                    },
                ),
            ]
        )

    match = _FR_INTENDED_ASSET_ACQUISITION_PRICE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed",
                "fr.text.intended_asset_acquisition_price_corrected.v1",
                {
                    "kind": "intended_asset_acquisition",
                    "action": "publication_corrected",
                    "asset": "social_shares",
                    "shares_count": _count(match.group("count")),
                    "share_nominal": match.group("nominal"),
                    "target": match.group("target").strip(),
                    "target_uid": match.group("target_uid"),
                    "target_place": match.group("target_place").strip(),
                    "price_limit": "maximum",
                    "price": match.group("price"),
                    "previous_price_limit": "minimum",
                    "previous_price": match.group("previous_price"),
                    "currency": "CHF",
                },
            )
        )

    match = _DE_HEAD_OFFICE_LEGACY_IDENTIFIER_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_identifier_changed",
                "de.text.head_office_legacy_identifier_removed.v1",
                {
                    "scope": "head_office",
                    "action": "legacy_identifier_removed",
                    "from": match.group("registry_id"),
                    "to": None,
                },
            )
        )

    match = _FR_REGISTRATION_SUPPLEMENT_REFERENCE_SHORT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected",
                "fr.text.registration_supplement_reference_short.v1",
                {
                    "action": "supplemented",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                },
            )
        )

    match = _DE_COMPANY_REINSTATED_BY_CANTONAL_COURT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "de.text.company_reinstated_by_cantonal_court.v1",
                {
                    "kind": "registration_reinstated",
                    "decision_date": _iso_date(match.group("date")),
                    "authority": match.group("authority").strip(),
                },
            )
        )

    match = _FR_FIVE_ASSOCIATES_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.five_associates_transfer_new_unsigned_associate.v1"
        sellers = [match.group("manager").strip(), *_split_fr_names(match.group("associates"))]
        transferred = _count(match.group("transferred"))
        for index, seller in enumerate(sellers):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant" if index == 0 else "associé",
                    extra={
                        "action": "shares_transferred",
                        "shares_before_reported": _count(match.group("before")),
                        "shares_transferred": transferred,
                        "shares_count": _count(match.group("remaining")),
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF",
                        "counterparty": match.group("buyer").strip(),
                    },
                )
            )
        events.append(
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("buyer"),
                place=match.group("place"), role="associé",
                extra={
                    "action": "appointed",
                    "new_associate": True,
                    "without_signature": True,
                    "heimat": match.group("origin").strip(),
                    "shares_received": transferred * len(sellers),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            )
        )

    match = _DE_MANAGEMENT_AUDIT_WAIVER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", "de.text.management_audit_waiver.v1",
                {
                    "kind": "limited_audit_waiver",
                    "action": "granted",
                    "date": _iso_date(match.group("date")),
                    "declarants": "management",
                },
            )
        )

    match = _FR_BRANCH_REMOVED_AFTER_SEAT_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "fr.text.branch_removed_after_seat_transfer.v1",
                {
                    "action": "removed_after_seat_transfer",
                    "from": match.group("from_place").strip(),
                    "to": match.group("to_place").strip(),
                    "branch_registry_id": match.group("registry_id"),
                    "successor_uid": match.group("uid"),
                },
            )
        )

    match = _FR_EXISTING_AND_NEW_ADMINISTRATORS_SIGNING_RESTRICTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrators_pair_signing_restricted.v1"
        for group in ("existing1", "existing2"):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "signing_authority_changed", rule_id, match.group(group),
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "continued_with_restriction",
                        "cannot_sign_with_each_other": True,
                    },
                )
            )
        for index in (1, 2):
            events.append(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(f"new{index}"),
                    place=match.group(f"place{index}"), role="administrateur",
                    signing="Kollektivunterschrift zu zweien",
                    extra={
                        "action": "appointed",
                        "heimat": match.group(f"origin{index}").strip(),
                        "cannot_sign_with_each_other": True,
                    },
                )
            )

    match = _DE_BRANCH_RELOCATION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", "de.text.branch_relocation_fragment.v1",
                {
                    "action": "seat_changed",
                    "from": "Zürich",
                    "to": match.group("to_place").strip(),
                    "branch_uid": match.group("uid"),
                    "register_canton": match.group("register_canton").upper(),
                },
            )
        )

    match = _DE_LLC_TO_CORPORATION_TRANSFORMATION.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.llc_to_corporation_transformation.v1"
        common = {
            "action": "transformed",
            "from_legal_form": "Gesellschaft mit beschränkter Haftung",
            "to_legal_form": "Aktiengesellschaft",
            "transformation_plan_date": _iso_date(match.group("plan_date")),
            "balance_sheet_date": _iso_date(match.group("balance_date")),
            "assets": match.group("assets"),
            "liabilities": match.group("liabilities"),
            "currency": "CHF",
        }
        events.extend(
            [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "legal_form_changed", rule_id,
                    {
                        **common,
                        "capital_after_increase": match.group("capital"),
                        "shares_issued": _count(match.group("shares")),
                        "share_kind": "Namenaktien",
                        "share_nominal": match.group("share_nominal"),
                    },
                ),
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "capital_changed", rule_id,
                    {
                        "kind": "capital_increased_for_transformation",
                        "to_nominal": match.group("capital"),
                        "shares_count": _count(match.group("shares")),
                        "share_kind": "Namenaktien",
                        "share_nominal": match.group("share_nominal"),
                        "currency": "CHF",
                    },
                ),
            ]
        )

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
