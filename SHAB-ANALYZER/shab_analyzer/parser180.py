from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH = re.compile(
    r"^Transfert de patrimoine:\s*Selon contrat du "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*la société a transféré des "
    r"actifs pour CHF (?P<assets>[\d'.]+) et aucun passif envers les tiers,\s*à "
    r"(?P<recipient>.+?) à (?P<place>[^()]+?)\s*\((?P<recipient_canton>[A-Z]{2})\)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*Contre-prestation:\s*CHF "
    r"(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED = re.compile(
    r"^Suppression de la clause statutaire relative à l['’]augmentation autorisée "
    r"du capital-actions,\s*fondée sur la décision d['’]autorisation du "
    r"(?P<removed_date>\d{2}\.\d{2}\.\d{4})(?:,\s*le délai étant écoulé)?\s*\.\s*"
    r"L['’]assemblée générale a "
    r"introduit une clause statutaire relative à une nouvelle augmentation "
    r"autorisée du capital-actions par décision du "
    r"(?P<introduced_date>\d{2}\.\d{2}\.\d{4});\s*pour les détails,\s*voir les "
    r"statuts\.?$",
    re.I | re.UNICODE,
)
_DE_OPERATIONAL_BUSINESS_TRANSFER_SHARES_AND_CREDIT = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss "
    r"Vermögensübertragungsvertrag vom (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) "
    r"und Bilanz per (?P<balance_date>\d{2}\.\d{2}\.\d{4}) deren operativen "
    r"Geschäftsbetrieb mit Aktiven von CHF (?P<assets>[\d'.]+) und Fremdkapital "
    r"von CHF (?P<liabilities>[\d'.]+) auf die (?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*(?P<share_count>[\d']+) Namenaktien zu CHF "
    r"(?P<share_nominal>[\d'.]+) und eine Gutschrift als Forderung von CHF "
    r"(?P<claim>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_IT_DISSOLUTION_APPEAL_GRANTED = re.compile(
    r"^Nuova ditta:\s*(?P<name>.+?)\.\s*\[radiati:\s*Con decreto della "
    r"(?P<lower_authority>.+?) del (?P<dissolution_date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"è stato dichiarato lo scioglimento della società e ordinata la liquidazione "
    r"in via di fallimento \((?P<legal_basis>art\.\s*731b cpv\.\s*1 cfr\.\s*3 CO)\)\.\]\.\s*"
    r"Con decisione del (?P<decision_date>\d{2}\.\d{2}\.\d{4}),\s*il "
    r"(?P<appeal_authority>.+?) ha annullato la decisione di scioglimento della "
    r"(?P=lower_authority) del (?P=dissolution_date),\s*in quanto la società ha "
    r"ripristinato la situazione legale relativa alla sua organizzazione\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}) Aktiven von CHF "
    r"(?P<assets>[\d'.]+) auf die (?P<recipient>.+?),\s*in "
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*keine\.?$",
    re.I | re.UNICODE,
)
_DE_OUTGOING_SPIN_OFF_UID_BEFORE_PLACE = re.compile(
    r"^Abspaltung:\s*Ein Teil der Aktiven und Passiven geht gemäss Spaltungsplan "
    r"vom (?P<date>\d{2}\.\d{2}\.\d{4}) auf die (?P<newly_founded>neu gegründete )?"
    r"(?P<recipient>.+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in "
    r"(?P<place>[^,.;]+),\s*über\.?$",
    re.I | re.UNICODE,
)
_DE_JOINT_ASSET_TRANSFER_SHARES_EXCHANGE = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt zusammen mit der "
    r"(?P<co_transferor1>.+?)\s*\((?P<co_uid1>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"(?: mit Sitz in |,\s*in )(?P<co_place1>.+?) und der "
    r"(?P<co_transferor2>.+?)\s*\((?P<co_uid2>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"(?: mit Sitz in |,\s*in )(?P<co_place2>.+?)(?:,\s*in Gesamthandschaft| in Gesamthandschaft),\s*"
    r"gemäss Vertrag vom (?P<agreement_date>\d{2}\.\d{2}\.\d{4}) "
    r"(?P<transferred_count>[\d']+) Namenaktien zu CHF "
    r"(?P<transferred_nominal>[\d'.]+) der (?P<transferred_issuer>.+?)\s*"
    r"\((?P<transferred_uid>CHE-\d{3}\.\d{3}\.\d{3})\)"
    r"(?: mit Sitz in |,\s*in )(?P<transferred_place>.+?)(?:,\s*im Wert| im Wert) "
    r"von insgesamt CHF (?P<transferred_value>[\d'.]+)\.\s*Als Gegenleistung "
    r"erhält die Gesellschaft (?P<consideration_count>[\d']+) Namenaktien zu CHF "
    r"(?P<consideration_nominal>[\d'.]+) der (?P<consideration_issuer>.+?),\s*"
    r"(?:Firma neu:\s*|neu:\s*)(?P<consideration_new_name>.+?)\s*"
    r"\((?P<consideration_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*in "
    r"(?P<consideration_place>[^.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_SHARE_TRANSFER_UNSIGNED = re.compile(
    r"^L['’]associée (?P<seller>[^,.;]+) cède (?P<transferred>[\d']+) de ses "
    r"(?P<before>[\d']+) parts de CHF (?P<nominal>[\d'.]+) à "
    r"(?P<buyer>[^,.;]+),\s*de (?P<origin>[^,.;]+),\s*à "
    r"(?P<place>[^,.;]+),\s*nouvelle associée sans signature\.\s*"
    r"(?P=seller) reste titulaire de (?P<remaining>[\d']+) parts de CHF "
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATOR_WITHOUT_SIGNING_CORRECTED_OMITTED = re.compile(
    r"^L['’]inscription (?:no|n°)\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) est rectifiée en ce sens que "
    r"(?P<name>[^,.;]+) est nommé administrateur sans signature sociale "
    r"\(et non(?:\s+avec (?P<previous_signing>signature individuelle))?\s*\)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER_CASH = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*le titulaire a transféré des "
    r"actifs pour CHF (?P<assets>[\d'.]+) et des passifs envers les tiers de CHF "
    r"(?P<liabilities>[\d'.]+),\s*à (?P<recipient>.+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*à "
    r"(?P<place>[^()]+?)\s*\((?P<recipient_canton>[A-Z]{2})\)\.\s*"
    r"Contre-prestation:\s*CHF (?P<consideration>[\d']+(?:\.\d+)?)\.?$",
    re.I | re.UNICODE,
)
_DE_BANKRUPTCY_APPEAL_GRANTED_WITH_HISTORY = re.compile(
    r"^\[gestrichen:\s*Mit Mitteilung des (?P<appeal_authority>.+?) vom "
    r"(?P<suspension_date>\d{2}\.\d{2}\.\d{4}) ist dem Rekurs gegen den Entscheid "
    r"des (?P<bankruptcy_court>.+?) vom "
    r"(?P<bankruptcy_date>\d{2}\.\d{2}\.\d{4}) betreffend Konkurseröffnung "
    r"aufschiebende Wirkung zuerkannt worden\.\s*Demnach wird die Eintragung "
    r"betreffend Konkurseröffnung über die Gesellschaft im Handelsregister "
    r"gestrichen\.\]\.\s*In Gutheissung des Rekurses hat das "
    r"(?P<final_appeal_authority>.+?) "
    r"mit Entscheid vom (?P<decision_date>\d{2}\.\d{2}\.\d{4}) den Entscheid des "
    r"(?P=bankruptcy_court) vom (?P=bankruptcy_date),\s*mit dem über die Gesellschaft "
    r"der Konkurs eröffnet wurde,\s*aufgehoben\.?$",
    re.I | re.UNICODE,
)
_DE_OMITTED_PREVIOUS_DOMICILE_CORRECTED = re.compile(
    r"^Im SHAB Nr\.\s*(?P<issue>\d+) vom "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}) publizierten TR-Eintrag "
    r"(?P<entry>[\d/]+) wurde irrtümlicherweise das \[bisher:\s*in "
    r"(?P<previous_place>[^\]]+)\] weggelassen\.?$",
    re.I | re.UNICODE,
)
_FR_WRONG_COMPANY_BANKRUPTCY_CORRECTED = re.compile(
    r"^Rectification de l['’]inscription n°\s*(?P<entry>[\d']+) du "
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4}) \(FOSC du "
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*Id (?P<notice_id>\d+)\):\s*"
    r"L['’]inscription concernant l['’]ouverture de la faillite est radiée\.\s*"
    r"La faillite a en effet été prononcée à l['’]encontre de la société "
    r"(?P<intended_company>.+?)\s*\((?P<intended_uid>CHE-\d{3}\.\d{3}\.\d{3})\) "
    r"et non pas (?P<wrong_company>.+?)\.\s*Nouvelle raison sociale:\s*"
    r"(?P<new_name>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATE_APPOINTED_MANAGER_CONTINUES_SIGNING = re.compile(
    r"^L['’]associé (?P<name>[^,.;]+) a été nommé gérant et continue à signer "
    r"(?:individuellement|individuelement)\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_PROPRIETOR_ASSET_TRANSFER_SHARES_AND_CLAIM = re.compile(
    r"^Selon contrat de transfert de patrimoine du "
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4}),\s*le titulaire a transféré "
    r"certains actifs pour CHF (?P<assets>[\d'.]+) et certains passifs envers les "
    r"tiers pour CHF (?P<liabilities>[\d'.]+) à la "
    r"(?P<recipient_legal_form>société anonyme)\s+\"(?P<recipient>[^\"]+)\",\s*à "
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*(?P<share_count>[\d']+) actions nominatives de CHF "
    r"(?P<share_nominal>[\d'.]+),\s*(?:(?P<restriction>liées selon statuts),\s*|,?\s*)"
    r"entièrement libérées et une créance de "
    r"CHF (?P<claim>[\d'.]+) en faveur de l['’]apporteur\.?$",
    re.I | re.UNICODE,
)


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _money(raw: str) -> Decimal:
    return Decimal(raw.replace("'", ""))


def _unquote(raw: str) -> str:
    return raw.strip().strip('"').strip()


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


def extract_parser180_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 180."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _FR_COMPANY_ASSET_TRANSFER_NO_LIABILITIES_CASH.fullmatch(leftover)
    if match and _money(match.group("assets")) == _money(match.group("consideration")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.company_asset_transfer_no_liabilities_cash.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": "0",
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_canton": match.group("recipient_canton"),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "cash",
                "consideration_amount": match.group("consideration"),
            },
        )], ""

    match = _FR_AUTHORIZED_CAPITAL_CLAUSE_REPLACED.fullmatch(leftover)
    if match:
        rule_id = "fr.text.authorized_capital_clause_replaced_decision_wording.v1"
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "removed",
                    "decision_date": _iso_date(match.group("removed_date")),
                    "reason": "authorization_period_elapsed",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    "kind": "authorized_capital_clause", "action": "introduced",
                    "decision_date": _iso_date(match.group("introduced_date")),
                    "capital_kind": "capital-actions", "details_in_statutes": True,
                },
            ),
        ], ""

    match = _DE_OPERATIONAL_BUSINESS_TRANSFER_SHARES_AND_CREDIT.fullmatch(leftover)
    if match and (
        _money(match.group("assets")) - _money(match.group("liabilities"))
        == _count(match.group("share_count")) * _money(match.group("share_nominal"))
        + _money(match.group("claim"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.operational_business_transfer_shares_credit.v1", {
                "source_kind": "company", "scope": "operational_business",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_claim",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_claim": match.group("claim"),
            },
        )], ""

    match = _IT_DISSOLUTION_APPEAL_GRANTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "it.text.dissolution_appeal_granted_organization_restored.v1", {
                "kind": "dissolution_revoked", "action": "appeal_granted",
                "company_name": match.group("name").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "dissolution_date": _iso_date(match.group("dissolution_date")),
                "appeal_authority": match.group("appeal_authority").strip(),
                "lower_authority": match.group("lower_authority").strip(),
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "legal_organization_restored": True,
            },
        )], ""

    transfer_parts = re.split(r"(?=Vermögensübertragung:)", leftover)
    transfer_parts = [part.strip() for part in transfer_parts if part.strip()]
    if len(transfer_parts) == 2:
        transfer_matches = [
            _DE_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(part)
            for part in transfer_parts
        ]
        if all(transfer_matches):
            rule_id = "de.text.two_asset_transfers_assets_only_no_consideration.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "assets_transferred", rule_id, {
                        "source_kind": "company",
                        "agreement_date": _iso_date(match.group("agreement_date")),
                        "assets": match.group("assets"), "currency": "CHF",
                        "recipient": match.group("recipient").strip(),
                        "recipient_place": match.group("place").strip(),
                        "recipient_uid": match.group("uid"),
                        "consideration_kind": "none", "gratuitous": True,
                    },
                )
                for match in transfer_matches
                if match is not None
            ], ""

    match = _DE_OUTGOING_SPIN_OFF_UID_BEFORE_PLACE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.outgoing_spin_off_uid_before_place.v1", {
                "kind": "spin_off_distribution",
                "date": _iso_date(match.group("date")), "document": "spaltungsplan",
                "scope": "part_of_assets_and_liabilities",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_newly_founded": bool(match.group("newly_founded")),
            },
        )], ""

    match = _DE_JOINT_ASSET_TRANSFER_SHARES_EXCHANGE.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.joint_asset_transfer_shares_exchange.v1", {
                "source_kind": "company", "ownership_kind": "joint_ownership",
                "co_transferors": [
                    {
                        "name": _unquote(match.group("co_transferor1")),
                        "uid": match.group("co_uid1"),
                        "place": match.group("co_place1").strip(),
                    },
                    {
                        "name": _unquote(match.group("co_transferor2")),
                        "uid": match.group("co_uid2"),
                        "place": match.group("co_place2").strip(),
                    },
                ],
                "agreement_date": _iso_date(match.group("agreement_date")),
                "transferred_asset_kind": "registered_shares",
                "transferred_shares_count": _count(match.group("transferred_count")),
                "transferred_share_nominal": match.group("transferred_nominal"),
                "transferred_issuer": _unquote(match.group("transferred_issuer")),
                "transferred_issuer_uid": match.group("transferred_uid"),
                "transferred_issuer_place": match.group("transferred_place").strip(),
                "transferred_value": match.group("transferred_value"),
                "currency": "CHF", "consideration_kind": "registered_shares",
                "consideration_shares_count": _count(match.group("consideration_count")),
                "consideration_share_nominal": match.group("consideration_nominal"),
                "consideration_issuer": _unquote(match.group("consideration_issuer")),
                "consideration_issuer_new_name": _unquote(
                    match.group("consideration_new_name")
                ),
                "consideration_issuer_uid": match.group("consideration_uid"),
                "consideration_issuer_place": match.group("consideration_place").strip(),
            },
        )], ""

    match = _FR_ASSOCIATE_SHARE_TRANSFER_UNSIGNED.fullmatch(leftover)
    if match and (
        match.group("nominal") == match.group("remaining_nominal")
        and _count(match.group("before"))
        == _count(match.group("transferred")) + _count(match.group("remaining"))
    ):
        rule_id = "fr.persons.associate_share_transfer_unsigned.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "origin": match.group("origin").strip(),
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("transferred")),
                    "new_associate": True, "without_signature": True,
                },
            ),
        ], ""

    match = _FR_ADMINISTRATOR_WITHOUT_SIGNING_CORRECTED_OMITTED.fullmatch(leftover)
    if match:
        previous_signing = match.group("previous_signing")
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.administrator_without_signing_corrected.v1",
            match.group("name"), role="administrateur", extra={
                "action": "appointment_corrected", "without_signature": True,
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                **(
                    {"previous_signing": "Einzelunterschrift"}
                    if previous_signing
                    else {"previous_value_omitted_in_source": True}
                ),
            },
        )], ""

    transfer_parts = re.split(r"(?=Transfert de patrimoine:)", leftover)
    transfer_parts = [part.strip() for part in transfer_parts if part.strip()]
    if len(transfer_parts) == 2:
        transfer_matches = [
            _FR_SOLE_PROPRIETOR_ASSET_TRANSFER_CASH.fullmatch(part)
            for part in transfer_parts
        ]
        if all(transfer_matches):
            rule_id = "fr.text.two_sole_proprietor_asset_transfers_cash.v1"
            return [
                _event(
                    publication_id, published_at, org_uid, plz, canton,
                    "assets_transferred", rule_id, {
                        "source_kind": "sole_proprietor",
                        "agreement_date": _iso_date(match.group("agreement_date")),
                        "assets": match.group("assets"),
                        "liabilities": match.group("liabilities"),
                        "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                        "recipient": match.group("recipient").strip(),
                        "recipient_place": match.group("place").strip(),
                        "recipient_canton": match.group("recipient_canton"),
                        "recipient_uid": match.group("uid"),
                        "consideration_kind": "cash",
                        "consideration_amount": match.group("consideration"),
                    },
                )
                for match in transfer_matches
                if match is not None
            ], ""

    match = _DE_BANKRUPTCY_APPEAL_GRANTED_WITH_HISTORY.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.bankruptcy_appeal_granted_with_history.v1", {
                "kind": "bankruptcy_revoked", "action": "appeal_granted",
                "appeal_authority": match.group("appeal_authority").strip(),
                "final_appeal_authority": match.group("final_appeal_authority").strip(),
                "bankruptcy_court": match.group("bankruptcy_court").strip(),
                "decision_date": _iso_date(match.group("decision_date")),
                "bankruptcy_date": _iso_date(match.group("bankruptcy_date")),
                "suspensive_effect_date": _iso_date(match.group("suspension_date")),
                "previous_status_restored": True,
            },
        )], ""

    match = _DE_OMITTED_PREVIOUS_DOMICILE_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.omitted_previous_domicile_corrected.v1", {
                "kind": "previous_domicile_omitted", "action": "supplemented",
                "issue": match.group("issue"), "entry": match.group("entry"),
                "notice_date": _iso_date(match.group("notice_date")),
                "previous_place": match.group("previous_place").strip(),
                "previously_omitted_by_error": True,
            },
        )], ""

    match = _FR_WRONG_COMPANY_BANKRUPTCY_CORRECTED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "fr.text.wrong_company_bankruptcy_corrected.v1", {
                "kind": "bankruptcy", "action": "erroneous_registration_removed",
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_id": match.group("notice_id"),
                "intended_company": match.group("intended_company").strip(),
                "intended_company_uid": match.group("intended_uid"),
                "wrongly_affected_company": match.group("wrong_company").strip(),
                "new_name": match.group("new_name").strip(),
                "bankruptcy_registration_deleted": True,
            },
        )], ""

    match = _FR_ASSOCIATE_APPOINTED_MANAGER_CONTINUES_SIGNING.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.associate_appointed_manager_continues_signing.v1",
            match.group("name"), role="associé-gérant", signing="Einzelunterschrift",
            extra={"action": "appointed_manager", "signing_continues": True},
        )], ""

    match = _FR_SOLE_PROPRIETOR_ASSET_TRANSFER_SHARES_AND_CLAIM.fullmatch(leftover)
    if match and (
        _money(match.group("assets")) - _money(match.group("liabilities"))
        == _count(match.group("share_count")) * _money(match.group("share_nominal"))
        + _money(match.group("claim"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.sole_proprietor_asset_transfer_shares_claim.v2", {
                "source_kind": "sole_proprietor",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_legal_form": match.group("recipient_legal_form").lower(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "registered_shares_and_claim",
                "consideration_shares_count": _count(match.group("share_count")),
                "consideration_share_nominal": match.group("share_nominal"),
                "consideration_shares_fully_paid": True,
                "consideration_shares_transfer_restricted": bool(
                    match.group("restriction")
                ),
                "consideration_claim": match.group("claim"),
            },
        )], ""

    return [], text
