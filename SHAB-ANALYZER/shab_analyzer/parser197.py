from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_CAPITAL_BAND_AND_CONDITIONAL_CLAUSE_ARTICLES = re.compile(
    r"^L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"marge de fluctuation du capital-actions par décision du\s+"
    r"(?P<band_date>\d{2}\.\d{2}\.\d{4});\s*pour les détails,\s*voir les "
    r"statuts\s*\(art\.\s*(?P<band_article>[^)]+)\)\.\s*"
    r"L['’]assemblée générale a introduit une clause statutaire relative à une "
    r"augmentation du capital-actions au moyen d['’]un capital conditionnel,\s*"
    r"par décision du\s+(?P<conditional_date>\d{2}\.\d{2}\.\d{4});\s*"
    r"pour les détails,\s*voir les statuts\s*"
    r"\(art\.\s*(?P<conditional_article>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSOCIATION_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Der Verein überträgt gemäss "
    r"Vermögensübertragungsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_INTENDED_ACQUISITION_TYPO_CORRECTED_FRAGMENT = re.compile(
    r"^Schreibfehler\s*\((?P<incorrect>[^()]+?)\s+statt\s+"
    r"(?P<correct>[^()]+?)\)\s+korrigiert\.\s*eingetragenen "
    r"Einzelunternehmens\s+(?P<source>.+?),\s*in\s+(?P<place>[^,]+),\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*gemäss der Schlussbilanz "
    r"per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\s+mit Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+zum Preis von höchstens CHF\s+"
    r"(?P<maximum_price>[\d'.]+)\s+zu übernehmen\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_BOARD_SEVEN_WITHOUT_SIGNATURE = re.compile(
    r"^Conseil de fondation:\s*"
    r"(?P<name1>[^,]+),\s*d['’](?P<origin1>[^,]+),\s*"
    r"(?P<role1>président),\s*"
    r"(?P<name2>[^,]+),\s*de\s+(?P<origin2>[^,]+),\s*"
    r"(?P<role2>vice-président),\s*"
    r"(?P<name3>[^,]+),\s*de\s+(?P<origin3>[^,]+),\s*"
    r"(?P<role3>secrétaire),\s*"
    r"(?P<name4>[^,]+),\s*de\s+(?P<origin4>[^,]+),\s*"
    r"(?P<name5>[^,]+),\s*de\s+(?P<origin5>[^,]+),\s*"
    r"(?P<name6>[^,]+),\s*de\s+(?P<origin6>[^,]+),\s*et\s*"
    r"(?P<name7>[^,]+),\s*de\s+(?P<origin7>[^,]+),\s*"
    r"tous les sept domiciliés à\s+(?P<place>[^,.;]+),\s*lesquels "
    r"n['’]exercent pas la signature sociale\.?$",
    re.I | re.UNICODE,
)
_DE_REMOVED_ADDITIONAL_ADDRESS_REGISTER_HEADING = re.compile(
    r"^\[Die folgenden weiteren Adressen werden im Handelsregister gelöscht\]\s*"
    r"\[gestrichen:\s*Weitere Adresse:\s*(?P<address>[^\]]+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENERAL_RETAINED_CORRECTION = re.compile(
    r"^L['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que\s+"
    r"(?P<name>[^,.;]+)\s+reste\s+(?P<role>directeur général)"
    r"(?:\s+avec\s+(?P<signing>signature collective à deux))?\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_HISTORY = re.compile(
    r"^Mit Beschluss der Generalversammlung vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wird die Statutenbestimmung "
    r"über die mit Ermächtigungsbeschluss vom\s+"
    r"(?P<authorization_date>\d{2}\.\d{2}\.\d{4})\s+beschlossene genehmigte "
    r"Kapitalerhöhung gestrichen\.\s*\[bisher:\s*Die Generalversammlung hat "
    r"mit Beschluss vom\s+(?P<history_date>\d{2}\.\d{2}\.\d{4})\s+den "
    r"Beschluss über die Ermächtigung einer genehmigten Kapitalerhöhung vom\s+"
    r"(?P<previous_authorization_date>\d{2}\.\d{2}\.\d{4})\s+gemäss näherer "
    r"Umschreibung in den Statuten angepasst\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_REINSTATED_ART_164_WITH_HISTORY = re.compile(
    r"^Die am\s+(?P<deletion_date>\d{2}\.\d{2}\.\d{4})\s+gelöschte "
    r"Gesellschaft wird auf Grund des Urteils des\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+im Sinne von\s+"
    r"(?P<legal_basis>Art\.\s*164 Abs\.\s*1 lit\.\s*d HRegV)\s+wieder in das "
    r"Handelsregister eingetragen und besteht entsprechend den früheren "
    r"Eintragungen weiter\.\s*\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_INVESTMENT_CLAIMS_NET_ASSET_VALUE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<claims>[\d'.]+)\s+Ansprüche an der Anlagegruppe\s+"
    r"[\"“](?P<investment_group>[^\"”]+)[\"”]\s+mit einem Nettoinventarwert "
    r"von CHF\s+(?P<net_asset_value>[\d'.]+)\s+pro Anspruch\s*"
    r"\(Buchwert\s*\(Swiss GAAP FER\)\s*per\s+"
    r"(?P<book_date>\d{2}\.\d{2}\.\d{4})\)\s+mit Wirkung per\s+"
    r"(?P<effective_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_AUTHORIZED_CAPITAL_EXPIRED_AND_REINTRODUCED = re.compile(
    r"^Streichung der Statutenbestimmung über die mit Ermächtigungsbeschluss "
    r"vom\s+(?P<previous_date>\d{2}\.\d{2}\.\d{4})\s+eingeführte genehmigte "
    r"Kapitalerhöhung infolge Zeitablaufs\.\s*\.\s*Die Gesellschaft hat mit "
    r"Beschluss vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+eine genehmigte "
    r"Kapitalerhöhung gemäss näherer Umschreibung in den Statuten beschlossen\.?$",
    re.I | re.UNICODE,
)
_FR_BOARD_SECRETARY_CHANGED_PAIR_CONTINUES_SIGNING = re.compile(
    r"^Les membres du conseil\s+(?P<name1>[^,.;]+),\s*nommée\s+"
    r"(?P<role1>secrétaire)\s+et\s+(?P<name2>[^,.;]+),\s*jusqu['’]ici\s+"
    r"(?P<previous_role2>secrétaire),\s*continuent à signer collectivement à "
    r"deux\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_CLOSED_AFTER_BUSINESS_TRANSFER_PENDING_TAX = re.compile(
    r"^Angaben zur Zweigniederlassung neu:\s*Die Zweigniederlassung ist infolge "
    r"Übergang des Geschäftes auf die\s+(?P<successor>.+?)\s+aufgehoben\.\s*"
    r"\[Die Löschung erfolgt sobald die Zustimmungen der Steuerverwaltung "
    r"vorliegen\.\]\.?$",
    re.I | re.UNICODE,
)
_DE_NAMED_ENTITY_ASSET_TRANSFER_TWO_DATES_PRICE_ADJUSTMENT = re.compile(
    r"^Vermögensübertragung:\s*Die\s+(?P<source>.+?)\s+überträgt gemäss Vertrag "
    r"vom\s+(?P<agreement_date1>\d{2}\.\d{2}\.\d{4})/"
    r"(?P<agreement_date2>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\s+sowie ein "
    r"zusätzlicher Betrag gemäss vertraglicher Preisanpassungsklausel\.?$",
    re.I | re.UNICODE,
)
_DE_COMPANY_DELETION_WRONG_CORRECTED = re.compile(
    r"^Die Löschung der Gesellschaft\s*\(SHAB Nr\.\s*(?P<issue>\d+)\s+vom\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4})\)\s+ist zu Unrecht erfolgt und "
    r"wird hiermit berichtigt\.\s*\[bisher:\s*(?P<previous>.+?)\]\.?$",
    re.I | re.UNICODE,
)
_FR_LIMITED_PARTNERSHIP_CAPITAL_INCREASED = re.compile(
    r"^Contrat de société modifié les\s+(?P<day1>\d{1,2})\s+et\s+"
    r"(?P<day2>\d{1,2})\s+(?P<month>mai)\s+(?P<year>\d{4})\.\s*"
    r"Le montant de la commandite est augmenté de CHF\s+"
    r"(?P<previous>[\d'.]+)\s+à CHF\s+(?P<total>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_SIX_SIGNATORIES_COLLECTIVE_NOT_AMONG_THEMSELVES = re.compile(
    r"^Signature collective à deux,\s*toutefois pas entre eux,\s*est conférée à\s+"
    r"(?P<name1>[^,]+),\s*de\s+(?P<origin1>[^,]+),\s*à\s+(?P<place1>[^,]+),\s*"
    r"(?P<name2>[^,]+),\s*de\s+(?P<origin2>[^,]+),\s*à\s+(?P<place2>[^,]+),\s*"
    r"(?P<name3>[^,]+),\s*d['’](?P<origin3>[^,]+),\s*à\s+(?P<place3>[^,]+),\s*"
    r"(?P<name4>[^,]+),\s*de\s+(?P<origin4>[^,]+),\s*à\s+(?P<place4>[^,]+),\s*"
    r"(?P<name5>[^,]+),\s*de\s+(?P<origin5>[^,]+),\s*à\s+(?P<place5>[^,]+),\s*"
    r"et\s+(?P<name6>[^,]+),\s*de\s+(?P<origin6>[^,]+),\s*à\s+"
    r"(?P<place6>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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


def extract_parser197_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 197."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_CAPITAL_BAND_AND_CONDITIONAL_CLAUSE_ARTICLES.fullmatch(leftover)
    if match:
        rule_id = "fr.text.capital_band_and_conditional_clause_articles.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "capital_band_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("band_date")),
                    "statute_article": match.group("band_article").strip(),
                    "details_in_statutes": True,
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "conditional_share_capital_clause",
                    "action": "introduced",
                    "decision_date": _iso_date(match.group("conditional_date")),
                    "statute_article": match.group("conditional_article").strip(),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_ASSOCIATION_ASSET_TRANSFER_INVENTORY_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.association_asset_transfer_inventory_no_consideration.v1", {
                "source_kind": "association",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _DE_INTENDED_ACQUISITION_TYPO_CORRECTED_FRAGMENT.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("maximum_price"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected",
            "de.text.intended_acquisition_typo_corrected_fragment.v1", {
                "kind": "intended_asset_acquisition",
                "action": "publication_corrected",
                "incorrect_term": match.group("incorrect").strip(),
                "correct_term": match.group("correct").strip(),
                "source": match.group("source").strip(),
                "source_place": match.group("place").strip(),
                "source_uid": match.group("uid"),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital",
                "maximum_price": match.group("maximum_price"), "currency": "CHF",
            },
        )], ""

    match = _FR_FOUNDATION_BOARD_SEVEN_WITHOUT_SIGNATURE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.foundation_board_seven_without_signature.v1"
        place = match.group("place")
        events = []
        for index in range(1, 8):
            role = match.groupdict().get(f"role{index}") or "membre du conseil de fondation"
            events.append(_person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group(f"name{index}"),
                place=place, role=role, extra={
                    "action": "appointed",
                    "origin": match.group(f"origin{index}").strip(),
                    "without_signature": True,
                },
            ))
        return events, ""

    match = _DE_REMOVED_ADDITIONAL_ADDRESS_REGISTER_HEADING.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.additional_address_register_removed.v1", {
                "action": "removed", "kind": "additional_address",
                "address": match.group("address").strip().rstrip("."),
                "commercial_register_deletion": True,
            },
        )], ""

    match = _FR_DIRECTOR_GENERAL_RETAINED_CORRECTION.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_general_retained_correction.v1",
            match.group("name"), role=match.group("role"),
            signing=(
                "Kollektivunterschrift zu zweien"
                if match.group("signing") else None
            ), extra={
                "action": "retention_corrected", "remains_registered": True,
                "signing_continues": bool(match.group("signing")),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_CLAUSE_REMOVED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.authorized_capital_clause_removed_history.v1", {
                "kind": "authorized_capital_clause", "action": "removed",
                "decision_date": _iso_date(match.group("decision_date")),
                "authorization_date": _iso_date(match.group("authorization_date")),
                "previous_adjustment_date": _iso_date(match.group("history_date")),
                "previous_authorization_date": _iso_date(
                    match.group("previous_authorization_date")
                ),
                "previous_entry_removed": True,
            },
        )], ""

    match = _DE_COMPANY_REINSTATED_ART_164_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_reinstated_art_164_history.v1", {
                "kind": "company_reinstated", "action": "reinstated",
                "deletion_date": _iso_date(match.group("deletion_date")),
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "continues_under_previous_entries": True,
                "previous_entry": match.group("previous").strip(),
                "previous_entry_removed": True,
            },
        )], ""

    match = _DE_ASSET_TRANSFER_INVESTMENT_CLAIMS_NET_ASSET_VALUE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.asset_transfer_investment_claims_net_asset_value.v1", {
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "currency": "CHF",
                "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "investment_group_claims",
                "claims": match.group("claims"),
                "investment_group": match.group("investment_group").strip(),
                "net_asset_value_per_claim": match.group("net_asset_value"),
                "valuation_standard": "Swiss GAAP FER",
                "book_date": _iso_date(match.group("book_date")),
                "effective_date": _iso_date(match.group("effective_date")),
            },
        )], ""

    match = _DE_AUTHORIZED_CAPITAL_EXPIRED_AND_REINTRODUCED.fullmatch(leftover)
    if match:
        rule_id = "de.text.authorized_capital_expired_and_reintroduced.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "authorization_date": _iso_date(match.group("previous_date")),
                    "reason": "authorization_expired",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("date")),
                    "details_in_statutes": True,
                },
            ),
        ], ""

    match = _FR_BOARD_SECRETARY_CHANGED_PAIR_CONTINUES_SIGNING.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.board_secretary_changed_pair_continues_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name1"),
                role=match.group("role1"), signing="Kollektivunterschrift zu zweien",
                extra={"action": "appointed_secretary", "signing_continues": True},
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("name2"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "secretary_role_ended",
                    "previous_role": match.group("previous_role2"),
                    "signing_continues": True,
                },
            ),
        ], ""

    match = _DE_BRANCH_CLOSED_AFTER_BUSINESS_TRANSFER_PENDING_TAX.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_closed_business_transfer_pending_tax.v1", {
                "action": "closed", "business_operations_ceased": True,
                "business_transferred": True,
                "successor": match.group("successor").strip(),
                "deletion_pending": True,
                "reason": "tax_authority_approvals_pending",
            },
        )], ""

    match = _DE_NAMED_ENTITY_ASSET_TRANSFER_TWO_DATES_PRICE_ADJUSTMENT.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred",
            "de.text.named_entity_asset_transfer_two_dates_price_adjustment.v1", {
                "source": match.group("source").strip(),
                "agreement_dates": [
                    _iso_date(match.group("agreement_date1")),
                    _iso_date(match.group("agreement_date2")),
                ],
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash_and_variable_price_adjustment",
                "additional_consideration": "contractual_price_adjustment_clause",
            },
        )], ""

    match = _DE_COMPANY_DELETION_WRONG_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.company_deletion_wrong_corrected.v1", {
                "kind": "company_reinstated", "action": "deletion_corrected",
                "issue": match.group("issue"),
                "notice_date": _iso_date(match.group("notice_date")),
                "deletion_was_erroneous": True,
                "previous_entry": match.group("previous").strip(),
                "previous_entry_removed": True,
            },
        )], ""

    match = _FR_LIMITED_PARTNERSHIP_CAPITAL_INCREASED.fullmatch(leftover)
    if match:
        year = int(match.group("year"))
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "fr.text.limited_partnership_capital_increased.v1", {
                "kind": "limited_partnership_capital", "action": "increased",
                "partnership_agreement_dates": [
                    f"{year:04d}-05-{int(match.group('day1')):02d}",
                    f"{year:04d}-05-{int(match.group('day2')):02d}",
                ],
                "from": match.group("previous"), "to": match.group("total"),
                "currency": "CHF",
            },
        )], ""

    match = _FR_SIX_SIGNATORIES_COLLECTIVE_NOT_AMONG_THEMSELVES.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.six_signatories_collective_not_among_themselves.v1"
        names = [match.group(f"name{index}").strip() for index in range(1, 7)]
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "signing_authority_changed", rule_id, match.group(f"name{index}"),
                place=match.group(f"place{index}"),
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "signing_granted",
                    "origin": match.group(f"origin{index}").strip(),
                    "cannot_sign_with": [name for name in names if name != names[index - 1]],
                    "not_among_themselves": True,
                },
            )
            for index in range(1, 7)
        ], ""

    return [], leftover
