from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_STATUTES_RIGHTS_REMOVED_AND_TRANSFER_DEROGATION = re.compile(
    r"^Les statuts ne prévoient plus d['’]obligation de fournir des prestations "
    r"accessoires,\s*droits de préférence,\s*de préemption ou d['’]emption\.\s*"
    r"Les statuts dérogent à la loi quant aux modalités du transfert des parts "
    r"sociales:\s*pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_TEXT_CALL_UNCHANGED = re.compile(
    r"^Mit dem SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Nr\.\s*"
    r"(?P<entry>[\d']+)\s+vom\s+(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wurde versehentlich der Text aufgerufen,\s*jedoch bleibt der Text weiterhin "
    r"unverändert gültig\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_TRANSFER_WITH_OPTIONAL_MANAGER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+a cédé\s+(?P<transferred>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?:(?P<country>[A-Z]{1,3}),\s*)?"
    r"nouvel associé pour\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+),\s*lequel associé n['’]exerce pas la signature "
    r"sociale\.\s*Par conséquent,\s*(?P=seller)\s+est\s+"
    r"(?:désormais|maintenant)\s+(?:titulaire de|associé pour)\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)"
    r"(?:\.\s*(?P<manager>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<manager_origin>[^,.;]+),\s*à\s+(?P<manager_place>[^,.;]+)\s+"
    r"est nommé\s+(?P<manager_role>gérant))?\.?$",
    re.I | re.UNICODE,
)
_DE_FULL_ADDRESS_AND_AUDITOR_RENAMED = re.compile(
    r"^Vollständige Adresse:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.\s*"
    r"Die eingetragene Revisionsstelle\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+firmiert neu\s+"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_INCOMPLETE_UID = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<identifier>CHE-\d{3}\.\d{3}\.\d{2})\)\.?$",
    re.I | re.UNICODE,
)
_IT_CORRECT_PERSON_DETAILS = re.compile(
    r"^Nome corretto:\s*(?P<surname>[^,.;]+),\s*(?P<given_names>[^,.;]+),\s*"
    r"(?P<nationality>cittadin[oa]\s+[^,.;]+),\s*in\s+(?P<place>[^,.;]+)\s*"
    r"(?:\((?P<municipality>[^)]+)\))?,\s*(?P<role>[^,.;]+),\s*"
    r"con firma\s+(?P<sign>individuale),\s*con\s+(?P<shares>[\d']+)\s+"
    r"quote da CHF\s+(?P<nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_MANAGERS_WITH_CHANGED_SIGNING = re.compile(
    r"^Gérants:\s*(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+?)\s*"
    r"(?:\((?P<canton1>[A-Z]{2})\))?,\s*(?P<role1>président),\s*"
    r"(?P<name2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*à\s+"
    r"(?P<place3>[^,.;]+),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de\s+(?P=name2)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_NAME_AND_ORIGIN_CHANGED = re.compile(
    r"^Le\s+(?P<role>gérant)\s+(?P<previous_name>[^,.;]+),\s*lequel se nomme "
    r"maintenant\s+(?P<name>[^,.;]+),\s*est désormais de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_REPUDIATED_ESTATE_BANKRUPTCY = re.compile(
    r"^Par décision du\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+prononcée par\s+"
    r"(?P<authority>.+?),\s*la succession répudiée du titulaire sera liquidée "
    r"selon les règles de la faillite\.?$",
    re.I | re.UNICODE,
)
_FR_LIQUIDATOR_FOUNDATION_INDIVIDUAL_SIGNING = re.compile(
    r"^Le\s+(?P<role>liquidateur)\s+(?P<name>[^,.;]+)\s+engage désormais la "
    r"fondation par sa signature\s+(?P<sign>individuelle)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_COMPANY_MERGER_WITH_DEFICIT = re.compile(
    r"^reprise des actifs et passifs de\s+(?P<name1>.+?),\s*à\s+"
    r"(?P<place1>[^()]+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"selon contrat de fusion du\s+(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})\s+"
    r"et bilan intermédiaire au\s+(?P<balance_date1>\d{2}\.\d{2}\.\d{4})\s+"
    r"présentant des actifs de CHF\s+(?P<assets1>[\d'.]+)\s+et des passifs "
    r"envers les tiers de CHF\s+(?P<liabilities1>[\d'.]+),\s*et de\s+"
    r"(?P<name2>.+?),\s*à\s+(?P<place2>[^()]+?)\s*"
    r"\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*selon contrat de fusion du\s+"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+et bilan intermédiaire au\s+"
    r"(?P<balance_date2>\d{2}\.\d{2}\.\d{4})\s+présentant des actifs de CHF\s+"
    r"(?P<assets2>[\d'.]+)\s+et des passifs envers les tiers de CHF\s+"
    r"(?P<liabilities2>[\d'.]+)\.\s*Selon une attestation d['’]un expert-réviseur "
    r"agré[eé],\s*(?P<acquirer>.+?)\s+dispose de fonds propres librement disponibles "
    r"équivalant au moins au montant du découvert et du surendettement des sociétés "
    r"transférantes\.\s*La totalité du capital-actions des sociétés transférantes "
    r"étant détenu par la société reprenante,\s*la fusion ne donne pas lieu à une "
    r"augmentation de capital,\s*ni à une attribution d['’]actions\.?$",
    re.I | re.UNICODE,
)
_FR_STATUTES_DATE_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que les statuts sont "
    r"modifiés le\s+(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.?$",
    re.I | re.UNICODE,
)
_FR_AUDIT_WAIVER_WRITTEN_DATE = re.compile(
    r"^Selon déclaration du\s+(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"la société n['’]est pas soumise à une révision ordinaire et renonce à une "
    r"révision restreinte\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PERSON_ORIGIN_DOMICILE_SUPPLEMENT = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que\s+"
    r"(?P<name1>[^,.;]+)\s+est originaire de\s+(?P<origin1>[^,.;]+)\s+et "
    r"domiciliée? à\s+(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name2>[^,.;]+)\s+est originaire de\s+(?P<origin2>[^,.;]+)\s+et "
    r"domiciliée? à\s+(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_FR_COLLECTIVE_SIGNING_FOUR_SHARED_ORIGIN = re.compile(
    r"^Signature collective à deux est conférée à\s+(?P<name1>[^,.;]+)\s+et\s+"
    r"(?P<name2>[^,.;]+),\s*tous deux à\s+(?P<place12>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*et\s+"
    r"(?P<name4>[^,.;]+),\s*à\s+(?P<place4>[^,.;]+),\s*les quatre de\s+"
    r"(?P<origin>[^,.;]+)\.?$",
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


def extract_parser130_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 130."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_STATUTES_RIGHTS_REMOVED_AND_TRANSFER_DEROGATION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.rights_removed_transfer_derogation.v1",
            {
                "action": "modified",
                "ancillary_obligations_removed": True,
                "rights_removed": ["preference", "preemption", "emption"],
                "share_transfer_derogates_from_law": True,
                "details_in_statutes": True,
            },
        ))

    match = _DE_ERRONEOUS_TEXT_CALL_UNCHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.erroneous_text_call_unchanged.v1",
            {
                "action": "previous_text_confirmed_unchanged",
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _FR_ASSOCIATE_TRANSFER_WITH_OPTIONAL_MANAGER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.associate_transfer_unsigned_optional_manager.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "currency": "CHF",
            "share_nominal": match.group("nominal"),
            "shares_transferred": _count(match.group("transferred")),
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé",
                extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associé",
                extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "heimat": match.group("origin").strip(),
                    "country": match.group("country"),
                    "new_associate": True,
                    "without_signature": True,
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ])
        if match.group("manager"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("manager_place"), role=match.group("manager_role"),
                extra={
                    "action": "appointed",
                    "heimat": match.group("manager_origin").strip(),
                },
            ))

    match = _DE_FULL_ADDRESS_AND_AUDITOR_RENAMED.search(leftover)
    if match:
        consume(match)
        rule_id = "de.text.full_address_and_auditor_renamed.v1"
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id,
                {
                    "action": "completed", "address": address,
                    "street": f"{match.group('street').strip()} {match.group('house')}",
                    "postal_code": match.group("postal_code"),
                    "locality": match.group("locality").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="Revisionsstelle",
                extra={
                    "action": "name_changed",
                    "previous_name": match.group("previous_name").strip(),
                    "previous_uid": match.group("previous_uid"),
                },
            ),
        ])

    match = _DE_BRANCH_ADDED_INCOMPLETE_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_added_incomplete_uid.v1",
            {
                "action": "added", "place": match.group("place").strip(),
                "branch_identifier": match.group("identifier").upper(),
                "identifier_incomplete": True,
            },
        ))

    match = _IT_CORRECT_PERSON_DETAILS.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "it.persons.correct_details.v1",
            f"{match.group('surname').strip()}, {match.group('given_names').strip()}",
            place=match.group("place"), role=match.group("role").strip(),
            signing="Einzelunterschrift",
            extra={
                "action": "details_corrected",
                "nationality": match.group("nationality").strip(),
                "municipality": match.group("municipality"),
                "shares_count": _count(match.group("shares")),
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
            },
        ))

    match = _FR_THREE_MANAGERS_WITH_CHANGED_SIGNING.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_managers_changed_signing.v1"
        people = (
            ("name1", "place1", "gérant président", "origin1"),
            ("name2", None, "gérant", None),
            ("name3", "place3", "gérant", "origin3"),
        )
        for name_key, place_key, role, origin_key in people:
            extra = {
                "action": "signing_changed" if name_key == "name2" else "details_recorded"
            }
            if origin_key:
                extra["heimat"] = match.group(origin_key).strip()
            if name_key == "name1" and match.group("canton1"):
                extra["place_canton"] = match.group("canton1")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_key),
                place=match.group(place_key) if place_key else None,
                role=role, signing="Kollektivunterschrift zu zweien", extra=extra,
            ))

    match = _FR_MANAGER_NAME_AND_ORIGIN_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.manager_name_origin_changed.v1",
            match.group("name"), role=match.group("role"),
            extra={
                "action": "name_and_origin_changed",
                "previous_name": match.group("previous_name").strip(),
                "heimat": match.group("origin").strip(),
            },
        ))

    match = _FR_REPUDIATED_ESTATE_BANKRUPTCY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.repudiated_estate_bankruptcy.v1",
            {
                "kind": "repudiated_estate_liquidation_ordered",
                "procedure": "bankruptcy_rules",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "scope": "owner_estate",
            },
        ))

    match = _FR_LIQUIDATOR_FOUNDATION_INDIVIDUAL_SIGNING.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed",
            "fr.persons.liquidator_foundation_individual_signing.v1",
            match.group("name"), role=match.group("role"),
            signing="Einzelunterschrift",
            extra={"action": "changed", "organization_kind": "foundation"},
        ))

    match = _FR_TWO_COMPANY_MERGER_WITH_DEFICIT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.two_company_merger_with_deficit.v1"
        for index in (1, 2):
            events.append(_event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", rule_id,
                {
                    "kind": "absorption",
                    "absorbed_name": match.group(f"name{index}").strip(),
                    "absorbed_place": match.group(f"place{index}").strip(),
                    "absorbed_uid": match.group(f"uid{index}"),
                    "agreement_date": _iso_date(match.group(f"agreement_date{index}")),
                    "balance_date": _iso_date(match.group(f"balance_date{index}")),
                    "assets": match.group(f"assets{index}"),
                    "liabilities": match.group(f"liabilities{index}"),
                    "currency": "CHF",
                    "acquirer": match.group("acquirer").strip(),
                    "free_equity_confirmation": True,
                    "same_shareholder": True,
                    "capital_increase": False,
                    "share_allocation": False,
                },
            ))

    match = _FR_STATUTES_DATE_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.statutes_date_supplement.v1",
            {
                "action": "publication_supplemented",
                "date": _french_date(match.group("date")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_AUDIT_WAIVER_WRITTEN_DATE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "audit_requirement_changed", "fr.text.audit_waiver_written_date.v1",
            {
                "kind": "limited_audit_waiver", "action": "declared",
                "date": _french_date(match.group("date")),
                "ordinary_audit_required": False,
                "limited_audit_waived": True,
            },
        ))

    match = _FR_TWO_PERSON_ORIGIN_DOMICILE_SUPPLEMENT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_origin_domicile_supplement.v1"
        reference = {
            "action": "origin_and_domicile_supplemented",
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
            "notice_date": _iso_date(match.group("notice_date")),
            "notice_ref": match.group("notice_ref"),
        }
        for index in (1, 2):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                extra={
                    **reference,
                    "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            ))

    match = _FR_COLLECTIVE_SIGNING_FOUR_SHARED_ORIGIN.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.collective_signing_four_shared_origin.v1"
        people = (
            ("name1", "place12"),
            ("name2", "place12"),
            ("name3", "place3"),
            ("name4", "place4"),
        )
        for name_key, place_key in people:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(name_key),
                place=match.group(place_key),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "granted", "heimat": match.group("origin").strip()
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .,;")
    return events, leftover
