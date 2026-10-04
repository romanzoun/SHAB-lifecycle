from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_DOCUMENT_LIST_SUPPLEMENTED_TYPO = re.compile(
    r"^Die Liste der Belege? wurde ergänzt\.?$", re.I | re.UNICODE
)
_FR_MANAGERS_MOVED_PRESIDENT_INDIVIDUAL = re.compile(
    r"^Gérants:\s*(?P<president>[^,.;]+),\s*maintenant domicilié(?:e)? à\s*"
    r"(?P<president_place>[^(),.;]+?)\s*\((?P<president_canton>[^)]+)\),\s*"
    r"nommé(?:e)? président(?:e)?,\s*et\s*(?P<member>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<member_place>[^(),.;]+?)\s*\((?P<member_canton>[^)]+)\),\s*"
    r"lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_REGISTRATION_SUPPLEMENT_REFERENCE = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_id>\d+)\) est complétée en ce sens que\.?$",
    re.I | re.UNICODE,
)
_DE_NOMINAL_REDUCTION_AND_RESTORATION = re.compile(
    r"^Bei der Kapitalherabsetzung vom\s+(?P<reduction_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird der Nennwert der\s+(?P<count>[\d']+)\s+(?P<share_kind>Namenaktien)\s+"
    r"zu\s+(?P<currency>[A-Z]{3})\s+(?P<from_nominal>[\d'.]+)\s+auf\s+"
    r"[A-Z]{3}\s+(?P<reduced_nominal>[\d'.]+)\s+herabgesetzt\.\s*"
    r"Gleichzeitig wird bei der ordentlichen Kapitalerhöhung vom\s+"
    r"(?P<increase_date>\d{2}\.\d{2}\.\d{4})\s+der Nennwert dieser Aktien "
    r"durch Umwandlung von frei verwendbarem Eigenkapital auf\s+"
    r"[A-Z]{3}\s+(?P<restored_nominal>[\d'.]+)\s+erhöht\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED = re.compile(
    r"^Diese Gesellschaft, welche am\s+(?P<deleted_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"infolge Konkurses im Sinne von\s+(?P<legal_basis>Art\.\s*159 HRegV)\s+"
    r"gelöscht wurde, wird gemäss Entscheid des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder als durch Konkurs "
    r"aufgelöst in das Handelsregister eingetragen\.\s*Datum der "
    r"Konkurseröffnung:\s*(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"(?P<bankruptcy_time>\d{1,2}[.:]\d{2})\s+Uhr\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_AUDIT_EXEMPTION = re.compile(
    r"^Selon décision de l['’]autorité de surveillance du\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4}),\s*la fondation est "
    r"dispensée de désigner un organe de révision,\s*conformément à "
    r"l['’](?P<legal_basis>article 83b,\s*al\.\s*2 CC)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_DELETION_REINSTATED = re.compile(
    r"^(?:Berichtigung des im SHAB Nr\.\s*\d+ vom\s+\d{2}\.\d{2}\.\d{4}\s+"
    r"publizierten TR-Eintrags Nr\.\s*[\d']+ vom\s+"
    r"\d{2}\.\d{2}\.\d{4}\.\s*)?"
    r"Die mit Tagesregistereintrag vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"irrtümliche Löschung wird wieder ins Handelsregister eingetragen\.\s*"
    r"Die Publikation im SHAB Nr\.\s*(?P<issue>\d+) vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+wird widerrufen\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_RENAMED_MIXED_LANGUAGE = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d-]+)\),\s*(?P<role>Revisionsstelle),\s*"
    r"neue Firma\s+(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_ASSOCIATE_SELLER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*(?P<seller_role>associé-gérant),\s*cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^,.;]+),\s*nouvel associé avec\s+(?P<buyer_count>[\d']+) "
    r"parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*gérant\s+(?P=seller),\s*"
    r"lequel est élu président,\s*reste titulaire de\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BANKRUPTCY_EFFECT_SUSPENDED_DIRECT = re.compile(
    r"^(?P<authority>Le président du Tribunal de l['’]arrondissement de .+?)\s+"
    r"a prononcé l['’]effet suspensif de la faillite le\s+"
    r"(?P<date>\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|"
    r"septembre|octobre|novembre|décembre)\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ACTIVITY_REINSTATED = re.compile(
    r"^L['’]activité de l['’]entreprise individuelle n['’]ayant en réalité pas "
    r"cessé,\s*l['’]inscription est rétablie\.?$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_SEAT_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+) du\s*"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s*"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_id>\d+)\) est complétée en ce sens que le siège principal "
    r"est à\s+(?P<place>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_FOREIGN_COMPANY = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’](?P<seller_role>associé-gérant)\s+"
    r"(?P<seller>[^,.;]+) détient\s+(?P<seller_count>[\d']+) parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+) par suite de cession de\s+"
    r"(?P<transferred>[\d']+) parts à\s+(?P<buyer>.+?)\s*"
    r"\((?P<registry_id>[^)]+)\),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"(?P<country>[A-Z]{1,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+) parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_SEAT_TRANSFER_SIMPLE = re.compile(
    r"^La succursale\s+(?P<region>.+?)\s+a transféré son siège de\s+"
    r"(?P<from_place>[^()]+?)\s*\((?P<from_canton>[^)]+)\) à\s+"
    r"(?P<to_place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_SPLIT_SIGNING = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé(?:e)? président(?:e)?,\s*"
    r"(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+)\.\s*"
    r"Signature individuelle du président ou collective à deux des deux autres "
    r"membres du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE = re.compile(
    r"^L['’](?P<seller_role>associé-gérant)\s+(?P<seller>[^,.;]+),\s*"
    r"désormais à\s+(?P<seller_place>[^,.;]+),\s*cède\s+"
    r"(?P<transferred>[\d']+) de ses\s+(?P<before>[\d']+) parts de CHF\s+"
    r"(?P<nominal>[\d'.]+) à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s*"
    r"(?P<place>[^(),.;]+?)\s*\((?P<country>[^)]+)\),\s*nouvel associé,\s*"
    r"sans signature\.\s*(?P=seller) reste titulaire de\s+"
    r"(?P<seller_count>[\d']+) parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
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
    day, month, year = raw.lower().split()
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


def extract_parser97_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 97."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_DOCUMENT_LIST_SUPPLEMENTED_TYPO.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.documents_supplemented_typo.v1",
            {"kind": "documents_updated", "action": "supplemented"},
        ))

    match = _FR_MANAGERS_MOVED_PRESIDENT_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.managers_moved_president_individual.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                place=match.group("president_place"), role="gérant et président",
                signing="Einzelunterschrift",
                extra={
                    "action": "domicile_and_role_changed",
                    "place_canton": match.group("president_canton"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("member_place"), role="gérante",
                signing="Einzelunterschrift",
                extra={
                    "action": "appointed",
                    "nationality": match.group("origin").strip(),
                    "place_canton": match.group("member_canton"),
                },
            ),
        ])

    match = _FR_REGISTRATION_SUPPLEMENT_REFERENCE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "fr.text.registration_supplement_reference.v1",
            {
                "action": "registration_supplemented",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _DE_NOMINAL_REDUCTION_AND_RESTORATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.nominal_reduction_and_restoration.v1",
            {
                "kind": "nominal_value_reduction_and_increase",
                "reduction_date": _iso_date(match.group("reduction_date")),
                "increase_date": _iso_date(match.group("increase_date")),
                "shares_count": _count(match.group("count")),
                "share_kind": match.group("share_kind"),
                "from_nominal": match.group("from_nominal"),
                "reduced_nominal": match.group("reduced_nominal"),
                "restored_nominal": match.group("restored_nominal"),
                "currency": match.group("currency"),
                "increase_source": "freely_disposable_equity",
            },
        ))

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated.v1",
            {
                "kind": "bankruptcy_company_reinstated",
                "deleted_date": _iso_date(match.group("deleted_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "bankruptcy_time": match.group("bankruptcy_time").replace(".", ":"),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "dissolved_by_bankruptcy": True,
                "registry_reinstated": True,
            },
        ))

    match = _FR_FOUNDATION_AUDIT_EXEMPTION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.foundation_audit_exemption.v1",
            {
                "kind": "auditor_appointment_exemption",
                "action": "granted",
                "entity": "foundation",
                "date": _french_date(match.group("date")),
                "authority": "autorité de surveillance",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        ))

    match = _DE_ERRONEOUS_DELETION_REINSTATED.search(leftover)
    if match:
        consume(match)
        common = {
            "entry_date": _iso_date(match.group("entry_date")),
            "issue": match.group("issue"),
            "notice_date": _iso_date(match.group("notice_date")),
        }
        rule_id = "de.text.erroneous_deletion_reinstated.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {"kind": "registry_reinstatement", "action": "reinstated", **common},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {"kind": "notice", "action": "revoked", **common},
            ),
        ])

    match = _DE_AUDITOR_RENAMED_MIXED_LANGUAGE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_renamed_mixed_language.v2",
            match.group("name"), uid=match.group("uid"), role=match.group("role"),
            extra={
                "action": "company_name_and_identifier_changed",
                "previous_name": match.group("previous").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
                "uid": match.group("uid"),
            },
        ))

    match = _FR_TRANSFER_TO_ASSOCIATE_SELLER_PRESIDENT.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.transfer_to_associate_seller_president.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                role="associé-gérant et président",
                extra={
                    "action": "shares_transferred_and_elected_president",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_BANKRUPTCY_EFFECT_SUSPENDED_DIRECT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.bankruptcy_effect_suspended_direct.v1",
            {
                "kind": "bankruptcy_effect_suspended",
                "decision_date": _french_date(match.group("date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _FR_SOLE_PROPRIETOR_ACTIVITY_REINSTATED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.sole_proprietor_activity_reinstated.v1",
            {
                "kind": "registration_reinstated",
                "entity": "sole_proprietorship",
                "reason": "activity_had_not_ceased",
            },
        ))

    match = _FR_HEAD_OFFICE_SEAT_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.head_office_seat_supplement.v1",
            {
                "scope": "head_office",
                "action": "registration_supplemented",
                "to": match.group("place").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
            },
        ))

    match = _FR_TRANSFER_TO_FOREIGN_COMPANY.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.transfer_to_foreign_company.v1"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role=match.group("seller_role"),
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée",
                extra={
                    "action": "appointed",
                    "organization": True,
                    "registry_id": match.group("registry_id").strip(),
                    "country_code": match.group("country"),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"),
                    "currency": "CHF",
                },
            ),
        ])

    match = _FR_BRANCH_SEAT_TRANSFER_SIMPLE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.branch_seat_transfer_simple.v1",
            {
                "scope": "branch",
                "region": match.group("region").strip(),
                "from": match.group("from_place").strip(),
                "from_canton": match.group("from_canton").strip(),
                "to": match.group("to_place").strip(),
                "branch_uid": match.group("uid"),
            },
        ))

    match = _FR_ADMINISTRATION_THREE_SPLIT_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.administration_three_split_signing.v1"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("president"),
            role="président du conseil d'administration",
            signing="Einzelunterschrift", extra={"action": "appointed"},
        ))
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role="membre du conseil d'administration",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                },
            ))

    match = _FR_TRANSFER_TO_NEW_UNSIGNED_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        rule_id = "fr.persons.transfer_to_new_unsigned_associate.v2"
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role=match.group("seller_role"),
                extra={
                    "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("seller_count")),
                    "share_nominal": match.group("seller_nominal"),
                    "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    "action": "appointed",
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country").strip(),
                    "counterparty": seller,
                    "shares_received": transferred,
                    "shares_count": transferred,
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                    "without_signature": True,
                },
            ),
        ])

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
