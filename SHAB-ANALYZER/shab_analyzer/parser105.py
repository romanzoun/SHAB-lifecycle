from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_DOMICILE_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+?)\s+est à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<country>[^)]+)\)\s*\(et non\s+(?:à\s+)?"
    r"(?P<previous_place>[^()]+?)\s*\((?P<previous_country>[^)]+)\)\s+"
    r"comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_NEW_ASSOCIATE = re.compile(
    r"^Les associés-gérants\s+(?P<seller1>[^,.;]+?)\s+et\s+"
    r"(?P<seller2>[^,.;]+?)\s+cèdent chacun\s+"
    r"(?P<transferred>[\d']+)\s+de leurs\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*de\s+"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*nouvel associé avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"sans signature;\s*(?P=seller1)\s+et\s+(?P=seller2)\s+restent chacun "
    r"titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_RECIPIENT_PLACE_UID = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"Aktiven von CHF\s+(?P<assets>[\d'.]+)\s+auf die\s+"
    r"(?P<recipient>.+?),\s*in\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+die definitive Nachlassstundung bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\s*"
    r"\[bisher:\s*Mit Entscheid vom\s+"
    r"(?P<previous_decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P=authority)\s+die mit Verfügung vom\s+"
    r"(?P<grant_date>\d{2}\.\d{2}\.\d{4})\s+gewährte definitive "
    r"Nachlassstundung bis am\s+"
    r"(?P<previous_until>\d{2}\.\d{2}\.\d{4})\s+verlängert\.\]\.?$",
    re.I | re.UNICODE,
)
_IT_FOUNDATION_DEED_CHANGED_AUTHORITY_UID = re.compile(
    r"^Atto di fondazione modificato con decisione della\s+"
    r"(?P<authority>.+?)\s*\((?P<authority_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"in\s+(?P<authority_place>[^,.;]+)\s+in data\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+anche su punti non soggetti a "
    r"pubblicazione\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation avec le président:\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS_WITH_NAMED_SIGNER = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*(?P<role1>président),\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s+(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*et\s+"
    r"(?P<name3>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin3>[^,.;]+),\s*à\s+(?P<place3>[^,.;]+),\s*"
    r"(?P<country3>[A-Z]{1,3}),\s*sont membres du conseil "
    r"d['’]administration,\s*tous trois avec\s+(?P<signing_with>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_INDIVIDUAL = re.compile(
    r"^Liquidateurs:\s*(?P<name1>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin1>[^,.;]+),\s*à\s*"
    r"(?P<place1>[^,.;]+),\s*(?P<country1>[A-Z]{1,3}),\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"liquidateur,\s*tous deux\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_REINSTATED_AFTER_ERRONEOUS_DELETION = re.compile(
    r"^Société radiée le\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]inscription de la radiation de la société ayant été opérée à tort,\s*"
    r"l['’]inscription de la société est rétablie\.?$",
    re.I | re.UNICODE,
)
_DE_NEW_OTHER_ADDRESSES = re.compile(
    r"^Neue andere Adressen:\s*(?P<addresses>.+)\.?$", re.I | re.UNICODE
)
_DE_ADDRESS_ITEM = re.compile(
    r"(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>.+)",
    re.UNICODE,
)
_FR_TRADE_NAME_DELETED_CONTINUED = re.compile(
    r"^La raison de commerce est radiée,\s*les activités continuant sous une "
    r"autre forme juridique\.?$",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME_AND_DOMICILE_CHANGED = re.compile(
    r"^Par suite de changement d['’]état civil,\s*"
    r"(?P<previous_name>[^,.;]+?)\s+porte désormais le nom de\s+"
    r"(?P<name>[^,.;]+),\s*elle est maintenant domiciliée à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{1,3})\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_STRUCTURE_CORRECTED_WITH_NOTICE = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que le "
    r"capital-actions est divisé en\s+(?P<count>[\d']+)\s+"
    r"(?P<share_kind>actions au porteur) de CHF\s+(?P<nominal>[\d'.]+)\s*"
    r"\(et non en\s+(?P<previous_count>[\d']+)\s+actions au porteur de CHF\s+"
    r"(?P<previous_nominal>[\d'.]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE = re.compile(
    r"^Augmentation conditionnelle du capital-participation fondée sur la "
    r"décision relative à l['’]octroi de droits du\s+"
    r"(?P<rights_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Nouveau capital-participation entièrement libéré:\s*CHF\s+"
    r"(?P<total>[\d'.]+),\s*divisé en\s+(?P<count>[\d']+)\s+bons de "
    r"participation nominatifs de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"Le conseil d['’]administration a modifié une clause statutaire relative à "
    r"une augmentation conditionnelle du capital-participation\s*"
    r"\(selon décision relative à l['’]octroi de droits de l['’]assemblée "
    r"générale du\s+(?P<clause_rights_date>\d{2}\.\d{2}\.\d{4})\),\s*"
    r"par décision du\s+(?P<change_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"pour le détail cf\. statuts\.?$",
    re.I | re.UNICODE,
)
_FR_PAIR_ORIGIN_CHANGED_SHORT = re.compile(
    r"^(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?)\s+sont "
    r"(?:maintenant|désormais) de\s+(?P<origin>[^,.;]+)\.?$",
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


def extract_parser105_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 105."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _FR_DOMICILE_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.domicile_corrected_with_notice.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "domicile_corrected",
                "country": match.group("country").strip(),
                "previous_place": match.group("previous_place").strip(),
                "previous_country": match.group("previous_country").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_TWO_MANAGERS_TRANSFER_TO_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_managers_transfer_to_new_associate.v1"
        seller_names = [match.group("seller1").strip(), match.group("seller2").strip()]
        for seller in seller_names:
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé-gérant",
                extra={
                    "action": "shares_transferred",
                    "counterparty": match.group("buyer").strip(),
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"),
                    "currency": "CHF",
                },
            ))
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, match.group("buyer"),
            place=match.group("place"), role="associé",
            extra={
                "action": "shares_received",
                "counterparties": seller_names,
                "shares_received": _count(match.group("buyer_count")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"),
                "currency": "CHF", "heimat": match.group("origin").strip(),
                "new_associate": True, "without_signature": True,
            },
        ))

    match = _DE_ASSET_TRANSFER_RECIPIENT_PLACE_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_recipient_place_uid.v1",
            {
                "date": _iso_date(match.group("date")),
                "assets": match.group("assets"), "currency": "CHF",
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_currency": "CHF",
            },
        ))

    match = _DE_DEFINITIVE_MORATORIUM_EXTENDED_WITH_HISTORY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.definitive_moratorium_extended_history.v1",
            {
                "kind": "composition_moratorium_extended",
                "moratorium_type": "definitive",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "until": _iso_date(match.group("until")),
                "grant_date": _iso_date(match.group("grant_date")),
                "previous_decision_date": _iso_date(match.group("previous_decision_date")),
                "previous_until": _iso_date(match.group("previous_until")),
            },
        ))

    match = _IT_FOUNDATION_DEED_CHANGED_AUTHORITY_UID.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "it.text.foundation_deed_changed_authority_uid.v1",
            {
                "kind": "foundation_deed_non_public_changes",
                "date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "authority_uid": match.group("authority_uid"),
                "authority_place": match.group("authority_place").strip(),
                "non_public_changes": True,
            },
        ))

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.foundation_member_with_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed", "heimat": match.group("origin").strip(),
                "signing_with": "président",
            },
        ))

    match = _FR_THREE_BOARD_MEMBERS_WITH_NAMED_SIGNER.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.three_board_members_with_named_signer.v1"
        for index in range(1, 4):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                role=(match.group("role1") if index == 1 else "membre du conseil d'administration"),
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "heimat": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                    "signing_with": match.group("signing_with").strip(),
                },
            ))

    match = _FR_TWO_LIQUIDATORS_INDIVIDUAL.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.two_liquidators_individual.v1"
        for index in range(1, 3):
            extra = {
                "action": "appointed",
                "heimat": match.group(f"origin{index}").strip(),
            }
            country = match.groupdict().get(f"country{index}")
            if country:
                extra["country"] = country
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="liquidateur",
                signing="Einzelunterschrift", extra=extra,
            ))

    match = _FR_COMPANY_REINSTATED_AFTER_ERRONEOUS_DELETION.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.company_reinstated_erroneous_deletion.v1",
            {
                "kind": "registration_reinstated", "action": "reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "reason": "erroneous_deletion", "registry_reinstated": True,
            },
        ))

    match = _DE_NEW_OTHER_ADDRESSES.search(leftover)
    if match:
        raw_addresses = [item.strip().rstrip(".") for item in match.group("addresses").split(";")]
        address_matches = [_DE_ADDRESS_ITEM.fullmatch(item) for item in raw_addresses]
        if len(address_matches) >= 2 and all(address_matches):
            consume(match)
            for raw_address, address_match in zip(raw_addresses, address_matches):
                assert address_match is not None
                events.append(_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "address_changed", "de.text.new_other_addresses.v1",
                    {
                        "kind": "additional_address", "action": "added",
                        "address": raw_address,
                        "street": address_match.group("street").strip(),
                        "house": address_match.group("house"),
                        "postal_code": address_match.group("postal_code"),
                        "locality": address_match.group("locality").strip(),
                    },
                ))

    match = _FR_TRADE_NAME_DELETED_CONTINUED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_deleted", "fr.text.trade_name_deleted_continued.v1",
            {
                "reason": "continued_under_other_legal_form",
                "scope": "organization", "business_continues": True,
            },
        ))

    match = _FR_CIVIL_NAME_AND_DOMICILE_CHANGED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.civil_name_and_domicile_changed.v1",
            match.group("name"), place=match.group("place"),
            extra={
                "action": "name_and_domicile_changed",
                "previous_name": match.group("previous_name").strip(),
                "reason": "civil_status_change", "country": match.group("country"),
            },
        ))

    match = _FR_SHARE_STRUCTURE_CORRECTED_WITH_NOTICE.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.share_structure_corrected_with_notice.v1",
            {
                "kind": "share_structure", "action": "corrected",
                "currency": "CHF", "shares_count": _count(match.group("count")),
                "share_nominal": match.group("nominal"),
                "share_kind": match.group("share_kind").lower(),
                "previous_shares_count": _count(match.group("previous_count")),
                "previous_share_nominal": match.group("previous_nominal"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_CONDITIONAL_PARTICIPATION_CAPITAL_AND_CLAUSE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.conditional_participation_capital_clause_changed.v1"
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_increase",
                    "rights_decision_date": _iso_date(match.group("rights_date")),
                    "currency": "CHF", "total": match.group("total"),
                    "fully_paid": True,
                    "participation_certificates_count": _count(match.group("count")),
                    "participation_certificate_nominal": match.group("nominal"),
                    "registered": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "statutes_changed", rule_id,
                {
                    "kind": "conditional_participation_capital_clause",
                    "action": "changed",
                    "rights_decision_date": _iso_date(match.group("clause_rights_date")),
                    "decision_date": _iso_date(match.group("change_date")),
                    "details_in_statutes": True,
                },
            ),
        ])

    match = _FR_PAIR_ORIGIN_CHANGED_SHORT.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.pair_origin_changed_short.v1"
        for name_group in ("name1", "name2"):
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(name_group),
                extra={
                    "action": "origin_changed",
                    "heimat": match.group("origin").strip(),
                    "origin_changed": True,
                },
            ))

    leftover = re.sub(r"\s+", " ", leftover).strip(" .;")
    if leftover and not re.search(r"\w", leftover, re.UNICODE):
        leftover = ""
    return events, leftover
