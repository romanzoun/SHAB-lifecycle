from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_ARBITRATION_CLAUSE_IN_STATUTES = re.compile(
    r"^Schiedsklausel gemäss näherer Umschreibung in den Statuten\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_BY_RESOLUTION = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Beschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte Kapitalerhöhung "
    r"infolge Zeitablaufs?\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_SOLE_PROPRIETOR_REGISTRATION_CONTINUED = re.compile(
    r"^Da (?:der Inhaber|die Inhaberin) den Geschäftsbetrieb weiterführt,\s*"
    r"bleibt der Eintrag des Einzelunternehmens bestehen\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_FOREIGN_ASSOCIATE_WITH_COUNTRY_CODE = re.compile(
    r"^Nouve(?:l|lle) associé(?:e)?:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_FR_ADDITIONAL_ADDRESS_REGISTER_REMOVAL_FRAGMENT = re.compile(
    r"^\[L['’]inscription de du registre du commerce\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_AGREEMENT_WITH_ASSIGNMENT_CONFIRMED = re.compile(
    r"^Mit Verfügung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+den Nachlassvertrag mit Vermögensabtretung bestätigt\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_PROMOTED_AND_SECRETARY_APPOINTED = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*directeur,\s*nommé président,\s*"
    r"et\s+(?P<secretary>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*secrétaire,\s*"
    r"lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSET_TRANSFER_CASH = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_EXPIRED_APPOINTED_MANAGER = re.compile(
    r"^(?P<name>[^,.;]+),\s*dont la procuration est éteinte,\s*"
    r"est nommée gérante\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Les membres du conseil de fondation\s+(?P<signed>.+?)\s+"
    r"sont désignés liquidateurs(?: avec signature collective à deux)?(?:\.\s*|\s+)"
    r"Les membres du conseil de fondation\s+(?P<unsigned>.+?)\s+"
    r"sont désignés liquidateurs sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_PRESIDENT_SHARE_TRANSFER_AND_SECOND_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+),\s*lequel est désormais à\s+"
    r"(?P<seller_place>[^,.;]+)\s+et élu président,\s*cède une de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<buyer_place>[^,.;]+),\s*"
    r"nouvel associé avec\s+(?P<buyer_count>[\d']+)\s+part(?:s)? de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*gérant\s*;\s*(?P=seller)\s+reste "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.\s*L['’]associée\s+"
    r"(?P<manager>[^,.;]+),\s*qui est désormais à\s+"
    r"(?P<manager_place>[^,.;]+),\s*est nommée gérante avec signature individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTERED_SHARE_TRANSFER_RESTRICTION_REMOVED_STATUTORY = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+ne sont désormais plus restreintes quant à leur "
    r"transmissibilité selon les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_AUDIT_EXEMPTION = re.compile(
    r"^Selon dispense de l['’]autorité cantonale de surveillance des fondations "
    r"et des institutions de prévoyance du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la fondation n['’]est pas soumise à un "
    r"contrôle ordinaire et renonce à un contrôle restreint\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATRICES_AND_LIQUIDATION_ADDRESS = re.compile(
    r"^Liquidatrices:\s*(?P<president>[^,.;]+),\s*présidente,\s*et\s+"
    r"(?P<secretary>[^,.;]+),\s*secrétaire,\s*toutes deux gérantes,\s*"
    r"lesquelles continuent de signer individuellement\.\s*"
    r"Domicile de liquidation:\s*(?P<street>.+?)\s+(?P<street_number>\d+[A-Za-z]?),\s*"
    r"c/o\s+(?P<care_of>.+?),\s*(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_REINSTATED_BANKRUPTCY_REACTIVATED = re.compile(
    r"^La società è reiscritta come società in liquidazione giusta\s+"
    r"(?P<legal_basis>l['’]art\.\s*164 cpv\.\s*1 lett\.\s*d\) ORC)\s+con decreto "
    r"della\s+(?P<authority>.+?)\s+del\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"La procedura di fallimento è riattivata con medesimo decreto\.\s*"
    r"\[finora:\s*La procedura di fallimento è stata sospesa per mancanza di "
    r"attivo con decreto della\s+(?P<previous_authority>.+?)\s+del\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.\s*(?P<deletion_warning>.+?)\]\.?\s*"
    r"\[radiati:\s*(?P<previous_deletion>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_GRANTED_DIRECTOR_WITH_USAGE_NAME = re.compile(
    r"^Signature collective à deux a été conférée à\s+(?P<name>.+?),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3}),\s*"
    r"(?P<role>directrice)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _split_french_names(raw: str) -> list[str]:
    return [
        name.strip()
        for name in re.split(r",\s*|\s+et\s+", raw, flags=re.I)
        if name.strip()
    ]


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


def extract_parser156_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 156."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_ARBITRATION_CLAUSE_IN_STATUTES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.arbitration_clause_in_statutes.v1",
            {"kind": "arbitration_clause", "present": True, "details_in_statutes": True},
        ))

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_BY_RESOLUTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_expired_resolution.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_expired",
            },
        ))

    match = _DE_SOLE_PROPRIETOR_REGISTRATION_CONTINUED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_registration_continued.v1",
            {"kind": "registration_continued", "business_continues": True},
        ))

    match = _FR_NEW_FOREIGN_ASSOCIATE_WITH_COUNTRY_CODE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_foreign_associate_country_code.v1",
            match.group("name"), place=match.group("place"), role="associé",
            extra={
                "action": "appointed", "new_associate": True,
                "origin": match.group("origin").strip(),
                "country": match.group("country").upper(),
            },
        ))

    match = _FR_ADDITIONAL_ADDRESS_REGISTER_REMOVAL_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.additional_address_register_removal_fragment.v1",
            {
                "kind": "additional_address", "action": "removed_from_register",
                "source_fragment": match.group(0),
            },
        ))

    match = _DE_COMPOSITION_AGREEMENT_WITH_ASSIGNMENT_CONFIRMED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.composition_agreement_assignment_confirmed.v1",
            {
                "kind": "composition_agreement_confirmed",
                "agreement_type": "assignment_of_assets",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_DIRECTOR_PROMOTED_AND_SECRETARY_APPOINTED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.director_promoted_secretary_appointed.v1"
        signing = "Kollektivunterschrift zu zweien"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="directeur et président", signing=signing,
                extra={"action": "appointed_president", "previous_role": "directeur"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                place=match.group("place"), role="secrétaire", signing=signing,
                extra={
                    "action": "appointed_secretary",
                    "origin": match.group("origin").strip(),
                },
            ),
        ])

    match = _FR_COMPANY_ASSET_TRANSFER_CASH.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.company_asset_transfer_cash.v1",
            {
                "source_kind": "société", "agreement_date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
            },
        ))

    match = _FR_PROXY_EXPIRED_APPOINTED_MANAGER.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.proxy_expired_appointed_manager.v1",
            match.group("name"), role="gérante",
            extra={
                "action": "appointed_manager", "previous_authority": "procuration",
                "previous_authority_expired": True,
            },
        ))

    match = _FR_FOUNDATION_MEMBERS_APPOINTED_LIQUIDATORS.search(leftover)
    if match:
        signed = _split_french_names(match.group("signed"))
        unsigned = _split_french_names(match.group("unsigned"))
        if signed and unsigned:
            consume(match)
            rule_id = "fr.persons.foundation_members_appointed_liquidators.v1"
            for name in signed:
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name,
                    role="membre du conseil de fondation et liquidateur",
                    signing="Kollektivunterschrift zu zweien",
                    extra={"action": "appointed_liquidator", "remains_board_member": True},
                ))
            for name in unsigned:
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, name,
                    role="membre du conseil de fondation et liquidateur",
                    signing="ohne Zeichnungsberechtigung",
                    extra={
                        "action": "appointed_liquidator", "remains_board_member": True,
                        "without_signature": True,
                    },
                ))

    match = _FR_PRESIDENT_SHARE_TRANSFER_AND_SECOND_MANAGER.search(leftover)
    if match:
        before = _count(match.group("before"))
        buyer_count = _count(match.group("buyer_count"))
        remaining = _count(match.group("remaining"))
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        if before == remaining + 1 and buyer_count == 1 and len(nominals) == 1:
            consume(match)
            rule_id = "fr.persons.president_share_transfer_and_second_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            nominal = match.group("nominal")
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, place=match.group("seller_place"),
                    role="associé et président",
                    extra={
                        "action": "appointed_president_and_share_transferred",
                        "domicile_changed": True, "counterparty": buyer,
                        "shares_before": before, "shares_transferred": 1,
                        "shares_count": remaining, "share_nominal": nominal,
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                    role="associé-gérant",
                    extra={
                        "action": "appointed_manager_and_shares_received",
                        "counterparty": seller, "new_associate": True,
                        "origin": match.group("origin").strip(), "shares_received": 1,
                        "shares_count": buyer_count, "share_nominal": nominal,
                        "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("manager"),
                    place=match.group("manager_place"), role="associée-gérante",
                    signing="Einzelunterschrift",
                    extra={"action": "appointed_manager", "domicile_changed": True},
                ),
            ])

    match = _FR_REGISTERED_SHARE_TRANSFER_RESTRICTION_REMOVED_STATUTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.registered_share_restriction_removed_statutory.v1",
            {
                "kind": "share_transfer_restriction", "action": "removed",
                "registered": True, "details_in_statutes": True,
                "currency": "CHF", "share_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
            },
        ))

    match = _FR_FOUNDATION_AUDIT_EXEMPTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.foundation_audit_exemption.v1",
            {
                "kind": "audit_exemption", "action": "granted",
                "decision_date": _iso_date(match.group("date")),
                "authority": (
                    "autorité cantonale de surveillance des fondations "
                    "et des institutions de prévoyance"
                ),
                "ordinary_audit_required": False,
                "limited_audit_waived": True,
            },
        ))

    match = _FR_TWO_LIQUIDATRICES_AND_LIQUIDATION_ADDRESS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_manager_liquidators_with_address.v1"
        for group, role in (("president", "présidente"), ("secretary", "secrétaire")):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group),
                role=f"gérante, {role} et liquidatrice", signing="Einzelunterschrift",
                extra={
                    "action": "appointed_liquidator", "remains_manager": True,
                    "signing_continues": True,
                },
            ))
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.liquidation_address.v1",
            {
                "kind": "liquidation_address", "action": "changed",
                "street": match.group("street").strip(),
                "street_number": match.group("street_number"),
                "care_of": match.group("care_of").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _IT_COMPANY_REINSTATED_BANKRUPTCY_REACTIVATED.search(leftover)
    if match:
        consume(match)
        common = {
            "decision_date": _iso_date(match.group("date")),
            "authority": match.group("authority").strip(),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_reinstated_bankruptcy_reactivated.v1",
                {
                    **common, "kind": "registration_reinstated",
                    "state": "in_liquidation", "legal_basis": match.group("legal_basis"),
                    "previous_deletion": match.group("previous_deletion").strip(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", "it.text.company_reinstated_bankruptcy_reactivated.v1",
                {
                    **common, "kind": "bankruptcy_reopened",
                    "previous_state": "suspended_for_lack_of_assets",
                    "previous_decision_date": _iso_date(match.group("previous_date")),
                    "previous_authority": match.group("previous_authority").strip(),
                    "previous_deletion_warning": match.group("deletion_warning").strip(),
                },
            ),
        ])

    match = _FR_SIGNING_GRANTED_DIRECTOR_WITH_USAGE_NAME.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.director_signing_usage_name.v1",
            match.group("name"), place=match.group("place"),
            role=match.group("role"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "granted", "origin": match.group("origin").strip(),
                "country": match.group("country").upper(),
            },
        ))

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
