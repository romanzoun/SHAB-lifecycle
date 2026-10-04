from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_SIGNING_GRANTED_PROXY_REVOKED = re.compile(
    r"^Signature collective à deux de (?P<name>[^,.;]+);\s*"
    r"sa procuration est radiée\.?$",
    re.I | re.UNICODE,
)
_IT_ERRONEOUS_BANKRUPTCY_DISSOLUTION_ENTRY = re.compile(
    r"^\[La seguente iscrizione è stata iscritta erroneamente:\s*La società è "
    r"sciolta in seguito a fallimento pronunciato con decreto della "
    r"(?P<court>.+?) del (?P<decision_date>\d{2}\.\d{2}\.\d{4}) a far tempo "
    r"dal (?P<effective_date>\d{2}\.\d{2}\.\d{4}) alle ore "
    r"(?P<effective_time>\d{2}:\d{2})\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_VICE_PRESIDENT_AND_RESTRICTED_ADMINISTRATOR = re.compile(
    r"^(?P<vice_president>[^,.;]+) est nommé vice-président\.\s*"
    r"Nouvel administrateur toutefois avec le président ou le vice-président:\s*"
    r"(?P<administrator>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_MORATORIUM_AND_COMMISSIONER = re.compile(
    r"^Par décision du (?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?) a accordé au titulaire un sursis concordataire de "
    r"(?P<duration>[^,.;]+),\s*soit jusqu['’]au "
    r"(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<commissioner>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*est désigné en qualité "
    r"de commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_MODIFIED_AND_UNSIGNED_ADMINISTRATOR = re.compile(
    r"^Par décision du (?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"l['’]assemblée générale a modifié la clause statutaire du "
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4}) relative à une augmentation "
    r"autorisée du capital-actions selon statuts\.\s*Nouvel administrateur:\s*"
    r"(?P<name>[^,.;]+),\s*de et à\s*(?P<place>[^,.;]+),\s*"
    r"sans signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_POWERS_REVOKED_TYPO = re.compile(
    r"^Les pouvois des associés\s+(?P<name1>[^,.;]+),\s*jusqu['’]ici "
    r"(?P<role1>[^,.;]+),\s*et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici "
    r"(?P<role2>[^,.;]+),\s*sont radiés\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_REVOKED_APPOINTED_MANAGEMENT_MEMBER = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*est nommé(?:e)? "
    r"membre de la direction et engage désormais la société par sa signature "
    r"collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_SPLIT_THREE_CAPITAL_CLAUSES_AND_PROFIT_CERTIFICATES = re.compile(
    r"^Les (?P<from_count>[\d']+) actions nominatives de CHF "
    r"(?P<from_nominal>[\d'.]+),\s*formant l['’]entier du capital-actions,\s*"
    r"sont transformées en (?P<to_count>[\d']+) actions nominatives de CHF "
    r"(?P<to_nominal>[\d'.]+),\s*L['’]assemblée générale a introduit une clause "
    r"statutaire relative à une augmentation autorisée du capital par décision du "
    r"(?P<authorized_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*Pour les détails,\s*"
    r"voir les statuts\.\s*L['’]assemblée générale a introduit une clause "
    r"statutaire relative à une augmentation conditionnelle du capital-actions par "
    r"décision du (?P<conditional_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.\s*L['’]assemblée générale a introduit "
    r"une clause statutaire relative à une augmentation conditionnelle du "
    r"capital-participation par décision du "
    r"(?P<participation_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.\s*[ÉE]mission de bons de jouissance:\s*"
    r"(?P<certificate_count>[\d']+) bons de jouissance donnant droit à "
    r"(?P<rights>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_EQUAL_SHARES = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+),\s*désormais à "
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<seller2>[^,.;]+) cèdent chacun "
    r"(?P<transferred>[\d']+) de leurs (?P<before>[\d']+) parts de CHF "
    r"(?P<nominal>[\d'.]+) à l['’]associé-gérant (?P<buyer>[^,.;]+),\s*"
    r"désormais titulaire de (?P<buyer_count>[\d']+) parts de CHF "
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller1) et (?P=seller2) restent chacun "
    r"titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_MEMBER_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s*(?P<place>[^,.;]+),\s*président,\s*et\s*"
    r"(?P<member>[^,.;]+),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de (?P=member) sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_INDIVIDUAL = re.compile(
    r"^Administration:\s*(?P<member>[^,.;]+),\s*(?P<president>[^,.;]+),\s*"
    r"jusqu['’]ici (?P<previous_role1>[^,.;]+),\s*nommé président,\s*et\s*"
    r"(?P<changed_member>[^,.;]+),\s*jusqu['’]ici (?P<previous_role2>[^,.;]+),\s*"
    r"lesquels signent individuellement;\s*les pouvoirs de (?P=president) et "
    r"(?P=changed_member) sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_NAME_CHANGED = re.compile(
    r"^Sede principale a:\s*(?P<head_office>[^.]+)\.\s*Nuovo nome della ditta "
    r"della sede principale:\s*(?P<name>.+?)\s*\[finora:\s*(?P<previous_name>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_IT_STATUTES_DATE_CORRECTED = re.compile(
    r"^Data corretta dello statuto:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"\[non:\s*(?P<previous_date>\d{2}\.\d{2}\.\d{4})\]\.?$",
    re.I | re.UNICODE,
)
_FR_SEAT_CORRECTED = re.compile(
    r"^L['’]inscription\s+n[o°]\s*(?P<entry>[\d']+)\s+du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"le siège est à (?P<place>[^,.;]+) et non pas à "
    r"(?P<previous_place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_QUALIFIED_LIQUIDATORS_CONTINUE_INDIVIDUAL = re.compile(
    r"^Liquidateurs:\s*l['’]associé gérant\s+(?P<name1>[^,.;]+)\s+et le "
    r"directeur\s+(?P<name2>[^,.;]+),\s*lesquels continuent à signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_IT_BANKRUPTCY_APPEAL_REJECTED = re.compile(
    r"^Con decisione del (?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<authority>.+?) ha respinto il reclamo contro la decisione di apertura "
    r"del fallimento della (?P<court>.+?) del "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\.?$",
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
    day, month, year = raw.lower().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser138_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 138."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_SIGNING_GRANTED_PROXY_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_granted_proxy_revoked.v1",
            match.group("name"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "signing_changed", "previous_signing": "procuration",
                "previous_signing_revoked": True,
            },
        ))

    match = _IT_ERRONEOUS_BANKRUPTCY_DISSOLUTION_ENTRY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "it.text.erroneous_bankruptcy_dissolution_entry.v1",
            {
                "kind": "bankruptcy_dissolution", "action": "retracted_as_erroneous",
                "court": match.group("court").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "effective_date": _iso_date(match.group("effective_date")),
                "effective_time": match.group("effective_time"),
            },
        ))

    match = _FR_VICE_PRESIDENT_AND_RESTRICTED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.vice_president_and_restricted_administrator.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice_president"),
                role="vice-président", extra={"action": "appointed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("administrator"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                    "signing_with_roles": ["président", "vice-président"],
                },
            ),
        ])

    match = _FR_SOLE_PROPRIETOR_MORATORIUM_AND_COMMISSIONER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.sole_proprietor_moratorium_and_commissioner.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "composition_moratorium_granted", "subject": "sole_proprietor",
                    "decision_date": _french_date(match.group("decision_date")),
                    "duration": match.group("duration").strip(),
                    "until": _french_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("commissioner"),
                place=match.group("place"), role="commissaire au sursis",
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                },
            ),
        ])

    match = _FR_AUTHORIZED_CAPITAL_MODIFIED_AND_UNSIGNED_ADMINISTRATOR.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.authorized_capital_modified_and_unsigned_administrator.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "modified",
                    "decision_date": _iso_date(match.group("decision_date")),
                    "authorization_date": _iso_date(match.group("authorization_date")),
                    "details_in_statutes": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="administrateur",
                extra={
                    "action": "appointed", "heimat": match.group("place").strip(),
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_TWO_ASSOCIATE_POWERS_REVOKED_TYPO.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_associate_powers_revoked_typo.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group(f"name{index}"),
                role=match.group(f"role{index}").strip(),
                extra={"action": "powers_revoked", "associate": True},
            ))

    match = _FR_PROXY_REVOKED_APPOINTED_MANAGEMENT_MEMBER.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_revoked_appointed_management_member.v1",
            match.group("name"), role="membre de la direction",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed_and_signing_changed",
                "previous_signing": "procuration", "previous_signing_revoked": True,
            },
        ))

    match = _FR_SHARE_SPLIT_THREE_CAPITAL_CLAUSES_AND_PROFIT_CERTIFICATES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.share_split_three_capital_clauses_and_profit_certificates.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "share_split", "share_kind": "actions nominatives",
                    "currency": "CHF", "entire_share_capital": True,
                    "from_count": _count(match.group("from_count")),
                    "from_nominal": match.group("from_nominal"),
                    "to_count": _count(match.group("to_count")),
                    "to_nominal": match.group("to_nominal"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _french_date(match.group("authorized_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_capital_clause", "action": "introduced",
                    "decision_date": _french_date(match.group("conditional_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_clause",
                    "action": "introduced",
                    "decision_date": _french_date(match.group("participation_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "profit_certificates", "action": "issued",
                    "count": _count(match.group("certificate_count")),
                    "rights": match.group("rights").strip(),
                },
            ),
        ])

    match = _FR_TWO_MANAGERS_TRANSFER_EQUAL_SHARES.search(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("remaining_nominal"),
    }) == 1:
        consume(match)
        rule_id = "fr.persons.two_managers_transfer_equal_shares.v1"
        buyer = match.group("buyer").strip()
        transferred_each = _count(match.group("transferred"))
        common = {
            "share_nominal": match.group("nominal"), "currency": "CHF",
            "counterparty": buyer, "shares_before": _count(match.group("before")),
            "shares_transferred": transferred_each,
            "shares_count": _count(match.group("remaining")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller1"),
                place=match.group("place1"), role="associé-gérant",
                extra={"action": "domicile_changed_and_shares_transferred", **common},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("seller2"),
                role="associé-gérant", extra={"action": "shares_transferred", **common},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant",
                extra={
                    "action": "shares_received", "counterparties": [
                        match.group("seller1").strip(), match.group("seller2").strip(),
                    ],
                    "shares_received": transferred_each * 2,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_ADMINISTRATION_PRESIDENT_AND_MEMBER_COLLECTIVE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.president_and_member_collective_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="président",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("member"),
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "powers_changed"},
            ),
        ])

    match = _FR_ADMINISTRATION_THREE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_individual_signing.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                role="administrateur", signing="Einzelunterschrift",
                extra={"action": "administration_recorded"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift",
                extra={
                    "action": "role_and_powers_changed",
                    "previous_role": match.group("previous_role1").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("changed_member"),
                role=match.group("previous_role2").strip(), signing="Einzelunterschrift",
                extra={"action": "powers_changed"},
            ),
        ])

    match = _IT_HEAD_OFFICE_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.head_office_name_changed.v1",
            {
                "scope": "head_office", "head_office": match.group("head_office").strip(),
                "from": match.group("previous_name").strip(),
                "to": match.group("name").strip(),
            },
        ))

    match = _IT_STATUTES_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "it.text.statutes_date_corrected.v1",
            {
                "kind": "statutes_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_published_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_SEAT_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.seat_corrected.v1",
            {
                "action": "corrected", "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "from": match.group("previous_place").strip(),
                "to": match.group("place").strip(),
            },
        ))

    match = _FR_ROLE_QUALIFIED_LIQUIDATORS_CONTINUE_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.role_qualified_liquidators_continue_individual.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="associé gérant et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="directeur et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "signing_continues": True},
            ),
        ])

    match = _IT_BANKRUPTCY_APPEAL_REJECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.bankruptcy_appeal_rejected.v1",
            {
                "kind": "bankruptcy_opening_confirmed", "action": "appeal_rejected",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
