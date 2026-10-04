from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_REGISTERED_BOARD_MEMBER_UNSIGNED = re.compile(
    r"^Eingetragene Person:\s*(?P<name>[^,.;]+),\s*von\s+"
    r"(?P<origin>[^,.;]+),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>Verwaltungsratsmitglied),\s*ohne Unterschrift\.?$",
    re.I | re.UNICODE,
)
_FR_FIVE_LIQUIDATORS_APPOINTED = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<name3>[^,.;]+),\s*(?P<name4>[^,.;]+)\s+et\s+"
    r"(?P<name5>[^,.;]+)\s+sont nommés liquidateurs\s+"
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_IT_SOLE_ADMINISTRATOR_REMOVED_GOVERNANCE_VACANCY = re.compile(
    r"^Persone dimissionarie e firme cancellate:\s*"
    r"(?P<surname>[^,.;]+),\s*(?P<given>[^,.;]+),\s*"
    r"(?P<nationality>cittadino italiano),\s*in\s+(?P<place>[^,.;]+),\s*"
    r"(?P<role>amministratore unico),\s*con firma individuale\.\s*"
    r"\[la società è attualmente priva di amministrazione\s+"
    r"(?P<legal_basis>art\.\s*707 CO)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_PEOPLE_SHARED_DOMICILE = re.compile(
    r"^(?P<name1>[^,;]+?)\s+et\s+(?P<name2>[^,;]+?)\s+sont maintenant "
    r"domiciliés à\s+(?P<place>[^,.;]+),\s*(?P<country>[A-Z])\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_OFFICERS_PRESIDENCY_AND_DOMICILES = re.compile(
    r"^(?P<name1>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place1>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<name2>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<place2>[^,.;]+),\s*jusqu['’]ici président,\s*"
    r"continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_FR_DOMICILE_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT = re.compile(
    r"^(?P<seller>[^,.;]+),\s*qui est maintenant à\s+"
    r"(?P<seller_place>[^,.;]+),\s*cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé-gérant avec signature "
    r"individuelle,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller),\s*qui reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+),\s*est nommé président\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REGISTRY_ID_SUPPLEMENT_TYPO = re.compile(
    r"^Bei der nachfolgenden Mutation wurde die bisherige Firmennummer nicht "
    r"publiziert\.\s*Des erfolgt folgender Nachtrag:\s*(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<place>[^,.;]+),\s*(?P<role>Revisionsstelle)\s*"
    r"\[bisher:\s*(?P<previous_name>.+?)\s*"
    r"\((?P<previous_registry_id>CH-[\d.]+-\d)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_REPLACEMENT_MULTINATIONAL = re.compile(
    r"^(?P<removed>.+?)\s+ne sont plus membres du conseil de fondation\.\s*"
    r"(?P<added>.+?),\s*sont membres du conseil de fondation,\s*"
    r"sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_ITEM = re.compile(
    r"(?:^|,\s*)(?P<name>[^,]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,]+),\s*à\s+"
    r"(?P<place>[^,]+?)(?:,\s*(?P<country>[A-Z]{1,3}))?"
    r"(?=,\s*[^,]+,\s*(?:du|de la|des|de|d['’])\s*|$)",
    re.UNICODE,
)
_FR_SHARE_TRANSFER_TO_EXISTING_ASSOCIATE = re.compile(
    r"^(?!L['’]associé\b)(?P<seller>[^,.;]+)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associé\s+(?P<buyer>[^,.;]+),\s*"
    r"lequel devient ainsi titulaire de\s+(?P<buyer_count>[\d']+)\s+"
    r"parts sociales de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_SINGLE_COMPANY_TRANSLATION_ADDED = re.compile(
    r"^Nuove traduzioni della ditta:\s*\((?P<german>[^()]+)\)\.?$",
    re.I | re.UNICODE,
)
_IT_COMPANY_DELETION_BLOCKED_ART_155_MISSING_SPACE = re.compile(
    r"^La società\s*deve essere cancellata a seguito della procedura di cui "
    r"all['’]art\.\s*155 ORC\.\s*La cancellazione non può tuttavia essere "
    r"effettuata mancando il consenso delle autorità fiscali federali e "
    r"cantonali\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_FOUNDATION_MEMBERS_WITH_COUNTRIES = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{1,3}),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*à\s+"
    r"(?P<place2>[^,.;]+),\s*(?P<country2>[A-Z]{1,3}),\s*"
    r"sont membres du Conseil de Fondation,\s*"
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_DUPLICATE_PERSON_REMOVED = re.compile(
    r"^Personne et signature radiées parce qu['’]inscrites par erreur\s*"
    r"\(déjà inscrites\):\s*(?P<surname>[^,.;]+),\s*"
    r"(?P<given>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_FR_DISSOLUTION_GENERAL_PARTNER_LIQUIDATOR = re.compile(
    r"^La société est dissoute par décision de son assemblée générale du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"L['’]associée indéfiniment responsable\s+(?P<name>.+?)\s*"
    r"\((?P<registry_id>CH-[\d-]+)\)\s+est élue liquidatrice\.?$",
    re.I | re.UNICODE,
)
_DE_CONTRIBUTION_AND_ACQUISITION_SHARE_COUNT_CORRECTED = re.compile(
    r"^Der Eintrag Nr\.\s*(?P<entry>[\d']+)\s+vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(SHAB vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id\s+"
    r"(?P<notice_id>\d+)\)\s+ist wie folgt berichtigt:\s*"
    r"Sacheinlage und Sachübernahme:\s*Die Gesellschaft übernimmt gemäss "
    r"Vertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<count1>[\d']+)\s*\(und nicht\s+(?P<previous_count1>[\d']+)\)\s+"
    r"(?P<kind1>Namenaktien) zu CHF\s+(?P<nominal1>[\d'.]+)\s+der\s+"
    r"(?P<company1>.+?)\s*\((?P<uid1>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place1>[^,.;]+),\s*im Wert und zum Preis von CHF\s+"
    r"(?P<value1>[\d'.]+),\s*und\s+(?P<count2>[\d']+)\s+"
    r"(?P<kind2>Namenaktien) zu CHF\s+(?P<nominal2>[\d'.]+)\s+der\s+"
    r"(?P<company2>.+?)\s*\((?P<uid2>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place2>[^,.;]+),\s*im Wert und zum Preis von CHF\s+"
    r"(?P<value2>[\d'.]+)\.\s*Als Gegenleistung werden den Sacheinlegern\s+"
    r"(?P<issued_count>[\d']+)\s+Namenaktien zu CHF\s+"
    r"(?P<issued_nominal>[\d'.]+)\s+ausgegeben und CHF\s+"
    r"(?P<credit>[\d'.]+)\s+gutgeschrieben\.?$",
    re.I | re.UNICODE,
)
_DE_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Mit Entscheid vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+eine provisorische Nachlassstundung von\s+"
    r"(?P<duration>\w+)\s+Monaten,\s*d\.h\.\s*bis\s+"
    r"(?P<until>\d{2}\.\d{2}\.\d{4}),\s*bewilligt\.\s*"
    r"Als provisorischer Sachwalter wurde\s+(?P<name>[^,.;]+),\s*"
    r"(?P<qualifications>.+?),\s*(?P<street>[^,]+?\s+\d+[A-Za-z]?),\s*"
    r"(?P<po_box>Postfach\s+\d+),\s*(?P<postal_code>\d{4})\s+"
    r"(?P<place>[^,.;]+)\s+eingesetzt\.\s*Dieser hat die Geschäftstätigkeiten "
    r"während der provisorischen Nachlassstundung zu beaufsichtigen\.?$",
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
_NUMBER_WORDS = {
    "ein": 1,
    "eine": 1,
    "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _french_date(raw: str) -> str:
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", "").replace(".", ""))


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
        role=role.strip() if role else None,
        signing=signing,
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def _foundation_member_items(raw: str) -> list[dict[str, str | None]] | None:
    normalized = re.sub(
        r"\s+et\s+(?=[^,]+,\s*(?:du|de la|des|de|d['’])\s*)",
        ", ",
        raw.strip(),
        count=1,
        flags=re.I,
    )
    matches = list(_FR_FOUNDATION_MEMBER_ITEM.finditer(normalized))
    if not matches or matches[0].start() != 0 or matches[-1].end() != len(normalized):
        return None
    if any(previous.end() != current.start() for previous, current in zip(matches, matches[1:])):
        return None
    return [
        {
            "name": match.group("name").strip(),
            "origin": match.group("origin").strip(),
            "place": match.group("place").strip(),
            "country": match.group("country"),
        }
        for match in matches
    ]


def extract_parser231_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 231."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_REGISTERED_BOARD_MEMBER_UNSIGNED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.registered_board_member_unsigned.v1",
            match.group("name"), place=match.group("place"), role=match.group("role"),
            extra={
                "action": "registered", "origin": match.group("origin").strip(),
                "signing_authority": False,
            },
        )], ""

    match = _FR_FIVE_LIQUIDATORS_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.five_liquidators_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="liquidateur", signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_liquidator"},
            )
            for index in range(1, 6)
        ], ""

    match = _IT_SOLE_ADMINISTRATOR_REMOVED_GOVERNANCE_VACANCY.fullmatch(leftover)
    if match:
        rule_id = "it.persons.sole_administrator_removed_governance_vacancy.v1"
        name = f"{match.group('surname').strip()}, {match.group('given').strip()}"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, name, place=match.group("place"),
                role=match.group("role"), signing="Einzelunterschrift", extra={
                    "action": "removed", "nationality": match.group("nationality").strip(),
                    "signing_revoked": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "governance", "action": "administration_vacant",
                    "administration_present": False,
                    "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                },
            ),
        ], ""

    match = _FR_TWO_PEOPLE_SHARED_DOMICILE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_people_shared_domicile_country.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"), extra={
                    "action": "domicile_changed", "country": match.group("country"),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_TWO_OFFICERS_PRESIDENCY_AND_DOMICILES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_officers_presidency_and_domiciles.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role="président",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_president_and_domicile_changed",
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "presidency_ended_and_domicile_changed",
                    "previous_role": "président", "signing_continues": True,
                },
            ),
        ], ""

    match = _FR_DOMICILE_SHARE_TRANSFER_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match:
        nominals = {
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        remaining = _count(match.group("remaining"))
        if len(nominals) == 1 and before - transferred == remaining:
            rule_id = "fr.persons.domicile_share_transfer_new_manager_president.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    place=match.group("seller_place"), role="associé-gérant président",
                    extra={
                        "action": "shares_transferred_domicile_changed_and_appointed_president",
                        "counterparty": buyer, "shares_before": before,
                        "shares_transferred": transferred, "shares_count": remaining,
                        "share_nominal": match.group("nominal"), "currency": "CHF",
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"), role="associé-gérant",
                    signing="Einzelunterschrift", extra={
                        "action": "appointed_and_shares_received", "counterparty": seller,
                        "origin": match.group("origin").strip(),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                    },
                ),
            ], ""

    match = _DE_AUDITOR_REGISTRY_ID_SUPPLEMENT_TYPO.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.auditor_registry_id_supplement_typo.v1",
            match.group("name"), place=match.group("place"), uid=match.group("uid"),
            role=match.group("role"), extra={
                "action": "identification_supplemented",
                "previous_name": match.group("previous_name").strip(),
                "previous_registry_id": match.group("previous_registry_id"),
                "source_typo": "Des erfolgt",
            },
        )], ""

    match = _FR_FOUNDATION_BOARD_REPLACEMENT_MULTINATIONAL.fullmatch(leftover)
    if match:
        removed = [name.strip() for name in match.group("removed").split(",") if name.strip()]
        added = _foundation_member_items(match.group("added"))
        if len(removed) >= 2 and added:
            rule_id = "fr.persons.foundation_board_replacement_multinational.v1"
            events = [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_removed", rule_id, name,
                    role="membre du conseil de fondation", extra={"action": "removed"},
                )
                for name in removed
            ]
            events.extend(
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, str(item["name"]),
                    place=str(item["place"]), role="membre du conseil de fondation",
                    extra={
                        "action": "appointed", "origin": item["origin"],
                        "country": item["country"], "signing_authority": False,
                    },
                )
                for item in added
            )
            return events, ""

    match = _FR_SHARE_TRANSFER_TO_EXISTING_ASSOCIATE.fullmatch(leftover)
    if match:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        if match.group("nominal") == match.group("buyer_nominal") and transferred <= before:
            rule_id = "fr.persons.share_transfer_to_existing_associate.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "shares_transferred": transferred,
            }
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller, role="associé", extra={
                        **common, "action": "shares_transferred", "counterparty": buyer,
                        "shares_before": before, "shares_count": before - transferred,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associé", extra={
                        **common, "action": "shares_received", "counterparty": seller,
                        "shares_count": _count(match.group("buyer_count")),
                    },
                ),
            ], ""

    match = _IT_SINGLE_COMPANY_TRANSLATION_ADDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "it.text.single_company_translation_added.v1", {
                "kind": "company_name_translation", "action": "translation_added",
                "language": "de", "translation": match.group("german").strip(),
            },
        )], ""

    match = _IT_COMPANY_DELETION_BLOCKED_ART_155_MISSING_SPACE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.company_deletion_blocked_art155_missing_space.v1", {
                "kind": "deletion_blocked", "action": "deletion_pending",
                "scope": "company", "legal_basis": "Art. 155 ORC",
                "tax_authority_consent_missing": True,
                "missing_consents": ["federal_tax_authority", "cantonal_tax_authority"],
                "source_missing_space": True,
            },
        )], ""

    match = _FR_TWO_FOUNDATION_MEMBERS_WITH_COUNTRIES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_foundation_members_with_countries.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du Conseil de Fondation",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": match.group(f"country{index}"),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_ERRONEOUS_DUPLICATE_PERSON_REMOVED.fullmatch(leftover)
    if match:
        name = f"{match.group('surname').strip()}, {match.group('given').strip()}"
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_removed", "fr.persons.erroneous_duplicate_person_removed.v1",
            name, place=match.group("place"), signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "erroneous_duplicate_removed",
                "origin": match.group("origin").strip(), "signing_revoked": True,
                "already_registered": True,
            },
        )], ""

    match = _FR_DISSOLUTION_GENERAL_PARTNER_LIQUIDATOR.fullmatch(leftover)
    if match:
        rule_id = "fr.text.dissolution_general_partner_liquidator.v1"
        decision_date = _french_date(match.group("decision_date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "dissolution", "action": "dissolved",
                    "decision_date": decision_date,
                    "decision_body": "assemblée générale",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                role="associée indéfiniment responsable, liquidatrice", extra={
                    "action": "appointed_liquidator", "decision_date": decision_date,
                    "registry_id": match.group("registry_id"),
                },
            ),
        ], ""

    match = _DE_CONTRIBUTION_AND_ACQUISITION_SHARE_COUNT_CORRECTED.fullmatch(leftover)
    if match:
        count1 = _count(match.group("count1"))
        count2 = _count(match.group("count2"))
        nominal1 = _count(match.group("nominal1"))
        nominal2 = _count(match.group("nominal2"))
        value1 = _count(match.group("value1"))
        value2 = _count(match.group("value2"))
        issued_count = _count(match.group("issued_count"))
        issued_nominal = _count(match.group("issued_nominal"))
        credit = _count(match.group("credit"))
        if (
            count1 * nominal1 == value1
            and count2 * nominal2 == value2
            and issued_count * issued_nominal + credit == value1 + value2
        ):
            contributions = [
                {
                    "company": match.group(f"company{index}").strip(),
                    "uid": match.group(f"uid{index}"),
                    "place": match.group(f"place{index}").strip(),
                    "share_count": _count(match.group(f"count{index}")),
                    "share_kind": match.group(f"kind{index}"),
                    "share_nominal": match.group(f"nominal{index}"),
                    "value": match.group(f"value{index}"),
                    "currency": "CHF",
                }
                for index in (1, 2)
            ]
            contributions[0]["previous_incorrect_share_count"] = _count(
                match.group("previous_count1")
            )
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected",
                "de.text.contribution_and_acquisition_share_count_corrected.v1", {
                    "kind": "contribution_in_kind_and_asset_acquisition",
                    "action": "source_share_count_corrected",
                    "entry": match.group("entry"),
                    "entry_date": _iso_date(match.group("entry_date")),
                    "notice_date": _iso_date(match.group("notice_date")),
                    "notice_id": match.group("notice_id"),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "contributions": contributions,
                    "issued_shares_count": issued_count,
                    "issued_share_nominal": match.group("issued_nominal"),
                    "credit": match.group("credit"), "currency": "CHF",
                },
            )], ""

    match = _DE_PROVISIONAL_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        duration = _NUMBER_WORDS.get(match.group("duration").casefold())
        if duration is not None:
            rule_id = "de.text.provisional_moratorium_with_commissioner_oversight.v1"
            common = {
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            }
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "status_changed", rule_id, {
                        **common, "kind": "composition_moratorium_granted",
                        "action": "granted", "moratorium_type": "provisional",
                        "duration_months": duration,
                        "until": _iso_date(match.group("until")),
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("name"),
                    place=match.group("place"), role="provisorischer Sachwalter", extra={
                        **common, "action": "appointed",
                        "qualifications": re.sub(
                            r"\s+", " ", match.group("qualifications").strip()
                        ),
                        "street": match.group("street").strip(),
                        "post_office_box": match.group("po_box").strip(),
                        "postal_code": match.group("postal_code"),
                        "oversight_scope": "business_operations",
                    },
                ),
            ], ""

    return [], leftover
