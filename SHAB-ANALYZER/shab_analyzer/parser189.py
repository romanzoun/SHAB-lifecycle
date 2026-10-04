from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_DE_CAPITAL_BANDS_AND_CLAUSES = re.compile(
    r"^Kapitalband \(Aktienkapital\) gemäss näherer Umschreibung in den Statuten\.\s*"
    r"Kapitalband \(Partizipationskapital\) gemäss näherer Umschreibung in den Statuten\.\s*"
    r"Mit Beschluss der Generalversammlung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+beschlossene genehmigte "
    r"Aktienkapitalerhöhung gestrichen\.\s*\[bisher:\s*Die Generalversammlung hat mit "
    r"Beschluss vom\s+(?P<previous_share_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Aktienkapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\.\]\.\s*"
    r"Mit Beschluss der Generalversammlung vom\s+(?P<participation_decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"wird die Statutenbestimmung über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<participation_authorization_date>\d{2}\.\d{2}\.\d{4})\s+beschlossene "
    r"genehmigte Partizipationskapitalerhöhung gestrichen\.\s*\[bisher:\s*Die "
    r"Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<previous_participation_date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Partizipationskapitalerhöhung gemäss näherer Umschreibung in den Statuten "
    r"eingeführt\.\]\.\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<conditional_share_decision_date>\d{2}\.\d{2}\.\d{4})\s+die Statutenbestimmung "
    r"über die bedingte Aktienkapitalerhöhung vom\s+"
    r"(?P<conditional_share_previous_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\s*"
    r"\[bisher:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<conditional_share_history_date>\d{2}\.\d{2}\.\d{4})\s+eine bedingte "
    r"Aktienkapitalerhöhung gemäss näherer Umschreibung in den Statuten eingeführt\.\]\.\s*"
    r"Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<conditional_participation_decision_date>\d{2}\.\d{2}\.\d{4})\s+die "
    r"Statutenbestimmung über die bedingte Partizipationskapitalerhöhung vom\s+"
    r"(?P<conditional_participation_previous_date>\d{2}\.\d{2}\.\d{4})\s+geändert\.\s*"
    r"\[bisher:\s*Die Generalversammlung hat mit Beschluss vom\s+"
    r"(?P<conditional_participation_history_date>\d{2}\.\d{2}\.\d{4})\s+eine "
    r"bedingte Partizipationskapitalerhöhung gemäss näherer Umschreibung in den "
    r"Statuten eingeführt\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_DEFICIT_SAME_OWNER = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+(?P<company>.+?),\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von "
    r"CHF\s*(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s*"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Gemäss Bestätigung der zugelassenen Revisionsexpertin liegen Rangrücktritte "
    r"im Umfang des Kapitalverlustes und der Überschuldung der übernehmenden "
    r"Gesellschaft vor\.\s*Es findet weder eine Kapitalerhöhung noch eine Zuteilung "
    r"von Stammanteilen statt,\s*da die einzige Gesellschafterin der übertragenden "
    r"Gesellschaft bereits Gesellschafterin der übernehmenden Gesellschaft ist\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_REGISTERED_SHARES = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s*"
    r"(?P<assets>[\d'.]+)\s+und Passiven \(Fremdkapital\) von CHF\s*"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?)"
    r"(?:,\s*in\s+(?P<place_before>[^().]+?)\s*\((?P<uid_after>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"|\s*\((?P<uid_before>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in\s+(?P<place_after>[^.]+?))\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d']+)\s+Namenaktien zu CHF\s*"
    r"(?P<share_nominal>[\d'.]+)"
    r"(?:\s+der\s+(?P<issuer>.+?)(?:\s*\((?P<issuer_uid>CHE-\d{3}\.\d{3}\.\d{3})\))?)?"
    r"(?:\s+und Gutschrift einer Forderung von CHF\s*(?P<claim>[\d'.]+))?\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_ASSOCIATES_INDIVIDUAL_PROCURATION = re.compile(
    r"^Les associés\s+(?P<name1>[^,.;]+?)\s+et\s+(?P<name2>[^,.;]+?),\s*"
    r"signent désormais par procuration individuelle\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_BOARD_MEMBERS = re.compile(
    r"^(?P<name1>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin1>[^,.;]+),\s*à\s*(?P<place1>[^,.;]+),?\s*et\s*"
    r"(?P<name2>[^,.;]+),\s*(?:du|de la|des|de|d['’])\s*"
    r"(?P<origin2>[^,.;]+),\s*à\s*(?P<place2>[^,.;]+),\s*"
    r"(?P<country2>[A-Z]{1,3}),\s*sont membres du conseil "
    r"(?P<board>de fondation|d['’]administration)"
    r"(?:\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_TRANSLATION_ADDED = re.compile(
    r"^Adjonction d['’]une traduction à la raison sociale:\s*"
    r"(?P<name>[^\[]+?)\s*\[(?P<translation>[^\]]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_REPLACED = re.compile(
    r"^L['’]assemblée générale a supprimé une clause statutaire relative à une "
    r"augmentation autorisée du capital \(selon décision du\s+"
    r"(?P<old_date>\d{1,2}\s+[a-zéûô]+\s+\d{4})\) par décision du\s+"
    r"(?P<decision_date>\d{1,2}\s+[a-zéûô]+\s+\d{4})\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation autorisée du capital par décision du\s+"
    r"(?P<introduction_date>\d{1,2}\s+[a-zéûô]+\s+\d{4})\.\s*"
    r"Pour les détails,\s*voir les statuts\.?$",
    re.I | re.UNICODE,
)
_FR_FOUR_CAPITAL_CLAUSES = re.compile(
    r"^Suppression de la clause statutaire d['’]augmentation autorisée du "
    r"capital-actions adoptée par l['’]assemblée générale du\s+"
    r"(?P<old_authorized_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"L['’]assemblée générale du\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a adopté une clause statutaire relative à une augmentation autorisée du "
    r"capital-actions \(pour les détails:\s*voir les statuts\)\.\s*"
    r"L['’]assemblée générale du\s+(?P<conditional_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a modifié la clause statutaire relative à une augmentation conditionnelle "
    r"du capital-actions,\s*introduite par l['’]assemblée générale constitutive le\s+"
    r"(?P<conditional_old_date>\d{2}\.\d{2}\.\d{4})\s*"
    r"\(pour les détails:\s*voir les statuts\)\.\s*"
    r"L['’]assemblée générale du\s+(?P<participation_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"a introduit une clause statutaire relative à une augmentation conditionnelle "
    r"du capital-participations \(pour les détails:\s*voir les statuts\)\.?$",
    re.I | re.UNICODE,
)
_DE_PREVIOUS_BRANCH_ADDRESS = re.compile(
    r"^\[bisher:\s*Geschäftsstelle:\s*(?P<address>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_NEW_COMMITTEE_ROLE_PAIR = re.compile(
    r"^Nouveaux membres du comité(?:\s+avec signature collective à deux)?\s*:\s*"
    r"(?P<name1>[^,.;]+),\s*"
    r"(?P<role1>vice-président),\s*et\s*(?P<name2>[^,.;]+),\s*"
    r"(?P<role2>caissière),\s*tous deux de\s+(?P<origin>[^,.;]+),\s*"
    r"à\s+(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_DELETION_REINSTATED = re.compile(
    r"^Rectificatif:\s*la société ayant été radiée par erreur,\s*elle est "
    r"réinscrite comme ci-devant \(FOSC No\s+(?P<issue>\d+)\s+du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*publ\.\s*(?P<publication_id>\d+)\)\s*"
    r"\[biffé:\s*La liquidation étant terminée,\s*cette société est radiée\]\.?$",
    re.I | re.UNICODE,
)
_DE_AUDITOR_REPLACED = re.compile(
    r"^(?P<previous_name>.+?)\s*\((?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+"
    r"ist nicht mehr Revisionsstelle\.\s*Neue Revisionsstelle:\s*"
    r"(?P<name>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"in\s+(?P<place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_TWO_MANAGERS_TRANSFER_TO_CORPORATE_ASSOCIATE = re.compile(
    r"^Les gérants\s+(?P<seller1>[^,.;]+?)\s+et\s+(?P<seller2>[^,.;]+?)\s+"
    r"cèdent leurs\s+(?P<seller_count>[\d']+)\s+parts respectives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*au\s+(?P<place>[^,.;]+),\s*"
    r"nouvelle associée avec\s+(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\.?$",
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


def _amount(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


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


def extract_parser189_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 189."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _DE_CAPITAL_BANDS_AND_CLAUSES.fullmatch(leftover)
    if match and len({
        match.group("authorization_date"),
        match.group("previous_share_date"),
        match.group("participation_authorization_date"),
        match.group("previous_participation_date"),
        match.group("conditional_share_previous_date"),
        match.group("conditional_share_history_date"),
        match.group("conditional_participation_previous_date"),
        match.group("conditional_participation_history_date"),
    }) == 1 and len({
        match.group("decision_date"),
        match.group("participation_decision_date"),
        match.group("conditional_share_decision_date"),
        match.group("conditional_participation_decision_date"),
    }) == 1:
        rule_id = "de.text.capital_bands_and_four_clauses.v1"
        decision_date = _iso_date(match.group("decision_date"))
        previous_date = _iso_date(match.group("authorization_date"))
        changes = (
            ("capital_band", "introduced", "share_capital"),
            ("capital_band", "introduced", "participation_capital"),
            ("authorized_capital_clause", "removed", "share_capital"),
            ("authorized_participation_capital_clause", "removed", "participation_capital"),
            ("conditional_capital_clause", "modified", "share_capital"),
            ("conditional_participation_capital_clause", "modified", "participation_capital"),
        )
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": kind,
                    "action": action,
                    "capital_kind": capital_kind,
                    "decision_date": decision_date,
                    "previous_decision_date": previous_date,
                    "details_in_statutes": True,
                },
            )
            for kind, action, capital_kind in changes
        ], ""

    match = _DE_MERGER_DEFICIT_SAME_OWNER.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_deficit_same_owner.v1", {
                "action": "absorbed",
                "transferring_company": match.group("company").strip(),
                "transferring_company_place": match.group("place").strip(),
                "transferring_company_uid": match.group("uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "subordination_covers_capital_loss_and_overindebtedness": True,
                "capital_increase": False,
                "shares_allocated": False,
                "reason_no_shares": "same_sole_shareholder",
            },
        )], ""

    match = _DE_ASSET_TRANSFER_REGISTERED_SHARES.fullmatch(leftover)
    if match:
        uid = match.group("uid_after") or match.group("uid_before")
        place = match.group("place_before") or match.group("place_after")
        payload = {
            "source_kind": "company",
            "agreement_date": _iso_date(match.group("agreement_date")),
            "assets": match.group("assets"),
            "liabilities": match.group("liabilities"),
            "liabilities_kind": "third_party_capital",
            "currency": "CHF",
            "recipient": match.group("recipient").strip(),
            "recipient_place": place.strip(),
            "recipient_uid": uid,
            "consideration_kind": (
                "registered_shares_and_claim" if match.group("claim")
                else "registered_shares"
            ),
            "consideration_shares_count": _count(match.group("share_count")),
            "consideration_share_nominal": match.group("share_nominal"),
        }
        if match.group("issuer"):
            payload["consideration_issuer"] = match.group("issuer").strip()
        if match.group("issuer_uid"):
            payload["consideration_issuer_uid"] = match.group("issuer_uid")
        if match.group("claim"):
            payload["consideration_claim"] = match.group("claim")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_registered_shares.v1",
            payload,
        )], ""

    match = _FR_TWO_ASSOCIATES_INDIVIDUAL_PROCURATION.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.two_associates_individual_procuration.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                role="associé", signing="Einzelprokura",
                extra={"action": "procuration_granted"},
            )
            for index in (1, 2)
        ], ""

    match = _FR_TWO_BOARD_MEMBERS.fullmatch(leftover)
    if match:
        board = match.group("board").lower().replace("’", "'")
        role = f"membre du conseil {board}"
        rule_id = "fr.persons.two_board_members_foreign_second.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                place=match.group("place1"), role=role,
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "origin": match.group("origin1").strip()},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                place=match.group("place2"), role=role,
                signing="Kollektivunterschrift zu zweien",
                extra={
                    "action": "appointed",
                    "origin": match.group("origin2").strip(),
                    "country": match.group("country2").upper(),
                },
            ),
        ], ""

    match = _FR_COMPANY_TRANSLATION_ADDED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_name_changed", "fr.text.company_translation_added_brackets.v1", {
                "kind": "translation",
                "action": "added",
                "name": match.group("name").strip(),
                "translation": match.group("translation").strip(),
            },
        )], ""

    match = _FR_AUTHORIZED_CAPITAL_REPLACED.fullmatch(leftover)
    if match and match.group("decision_date").casefold() == match.group("introduction_date").casefold():
        rule_id = "fr.text.authorized_capital_clause_replaced.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause",
                    "action": "removed",
                    "previous_decision_date": _french_date(match.group("old_date")),
                    "decision_date": _french_date(match.group("decision_date")),
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause",
                    "action": "introduced",
                    "decision_date": _french_date(match.group("introduction_date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_FOUR_CAPITAL_CLAUSES.fullmatch(leftover)
    if match and len({
        match.group("decision_date"),
        match.group("conditional_date"),
        match.group("participation_date"),
    }) == 1:
        rule_id = "fr.text.four_capital_clauses.v1"
        decision_date = _iso_date(match.group("decision_date"))
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "previous_decision_date": _iso_date(match.group("old_authorized_date")),
                    "decision_date": decision_date,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "capital_kind": "capital-actions", "decision_date": decision_date,
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_capital_clause", "action": "modified",
                    "capital_kind": "capital-actions", "decision_date": decision_date,
                    "previous_decision_date": _iso_date(match.group("conditional_old_date")),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_participation_capital_clause",
                    "action": "introduced", "capital_kind": "capital-participations",
                    "decision_date": decision_date, "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_PREVIOUS_BRANCH_ADDRESS.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.previous_branch_address_removed.v1", {
                "kind": "branch_office", "action": "previous_entry_removed",
                "previous_address": match.group("address").strip(),
            },
        )], ""

    match = _FR_NEW_COMMITTEE_ROLE_PAIR.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.new_committee_role_pair.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=match.group("place"),
                role=f"membre du comité, {match.group(f'role{index}').lower()}",
                signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed", "origin": match.group("origin").strip()},
            )
            for index in (1, 2)
        ], ""

    match = _FR_ERRONEOUS_DELETION_REINSTATED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.erroneous_deletion_reinstated_with_history.v1", {
                "kind": "registration_reinstated", "action": "reinstated",
                "reason": "erroneous_deletion",
                "previous_deletion_reason": "liquidation_completed",
                "notice_issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_publication_id": match.group("publication_id"),
            },
        )], ""

    match = _DE_AUDITOR_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "de.persons.auditor_replaced.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_removed", rule_id, match.group("previous_name"),
                uid=match.group("previous_uid"), role="Revisionsstelle",
                extra={"action": "removed"},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name"),
                place=match.group("place"), uid=match.group("uid"),
                role="Revisionsstelle", extra={"action": "appointed"},
            ),
        ], ""

    match = _FR_TWO_MANAGERS_TRANSFER_TO_CORPORATE_ASSOCIATE.fullmatch(leftover)
    if match and (
        _count(match.group("buyer_count")) == 2 * _count(match.group("seller_count"))
        and _amount(match.group("nominal")) == _amount(match.group("buyer_nominal"))
    ):
        rule_id = "fr.persons.two_managers_transfer_to_corporate_associate.v1"
        buyer = match.group("buyer").strip()
        seller_count = _count(match.group("seller_count"))
        events = [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"seller{index}"),
                role="gérant", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_transferred": seller_count, "shares_count": 0,
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            )
            for index in (1, 2)
        ]
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, buyer, place=match.group("place"),
            uid=match.group("uid"), role="associée", extra={
                "action": "shares_received", "new_associate": True,
                "shares_received": _count(match.group("buyer_count")),
                "shares_count": _count(match.group("buyer_count")),
                "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
            },
        ))
        return events, ""

    return [], text
