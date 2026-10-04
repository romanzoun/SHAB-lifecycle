from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ASSOCIATES_SHARE_TRANSFER_AND_PRESIDENCY = re.compile(
    r"^Les statuts dérogent à la loi quant aux modalités du transfert des "
    r"parts sociales:\s*pour les détails,\s*voir les statuts\.\s*"
    r"(?P<associate>[^.;]+?)\s+et\s+(?P<seller>[^.;]+?)\s+ont maintenant "
    r"respectivement\s+(?P<associate_count>[\d']+)\s+et\s+"
    r"(?P<seller_before>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+)\.\s*(?P=seller),\s*qui est maintenant à\s+"
    r"(?P<seller_place>[^,.;]+),\s*cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before_again>[\d']+)\s+parts de\s+(?P=currency)\s+(?P<nominal_again>[\d'.]+)\s+"
    r"à\s+(?P<buyer>[^,.;]+),\s*d['’](?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<buyer_place>[^,.;]+),\s*nouvel associé-gérant(?: avec\s+"
    r"(?P<buyer_signing>signature individuelle))?,\s*avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+);\s*(?P=seller),\s*qui reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<seller_nominal>[\d'.]+),\s*est nommé président\.?$",
    re.I | re.UNICODE,
)
_FR_CURRENT_ADDITIONAL_ADDRESS = re.compile(
    r"^Autre adresse actuelle:\s*(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<place>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_COMPANY_REINSTATED = re.compile(
    r"^Diese infolge Konkurses im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*159 Abs\.\s*5 lit\.\s*a HRegV)\s+am\s+"
    r"(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+von Amtes wegen gelöschte "
    r"Gesellschaft wird gemäss Entscheid des\s+(?P<authority>zuständigen Einzelgerichts)\s+"
    r"vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder in das "
    r"Handelsregister eingetragen\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_PRESIDENT_AND_INDIVIDUAL_SIGNING = re.compile(
    r"^Gérants:\s*(?P<president>[^,.;]+),\s*maintenant originaire de\s+"
    r"(?P<president_origin>[^,.;]+),\s*nommé président,\s*et\s+"
    r"(?P<manager>[^,.;]+),\s*de\s+(?P<manager_origin>[^,.;]+),\s*à\s+"
    r"(?P<manager_place>[^,.;]+),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que la\s+"
    r"(?P<role>directrice) inscrite porte le nom de\s+(?P<name>[^()]+?)\s*"
    r"\(et non:\s*(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_PURPOSE_MODIFIED = re.compile(
    r"^Le but a été modifié\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_MANAGER_NAME_CORRECTED_WITH_NOTICE = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(publication FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+page\s+"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]"
    r"(?P<role>associé-gérant) est nommé\s+(?P<name>[^()]+?)\s*"
    r"\(et non\s+(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATION_DISSOLVED_BANKRUPTCY_LIQUIDATION = re.compile(
    r"^Par décision du\s+(?P<authority>.+?)\s+du\s+"
    r"(?P<decision_date>\d{1,2}\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"l['’]association a été déclarée dissoute conformément aux articles\s+"
    r"(?P<legal_basis>154 ORC et 69a CC);\s*sa liquidation a été ordonnée "
    r"selon les dispositions applicables à la faillite\.?$",
    re.I | re.UNICODE,
)
_DE_NATIONALITY_CORRECTED = re.compile(
    r"^Im SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\s+publizierten TR-Eintrag\s+"
    r"(?P<entry>[\d']+)\s+wurde irrtümlich\s*\[bisher:\s*"
    r"(?P<previous>[^\]]+)\]\s*publiziert\.\s*Korrekt ist\s*"
    r"\[bisher:\s*(?P<current>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_PROCEEDING_RESUMED_AFTER_SECURITY = re.compile(
    r"^Das mit Urteil des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven "
    r"eingestellte Konkursverfahren wird nun durchgeführt,\s*da im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*230 Abs\.\s*2 SchKG)\s+die Durchführung des "
    r"Konkursverfahrens verlangt und die erforderliche Sicherheit geleistet "
    r"wurde\.\s*\[bisher:\s*(?P<previous>.+)\]\.?$",
    re.I | re.DOTALL | re.UNICODE,
)
_FR_EXACT_GIVEN_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\),?\s*est rectifiée en ce sens que le prénom "
    r"exact de\s+(?P<previous_name>[^()]+?)\s+est\s+(?P<name>[^();]+?)\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_SHARE_TRANSFER_TO_ORGANIZATION = re.compile(
    r"^(?P<seller>[^,.;]+),\s*maintenant associé-gérant,\s*pour\s+"
    r"(?P<seller_count>[\d']+)\s+parts de\s+(?P<currency>[A-Z]{3})\s+"
    r"(?P<nominal>[\d'.]+),\s*par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<transferred_nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<registry_id>\d+)\),\s*maintenant associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de\s+(?P=currency)\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_COMMON_OWNER_ALL_INTERESTS = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE[ .-]\d{3}\.\d{3}\.\d{3})\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Aktiven von\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und "
    r"Fremdkapital von\s+(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+gehen "
    r"auf die übernehmende Gesellschaft über\.\s*Da dieselbe Rechtsträgerin "
    r"sämtliche Aktien und Stammanteile der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Zuteilung von Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)
_DE_TWO_BOARD_MEMBERS_APPOINTED = re.compile(
    r"^Eingetragene Personen neu oder mutierend:\s*"
    r"(?P<surname1>[^,;]+),\s*(?P<given1>[^,;]+),\s*von\s+"
    r"(?P<origin1>[^,;]+),\s*in\s+(?P<place1>[^,;]+),\s*"
    r"(?P<role1>Mitglied des Vorstandes),\s*mit\s+"
    r"(?P<signing1>Kollektivunterschrift zu zweien);\s*"
    r"(?P<surname2>[^,;]+),\s*(?P<given2>[^,;]+),\s*von\s+"
    r"(?P<origin2>[^,;]+),\s*in\s+(?P<place2>[^,;]+),\s*"
    r"(?P<role2>Mitglied des Vorstandes),\s*mit\s+"
    r"(?P<signing2>Kollektivunterschrift zu zweien)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_GIVEN_NAME_CORRECTED = re.compile(
    r"^Le prénom exact de l['’](?P<role>administrateur) est\s+"
    r"(?P<name>.+?)\s+et non pas\s+(?P<previous_name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_IT_HEAD_OFFICE_SUPPRESSION_BRANCH_DELETION_BLOCKED = re.compile(
    r"^,?\s*Sede principale a:\s*Nuova sede principale:\s*"
    r"(?P<head_office>[^()]+?)\s*\((?P<country>[A-Z]{2})\)\.\s*"
    r"Nuove disposizioni per la succursale:\s*La succursale deve essere "
    r"cancellata a seguito della soppressione della sede principale\.\s*"
    r"La cancellazione non può tuttavia essere effettuata mancando il consenso "
    r"delle autorità fiscali federali e cantonali\.?$",
    re.I | re.UNICODE,
)


_FRENCH_MONTHS = {
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


def _iso_french_date(raw: str) -> str:
    day, month, year = raw.lower().split()
    return f"{int(year):04d}-{_FRENCH_MONTHS[month]:02d}-{int(day):02d}"


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
        role=role.strip() if role else None,
        signing=signing.strip() if signing else None,
        payload={"name": clean_name, "place": clean_place, **(extra or {})},
    )


def extract_parser222_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 222."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ASSOCIATES_SHARE_TRANSFER_AND_PRESIDENCY.fullmatch(leftover)
    if match:
        counts = {
            "associate": _count(match.group("associate_count")),
            "before": _count(match.group("seller_before")),
            "before_again": _count(match.group("before_again")),
            "transferred": _count(match.group("transferred")),
            "seller": _count(match.group("seller_count")),
            "buyer": _count(match.group("buyer_count")),
        }
        nominals = {
            match.group("nominal"),
            match.group("nominal_again"),
            match.group("buyer_nominal"),
            match.group("seller_nominal"),
        }
        if (
            counts["before"] == counts["before_again"]
            and counts["before"] - counts["transferred"] == counts["seller"]
            and counts["transferred"] == counts["buyer"]
            and len(nominals) == 1
        ):
            rule_id = "fr.persons.associates_share_transfer_and_presidency.v1"
            currency = match.group("currency").upper()
            nominal = match.group("nominal")
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "statutes_changed", rule_id, {
                        "kind": "share_transfer_rules",
                        "action": "introduced",
                        "share_transfer_rules": "statutory_derogation",
                        "details_in_statutes": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group("associate"),
                    role="associé", extra={
                        "action": "shareholding_recorded",
                        "shares_count": counts["associate"],
                        "shares_nominal": nominal,
                        "currency": currency,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    place=match.group("seller_place"),
                    role="associé-gérant et président", extra={
                        "action": "shares_transferred_and_appointed_president",
                        "counterparty": buyer,
                        "shares_before": counts["before"],
                        "shares_transferred": counts["transferred"],
                        "shares_count": counts["seller"],
                        "shares_nominal": nominal,
                        "currency": currency,
                        "domicile_changed": True,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer,
                    place=match.group("buyer_place"), role="associé-gérant",
                    signing=(
                        "Einzelunterschrift"
                        if match.group("buyer_signing") else None
                    ),
                    extra={
                        "action": "shares_received_and_appointed_manager",
                        "counterparty": seller,
                        "origin": match.group("origin").strip(),
                        "new_associate": True,
                        "shares_received": counts["transferred"],
                        "shares_count": counts["buyer"],
                        "shares_nominal": nominal,
                        "currency": currency,
                    },
                ),
            ], ""

    match = _FR_CURRENT_ADDITIONAL_ADDRESS.fullmatch(leftover)
    if match:
        address = (
            f"{match.group('street').strip()} {match.group('house')}, "
            f"{match.group('postal_code')} {match.group('place').strip()}"
        )
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.current_additional_address.v1", {
                "kind": "additional_address", "action": "current_address_recorded",
                "address": address, "street": match.group("street").strip(),
                "house_number": match.group("house"),
                "postal_code": match.group("postal_code"),
                "place": match.group("place").strip(),
            },
        )], ""

    match = _DE_BANKRUPTCY_COMPANY_REINSTATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_company_reinstated.v1", {
                "kind": "bankruptcy", "action": "reinstated_after_ex_officio_deletion",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
            },
        )], ""

    match = _FR_TWO_MANAGERS_PRESIDENT_AND_INDIVIDUAL_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_managers_president_individual_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="gérant et président", signing="Einzelunterschrift", extra={
                    "action": "appointed_president",
                    "origin": match.group("president_origin").strip(),
                    "origin_changed": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("manager"),
                place=match.group("manager_place"), role="gérant",
                signing="Einzelunterschrift", extra={
                    "action": "registered",
                    "origin": match.group("manager_origin").strip(),
                },
            ),
        ], ""

    match = _FR_DIRECTOR_NAME_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    if _FR_PURPOSE_MODIFIED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "fr.text.purpose_modified.v1", {
                "action": "modified", "detail_published": False,
            },
        )], ""

    match = _FR_ASSOCIATE_MANAGER_NAME_CORRECTED_WITH_NOTICE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.associate_manager_name_corrected_with_notice.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_ASSOCIATION_DISSOLVED_BANKRUPTCY_LIQUIDATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "fr.text.association_dissolved_bankruptcy_liquidation.v1", {
                "kind": "dissolution", "action": "dissolved",
                "organization_kind": "association",
                "decision_date": _iso_french_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": match.group("legal_basis"),
                "liquidation": True,
                "liquidation_procedure": "bankruptcy",
            },
        )], ""

    match = _DE_NATIONALITY_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.nationality_corrected.v1", {
                "scope": "officer_nationality", "action": "corrected",
                "from": match.group("previous").strip(),
                "to": match.group("current").strip(),
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "entry": match.group("entry"),
            },
        )], ""

    match = _DE_BANKRUPTCY_PROCEEDING_RESUMED_AFTER_SECURITY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed",
            "de.text.bankruptcy_proceeding_resumed_after_security.v1", {
                "kind": "bankruptcy", "action": "proceeding_resumed",
                "suspension_date": _iso_date(match.group("suspension_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "continuation_requested": True,
                "security_provided": True,
                "previous": match.group("previous").strip(),
            },
        )], ""

    match = _FR_EXACT_GIVEN_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.exact_given_name_corrected.v2",
            match.group("name"), extra={
                "action": "given_name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _FR_MANAGER_SHARE_TRANSFER_TO_ORGANIZATION.fullmatch(leftover)
    if match:
        seller_count = _count(match.group("seller_count"))
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        nominals = {
            match.group("nominal"),
            match.group("transferred_nominal"),
            match.group("buyer_nominal"),
        }
        if len(nominals) == 1:
            rule_id = "fr.persons.manager_share_transfer_to_organization.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            currency = match.group("currency").upper()
            nominal = match.group("nominal")
            return [
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    role="associé-gérant", extra={
                        "action": "shares_transferred_and_appointed_manager",
                        "counterparty": buyer,
                        "shares_before": seller_count + transferred,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                        "shares_nominal": nominal,
                        "currency": currency,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associée", extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "registry_id": match.group("registry_id"),
                        "shares_before": buyer_count - transferred,
                        "shares_received": transferred,
                        "shares_count": buyer_count,
                        "shares_nominal": nominal,
                        "currency": currency,
                    },
                ),
            ], ""

    match = _DE_MERGER_COMMON_OWNER_ALL_INTERESTS.fullmatch(leftover)
    if match:
        absorbed_uid = re.sub(r"^CHE[ .-]", "CHE-", match.group("absorbed_uid"))
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_common_owner_all_interests.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": absorbed_uid,
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "currency": match.group("currency").upper(),
                "common_owner_holds_all_interests": True,
                "interest_kinds": ["Aktien", "Stammanteile"],
                "capital_increase": False,
                "share_allocation": False,
            },
        )], ""

    match = _DE_TWO_BOARD_MEMBERS_APPOINTED.fullmatch(leftover)
    if match:
        rule_id = "de.persons.two_board_members_appointed.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id,
                f"{match.group(f'surname{index}')}, {match.group(f'given{index}')}",
                place=match.group(f"place{index}"), role=match.group(f"role{index}"),
                signing=match.group(f"signing{index}"), extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                },
            )
            for index in (1, 2)
        ], ""

    match = _FR_ADMINISTRATOR_GIVEN_NAME_CORRECTED.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_given_name_corrected.v1",
            match.group("name"), role=match.group("role"), extra={
                "action": "given_name_corrected",
                "previous_name": match.group("previous_name").strip(),
            },
        )], ""

    match = _IT_HEAD_OFFICE_SUPPRESSION_BRANCH_DELETION_BLOCKED.fullmatch(leftover)
    if match:
        rule_id = "it.text.head_office_suppression_branch_deletion_blocked.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "seat_changed", rule_id, {
                    "kind": "head_office", "action": "changed",
                    "to": match.group("head_office").strip(),
                    "country": match.group("country").upper(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "branch_deletion_pending",
                    "reason": "head_office_suppressed",
                    "deletion_blocked": True,
                    "deletion_blocked_reason": (
                        "federal_and_cantonal_tax_authority_consent_missing"
                    ),
                },
            ),
        ], ""

    return [], leftover
