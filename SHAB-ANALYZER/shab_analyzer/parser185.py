from __future__ import annotations

import re
from decimal import Decimal

from .keys import person_key
from .models import Event


_IT_CORPORATE_ASSET_TRANSFER_RENAMED = re.compile(
    r"^Trasferimento di patrimonio:\s*secondo contratto del\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+la società ha trasferito alla\s+"
    r"(?P<previous_recipient>.+?)\s*\(nuova:\s*(?P<recipient>.+?)\)\s*,\s*"
    r"in\s+(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"attivi per CHF\s+(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*Contro prestazione:\s*"
    r"(?P<consideration>nessuna)\.?$",
    re.I | re.UNICODE,
)
_DE_HEAD_OFFICE_CAPITAL_WITH_SHARES = re.compile(
    r"^Kapital Hauptsitz neu:\s*(?P<currency>[A-Z]{3})\s+"
    r"(?P<to_capital>[\d'.]+),\s*(?P<to_count>[\d']+)\s+Anteile zu\s+"
    r"(?P=currency)\s+(?P<to_nominal>[\d'.]+)\s*"
    r"\[bisher:\s*Kapital Hauptsitz:\s*(?P<from_currency>[A-Z]{3})\s+"
    r"(?P<from_capital>[\d'.]+),\s*Liberierung\s+(?P<paid_currency>[A-Z]{3})\s+"
    r"(?P<from_paid>[\d'.]+),\s*(?P<from_count>[\d']+)\s+Anteile zu\s+"
    r"(?P<nominal_currency>[A-Z]{3})\s+(?P<from_nominal>[\d'.]+)\]\.?$",
    re.I | re.UNICODE,
)
_FR_ADMINISTRATION_THREE_COLLECTIVE = re.compile(
    r"^Administration:\s*(?P<president>[^,.;]+),\s*président,\s*"
    r"(?P<member1>[^,.;]+)\s+et\s+(?P<member2>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*lesquels signent collectivement à deux\.?$",
    re.I | re.UNICODE,
)
_DE_CROSS_BORDER_MERGER_US_LLC = re.compile(
    r"^Grenzüberschreitende Fusion gemäss\s+(?P<legal_basis>Art\.\s*163a IPRG):\s*"
    r"Übernahme der Aktiven und Passiven der\s+(?P<absorbed_name>.+?),\s*in\s+"
    r"(?P<absorbed_place>[^()]+?)\s*\((?P<absorbed_country>[A-Z]{2})\),\s*"
    r"einer\s+(?P<absorbed_legal_form>Limited Liability Company)\s+nach dem Recht "
    r"des\s+(?P<jurisdiction>US-Bundesstaates [^,.;]+),\s*gemäss Fusionsvertrag "
    r"vom\s+(?P<agreement_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+und "
    r"Bilanz per\s+(?P<balance_date>\d{1,2}\.\s+[A-Za-zÄÖÜäöü]+\s+\d{4})\s+"
    r"Aktiven von\s+(?P<currency>[A-Z]{3})\s+(?P<assets>[\d'.]+)\s+und "
    r"Fremdkapital von\s+(?P=currency)\s+(?P<liabilities>[\d'.]+)\s+gehen auf "
    r"die übernehmende Gesellschaft über\.\s*Da dieselbe Gesellschafterin "
    r"sämtliche Stammanteile/Mitgliedschaftsanteile der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine Zuteilung "
    r"von Stammanteilen statt\.?$",
    re.I | re.UNICODE,
)
_FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT = re.compile(
    r"^Jusqu['’]ici titulaire de\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+),\s*l['’]associée-gérante\s+(?P<seller>[^,.;]+)\s+"
    r"détient\s+(?P<remaining>[\d']+)\s+parts de CHF\s+"
    r"(?P<remaining_nominal>[\d'.]+)\s+par suite de cession de\s+"
    r"(?P<transferred>[\d']+)\s+parts à\s+(?P<buyer>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])\s*(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+),\s*(?P<country>[A-Z]{2,3}),\s*nouvelle associée pour\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+),\s*"
    r"nommée gérante et présidente(?P<signing>\s+avec signature collective à deux)?\.?$",
    re.I | re.UNICODE,
)
_FR_MASS_SHARE_TRANSFER = re.compile(
    r"^(?P<seller>[^,.;]+)\s+cède\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts de CHF\s+(?P<nominal>[\d'.]+),\s*"
    r"(?P<allocations>par\s+.+?)\.\s*(?P=seller)\s+reste titulaire de\s+"
    r"(?P<remaining>[\d']+)\s+parts de CHF\s+(?P<remaining_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_FR_MASS_SHARE_ALLOCATION = re.compile(
    r"(?:^|,\s*(?:et\s+)?)par\s+(?P<count>[\d']+)\s+parts? de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à\s+(?P<details>.+?)"
    r"(?=,\s*(?:et\s+)?par\s+[\d']+\s+parts? de CHF|$)",
    re.I | re.UNICODE,
)
_DE_DOMESTIC_MERGER_SAME_SHAREHOLDER = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven der\s+"
    r"(?P<absorbed_name>.+?),\s*in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{2,3}\.\d{3}\.\d{3})\),\s*gemäss "
    r"Fusionsvertrag vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und "
    r"Bilanz per\s+(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s*von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da derselbe Aktionär sämtliche Aktien der an der Fusion beteiligten "
    r"Gesellschaften hält,\s*findet weder eine Kapitalerhöhung noch eine "
    r"Aktienzuteilung statt\.?$",
    re.I | re.UNICODE,
)
_DE_DISSOLUTION_DEED_REPLACED = re.compile(
    r"^Die hiermit in die Belegliste aufgenommene Öffentliche Urkunde vom\s+"
    r"(?P<document_date>\d{2}\.\d{2}\.\d{4})\s+über die Auflösung der\s+"
    r"(?P<company>.+?)\s+ersetzt diejenige Öffentliche Urkunde vom\s+"
    r"(?P<previous_document_date>\d{2}\.\d{2}\.\d{4})\s+über die Auflösung der\s+"
    r"(?P<previous_company>.+?)\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_RENAMED = re.compile(
    r"^Nouvelle raison sociale de l['’]associée\s+(?P<previous_name>.+?):\s*"
    r"(?P<name>.+?)\.?$",
    re.I | re.UNICODE,
)
_IT_MERGER_SAME_SHAREHOLDER_SUBORDINATION = re.compile(
    r"^Fusione:\s*ripresa di attivi e passivi di\s+(?P<absorbed_name>.+?),\s*"
    r"in\s+(?P<absorbed_place>[^()]+?)\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*secondo il contratto "
    r"di fusione del\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+e bilancio al\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4}),\s*che presenta attivi per CHF\s+"
    r"(?P<assets>[\d'.]+)\s+e passivi verso terzi per CHF\s+"
    r"(?P<liabilities>[\d'.]+)\.\s*La totalità del capitale azionario delle due "
    r"società è detenuta dallo stesso azionista,\s*la fusione avviene dunque senza "
    r"aumento di capitale e senza attribuzione di azioni\.\s*Conformemente "
    r"all['’]attestazione di un perito revisore abilitato,\s*dei crediti per un "
    r"ammontare almeno equivalente allo scoperto rispettivamente al "
    r"sovraindebitamento sono stati postergati\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_ASSETS_ONLY_AMOUNTED = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.\s*"
    r"Die Gegenleistung beträgt CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_BARE_BRANCH_REMOVED = re.compile(
    r"^\[gestrichen:\s*(?P<place>[^()\]]+?)\s*\(HR\s+"
    r"(?P<register_canton>[A-Z]{2})\)\s*"
    r"\((?P<uid>CHE-\d{3}[.-]\d{3}[.-]\d{3})\)\]\.?$",
    re.I | re.UNICODE,
)
_FR_EXISTING_ASSOCIATE_SHARE_TRANSFER = re.compile(
    r"^L['’]associé\s+(?P<seller>[^,.;]+),\s*maintenant domicilié à\s+"
    r"(?P<seller_place>[^,.;]+),\s*a cédé\s+(?P<transferred>[\d']+)\s+de ses\s+"
    r"(?P<before>[\d']+)\s+parts sociales de CHF\s+(?P<nominal>[\d'.]+)\s+à "
    r"l['’]associé\s+(?P<buyer>[^,.;]+)\.\s*Ils sont désormais chacun titulaires "
    r"de\s+(?P<each_count>[\d']+)\s+parts sociales de CHF\s+"
    r"(?P<each_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_ASSET_TRANSFER_MISSING_UID_PAREN = re.compile(
    r"^Vermögensübertragung:\s*Die Gesellschaft überträgt gemäss Vertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+auf die\s+(?P<recipient>.+?),\s*in\s+"
    r"(?P<place>[^()]+?)\s*\((?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\.\s*"
    r"Gegenleistung:\s*CHF\s+(?P<consideration>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)
_DE_FAILED_CONTRIBUTION_IN_KIND = re.compile(
    r"^Infolge Unmöglichkeit konnte das\s+(?P<asset>.+?)\s+im Wert und zum Preis "
    r"von CHF\s+(?P<value>[\d'.]+)\s+gemäss Sacheinlage-/Sachübernahmevertrag "
    r"vom\s+(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+nicht übertragen werden\.\s*"
    r"Das Kapital wurde nicht vollständig liberiert\.?$",
    re.I | re.UNICODE,
)
_FR_SHARE_TRANSFER_RESTRICTION_INTRODUCED = re.compile(
    r"^Les\s+(?P<count>[\d']+)\s+actions nominatives de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+sont désormais restreintes quant à la "
    r"transmissibilité\.?$",
    re.I | re.UNICODE,
)


_GERMAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
}


def _iso_date(raw: str) -> str:
    day, month, year = raw.split(".")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _german_date(raw: str) -> str:
    day, month, year = raw.replace(".", "", 1).casefold().split()
    return f"{int(year):04d}-{_GERMAN_MONTHS[month]:02d}-{int(day):02d}"


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


def _mass_share_transfer_events(
    match: re.Match[str],
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> list[Event] | None:
    allocations_raw = match.group("allocations")
    allocations = list(_FR_MASS_SHARE_ALLOCATION.finditer(allocations_raw))
    if not allocations or allocations[0].start() != 0 or allocations[-1].end() != len(allocations_raw):
        return None
    if any(left.end() != right.start() for left, right in zip(allocations, allocations[1:])):
        return None
    nominal = match.group("nominal")
    transferred = _count(match.group("transferred"))
    before = _count(match.group("before"))
    remaining = _count(match.group("remaining"))
    if (
        any(item.group("nominal") != nominal for item in allocations)
        or match.group("remaining_nominal") != nominal
        or sum(_count(item.group("count")) for item in allocations) != transferred
        or before - transferred != remaining
    ):
        return None

    rule_id = "fr.persons.mass_share_transfer.v1"
    seller = match.group("seller").strip()
    events = [_person_event(
        publication_id, published_at, org_uid, plz, canton,
        "officer_changed", rule_id, seller, role="associé", extra={
            "action": "shares_transferred",
            "shares_before": before,
            "shares_transferred": transferred,
            "shares_count": remaining,
            "share_nominal": nominal,
            "currency": "CHF",
            "recipient_count": len(allocations),
        },
    )]
    for item in allocations:
        details = item.group("details").strip()
        recipient = details.split(",", 1)[0].strip()
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", rule_id, recipient, role="associé", extra={
                "action": "shares_received",
                "counterparty": seller,
                "shares_received": _count(item.group("count")),
                "share_nominal": item.group("nominal"),
                "currency": "CHF",
                "recipient_details": details,
            },
        ))
    return events


def extract_parser185_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 185."""
    del language  # Historical publications can contain another language.
    leftover = text.strip()

    match = _IT_CORPORATE_ASSET_TRANSFER_RENAMED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "it.text.corporate_asset_transfer_renamed_no_consideration.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities",
                "currency": "CHF",
                "recipient": match.group("recipient").strip(),
                "previous_recipient": match.group("previous_recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration_kind": "none",
                "gratuitous": True,
            },
        )], ""

    match = _DE_HEAD_OFFICE_CAPITAL_WITH_SHARES.fullmatch(leftover)
    if match and len({
        match.group("currency"), match.group("from_currency"),
        match.group("paid_currency"), match.group("nominal_currency"),
    }) == 1:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "capital_changed", "de.text.head_office_capital_with_shares.v1", {
                "scope": "head_office",
                "currency": match.group("currency").upper(),
                "from_nominal": match.group("from_capital"),
                "to_nominal": match.group("to_capital"),
                "from_paid": match.group("from_paid"),
                "from_shares_count": _count(match.group("from_count")),
                "to_shares_count": _count(match.group("to_count")),
                "from_share_nominal": match.group("from_nominal"),
                "to_share_nominal": match.group("to_nominal"),
            },
        )], ""

    match = _FR_ADMINISTRATION_THREE_COLLECTIVE.fullmatch(leftover)
    if match:
        rule_id = "fr.persons.administration_three_collective.v1"
        signing = "Kollektivunterschrift zu zweien"
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, match.group("president"),
                role="président", signing=signing, extra={"action": "appointed"},
            ),
            *[
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, match.group(group),
                    place=match.group("place"), role="administrateur",
                    signing=signing, extra={
                        "action": "appointed", "origin": match.group("origin").strip(),
                    },
                )
                for group in ("member1", "member2")
            ],
        ], ""

    match = _DE_CROSS_BORDER_MERGER_US_LLC.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.cross_border_merger_us_llc.v1", {
                "kind": "cross_border_merger",
                "legal_basis": re.sub(r"\s+", " ", match.group("legal_basis")),
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_country": match.group("absorbed_country"),
                "absorbed_legal_form": match.group("absorbed_legal_form"),
                "absorbed_jurisdiction": match.group("jurisdiction").strip(),
                "agreement_date": _german_date(match.group("agreement_date")),
                "balance_date": _german_date(match.group("balance_date")),
                "currency": match.group("currency").upper(),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "same_shareholder": True,
                "capital_increase": False,
                "share_allocation": False,
            },
        )], ""

    match = _FR_MANAGER_TRANSFER_TO_NEW_MANAGER_PRESIDENT.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("remaining"))
        and _count(match.group("transferred")) == _count(match.group("buyer_count"))
        and len({
            match.group("nominal"), match.group("remaining_nominal"),
            match.group("buyer_nominal"),
        }) == 1
    ):
        rule_id = "fr.persons.manager_transfer_to_new_manager_president.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, role="associée-gérante", extra={
                    "action": "shares_transferred", "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                    "shares_count": _count(match.group("remaining")),
                    "share_nominal": match.group("nominal"), "currency": "CHF",
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, place=match.group("place"),
                role="associée-gérante présidente",
                signing=(
                    "Kollektivunterschrift zu zweien"
                    if match.group("signing") else None
                ), extra={
                    "action": "appointed_and_shares_received", "counterparty": seller,
                    "origin": match.group("origin").strip(),
                    "country": match.group("country"), "new_associate": True,
                    "shares_received": _count(match.group("transferred")),
                    "shares_count": _count(match.group("buyer_count")),
                    "share_nominal": match.group("buyer_nominal"), "currency": "CHF",
                },
            ),
        ], ""

    match = _FR_MASS_SHARE_TRANSFER.fullmatch(leftover)
    if match:
        events = _mass_share_transfer_events(
            match, publication_id, published_at, org_uid, plz, canton,
        )
        if events:
            return events, ""

    match = _DE_DOMESTIC_MERGER_SAME_SHAREHOLDER.fullmatch(leftover)
    if match:
        absorbed_uid = match.group("absorbed_uid")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.domestic_merger_same_shareholder_malformed_uid.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": absorbed_uid,
                "absorbed_uid_valid": bool(re.fullmatch(r"CHE-\d{3}\.\d{3}\.\d{3}", absorbed_uid)),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "borrowed_capital", "currency": "CHF",
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False,
            },
        )], ""

    match = _DE_DISSOLUTION_DEED_REPLACED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "publication_corrected", "de.text.dissolution_deed_replaced.v1", {
                "action": "supporting_document_replaced",
                "document": "public_dissolution_deed",
                "document_date": _iso_date(match.group("document_date")),
                "company": match.group("company").strip(),
                "previous_document_date": _iso_date(match.group("previous_document_date")),
                "previous_company": match.group("previous_company").strip(),
                "filed_in_document_list": True,
            },
        )], ""

    match = _FR_CORPORATE_ASSOCIATE_RENAMED.fullmatch(leftover)
    if match and not re.search(
        r"\bCHE-\d{3}\.\d{3}\.\d{3}\b|\bet nouveau siège\s*:",
        match.group("name"),
        re.I | re.UNICODE,
    ):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.corporate_associate_renamed.v1", {
                "kind": "corporate_associate", "action": "name_changed",
                "previous_name": match.group("previous_name").strip(),
                "name": match.group("name").strip(),
            },
        )], ""

    match = _IT_MERGER_SAME_SHAREHOLDER_SUBORDINATION.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "it.text.merger_same_shareholder_subordination.v1", {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "liabilities_kind": "third_party_liabilities", "currency": "CHF",
                "same_shareholder": True, "capital_increase": False,
                "share_allocation": False, "claims_subordinated": True,
                "subordination_covers_deficit_or_overindebtedness": True,
                "auditor_confirmation": True,
            },
        )], ""

    match = _DE_ASSET_TRANSFER_ASSETS_ONLY_AMOUNTED.fullmatch(leftover)
    if match and _amount(match.group("assets")) == _amount(match.group("consideration")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_assets_only_amounted_cash.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "currency": "CHF",
            },
        )], ""

    match = _DE_BARE_BRANCH_REMOVED.fullmatch(leftover)
    if match:
        branch_uid = "CHE-" + match.group("uid")[4:].replace("-", ".")
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.bare_branch_removed.v1", {
                "action": "removed", "place": match.group("place").strip(),
                "register_canton": match.group("register_canton").upper(),
                "branch_uid": branch_uid,
            },
        )], ""

    match = _FR_EXISTING_ASSOCIATE_SHARE_TRANSFER.fullmatch(leftover)
    if match and (
        _count(match.group("before")) - _count(match.group("transferred"))
        == _count(match.group("each_count"))
        and match.group("nominal") == match.group("each_nominal")
    ):
        rule_id = "fr.persons.existing_associate_share_transfer.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        common = {
            "shares_count": _count(match.group("each_count")),
            "share_nominal": match.group("nominal"), "currency": "CHF",
        }
        return [
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller, place=match.group("seller_place"),
                role="associé", extra={
                    **common, "action": "domicile_changed_and_shares_transferred",
                    "counterparty": buyer,
                    "shares_before": _count(match.group("before")),
                    "shares_transferred": _count(match.group("transferred")),
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer, role="associé", extra={
                    **common, "action": "shares_received", "counterparty": seller,
                    "shares_received": _count(match.group("transferred")),
                },
            ),
        ], ""

    match = _DE_ASSET_TRANSFER_MISSING_UID_PAREN.fullmatch(leftover)
    if match and _amount(match.group("assets")) == _amount(match.group("consideration")):
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "assets_transferred", "de.text.asset_transfer_missing_uid_parenthesis.v1", {
                "source_kind": "company",
                "agreement_date": _iso_date(match.group("agreement_date")),
                "assets": match.group("assets"), "liabilities_transferred": False,
                "recipient": match.group("recipient").strip(),
                "recipient_uid": match.group("uid"),
                "recipient_place": match.group("place").strip(),
                "consideration": match.group("consideration"),
                "consideration_kind": "cash", "currency": "CHF",
                "source_format_issue": "missing_closing_parenthesis_after_recipient_uid",
            },
        )], ""

    match = _DE_FAILED_CONTRIBUTION_IN_KIND.fullmatch(leftover)
    if match:
        rule_id = "de.text.failed_contribution_in_kind_capital_not_fully_paid.v1"
        common = {
            "agreement_date": _iso_date(match.group("agreement_date")),
            "asset": match.group("asset").strip(), "value": match.group("value"),
            "price": match.group("value"), "currency": "CHF",
            "reason": "transfer_impossible",
        }
        return [
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "organization_changed", rule_id, {
                    **common, "kind": "contribution_in_kind", "action": "not_transferred",
                },
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "capital_changed", rule_id, {
                    **common, "kind": "capital_payment", "capital_fully_paid": False,
                },
            ),
        ], ""

    match = _FR_SHARE_TRANSFER_RESTRICTION_INTRODUCED.fullmatch(leftover)
    if match:
        return [_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed", "fr.text.share_transfer_restriction_introduced.v1", {
                "kind": "share_transfer_restriction", "action": "introduced",
                "shares_count": _count(match.group("count")),
                "share_kind": "actions nominatives",
                "nominal": match.group("nominal"), "currency": "CHF",
            },
        )], ""

    return [], text
