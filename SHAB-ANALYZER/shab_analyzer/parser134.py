from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADDRESS_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"l['’]adresse exacte est\s*:\s*(?P<address>.+?)\s*"
    r"\(et non pas\s+(?P<previous_address>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_RESOLUTION_REVOKED = re.compile(
    r"^Mit Beschluss vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat die "
    r"Generalversammlung ihren Beschluss betreffend Auflösung der Gesellschaft vom\s+"
    r"(?P<original_date>\d{2}\.\d{2}\.\d{4})\s+widerrufen\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGERS_PRESIDENT_AND_SIGNING_CHANGED = re.compile(
    r"^Gérants\s*:\s*(?P<president>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*président,\s*et\s+"
    r"(?P<manager>[^,.;]+),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de\s+(?P=manager)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_ANCILLARY_OBLIGATIONS_NEGATED_VARIANT = re.compile(
    r"^\[non:\s*(?:Obligations de fournir des\s+)?prestations accessoires,\s*"
    r"droits de préférence,\s*de préemption ou d['’]emption:\s*"
    r"(?P<reference>pour les détails,\s*voir les statuts|selon statuts)\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_CORRECTION = re.compile(
    r"^In dem mit SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+wurde "
    r"der Text für die Aufhebung des Verzichts auf die eingeschränkte Revision "
    r"aufgrund eines Systemfehlers falsch wiedergegeben\.\s*Richtig wäre:\s*"
    r"\[Der Verzicht auf eingeschränkte Revision wurde aufgehoben\.\]\s*"
    r"\[gestrichen:\s*Gemäss Erklärung der Gründerin vom\s+"
    r"(?P<declaration_date>\d{2}\.\d{2}\.\d{4})\s+untersteht die Gesellschaft "
    r"keiner ordentlichen Revision und verzichtet auf eine eingeschränkte Revision\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_TWO_DECISION_DATES = re.compile(
    r"^(?P<prefix_date>\d{2}\.\d{2}\.\d{4})\.\s*Die Gesellschaft hat mit "
    r"Beschluss vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+bzw\.\s*"
    r"(?P<additional_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_LIMITED_PARTNER_WITH_PROCURATION = re.compile(
    r"^Nouvelle associée commanditaire\s*:\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+),\s*avec une commandite de CHF\s+"
    r"(?P<contribution>[\d'.]+),\s*laquelle engage la société par "
    r"procuration individuelle\.?$",
    re.I | re.UNICODE,
)
_DE_INTENDED_SOLE_PROPRIETORSHIP_ACQUISITION_FRAGMENT = re.compile(
    r'^eingetragenen,\s*unter der Firma\s+["“](?P<source_name>.+?)["”]\s+'
    r"geführten Einzelunternehmens,\s*in\s+(?P<source_place>[^,.;]+),\s*"
    r"mit sämtlichen Aktiven\s*\(inkl\.\s*(?P<included_asset>.+?)\)\s+und "
    r"Passiven gemäss einer noch zu erstellenden Übernahmebilanz zum Preis von "
    r"höchstens CHF\s+(?P<maximum_price>[\d'.]+)\s+zu übernehmen\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*de et à\s+(?P<place1>[^,.;]+),\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*sont membres du conseil,\s*sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_REINSTATEMENT_ORDERED_DECISION_FIRST = re.compile(
    r"^Selon décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<authority>.+?)\s+a ordonné la réinscription de la société "
    r"au registre du commerce\.?$",
    re.I | re.UNICODE,
)
_DE_AUDIT_WAIVER_ENTRY_REMOVED_AND_AUDITOR_ADDED = re.compile(
    r"^Der Eintrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+betreffend den "
    r"Verzicht auf eine eingeschränkte Revision ist gelöscht\.\s*"
    r"Neue Revisionsstelle:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_ASSOCIATE_SHARE_BALANCES = re.compile(
    r"^(?P<seller1>[^,.;]+)\s+et\s+(?P<seller2>[^,.;]+)\s+ont cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+aux "
    r"nouveaux associés\s+(?P<buyer1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*"
    r"à\s+(?P<place1>[^,.;]+)\s+et\s+(?P<buyer2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3});\s*"
    r"lesquels associés n['’]exercent pas la signature sociale\.\s*Associés:\s*"
    r"(?P=seller1)\s+pour\s+(?P<seller_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal1>[\d'.]+),\s*(?P=seller2)\s+pour\s+"
    r"(?P<seller_count2>[\d']+)\s+parts de CHF\s+(?P<seller_nominal2>[\d'.]+),\s*"
    r"(?P=buyer1),?\s+pour\s+(?P<buyer_count1>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal1>[\d'.]+)\s+et\s+(?P=buyer2)\s+pour\s+"
    r"(?P<buyer_count2>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal2>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_ELECTED_LIQUIDATOR_TYPO = re.compile(
    r"^L['’]associé-géant\s+(?P<name>[^,.;]+),\s*dont la signature est "
    r"radiée,\s*est élu liquidateur\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_AND_SUBDIRECTOR_ROLE_SWAP = re.compile(
    r"^(?P<director>[^,.;]+),\s*jusqu['’]ici sous-directrice,\s*nommée "
    r"directrice,\s*signe désormais collectivement à deux sans autre restriction\.\s*"
    r"(?P<subdirector>[^,.;]+),\s*jusqu['’]ici directrice,\s*maintenant "
    r"sous-directrice,\s*continue à signer collectivement à deux,\s*"
    r"avec un administrateur\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_SUSPENSIVE_SIMPLE = re.compile(
    r"^Der Abteilungspräsident der\s+(?P<department>.+?)\s+des\s+"
    r"(?P<authority>.+?)\s+hat mit Entscheid vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der gegen die Konkurseröffnung "
    r"erhobenen Beschwerde aufschiebende Wirkung zuerkannt\.?$",
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
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser134_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 134."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_ADDRESS_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.address_corrected_exact.v1",
            {
                "action": "corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "to": match.group("address").strip(),
                "from": match.group("previous_address").strip(),
            },
        ))

    match = _DE_DISSOLUTION_RESOLUTION_REVOKED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.dissolution_resolution_revoked.v1",
            {
                "kind": "dissolution_revoked",
                "action": "reinstated",
                "decision_date": _iso_date(match.group("decision_date")),
                "original_date": _iso_date(match.group("original_date")),
                "deciding_body": "Generalversammlung",
            },
        ))

    match = _FR_MANAGERS_PRESIDENT_AND_SIGNING_CHANGED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.managers_president_and_signing_changed.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("place"), role="gérant président",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed_president",
                    "heimat": match.group("origin").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group("manager"),
                role="gérant", signing="Kollektivunterschrift zu zweien",
                extra={"action": "signing_changed"},
            ),
        ])

    match = _FR_ANCILLARY_OBLIGATIONS_NEGATED_VARIANT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.ancillary_obligations_negated_variant.v1",
            {
                "kind": "ancillary_obligations",
                "action": "correction_negated",
                "statutes_reference": match.group("reference").strip(),
            },
        ))

    match = _DE_AUDIT_WAIVER_CORRECTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "de.text.audit_waiver_correction.v1",
            {
                "kind": "limited_audit_waiver",
                "action": "removed",
                "limited_audit_waived": False,
                "correction_reason": "system_error",
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "declaration_date": _iso_date(match.group("declaration_date")),
            },
        ))

    match = _DE_AUTHORIZED_CAPITAL_TWO_DECISION_DATES.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_two_decision_dates.v1",
            {
                "kind": "authorized_capital",
                "action": "introduced",
                "decision_date": _iso_date(match.group("decision_date")),
                "additional_decision_date": _iso_date(match.group("additional_date")),
                "prefix_date": _iso_date(match.group("prefix_date")),
            },
        ))

    match = _FR_NEW_LIMITED_PARTNER_WITH_PROCURATION.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.new_limited_partner_with_procuration.v1",
            match.group("name"), place=match.group("place"),
            role="associée commanditaire", signing="Einzelprokura",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "limited_partnership_contribution": match.group("contribution"),
                "currency": "CHF",
            },
        ))

    match = _DE_INTENDED_SOLE_PROPRIETORSHIP_ACQUISITION_FRAGMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.intended_sole_proprietorship_acquisition_fragment.v1",
            {
                "kind": "intended_asset_acquisition",
                "action": "introduced",
                "source": match.group("source_name").strip(),
                "source_place": match.group("source_place").strip(),
                "included_asset": match.group("included_asset").strip(),
                "maximum_price": match.group("maximum_price"),
                "currency": "CHF",
                "includes_all_assets_and_liabilities": True,
                "balance_sheet_pending": True,
            },
        ))

    match = _FR_TWO_BOARD_MEMBERS_WITHOUT_SIGNATURE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_board_members_without_signature.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="membre du conseil",
                extra={
                    "action": "appointed",
                    "heimat": match.group("place1").strip(),
                    "without_signature": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="membre du conseil",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin2").strip(),
                    "country": match.group("country2").upper(),
                    "without_signature": True,
                },
            ),
        ])

    match = _FR_REINSTATEMENT_ORDERED_DECISION_FIRST.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.reinstatement_ordered_decision_first.v1",
            {
                "kind": "company_reinstated",
                "action": "reinstatement_ordered",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_AUDIT_WAIVER_ENTRY_REMOVED_AND_AUDITOR_ADDED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.audit_waiver_entry_removed_auditor_added.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "audit_requirement_changed", rule_id,
                {
                    "kind": "limited_audit_waiver",
                    "action": "removed",
                    "entry_date": _iso_date(match.group("date")),
                    "limited_audit_waived": False,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="Revisionsstelle",
                extra={"action": "appointed", "uid": match.group("uid")},
            ),
        ])

    match = _FR_FOUR_ASSOCIATE_SHARE_BALANCES.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.four_associate_share_balances.v1"
        common = {"currency": "CHF", "share_nominal": match.group("nominal")}
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="associé",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "joint_shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group(f"seller_count{index}")),
                },
            ))
        for index in (1, 2):
            extra = {
                **common,
                "action": "shares_received",
                "new_associate": True,
                "without_signature": True,
                "shares_count": _count(match.group(f"buyer_count{index}")),
                "shares_received": _count(match.group(f"buyer_count{index}")),
                "heimat": match.group(f"origin{index}").strip(),
            }
            if index == 2:
                extra["country"] = match.group("country2").upper()
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"buyer{index}"),
                place=match.group(f"place{index}"), role="associé", extra=extra,
            ))

    match = _FR_ASSOCIATE_MANAGER_ELECTED_LIQUIDATOR_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_manager_elected_liquidator_typo.v1",
            match.group("name"), role="associé-gérant et liquidateur",
            extra={
                "action": "appointed_liquidator",
                "signature_revoked": True,
                "source_role_typo": "associé-géant",
            },
        ))

    match = _FR_DIRECTOR_AND_SUBDIRECTOR_ROLE_SWAP.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.director_and_subdirector_role_swap.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("director"),
                role="directrice", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_and_signing_changed",
                    "previous_role": "sous-directrice",
                    "signing_restriction_removed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("subdirector"),
                role="sous-directrice", signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed",
                    "previous_role": "directrice",
                    "signing_restriction": "avec un administrateur",
                    "signing_continues": True,
                },
            ),
        ])

    match = _DE_BANKRUPTCY_APPEAL_SUSPENSIVE_SIMPLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_suspensive_simple.v1",
            {
                "kind": "bankruptcy_appeal_suspensive_effect",
                "action": "granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "department": match.group("department").strip(),
            },
        ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
