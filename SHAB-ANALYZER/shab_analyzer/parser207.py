from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_FR_ADMINISTRATORS_ROLES_AND_SIGNING_CONTINUE = re.compile(
    r"^Les administrateurs de\s+(?P<name1>[^,;]+),\s*nommé en outre\s+"
    r"(?P<role1>directeur général)\s+et\s+(?P<name2>[^,;]+),\s*"
    r"maintenant domicilié à\s+(?P<place2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<role2>directeur),\s*continuent à signer collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_NON_PUBLIC_STATUTES_FACTS_RESIDUE = re.compile(
    r"^\[Statuten\s*\]$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PURPOSE_CHANGED_WITH_HISTORY = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*"
    r"(?P<purpose>Betrieb aller Versicherungszweige,\s*mit Ausnahme der "
    r"Lebensversicherung,.+?)\s*\[bisher:\s*"
    r"(?P<previous>Gegenstand des Unternehmens:\s*.+?)\s*\]\.?$",
    re.I | re.UNICODE,
)
_DE_LIMITED_PARTNERSHIP_CAPITAL_CHE_TYPO = re.compile(
    r"^Kommanditsumme neu:\s*(?P<currency>CHE)\s+(?P<to>[\d'.]+)\s*"
    r"\[bisher:\s*CHF\s+(?P<from>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_IT_COMPOSITION_AGREEMENT_HOMOLOGATED = re.compile(
    r"^Con decreto della\s+(?P<authority>.+?)\s+del\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+il concordato ordinario è stato "
    r"omologato\.\s*L['’]esecuzione del concordato viene affidata al "
    r"commissario,\s*il quale potrà prendere tutti i provvedimenti necessari "
    r"per l['’]esecuzione e garantirne l['’]adempimento\.?$",
    re.I | re.UNICODE,
)
_FR_PROVISIONAL_MORATORIUM_UNTIL_WITH_COMMISSIONER = re.compile(
    r"^Par prononcé rendu le\s+(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"(?P<authority>.+?)\s+a accordé à la société un sursis concordataire "
    r"provisoire jusqu['’]au\s+(?P<until>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4})\.\s*"
    r"(?P<name>[^,.;]+),\s*de\s+(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*est inscrit en qualité de commissaire au sursis\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_AFTER_ART155_DELETION = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte "
    r"Gesellschaft wird auf Grund des Urteils des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wieder in das Handelsregister "
    r"eingetragen und besteht entsprechend den früheren Eintragungen weiter\.\s*"
    r"\[bisher:\s*(?P<previous>Die Gesellschaft wird in Anwendung von Art\.\s*"
    r"155 HRegV von Amtes wegen gelöscht,\s*weil .+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTER_AND_ADDITIONAL_BRANCH_RESIDUE = re.compile(
    r"^\(HR\s+(?P<previous_register>[A-Z]{2})\)\.\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s*"
    r"\(HR\s+(?P<register>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_PREVIOUS_IDENTIFIER_AND_ADDITIONAL_BRANCH = re.compile(
    r"^\[bisher:\s*(?P<previous_place>[^()]+?)\s*"
    r"\((?P<previous_id>CH-[\d.-]+)\)\]\.?\s*"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_LAST_SHAB_CITATION_CORRECTED = re.compile(
    r"^\[Das letzte SHAB-Zitat lautet richtig SHAB-Nr\.\s*"
    r"(?P<issue>\d+)\s+vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+und nicht "
    r"SHAB-Nr\.\s*(?P<previous_issue>\d+)\s+vom\s+"
    r"(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.\]$",
    re.I | re.UNICODE,
)
_FR_ADDRESS_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]adresse est:\s*"
    r"(?P<address>.+?),\s*(?P<postal_code>\d{4})\s+(?P<locality>[^()]+?)\s*"
    r"\(et non\s+(?P<incorrect>[^,()]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_BANKRUPTCY_SUSPENDED_FINAL = re.compile(
    r"^Bemerkungen zum Hauptsitz neu:\s*(?P<authority>.+?)\s+hat das "
    r"Konkursverfahren am\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+mangels Aktiven "
    r"eingestellt\.\s*Die Einstellung ist am\s+"
    r"(?P<final_date>\d{2}\.\d{2}\.\d{4})\s+definitiv geworden\.?$",
    re.I | re.UNICODE,
)
_FR_SHARES_TRANSFERRED_BY_MERGER_TO_NEW_ASSOCIATE_SHORT = re.compile(
    r"^Par suite de fusion,\s*les\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"sont transférée?s? à\s+(?P<buyer>.+?)\s*"
    r"\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*nouvelle associée avec\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS = re.compile(
    r"^Liquidateurs:\s*les associés gérants\s+(?P<name1>[^,.;]+?)\s+et\s+"
    r"(?P<name2>[^,.;]+?),\s*lesquels signent individuellement\.?$",
    re.I | re.UNICODE,
)
_DE_ANCILLARY_OBLIGATIONS_ERRONEOUSLY_ENTERED = re.compile(
    r"^\[Die Nebenleistungspflichten wurden irrtümlich eingetragen\.\]$",
    re.I | re.UNICODE,
)
_FR_HEAD_OFFICE_NAME_AND_ENGLISH_BRANCH_NAME = re.compile(
    r"^Raison sociale du siège principal:\s*(?P<head_office_name>[^\[]+?)\s*"
    r"\[(?P<translation_nl>[^\]]+)\]\s*\[(?P<translation_de>[^\]]+)\]\s*"
    r"\[(?P<translation_en>[^\]]+)\]\.\s*Adjonction de la version anglaise "
    r"de la raison de commerce:\s*(?P<branch_name>[^\[]+?)\s*"
    r"\[(?P<branch_name_en>[^\]]+)\]\.?$",
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
    day, month, year = raw.lower().replace("1er", "1", 1).split()
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
        payload={
            "name": clean_name,
            "place": clean_place,
            **({"uid": uid} if uid else {}),
            **(extra or {}),
        },
    )


def extract_parser207_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 207."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_ADMINISTRATORS_ROLES_AND_SIGNING_CONTINUE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administrators_roles_signing_continue.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role="administrateur et directeur général",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "role_changed_and_signing_continues",
                    "appointed_role": match.group("role1").lower(),
                    "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role="administrateur",
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "domicile_changed_and_signing_continues",
                    "previous_role": match.group("role2").lower(),
                    "domicile_changed": True,
                    "signing_continues": True,
                },
            ),
        ], ""

    if _DE_NON_PUBLIC_STATUTES_FACTS_RESIDUE.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.non_public_statutes_facts_residue.v1", {
                "kind": "non_public_statutes_facts",
                "action": "changed",
                "publication_required": False,
            },
        )], ""

    match = _DE_BRANCH_PURPOSE_CHANGED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "purpose_changed", "de.text.branch_purpose_changed_history.v1", {
                "scope": "branch",
                "action": "changed",
                "from": match.group("previous").strip(),
                "to": match.group("purpose").strip(),
            },
        )], ""

    match = _DE_LIMITED_PARTNERSHIP_CAPITAL_CHE_TYPO.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.limited_partnership_capital_che_typo.v1", {
                "kind": "limited_partnership_capital",
                "action": "changed",
                "currency": "CHF",
                "source_currency_text": match.group("currency").upper(),
                "from": match.group("from"),
                "to": match.group("to"),
            },
        )], ""

    match = _IT_COMPOSITION_AGREEMENT_HOMOLOGATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.composition_agreement_homologated.v1", {
                "kind": "composition_agreement_homologated",
                "action": "homologated",
                "agreement_type": "ordinary",
                "decision_date": _iso_date(match.group("date")),
                "authority": match.group("authority").strip(),
                "execution_assigned_to_commissioner": True,
            },
        )], ""

    match = _FR_PROVISIONAL_MORATORIUM_UNTIL_WITH_COMMISSIONER.fullmatch(leftover)
    if match:
        rule_id = "fr.text.provisional_moratorium_until_with_commissioner.v1"
        commissioner = match.group("name").strip()
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id, {
                    "kind": "composition_moratorium_granted",
                    "action": "granted",
                    "moratorium_type": "provisional",
                    "decision_date": _french_date(match.group("date")),
                    "until": _french_date(match.group("until")),
                    "authority": match.group("authority").strip(),
                    "commissioner": commissioner,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, commissioner,
                place=match.group("place"), role="commissaire au sursis",
                extra={
                    "action": "appointed",
                    "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _DE_COMPANY_REINSTATED_AFTER_ART155_DELETION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_after_art155_deletion.v1", {
                "kind": "registration_reinstated",
                "action": "reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "previous_deletion_basis": "Art. 155 HRegV",
                "previous": match.group("previous").strip(),
                "company_continues": True,
                "registry_reinstated": True,
            },
        )], ""

    match = _DE_BRANCH_REGISTER_AND_ADDITIONAL_BRANCH_RESIDUE.fullmatch(leftover)
    if match:
        rule_id = "de.text.branch_register_and_additional_branch_residue.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "registry_recorded",
                    "register_canton": match.group("previous_register").upper(),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "added",
                    "place": match.group("place").strip(),
                    "branch_uid": match.group("uid"),
                    "register_canton": match.group("register").upper(),
                },
            ),
        ], ""

    match = _DE_BRANCH_PREVIOUS_IDENTIFIER_AND_ADDITIONAL_BRANCH.fullmatch(leftover)
    if match:
        rule_id = "de.text.branch_identifier_changed_and_branch_added.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "identifier_changed",
                    "place": match.group("previous_place").strip(),
                    "previous_registry_id": match.group("previous_id"),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "branch_changed", rule_id, {
                    "action": "added",
                    "place": match.group("place").strip(),
                    "branch_uid": match.group("uid"),
                },
            ),
        ], ""

    match = _DE_LAST_SHAB_CITATION_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.last_shab_citation_corrected.v1", {
                "kind": "last_shab_citation",
                "action": "corrected",
                "issue": match.group("issue"),
                "date": _iso_date(match.group("date")),
                "previous_issue": match.group("previous_issue"),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _FR_ADDRESS_CORRECTED.fullmatch(leftover)
    if match:
        address = (
            f"{match.group('address').strip()}, "
            f"{match.group('postal_code')} {match.group('locality').strip()}"
        )
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "fr.text.address_corrected_notice.v1", {
                "kind": "company_address",
                "action": "corrected",
                "address": address,
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
                "incorrect": match.group("incorrect").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_HEAD_OFFICE_BANKRUPTCY_SUSPENDED_FINAL.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.head_office_bankruptcy_suspended_final.v1", {
                "kind": "bankruptcy_suspended_no_assets",
                "scope": "head_office",
                "action": "suspended",
                "decision_date": _iso_date(match.group("date")),
                "final_date": _iso_date(match.group("final_date")),
                "authority": match.group("authority").strip(),
                "reason": "no_assets",
                "final": True,
            },
        )], ""

    match = _FR_SHARES_TRANSFERRED_BY_MERGER_TO_NEW_ASSOCIATE_SHORT.fullmatch(leftover)
    if match and (
        _count(match.group("count")) == _count(match.group("buyer_count"))
        and match.group("nominal") == match.group("buyer_nominal")
    ):
        rule_id = "fr.persons.shares_transferred_by_merger_new_associate_short.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_count": _count(match.group("count")),
            "share_nominal": match.group("nominal"),
            "currency": "CHF",
            "transfer_reason": "merger",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                uid=match.group("seller_uid"), role="associée",
                extra={
                    **common,
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer,
                place=match.group("place"), uid=match.group("buyer_uid"),
                role="associée",
                extra={
                    **common,
                    "action": "shares_received",
                    "counterparty": seller,
                    "counterparty_uid": match.group("seller_uid"),
                    "new_associate": True,
                },
            ),
        ], ""

    match = _FR_TWO_ASSOCIATE_MANAGERS_APPOINTED_LIQUIDATORS.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associate_managers_appointed_liquidators.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                role="associé-gérant et liquidateur",
                signing="Einzelunterschrift",
                extra={"action": "appointed_liquidator"},
            )
            for index in (1, 2)
        ], ""

    if _DE_ANCILLARY_OBLIGATIONS_ERRONEOUSLY_ENTERED.fullmatch(leftover):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.ancillary_obligations_erroneous_entry.v1", {
                "kind": "ancillary_obligations",
                "action": "publication_corrected",
                "ancillary_obligations": False,
                "erroneous_entry_removed": True,
            },
        )], ""

    match = _FR_HEAD_OFFICE_NAME_AND_ENGLISH_BRANCH_NAME.fullmatch(leftover)
    if match:
        rule_id = "fr.text.head_office_name_and_english_branch_name.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    "kind": "company_name",
                    "scope": "head_office",
                    "action": "recorded",
                    "name": match.group("head_office_name").strip(),
                    "translations": {
                        "nl": match.group("translation_nl").strip(),
                        "de": match.group("translation_de").strip(),
                        "en": match.group("translation_en").strip(),
                    },
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "company_name_changed", rule_id, {
                    "kind": "company_name_translation",
                    "scope": "branch",
                    "action": "translation_added",
                    "language": "en",
                    "name": match.group("branch_name").strip(),
                    "translation": match.group("branch_name_en").strip(),
                },
            ),
        ], ""

    return [], leftover
