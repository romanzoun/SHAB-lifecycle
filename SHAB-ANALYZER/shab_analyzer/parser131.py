from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATORS_BECOME_LIQUIDATORS = re.compile(
    r"^Par conséquent,\s*les administrateurs\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?)\s+sont liquidateurs et continuent de signer "
    r"individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_MERGER = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven des\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Bilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf den übernehmenden Verein über\.\s*"
    r"Die Mitglieder des übertragenden Vereins werden zu Mitgliedern des "
    r"übernehmenden Vereins\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED = re.compile(
    r"^\[Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte Kapitalerhöhung "
    r"infolge Zeitablaufs\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTION = re.compile(
    r"^Statutendatum:\s*(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(nicht:\s*(?P<previous_date>\d{2}\.\d{2}\.\d{4})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSET_TRANSFER_TO_COMPANY = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des actifs pour CHF\s+"
    r"(?P<assets>[\d'.]+)\s+et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+(?P<place>[^.]+)\.\s*"
    r"Contre-prestation:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_OFFICER_APPOINTMENT_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que\s+"
    r"(?P<vice>[^,.;]+)\s+est nommé vice-président et\s+"
    r"(?P<secretary>[^,.;]+),\s*secrétaire\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLUTION_LIQUIDATORS = re.compile(
    r"^Selon décision de son assemblée générale du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}),\s*l['’]association a "
    r"prononcé sa dissolution\.\s*\((?P<german_name>[^)]+)\)\s*"
    r"\((?P<italian_name>[^)]+)\)\.\s*(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?)\s+sont nommés liquidateurs toutefois pas entre eux,\s*"
    r"et\s+(?P<name3>[^,.;]+),\s*(?P<name4>[^,.;]+),\s*"
    r"(?P<name5>[^,.;]+)\s+et\s+(?P<name6>[^,.;]+)\s+sont nommés "
    r"liquidateurs avec signature collective à deux,\s*toutefois pas entre eux\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_SELLERS_TO_TWO_MANAGERS = re.compile(
    r"^(?P<seller1>[^,.;]+?)\s+et\s+(?P<seller2>[^,.;]+?)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+respectivement à\s+(?P<buyer1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s+"
    r"(?P<place1>[^,.;]+),\s*et\s+(?P<buyer2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*nouveaux associés-gérants avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\s+"
    r"chacun;\s*(?P=seller1)\s+et\s+(?P=seller2)\s+restent titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\s+"
    r"chacun\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die gewährte definitive Nachlassstundung um\s+"
    r"(?P<duration>\w+)\s+Monate bis zum\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_REMOVED_AND_AUDITOR_ADDED = re.compile(
    r"^Die Eintragung betreffend die Erklärung vom\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+über den Verzicht auf die eingeschränkte "
    r"Revision ist gelöscht\.\s*Revisionsstelle neu:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIGNING_SUPPLEMENT_UNRESTRICTED = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que l['’]administrateur "
    r"vice-président\s+(?P<name>[^,.;]+)\s+continue à signer collectivement à "
    r"deux,\s*désormais sans restriction\.?$",
    re.I | re.UNICODE,
)
_FR_SUPERVISORY_VALIDATION_FRAGMENT = re.compile(
    r"^et validés par décision de l['’](?P<authority>Autorité de surveillance) du\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_ADDITIONAL_BUSINESS_ADDRESS = re.compile(
    r"^Weitere Geschäftsadresse:\s*(?P<street>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_INCORRECT_SECRETARY_ROLE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+n['’]est pas\s+(?P<incorrect_role>secrétaire hors conseil)\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*qui est maintenant à\s+(?P<seller_place>[^,.;]+),\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant président avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMIN_SECRETARY_AND_SIGNER_CHANGES = re.compile(
    r"^(?P<name1>[^,.;]+),\s*dont la signature est radiée,\s*reste administrateur "
    r"et secrétaire\.\s*(?P<name2>[^,.;]+),\s*maintenant de\s+"
    r"(?P<origin>[^,.;]+),\s*continue à signer collectivement à deux,\s*"
    r"toutefois désormais sans restriction\.?$",
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
_DE_NUMBERS = {"ein": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.lower().replace("1er", "1").split()
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


def extract_parser131_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 131."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ADMINISTRATORS_BECOME_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administrators_become_liquidators_individual.v1"
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="administrateur et liquidateur", signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator", "continues_signing": True},
            ))

    match = _DE_ASSOCIATION_MERGER.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.association_merger_members_transfer.v1",
            {
                "kind": "absorption", "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("place").strip(),
                "absorbed_uid": match.group("uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "currency": "CHF", "members_became_acquirer_members": True,
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_expired_time.v1",
            {
                "kind": "authorized_capital_clause", "action": "removed",
                "authorization_date": _iso_date(match.group("date")),
                "reason": "authorization_expired",
            },
        ))

    match = _DE_STATUTES_DATE_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_correction_short.v1",
            {
                "action": "date_corrected", "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        ))

    match = _FR_ASSET_TRANSFER_TO_COMPANY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.asset_transfer_company_cash.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "recipient": match.group("recipient").strip(), "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"), "currency": "CHF",
            },
        ))

    match = _FR_OFFICER_APPOINTMENT_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.officer_appointment_supplement.v1"
        reference = {
            "action": "appointment_supplemented", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("vice"),
                role="vice-président", extra=reference,
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("secretary"),
                role="secrétaire", extra=reference,
            ),
        ])

    match = _FR_ASSOCIATION_DISSOLUTION_LIQUIDATORS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.association_dissolution_liquidators_restricted.v1"
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", rule_id,
            {
                "kind": "dissolved", "decision_date": _french_date(match.group("date")),
                "decision_body": "general_assembly",
                "translated_liquidation_names": [
                    match.group("german_name").strip(), match.group("italian_name").strip()
                ],
            },
        ))
        for index in range(1, 7):
            shared = "group_1" if index <= 2 else "group_2"
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur",
                signing=None if index <= 2 else "Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_liquidator", "signing_group": shared,
                    "cannot_sign_with_same_group": True,
                },
            ))

    match = _FR_TWO_SELLERS_TO_TWO_MANAGERS.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_sellers_to_two_managers.v1"
        sellers = [match.group("seller1").strip(), match.group("seller2").strip()]
        buyers = [match.group("buyer1").strip(), match.group("buyer2").strip()]
        transferred = _count(match.group("transferred"))
        for seller, buyer in zip(sellers, buyers):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ))
        for index, (buyer, seller) in enumerate(zip(buyers, sellers), start=1):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group(f"place{index}"),
                role="associé-gérant",
                extra={
                    "action": "shares_received_and_appointed", "counterparty": seller,
                    "heimat": match.group(f"origin{index}").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_duration.v1",
            {
                "kind": "composition_moratorium_extended", "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _DE_NUMBERS.get(match.group("duration").lower()),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _DE_AUDIT_WAIVER_REMOVED_AND_AUDITOR_ADDED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.audit_waiver_removed_auditor_added.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id,
                {
                    "kind": "limited_audit_waiver", "action": "removed",
                    "declaration_date": _iso_date(match.group("date")),
                    "limited_audit_waived": False,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="Revisionsstelle", uid=match.group("uid"),
                extra={"action": "appointed", "uid": match.group("uid")},
            ),
        ])

    match = _FR_SIGNING_SUPPLEMENT_UNRESTRICTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.signing_supplement_unrestricted.v1",
            match.group("name"), role="administrateur vice-président",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "restriction_removed", "continues_signing": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_SUPERVISORY_VALIDATION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.supervisory_validation_fragment.v1",
            {
                "action": "validated", "authority": match.group("authority"),
                "decision_date": _iso_date(match.group("date")),
            },
        ))

    match = _DE_ADDITIONAL_BUSINESS_ADDRESS.search(leftover)
    if match:
        consume(match)
        address = (
            f"{match.group('street').strip()}, {match.group('postal_code')} "
            f"{match.group('locality').strip()}"
        )
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.additional_business_address.v1",
            {
                "action": "added", "kind": "business_office", "address": address,
                "street": match.group("street").strip(),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_INCORRECT_SECRETARY_ROLE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.incorrect_secretary_role_corrected.v1",
            match.group("name"),
            extra={
                "action": "role_corrected", "incorrect_role": match.group("incorrect_role"),
                "role_applies": False, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_SHARE_TRANSFER_TO_MANAGER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.share_transfer_to_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé",
                extra={
                    "action": "domicile_changed_and_shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("remaining_nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant président",
                extra={
                    "action": "shares_received_and_appointed", "counterparty": seller,
                    "heimat": match.group("origin").strip(), "new_associate": True,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ])

    match = _FR_ADMIN_SECRETARY_AND_SIGNER_CHANGES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.admin_secretary_and_signer_changes.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name1"),
                role="administrateur et secrétaire",
                extra={"action": "signature_revoked", "remains_in_roles": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("name2"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "origin_changed_and_restriction_removed",
                    "heimat": match.group("origin").strip(), "continues_signing": True,
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
