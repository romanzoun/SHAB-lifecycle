from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_SOLE_PROPRIETOR_BUSINESS_CONTINUED = re.compile(
    r"^Der Geschäftsbetrieb wird weitergeführt\.\s*"
    r"Der Eintrag des Einzelunternehmens bleibt bestehen\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGEMENT_COMMITTEE_FIVE_MEMBERS = re.compile(
    r"^Comité de direction:\s*(?P<president>[^,.;]+),\s*présidente,\s*"
    r"(?P<vice_president>[^,.;]+),\s*vice-président,\s*"
    r"(?P<secretary>[^,.;]+),\s*secrétaire et caissière,\s*"
    r"(?P<member1>[^,.;]+)\s+et\s+(?P<member2>[^,.;]+),\s*"
    r"membres du conseil de fondation\.\s*Signature collective à deux de la "
    r"présidente,\s*du vice-président ou de la secrétaire et caissière\.\s*"
    r"Les autres membres du comité de direction n['’]exercent pas la "
    r"signature sociale\.?$",
    re.I | re.UNICODE,
)
_FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER = re.compile(
    r"^Par décision du\s+(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé au titulaire un sursis concordataire "
    r"définitif de\s+(?P<duration>[^,.;]+),\s*soit jusqu['’]au\s+"
    r"(?P<until>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"est désigné commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_IT_CORRECTED_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETOR = re.compile(
    r"^\[Nell['’]iscrizione è stata erroneamente tralasciata la seguente "
    r"indicazione\.\s*Nuova natura giuridica:\s*(?P<legal_form>ditta "
    r"individuale)\.\]\.?\s*\[La sede della ditta individuale è stata "
    r"indicata in modo errato\.\s*Il testo corretto è il seguente:\]\s*"
    r"L['’]associato\s+(?P<removed>[^,.;]+)\s+non fa più parte della "
    r"società\.\s*La stessa è sciolta dal\s+"
    r"(?P<dissolution_date>\d{2}\.\d{2}\.\d{4})\s+e cancellata\.\s*"
    r"Il socio\s+(?P<owner>[^,.;]+)\s+continua l['’]attività,\s*"
    r"giusta l['’]art\.\s*(?P<legal_basis>579 CO),\s*con la ditta individuale\s*"
    r"[\"“](?P<company_name>[^\"”]+)[\"”],\s*in\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_THREE_BOARD_MEMBERS_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s+(?P<place1>[^,.;]+),\s*"
    r"(?P<country1>[A-Z]{2,3}),\s*(?P<name2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin2>[^,.;]+),\s*"
    r"à\s+(?P<place2>[^,.;]+),\s*et\s+(?P<name3>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin3>[^,.;]+),\s*"
    r"à\s+(?P<place3>[^,.;]+),\s*(?P<country3>[A-Z]{2,3}),\s*"
    r"sont membres du conseil sans signature\.?$",
    re.I | re.UNICODE,
)
_FR_PROXY_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]\.?\s*)?(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens "
    r"qu['’]une procuration collective à deux a été conférée à\s+"
    r"(?P<name>[^()]+?)\s*\(et non pas\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?:n[o°]\.?\s*)?(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"le nouvel organe de révision est\s+(?P<name>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^()]+?)\s*\(et non pas\s+(?P<previous_name>.+?)\s*"
    r"\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<previous_place>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_DETAILED_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré "
    r"des actifs pour CHF\s+(?P<assets>[\d'.]+),\s*comprenant\s+"
    r"(?P<asset_details>.+?),\s*et des passifs envers les tiers pour CHF\s+"
    r"(?P<liabilities>[\d'.]+),\s*à\s+(?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+à\s+"
    r"(?P<place>[^.]+)\.\s*Contre-prestation:\s*(?P<consideration>aucune)\.?$",
    re.I | re.UNICODE,
)
_FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE = re.compile(
    r"^(?P<name>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"est membre du comité;\s*(?:il\s+)?n['’]exerce pas la signature\.?$",
    re.I | re.UNICODE,
)
_DE_MORATORIUM_APPEAL_SUSPENSIVE_EFFECT = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+hat\s+"
    r"(?P<authority>.+?)\s+der Beschwerde gegen den Entscheid vom\s+"
    r"(?P<appealed_decision_date>\d{2}\.\d{2}\.\d{4})\s+die aufschiebende "
    r"Wirkung zuerkannt\.\s*Die Nachlassstundung wird damit einstweilen "
    r"verlängert\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PERSON_DETAILS_REMOVED_SUPPLEMENT = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*\[Für den mit TR vom\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+vorgenommenen und im SHAB "
    r"Nr\.\s*(?P<notice_number>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten Eintrag ist,\s*"
    r"lediglich als Tagesregistertext,\s*nachzutragen:\s*Gestrichene "
    r"Personenangaben aufgrund geänderter Eintragungsvorschriften gemäss\s+"
    r"(?P<legal_basis>Art\.\s*110 HRegV)\.\]\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENERAL_BOARD_ROLE_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que "
    r"le nouveau directeur général\s+(?P<name>[^,.;]+)\s+n['’]est pas "
    r"membre du conseil d['’]administration\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_MENTION_WITH_ADDRESS = re.compile(
    r"^Inscription de la mention de l['’]existence d['’]une succursale à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<address>.+?)\s*"
    r"\((?P<uid>CHE[- ]\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_BRANCH_LEGACY_IDENTIFIER_REPLACED = re.compile(
    r"^Nouvelle succursale:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\[précédemment:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_id>CH-[\d.]+-\d+)\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_LIQUIDATORS_COLLECTIVE_SIGNING = re.compile(
    r"^Liquidateurs:\s*l['’](?P<role1>administrateur)\s+"
    r"(?P<name1>[^,.;]+),?\s*et\s+(?P<name2>[^,.;]+),\s*"
    r"(?P<role2>directeur),\s*lesquels signent collectivement à deux;\s*"
    r"les pouvoirs de\s+(?P<referenced_name>[^,.;]+)\s+sont modifiés en ce sens\.?$",
    re.I | re.UNICODE,
)
_DE_PERSON_NAME_CORRECTED_AND_APPOINTED_LIQUIDATOR = re.compile(
    r"^Eingetragene Person geändert:\s*(?P<previous_name>[^,.;]+),\s*"
    r"korrekterweise\s+(?P<name>[^,.;]+),\s*"
    r"(?P<previous_role>Verwaltungsratsmitglied),\s*"
    r"(?P<previous_sign>Einzelunterschrift),\s*neu\s+"
    r"(?P<role>Verwaltungsratsmitglied,\s*Liquidator),\s*"
    r"(?P<sign>Einzelunterschrift)\.?$",
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
    day, month, year = raw.casefold().replace("1er", "1", 1).split()
    return f"{int(year):04d}-{_FR_MONTHS[month]:02d}-{int(day):02d}"


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


def extract_parser237_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 237."""
    del language  # Historical publications regularly contain another language.
    leftover = text.strip()

    if _DE_SOLE_PROPRIETOR_BUSINESS_CONTINUED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.sole_proprietor_business_continued.v1", {
                "kind": "business_continued", "action": "continued",
                "organization_kind": "sole_proprietorship",
                "business_continues": True, "registration_remains": True,
            },
        )], ""

    match = _FR_MANAGEMENT_COMMITTEE_FIVE_MEMBERS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.management_committee_five_members.v1"
        people = (
            ("president", "présidente", "Kollektivunterschrift zu zweien", False),
            ("vice_president", "vice-président", "Kollektivunterschrift zu zweien", False),
            ("secretary", "secrétaire et caissière", "Kollektivunterschrift zu zweien", False),
            ("member1", "membre du conseil de fondation", None, True),
            ("member2", "membre du conseil de fondation", None, True),
        )
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(group), role=role,
                signing=signing, extra={
                    "action": "appointed", "committee": "comité de direction",
                    "without_signature": without_signature,
                },
            )
            for group, role, signing, without_signature in people
        ], ""

    match = _FR_DEFINITIVE_MORATORIUM_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.definitive_moratorium_with_commissioner.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted", "action": "granted",
                    "moratorium_type": "definitive",
                    "decision_date": _french_date(match.group("decision_date")),
                    "duration": match.group("duration").strip(),
                    "until": _french_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), role="commissaire au sursis", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _IT_CORRECTED_PARTNERSHIP_CONTINUED_AS_SOLE_PROPRIETOR.fullmatch(leftover)
    if match:
        rule_id = "it.text.corrected_partnership_continued_as_sole_proprietor.v1"
        common = {
            "action": "publication_corrected",
            "dissolution_date": _iso_date(match.group("dissolution_date")),
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    **common, "kind": "legal_form",
                    "legal_form": match.group("legal_form"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "address_changed", rule_id, {
                    **common, "kind": "seat", "place": match.group("place").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("removed"), role="associato",
                extra={**common, "action": "removed"},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_deleted", rule_id, {
                    **common, "kind": "partnership_dissolved_and_deleted",
                    "business_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("owner"),
                place=match.group("place"), role="titolare", extra={
                    **common, "action": "business_continued_as_sole_proprietor",
                    "legal_basis": match.group("legal_basis"),
                    "company_name": match.group("company_name").strip(),
                },
            ),
        ], ""

    match = _FR_THREE_BOARD_MEMBERS_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.three_board_members_without_signature.v1"
        events: list[Event] = []
        for index in (1, 2, 3):
            country = match.groupdict().get(f"country{index}")
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"), role="membre du conseil", extra={
                    "action": "appointed", "origin": match.group(f"origin{index}").strip(),
                    "country": country.upper() if country else None,
                    "without_signature": True,
                },
            ))
        return events, ""

    match = _FR_PROXY_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "signing_authority_changed", "fr.persons.proxy_name_corrected.v1",
            match.group("name"), signing="Kollektivprokura zu zweien", extra={
                "action": "name_corrected_and_proxy_granted",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_AUDITOR_CORRECTED.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.auditor_corrected.v2"
        reference = {
            "action": "publication_corrected", "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                place=match.group("previous_place"), uid=match.group("previous_uid"),
                role="organe de révision", extra={
                    **reference, "replacement": match.group("name").strip(),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="organe de révision", extra={
                    **reference, "replaces": match.group("previous_name").strip(),
                },
            ),
        ], ""

    match = _FR_DETAILED_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.detailed_asset_transfer_no_consideration.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "asset_details": match.group("asset_details").strip(),
                "liabilities": match.group("liabilities"), "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "none",
            },
        )], ""

    match = _FR_COMMITTEE_MEMBER_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.committee_member_without_signature.v1",
            match.group("name"), place=match.group("place"),
            role="membre du comité", extra={
                "action": "appointed", "origin": match.group("origin").strip(),
                "without_signature": True,
            },
        )], ""

    match = _DE_MORATORIUM_APPEAL_SUSPENSIVE_EFFECT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.moratorium_appeal_suspensive_effect.v1", {
                "kind": "composition_moratorium_extended", "action": "extended",
                "extension": "temporary", "appeal_suspensive_effect": True,
                "decision_date": _iso_date(match.group("decision_date")),
                "appealed_decision_date": _iso_date(match.group("appealed_decision_date")),
                "authority": match.group("authority").strip(),
            },
        )], ""

    match = _DE_BRANCH_PERSON_DETAILS_REMOVED_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_person_details_removed_supplement.v1", {
                "action": "person_details_removal_supplemented",
                "reason": "changed_registration_rules",
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_number": match.group("notice_number"),
                "notice_date": _iso_date(match.group("notice_date")),
                "legal_basis": match.group("legal_basis"),
                "daily_register_text_only": True,
            },
        )], ""

    match = _FR_DIRECTOR_GENERAL_BOARD_ROLE_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_general_board_role_corrected.v1",
            match.group("name"), role="directeur général", extra={
                "action": "role_corrected",
                "previous_role": "membre du conseil d'administration",
                "previous_role_removed": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _FR_BRANCH_MENTION_WITH_ADDRESS.fullmatch(leftover)
    if match:
        branch_uid = match.group("uid").replace("CHE ", "CHE-")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_mention_with_address.v1", {
                "action": "added", "place": match.group("place").strip(),
                "address": match.group("address").strip(), "branch_uid": branch_uid,
                "identifier_normalized": branch_uid != match.group("uid"),
            },
        )], ""

    match = _FR_BRANCH_LEGACY_IDENTIFIER_REPLACED.fullmatch(leftover)
    if match and match.group("place").strip() == match.group("previous_place").strip():
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "fr.text.branch_legacy_identifier_replaced.v1", {
                "action": "identifier_changed", "place": match.group("place").strip(),
                "branch_uid": match.group("uid"),
                "previous_registry_id": match.group("previous_id"),
            },
        )], ""

    match = _FR_TWO_LIQUIDATORS_COLLECTIVE_SIGNING.fullmatch(leftover)
    if match and match.group("name1").strip() == match.group("referenced_name").strip():
        rule_id = "fr.persons.two_liquidators_collective_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator_and_signing_changed",
                    "previous_role": match.group("role1"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                role="directeur et liquidateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed_liquidator",
                    "previous_role": match.group("role2"),
                },
            ),
        ], ""

    match = _DE_PERSON_NAME_CORRECTED_AND_APPOINTED_LIQUIDATOR.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "de.persons.name_corrected_appointed_liquidator.v1",
            match.group("name"), role=match.group("role").strip(),
            signing="Einzelunterschrift", extra={
                "action": "name_corrected_and_appointed_liquidator",
                "previous_name": match.group("previous_name").strip(),
                "previous_role": match.group("previous_role"),
                "previous_signing": "Einzelunterschrift",
            },
        )], ""

    return [], leftover
