from __future__ import annotations

import re

from .keys import person_key
from .models import Event


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


_DE_ART_934_DELETION_BLOCKED_FEDERAL = re.compile(
    r"^Das amtliche Verfahren zur Löschung der Rechtseinheit gemäss\s+"
    r"(?P<legal_basis>Art\.\s*934 OR i\.V\.m\. Art\.\s*153 HRegV)\s+"
    r"ist gemäss rechtskräftiger Verfügung vom\s+"
    r"(?P<date>\d{1,2}\.\s+(?:Januar|Februar|März|April|Mai|Juni|Juli|August|"
    r"September|Oktober|November|Dezember)\s+\d{4})\s+abgeschlossen\.\s*"
    r"Die Rechtseinheit kann mangels Zustimmung der\s+"
    r"(?P<tax_authority>Eidgenössischen Steuerverwaltungen)\s+noch nicht gelöscht werden\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_DEFINITIVE_MORATORIUM = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé au titulaire un sursis concordataire "
    r"définitif jusqu['’]au\s+(?P<until>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_SEAT_CHANGED = re.compile(
    r"^Sede principale a:\s*(?P<from>[^.]+)\.\s*"
    r"Nuova sede principale:\s*(?P<to>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_REGISTRATION_DATE_CORRECTED = re.compile(
    r"^Die Gesellschaft wurde am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"ins Handelsregister eingetragen,\s*nicht am\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_MIXED_FULL_ADDRESS_AND_REMOVED_FOUNDATION_MEMBER = re.compile(
    r"^Vollständige Adresse:\s*(?P<address>.+?)\.\s*Gelöschte Person:\s*"
    r"(?P<name>[^,.;]+),\s*(?P<role>Stiftungsratsmitglied),\s*"
    r"(?P<signing>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_BRANCH_CANTON_REGISTER = re.compile(
    r"^Zweigniederlassung neu:\s*\[gestrichen:\s*(?P<place>[^()\]]+?)\s*"
    r"\(HR\s+(?P<register_canton>[A-Z]{2})\)\]\.?$",
    re.I | re.UNICODE,
)
_DE_NAMED_ENTITY_ASSET_TRANSFER = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss Vertrag "
    r"vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s*von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ALL_SHARES_TRANSFERRED_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé ses\s+(?P<transferred>[\d']+)\s+"
    r"parts sociales de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+[\"“](?P<buyer>.+?)[\"”]\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"nouvelle associée avec\s+(?P<buyer_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_LIMITED_AND_TWO_GENERAL_PARTNERS = re.compile(
    r"^(?P<limited1>.+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est "
    r"maintenant associée commanditaire,\s*pour une commandite de CHF\s+"
    r"(?P<amount1>[\d']+(?:\.\d+)?\.-),\s*"
    r"(?P<limited2>.+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est "
    r"maintenant associée commanditaire,\s*pour une commandite de CHF\s+"
    r"(?P<amount2>[\d']+(?:\.\d+)?\.-),\s*et\s+"
    r"(?P<limited3>.+?)\s*\((?P<uid3>CHE-\d{3}\.\d{3}\.\d{3})\)\s+est "
    r"maintenant associée commanditaire,\s*pour une commandite de CHF\s+"
    r"(?P<amount3>[\d']+(?:\.\d+)?\.-)\.\s*"
    r"Nouveaux associés indéfiniment responsables:\s*"
    r"(?P<general1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"et\s+(?P<general2>[^,.;]+),\s*de\s+(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_SIMULTANEOUS_CAPITAL_REDUCTION_AND_INCREASE = re.compile(
    r"^Riduzione del capitale azionario di CHF\s+(?P<reduction>[\d'.]+)\s+"
    r"mediante annullamento di\s+(?P<cancelled_count>[\d']+)\s+azioni nominative "
    r"da CHF\s+(?P<cancelled_nominal>[\d'.]+)\.\s*Il capitale azionario è stato "
    r"simultaneamente aumentato mediante l['’]emissione di\s+"
    r"(?P<issued_count>[\d']+)\s+azioni nominative da CHF\s+"
    r"(?P<issued_nominal>[\d'.]+),\s*interamente liberate\.\s*"
    r"Fatti particolari:\s*Compensazione di crediti:\s*CHF\s+"
    r"(?P<setoff>[\d'.]+),\s*contro attribuzione di\s+(?P<setoff_count>[\d']+)\s+"
    r"azioni nominative da CHF\s+(?P<setoff_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de\s+(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+)\s+et\s+(?P<name2>[^,.;]+),\s*de\s+"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*sont membres du "
    r"conseil de fondation,\s*toutes deux\.?$",
    re.I | re.UNICODE,
)
_FR_INDIVIDUAL_PROXY_NAME_BEFORE_ROLE = re.compile(
    r"^Procuration individuelle a été conférée à\s+(?P<name>[^,.;]+),\s*"
    r"(?P<role>associé|associée)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_ROLE_CORRECTED_WITH_RESTRICTION = re.compile(
    r"^L['’]inscription\s+(?:N[o°]|n[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+n['’]est pas membre du conseil sans signature;\s*"
    r"elle est en réalité nommée\s+(?P<role>directrice),\s*avec\s+"
    r"(?P<required_with>un membre du conseil ou le directeur général)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SHARE_TRANSFER_AND_INDIVIDUAL_SIGNING = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associé\s+(?P<seller>[^,.;]+)\s+détient "
    r"désormais\s+(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+),\s*par suite de cession,\s*et signe maintenant "
    r"individuellement\.\s*Cessionnaire et nouvel associé:\s*"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_OPENING_REVOKED = re.compile(
    r"^Mit Beschluss vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die Verfügung des\s+(?P<court>.+?)\s+vom\s+"
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4})\s+betreffend die "
    r"Konkurseröffnung aufgehoben\.\s*Die Gesellschaft besteht entsprechend den "
    r"früheren Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_COLLECTIVE_PROXY_PAIR_WITH_REQUIRED_SIGNATORIES = re.compile(
    r"^Procuration collective à deux,\s*toutefois avec\s+(?P<required1>.+?)\s+et\s+"
    r"(?P<required2>.+?),\s*est conférée à\s+(?P<name1>.+?),\s*à\s+"
    r"(?P<place1>[^(),;]+)\s*\((?P<country1>[^()]+)\)\s+et\s+"
    r"(?P<name2>.+?),\s*à\s+(?P<place2>[^,.;]+),\s*tous deux de\s+"
    r"(?P<country2>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.lower().replace(".", "", 1).split()
    return f"{int(year):04d}-{_DE_MONTHS[month]:02d}-{int(day):02d}"


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
    uid: str | None = None,
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser118_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 118."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_ART_934_DELETION_BLOCKED_FEDERAL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.art_934_deletion_blocked_federal.v1",
            {
                "kind": "deletion_blocked",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "procedure_completed": True,
                "procedure_completed_at": _german_date(match.group("date")),
                "tax_authority": "federal",
                "tax_authority_consent_missing": True,
            },
        ))

    match = _FR_SOLE_PROPRIETOR_DEFINITIVE_MORATORIUM.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.sole_proprietor_definitive_moratorium.v1",
            {
                "kind": "composition_moratorium_granted",
                "moratorium_type": "definitive", "subject": "sole_proprietor",
                "decision_date": _iso_date(match.group("decision_date")),
                "until": _iso_date(match.group("until")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _IT_HEAD_OFFICE_SEAT_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "it.text.head_office_seat_changed.v1",
            {
                "scope": "head_office", "action": "changed",
                "from": match.group("from").strip(), "to": match.group("to").strip(),
            },
        ))

    match = _DE_REGISTRATION_DATE_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.registration_date_corrected.v1",
            {
                "kind": "registration_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_published_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _MIXED_FULL_ADDRESS_AND_REMOVED_FOUNDATION_MEMBER.search(leftover)
    if match:
        consume(match)
        rule_id = "mixed.persons.address_and_foundation_member_removed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {"action": "set", "address": match.group("address").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("name"),
                role=match.group("role"), signing=match.group("signing"),
                extra={"action": "removed"},
            ),
        ])

    match = _DE_REMOVED_BRANCH_CANTON_REGISTER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_removed_canton_register.v1",
            {
                "action": "removed", "place": match.group("place").strip(),
                "register_canton": match.group("register_canton").upper(),
            },
        ))

    match = _DE_NAMED_ENTITY_ASSET_TRANSFER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.named_entity_asset_transfer.v1",
            {
                "source": match.group("source").strip(),
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
            },
        ))

    match = _FR_ALL_SHARES_TRANSFERRED_TO_ORGANIZATION.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.all_shares_transferred_to_organization.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "all_shares_transferred", "counterparty": buyer,
                    "counterparty_uid": match.group("uid"),
                    "shares_transferred": transferred, "shares_count": 0,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", uid=match.group("uid"),
                extra={
                    "uid": match.group("uid"), "action": "shares_received",
                    "counterparty": seller, "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_THREE_LIMITED_AND_TWO_GENERAL_PARTNERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.limited_and_general_partners_added.v1"
        for index in range(1, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"limited{index}"),
                uid=match.group(f"uid{index}"), role="associée commanditaire",
                extra={
                    "uid": match.group(f"uid{index}"), "action": "appointed",
                    "limited_partnership_contribution": match.group(f"amount{index}"),
                    "currency": "CHF",
                },
            ))
        for index in range(1, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"general{index}"),
                place=match.group(f"place{index}"),
                role="associé indéfiniment responsable",
                extra={
                    "action": "appointed", "new_partner": True,
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _IT_SIMULTANEOUS_CAPITAL_REDUCTION_AND_INCREASE.search(leftover)
    if match:
        consume(match)
        rule_id = "it.text.simultaneous_capital_reduction_and_increase.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "action": "reduced", "amount": match.group("reduction"),
                    "currency": "CHF", "shares_cancelled": _count(match.group("cancelled_count")),
                    "share_nominal": match.group("cancelled_nominal"),
                    "share_kind": "azioni nominative",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "action": "increased", "simultaneous": True,
                    "currency": "CHF", "shares_issued": _count(match.group("issued_count")),
                    "share_nominal": match.group("issued_nominal"),
                    "share_kind": "azioni nominative", "fully_paid": True,
                    "consideration_kind": "claim_setoff",
                    "claims_set_off": match.group("setoff"),
                    "shares_allocated": _count(match.group("setoff_count")),
                    "allocated_share_nominal": match.group("setoff_nominal"),
                },
            ),
        ])

    match = _FR_TWO_FOUNDATION_MEMBERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_foundation_members_appointed.v1"
        for index in range(1, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil de fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_INDIVIDUAL_PROXY_NAME_BEFORE_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.individual_proxy_name_before_role.v1",
            match.group("name"), role=match.group("role"), signing="Einzelunterschrift",
            extra={"action": "proxy_granted"},
        ))

    match = _FR_DIRECTOR_ROLE_CORRECTED_WITH_RESTRICTION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_role_corrected_with_restriction.v1",
            match.group("name"), role=match.group("role"),
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "role_corrected", "previous_role": "membre du conseil",
                "previous_without_signature": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "required_with": ["un membre du conseil", "le directeur général"],
            },
        ))

    match = _FR_ASSOCIATE_SHARE_TRANSFER_AND_INDIVIDUAL_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_share_transfer_and_individual_signing.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        before = _count(match.group("before"))
        seller_count = _count(match.group("seller_count"))
        transferred = before - seller_count
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                signing="Einzelunterschrift",
                extra={
                    "action": "shares_transferred_and_signing_changed",
                    "counterparty": buyer, "shares_before": before,
                    "shares_transferred": transferred, "shares_count": seller_count,
                    "share_nominal": match.group("seller_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _DE_BANKRUPTCY_OPENING_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_opening_revoked.v1",
            {
                "kind": "bankruptcy_opening_revoked", "company_continues": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_court": match.group("court").strip(),
                "bankruptcy_decision_date": _iso_date(match.group("bankruptcy_date")),
                "previous": match.group("previous").strip(),
            },
        ))

    match = _FR_COLLECTIVE_PROXY_PAIR_WITH_REQUIRED_SIGNATORIES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.collective_proxy_pair_with_required_signatories.v1"
        required_with = [match.group("required1").strip(), match.group("required2").strip()]
        for index in range(1, 3):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="fondé de procuration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "proxy_granted", "required_with": required_with,
                    "country": match.group(f"country{index}").strip(),
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
