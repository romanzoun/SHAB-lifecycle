from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_DISSOLUTION_COURT_BANKRUPTCY = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<decision_time>\d{1,2}:\d{2})\s+Uhr,\s*wurde die Gesellschaft "
    r"aufgelöst und ihre Liquidation nach den Vorschriften über den Konkurs "
    r"angeordnet\.?$",
    re.I | re.UNICODE,
)
_FR_GENERAL_DIRECTOR_APPOINTED = re.compile(
    r"^(?P<name>[^,.;]+?)\s+est nommé(?:e)?\s+"
    r"(?P<role>directeur général|directrice générale)\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_TYPO_CHANGED = re.compile(
    r"^Nouveaux\s+stauts\s+du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_NAME_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription\s+(?:n°|no|N[o°])\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(FOSC du\s+(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que la raison "
    r"de commerce du siège principal est\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_PROFIT_CERTIFICATES_COUNT_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N°|n°|no|N[o°])?\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"est corrigée en ce sens que les bons de jouissance sont au nombre de\s+"
    r"(?P<count>[\d']+)\s*\(et non de\s+(?P<previous_count>[\d']+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_ENTRY_ERRONEOUS = re.compile(
    r"^\[Der Eintrag betreffend des Konkursverfahrens erfolgte irrtümlich "
    r"und die Eintragung bleibt wie bisher bestehen\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_SIGNATURE_REVOKED = re.compile(
    r"^L['’](?P<role>associée gérante|associé gérant)\s+"
    r"(?P<name>[^,.;]+),\s*jusqu['’]ici ayant une signature individuelle,\s*"
    r"n['’]exerce plus la signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_CAPITAL_NOMINAL_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:N°|n°|no|N[o°])\s*"
    r"(?P<entry>[\d']+)\s+du\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"est rectifiée en ce sens que le capital social de\s+"
    r"(?P<currency>[A-Z]{3})\s+(?P<capital>[\d'.]+)\s+est composé de\s+"
    r"(?P<count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<nominal>[\d'.]+)\s*\(et non de parts de\s+"
    r"(?P=currency)\s+(?P<previous_nominal>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_AND_PAID = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<capital>[\d'.]+);\s*Liberierung:\s*"
    r"(?:(?P<paid_currency>[A-Z]{3})\s+)?(?P<paid>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_BRANCH_IDENTIFIER_REPLACED = re.compile(
    r"^(?P<place>[^:()\[\]]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[finora:\s*(?P<previous_place>[^()\[\]]+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_ONE_LIQUIDATOR = re.compile(
    r"^Selon décision de son assemblée générale du\s+"
    r"(?P<decision_date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"l['’]association a prononcé sa dissolution\.\s*Le membre du comité\s+"
    r"(?P<name>[^,.;]+?)\s+est élu liquidateur"
    r"(?P<signing>\s+avec signature individuelle)?\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_AUDIT_EXEMPTION_GRANTED = re.compile(
    r"^Die Aufsichtsbehörde hat mit Verfügung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+die Befreiung der Stiftung "
    r"von der Pflicht zur Bezeichnung einer Revisionsstelle genehmigt\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+?)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<buyer_place>[^,.;]+),\s*nouvelle associée,\s*titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de "
    r"CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_ASSOCIATES_TRANSFER_TO_MANAGER = re.compile(
    r"^(?P<seller1>[^,.;]+),\s*(?P<seller2>[^,.;]+),\s*"
    r"(?P<seller3>[^,.;]+),\s*et\s+(?P<seller4>.+?)\s*"
    r"\((?P<seller4_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"cèdent respectivement\s+(?P<transfer1>[\d']+),\s*"
    r"(?P<transfer2>[\d']+),\s*(?P<transfer3>[\d']+)\s+et\s+"
    r"(?P<transfer4>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvel associé-gérant"
    r"(?P<signing>\s+avec signature collective à deux)?,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.\s*(?P=seller1),\s*(?P=seller2),\s*"
    r"(?P=seller3),\s*et\s+(?P=seller4)\s*\((?P=seller4_uid)\)\s+sont "
    r"désormais respectivement titulaires de\s+(?P<remaining1>[\d']+),\s*"
    r"(?P<remaining2>[\d']+),\s*(?P<remaining3>[\d']+),\s*et\s+"
    r"(?P<remaining4>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_PERSON_DOMICILES_CHANGED = re.compile(
    r"^Eingetragene Personen geändert:\s*"
    r"(?P<name1>[^,;]+),\s*(?P<signing1>Kollektivunterschrift zu zweien),\s*"
    r"nun in\s+(?P<place1>[^,;]+);\s*(?P<name2>[^,;]+),\s*"
    r"(?P<role2>.+?),\s*(?P<signing2>Kollektivunterschrift zu zweien),\s*"
    r"nun in\s+(?P<place2>[^,;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ROLE_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?:n°|no|N[o°])\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s*,?\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+est en réalité\s+(?P<role>[^()]+?)\s*"
    r"\(et non pas\s+(?P<previous_role>[^()]+?)\)\.?$",
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
        role=role.strip() if role else None,
        signing=signing.strip() if signing else None,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser218_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 218."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_DISSOLUTION_COURT_BANKRUPTCY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.court_dissolution_bankruptcy_liquidation.v1", {
                "kind": "dissolution_due_to_bankruptcy",
                "action": "dissolved_and_liquidation_ordered",
                "authority": match.group("authority").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "decision_time": match.group("decision_time"),
                "liquidation_procedure": "bankruptcy",
            },
        )], ""

    match = _FR_GENERAL_DIRECTOR_APPOINTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.general_director_appointed.v1",
            match.group("name"), role=match.group("role"),
            extra={"action": "appointed"},
        )], ""

    match = _FR_STATUTES_TYPO_CHANGED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_changed_stauts_typo.v1", {
                "action": "changed", "date": _iso_date(match.group("date")),
                "source_heading_typo": "stauts",
            },
        )], ""

    match = _FR_HEAD_OFFICE_NAME_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.head_office_name_supplement.v1", {
                "kind": "head_office_name", "action": "publication_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
                "name": match.group("name").strip(),
                "head_office_uid": match.group("uid"),
            },
        )], ""

    match = _FR_PROFIT_CERTIFICATES_COUNT_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.profit_certificates_count_corrected.v1", {
                "kind": "profit_certificates", "action": "publication_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "count": _count(match.group("count")),
                "previous_count": _count(match.group("previous_count")),
            },
        )], ""

    if _DE_BANKRUPTCY_ENTRY_ERRONEOUS.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.bankruptcy_entry_erroneous.v1", {
                "kind": "bankruptcy_proceedings_entry",
                "action": "erroneous_entry_disregarded",
                "previous_registration_remains": True,
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_SIGNATURE_REVOKED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.associate_manager_signature_revoked.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "revoked", "previous_signing": "Einzelunterschrift",
                "without_signature": True,
            },
        )], ""

    match = _FR_SHARE_CAPITAL_NOMINAL_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_capital_nominal_corrected.v1", {
                "kind": "share_capital_structure", "action": "publication_corrected",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "capital": match.group("capital"),
                "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "previous_share_nominal": match.group("previous_nominal"),
                "currency": match.group("currency").upper(),
            },
        )], ""

    match = _DE_HEAD_OFFICE_CAPITAL_AND_PAID.fullmatch(leftover)
    if match:
        currency = match.group("currency").upper()
        paid_currency = (match.group("paid_currency") or currency).upper()
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_capital_paid.v1", {
                "kind": "head_office_capital", "action": "changed",
                "capital": match.group("capital"), "currency": currency,
                "paid": match.group("paid"), "paid_currency": paid_currency,
            },
        )], ""

    match = _IT_BRANCH_IDENTIFIER_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "it.text.branch_identifier_replaced.v1", {
                "kind": "branch_identifier", "action": "identifier_replaced",
                "place": match.group("place").strip(), "uid": match.group("uid"),
                "previous_place": match.group("previous_place").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
            },
        )], ""

    match = _FR_ASSOCIATION_DISSOLVED_ONE_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.text.association_dissolved_one_liquidator.v1"
        name = match.group("name")
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": _french_date(match.group("decision_date")),
                    "deciding_body": "assemblée générale",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, name,
                role="membre du comité et liquidateur",
                signing=("Einzelunterschrift" if match.group("signing") else None),
                extra={
                    "action": "appointed_liquidator",
                    "previous_role": "membre du comité",
                },
            ),
        ], ""

    match = _DE_FOUNDATION_AUDIT_EXEMPTION_GRANTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed",
            "de.text.foundation_audit_exemption_granted_decision.v1", {
                "kind": "auditor_appointment_exemption", "action": "granted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": "Aufsichtsbehörde", "organization_kind": "foundation",
            },
        )], ""

    match = _FR_ASSOCIATE_TRANSFER_TO_ORGANIZATION.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.associate_transfer_to_organization.v1"
        transferred = _count(match.group("transferred"))
        before = _count(match.group("before"))
        remaining = _count(match.group("remaining"))
        buyer_count = _count(match.group("buyer_count"))
        if before - transferred == remaining and transferred == buyer_count:
            common = {"currency": "CHF", "share_nominal": match.group("nominal")}
            seller = match.group("seller")
            buyer = match.group("buyer")
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        **common, "action": "shares_transferred",
                        "counterparty": buyer.strip(), "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"), role="associée",
                    uid=match.group("buyer_uid"), extra={
                        "action": "appointed_and_shares_received",
                        "counterparty": seller.strip(), "new_associate": True,
                        "organization": True, "shares_received": transferred,
                        "shares_count": buyer_count,
                        "share_nominal": match.group("buyer_nominal"),
                        "currency": "CHF",
                    },
                ),
            ], ""

    match = _FR_FOUR_ASSOCIATES_TRANSFER_TO_MANAGER.fullmatch(leftover)
    if match:
        transfers = [_count(match.group(f"transfer{index}")) for index in range(1, 5)]
        remaining = [_count(match.group(f"remaining{index}")) for index in range(1, 5)]
        buyer_count = _count(match.group("buyer_count"))
        if sum(transfers) == buyer_count:
            rule_id = "fr.persons.four_associates_transfer_to_manager.v1"
            buyer = match.group("buyer").strip()
            events: list[Event] = []
            for index in range(1, 5):
                seller = match.group(f"seller{index}")
                seller_uid = match.group("seller4_uid") if index == 4 else None
                events.append(_person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé",
                    uid=seller_uid, extra={
                        "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": transfers[index - 1] + remaining[index - 1],
                        "shares_transferred": transfers[index - 1],
                        "shares_count": remaining[index - 1],
                        "share_nominal": match.group("remaining_nominal"),
                        "currency": "CHF", "organization": index == 4,
                    },
                ))
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé-gérant",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing") else None
                ),
                extra={
                    "action": "appointed_manager_and_shares_received",
                    "origin": match.group("origin").strip(), "new_associate": True,
                    "counterparties": [
                        match.group(f"seller{index}").strip() for index in range(1, 5)
                    ],
                    "shares_received": buyer_count, "shares_count": buyer_count,
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ))
            return events, ""

    match = _DE_TWO_PERSON_DOMICILES_CHANGED.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_domiciles_changed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), signing=match.group("signing1"),
                extra={"action": "domicile_changed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role=match.group("role2"),
                signing=match.group("signing2"),
                extra={"action": "domicile_changed"},
            ),
        ], ""

    match = _FR_ROLE_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.role_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "role_corrected",
                "previous_role": match.group("previous_role").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    return [], leftover
