from __future__ import annotations

from decimal import Decimal
import re

from .keys import person_key
from .models import Event


_FR_REGISTERED_SHARE_RESTRICTION = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+sont désormais restreintes quant à la "
    r"transmissibilité selon statuts\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_PAID_SHARES = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<total>[\d'.]+),\s*Liberierung:\s*(?P<paid_currency>[A-Z]{3})\s+"
    r"(?P<paid>[\d'.]+),\s*(?P<count>[\d']+)\s+Aktien zu\s+"
    r"(?P<nominal_currency>[A-Z]{3})\s+(?P<nominal>[\d'.]+)\s*"
    r"\[bisher:\s*(?P<previous_currency>[A-Z]{3})\s+"
    r"(?P<previous_total>[\d'.]+),\s*Liberierung:\s*"
    r"(?P<previous_paid_currency>[A-Z]{3})\s+(?P<previous_paid>[\d'.]+),\s*"
    r"(?P<previous_count>[\d']+)\s+Aktien zu\s+"
    r"(?P<previous_nominal_currency>[A-Z]{3})\s+"
    r"(?P<previous_nominal>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ORGANIZATIONS_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>.+?)\s*\((?P<seller_registry>[^)]+)\)\s+a cédé\s+"
    r"(?P<transferred>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Par conséquent,\s*(?P=buyer)\s*\((?P=buyer_uid)\)\s+et\s+"
    r"(?P=seller)\s*\((?P=seller_registry)\)\s+sont maintenant associées pour,\s*"
    r"respectivement,\s*(?P<buyer_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<buyer_nominal>[\d'.]+)\s+et\s+(?P<seller_count>[\d']+)\s+"
    r"parts de CHF\s+(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_REGISTER_CANTON_RESIDUE = re.compile(
    r"^\(HRA\s+(?P<register_canton>[A-Z]{2})\)\.?$",
    re.I | re.UNICODE,
)
_FR_EXISTING_MANAGER_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+"
    r"l['’]associé-gérant\s+(?P<buyer>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+a maintenant\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ASSOCIATES_SHARE_TRANSFER_AND_DOMICILES = re.compile(
    r"^(?P<seller>[^,.;]+),\s*maintenant à\s+(?P<seller_place>[^,.;]+),\s*"
    r"cède\s+(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+"
    r"parts de CHF\s+(?P<nominal>[\d'.]+)\s+à\s+(?P<buyer>[^,.;]+),\s*"
    r"maintenant à\s+(?P<buyer_place>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+)\.\s*"
    r"(?P=seller)\s+reste titulaire de\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_COMPANY_ASSET_TRANSFER_NO_CONSIDERATION = re.compile(
    r"^Transfert de patrimoine:\s*selon contrat du\s+"
    r"(?P<date>\d{1,2}(?:er)?\s+[A-Za-zÀ-ÿ]+\s+\d{4}),\s*"
    r"la société a transféré des actifs pour CHF\s+(?P<assets>[\d'.]+)\s+"
    r"et des passifs envers les tiers pour CHF\s+(?P<liabilities>[\d'.]+),\s*"
    r"à\s+(?P<recipient>.+?)\s+à\s+(?P<place>[^()]+?)\s*"
    r"\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Contre-prestation:\s*aucune\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_PRESIDENT_AND_MEMBER = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*nommé président,\s*"
    r"lequel continue à signer individuellement et\s+(?P<member>[^,.;]+),\s*"
    r"d['’](?P<origin>[^,.;]+),\s*à\s+(?P<place>[^,.;]+),\s*"
    r"avec signature collective à deux\.?$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_AUSTRIA_DEFICIT = re.compile(
    r"^Grenzüberschreitende Fusion gemäss\s+(?P<legal_basis>IPRG):\s*"
    r"Übernahme der Aktiven und Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_country>[A-Z]{2})\),\s*"
    r"(?P<absorbed_legal_form>Aktiengesellschaft) nach dem Recht von\s+"
    r"(?P<jurisdiction>[^()]+?)\s*\((?P<registry_id>FN\s+[^)]+)\),\s*"
    r"gemäss Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+"
    r"und Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*"
    r"Aktiven von\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und "
    r"Fremdkapital von\s+(?P<liabilities_currency>[A-Z]{3})\s+"
    r"(?P<liabilities>[\d'.]+),\s*d\.\s*h\.\s*ein Passivenüberschuss von\s+"
    r"(?P<deficit_currency>[A-Z]{3})\s+(?P<deficit>[\d'.]+),\s*gehen auf die "
    r"übernehmende Gesellschaft über\.\s*Gemäss Bestätigung des staatlich "
    r"beaufsichtigten Revisionsunternehmens verfügt die übernehmende Gesellschaft "
    r"über frei verwendbares Eigenkapital im Umfang des Kapitalverlustes und der "
    r"Überschuldung der übertragenden Gesellschaft\.\s*Da die übernehmende "
    r"Gesellschaft sämtliche Aktien der übertragenden Gesellschaft hält,\s*findet "
    r"weder eine Kapitalerhöhung noch eine Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_STATUTES_DATE_CORRECTED_COLON = re.compile(
    r"^Das Statutendatum lautet richtig:\s*(?P<date>\d{2}\.\d{2}\.\d{4}),\s*"
    r"nicht:\s*(?P<previous_date>\d{2}\.\d{2}\.\d{4})\.?$",
    re.I | re.UNICODE,
)
_DE_BRANCH_ADDED_BARE_UID = re.compile(
    r"^Zweigniederlassung neu:\s*(?P<place>[^()]+?)\s*"
    r"\((?P<identifier>\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_FR_PREVIOUS_SEAT_SUPPLEMENT = re.compile(
    r"^Complément:\s*l['’]inscription (?:n°|no)\s*(?P<entry>[\d']+) du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est complétée en ce sens que la société "
    r"était précédemment à\s+(?P<previous_seat>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_INVENTORY_LIABILITIES_CASH = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Inventar per\s+"
    r"(?P<inventory_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven von CHF\s+(?P<liabilities>[\d'.]+)\s+"
    r"\(Fremdkapital\)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_ORIGIN_CHANGED_RESIDUE = re.compile(
    r"^elle est désormais (?:originaire )?(?:du|de la|de l['’]|des|de|d['’])\s*"
    r"(?P<origin>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CIVIL_NAME_AND_ORIGIN_SEMICOLON = re.compile(
    r"^L['’](?P<role>associée-gérante)\s+(?P<previous_name>[^,.;]+)\s+"
    r"se nomme maintenant\s+(?P<name>[^,.;]+);\s*elle est désormais\s+"
    r"(?:originaire )?(?:du|de la|de l['’]|des|de|d['’])\s*"
    r"(?P<origin>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ERRONEOUS_BANKRUPTCY_ENTRY_CONTINUED = re.compile(
    r"^Die Konkurseröffnung vom\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+wurde "
    r"irrtümlich eingetragen\s*\((?P<reason>Verwechslung Firma)\)\.\s*"
    r"Die Gesellschaft besteht gemäss den bisherigen Eintragungen weiter\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_GENERAL_APPOINTED_BOARD_DELEGATE = re.compile(
    r"^(?P<name>[^,.;]+),\s*jusqu['’]ici\s+(?P<previous_role>directeur général),\s*"
    r"nommé\s+(?P<role>membre et délégué du conseil d['’]administration),\s*"
    r"signe désormais collectivement à deux sans autre restriction\.?$",
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


def extract_parser193_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
    prior_events: list[Event] | None = None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 193."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()
    prior_events = prior_events or []

    match = _FR_REGISTERED_SHARE_RESTRICTION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.registered_share_restriction_statutes.v1", {
                "kind": "share_transfer_restriction", "action": "introduced",
                "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "share_nominal": match.group("nominal"), "currency": "CHF",
                "details_in_statutes": True,
            },
        )], ""

    match = _DE_HEAD_OFFICE_CAPITAL_PAID_SHARES.fullmatch(leftover)
    if match:
        currencies = {
            match.group(group).upper() for group in (
                "currency", "paid_currency", "nominal_currency",
                "previous_currency", "previous_paid_currency",
                "previous_nominal_currency",
            )
        }
        if (
            len(currencies) == 1
            and _amount(match.group("total"))
            == _count(match.group("count")) * _amount(match.group("nominal"))
            and _amount(match.group("previous_total"))
            == _count(match.group("previous_count"))
            * _amount(match.group("previous_nominal"))
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", "de.text.head_office_capital_paid_shares_history.v1", {
                    "kind": "head_office_share_capital", "action": "changed",
                    "scope": "head_office", "currency": currencies.pop(),
                    "from_total": match.group("previous_total"),
                    "to_total": match.group("total"),
                    "from_paid": match.group("previous_paid"),
                    "to_paid": match.group("paid"),
                    "from_shares_count": _count(match.group("previous_count")),
                    "to_shares_count": _count(match.group("count")),
                    "from_share_nominal": match.group("previous_nominal"),
                    "to_share_nominal": match.group("nominal"),
                },
            )], ""

    match = _FR_ORGANIZATIONS_SHARE_TRANSFER.fullmatch(leftover)
    if match and len({
        match.group("nominal"), match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1:
        rule_id = "fr.persons.organizations_share_transfer_reallocation.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "foreign_registry_id": match.group("seller_registry").strip(),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("seller_count")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, uid=match.group("buyer_uid"),
                role="associée", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                },
            ),
        ], ""

    match = _DE_BRANCH_REGISTER_CANTON_RESIDUE.fullmatch(leftover)
    if match:
        previous_branch = next(
            (event for event in reversed(prior_events)
             if event.event_type == "branch_changed"),
            None,
        )
        payload = {
            "action": "registry_recorded",
            "register_canton": match.group("register_canton").upper(),
        }
        if previous_branch:
            for key in ("place", "branch_uid"):
                if previous_branch.payload.get(key):
                    payload[key] = previous_branch.payload[key]
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_register_canton_residue.v1", payload,
        )], ""

    match = _FR_EXISTING_MANAGER_SHARE_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
        and _count(match.group("buyer_count")) >= _count(match.group("transferred"))
    ):
        rule_id = "fr.persons.existing_manager_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associé", extra={
                    **common, "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé-gérant", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_before": buyer_count - transferred,
                    "shares_received": transferred, "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _FR_ASSOCIATES_SHARE_TRANSFER_AND_DOMICILES.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and len({
            match.group("nominal"), match.group("buyer_nominal"),
            match.group("remaining_nominal"),
        }) == 1
        and _count(match.group("buyer_count")) >= _count(match.group("transferred"))
    ):
        rule_id = "fr.persons.associates_share_transfer_and_domiciles.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        transferred = _count(match.group("transferred"))
        buyer_count = _count(match.group("buyer_count"))
        common = {"share_nominal": match.group("nominal"), "currency": "CHF"}
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé", extra={
                    **common, "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer, "shares_before": _count(match.group("before")),
                    "shares_transferred": transferred,
                    "shares_count": _count(match.group("remaining")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("buyer_place"),
                role="associé", extra={
                    **common, "action": "domicile_changed_and_shares_received",
                    "counterparty": seller, "shares_before": buyer_count - transferred,
                    "shares_received": transferred, "shares_count": buyer_count,
                },
            ),
        ], ""

    match = _FR_COMPANY_ASSET_TRANSFER_NO_CONSIDERATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "fr.text.company_asset_transfer_no_consideration.v1", {
                "source_kind": "company",
                "agreement_date": _french_date(match.group("date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration_kind": "none", "gratuitous": True,
            },
        )], ""

    match = _FR_ADMINISTRATION_PRESIDENT_AND_MEMBER.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_president_and_member_mixed_signing.v1"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing="Einzelunterschrift", extra={
                    "action": "appointed_president", "signing_continues": True,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("member"),
                place=match.group("place"), role="administrateur",
                signing="Kollektivunterschrift zu zweien", extra={
                    "action": "appointed", "origin": match.group("origin").strip(),
                },
            ),
        ], ""

    match = _DE_CROSS_BORDER_MERGER_AUSTRIA_DEFICIT.fullmatch(leftover)
    if match:
        currencies = {
            match.group("currency").upper(),
            match.group("liabilities_currency").upper(),
            match.group("deficit_currency").upper(),
        }
        if (
            len(currencies) == 1
            and _amount(match.group("liabilities")) - _amount(match.group("assets"))
            == _amount(match.group("deficit"))
        ):
            return [_event(
                publication_id, published_at, org_uid, plz, canton,
                "company_merged", "de.text.cross_border_merger_austria_deficit.v1", {
                    "kind": "cross_border_merger",
                    "legal_basis": match.group("legal_basis").upper(),
                    "absorbed_name": match.group("absorbed_name").strip(),
                    "absorbed_place": match.group("absorbed_place").strip(),
                    "absorbed_country": match.group("absorbed_country").upper(),
                    "absorbed_legal_form": match.group("absorbed_legal_form"),
                    "absorbed_jurisdiction": match.group("jurisdiction").strip(),
                    "absorbed_registry_id": match.group("registry_id").strip(),
                    "agreement_date": _iso_date(match.group("agreement_date")),
                    "balance_date": _iso_date(match.group("balance_date")),
                    "currency": currencies.pop(), "assets": match.group("assets"),
                    "liabilities": match.group("liabilities"),
                    "liabilities_kind": "third_party_capital",
                    "deficit": match.group("deficit"),
                    "freely_available_equity_covers_deficit": True,
                    "auditor_confirmation": True, "same_shareholder": True,
                    "capital_increase": False, "share_allocation": False,
                },
            )], ""

    match = _DE_STATUTES_DATE_CORRECTED_COLON.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "de.text.statutes_date_corrected_colon.v1", {
                "kind": "statutes_date", "action": "corrected",
                "date": _iso_date(match.group("date")),
                "previous_date": _iso_date(match.group("previous_date")),
            },
        )], ""

    match = _DE_BRANCH_ADDED_BARE_UID.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_added_bare_uid.v1", {
                "action": "added", "place": match.group("place").strip(),
                "branch_uid": f"CHE-{match.group('identifier')}",
                "source_identifier": match.group("identifier"),
            },
        )], ""

    match = _FR_PREVIOUS_SEAT_SUPPLEMENT.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "seat_changed", "fr.text.previous_seat_supplement.v1", {
                "kind": "previous_registered_seat", "action": "entry_supplemented",
                "previous_seat": match.group("previous_seat").strip(),
                "historical": True, "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        )], ""

    match = _DE_ASSET_TRANSFER_INVENTORY_LIABILITIES_CASH.fullmatch(leftover)
    if match and (
        _amount(match.group("assets")) - _amount(match.group("liabilities"))
        == _amount(match.group("consideration"))
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_inventory_liabilities_cash.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "inventory_date": _iso_date(match.group("inventory_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_capital", "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "recipient_place": match.group("place").strip(),
                "recipient_uid": match.group("uid"),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash",
            },
        )], ""

    match = _FR_CIVIL_NAME_AND_ORIGIN_SEMICOLON.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.civil_name_and_origin_semicolon.v1",
            match.group("name"), role=match.group("role").lower(), extra={
                "action": "name_and_origin_changed",
                "previous_name": match.group("previous_name").strip(),
                "origin": match.group("origin").strip(),
            },
        )], ""

    match = _FR_ORIGIN_CHANGED_RESIDUE.fullmatch(leftover)
    if match:
        previous_person = next(
            (event for event in reversed(prior_events)
             if event.person_key and event.payload.get("name")),
            None,
        )
        if previous_person:
            name = previous_person.payload["name"]
            return [Event(
                publication_id=publication_id,
                published_at=published_at,
                event_type="officer_changed",
                rule_id="fr.persons.origin_changed_residue.v1",
                org_uid=org_uid,
                person_key=previous_person.person_key,
                plz=plz,
                canton=canton,
                role=previous_person.role,
                payload={
                    "name": name, "action": "origin_changed",
                    "origin": match.group("origin").strip(),
                    "subject_reference": "previously_named_officer",
                },
            )], ""

    match = _DE_ERRONEOUS_BANKRUPTCY_ENTRY_CONTINUED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.erroneous_bankruptcy_entry_continued.v1", {
                "kind": "bankruptcy_entry_reversed", "action": "corrected",
                "bankruptcy_date": _iso_date(match.group("date")),
                "reason": "company_confusion", "previous_status_restored": True,
                "company_continues": True,
            },
        )], ""

    match = _FR_DIRECTOR_GENERAL_APPOINTED_BOARD_DELEGATE.fullmatch(leftover)
    if match:
        return [_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_general_appointed_board_delegate.v1",
            match.group("name"), role=match.group("role").lower(),
            signing="Kollektivunterschrift zu zweien", extra={
                "action": "appointed_board_member_and_delegate",
                "previous_role": match.group("previous_role").lower(),
                "signing_restriction_removed": True,
            },
        )], ""

    return [], text
