from __future__ import annotations

import re

from .keys import person_key
from .models import Event


_DE_BRANCH_PREVIOUS_PLACE_GISWIL = re.compile(
    r"^\[bisher:\s*(?P<previous_place>Giswil)\]\.?$",
    re.I | re.UNICODE,
)
_FR_AUDITOR_IDENTIFIER_CORRECTED = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"numéro IDE de l['’]organe de révision\s+(?P<name>.+?)\s+est le\s+"
    r"(?P<uid>CHE-\d{3}\.\d{3}\.\d{3})\s*\(et non pas le\s+"
    r"(?P<previous_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\.?$",
    re.I | re.UNICODE,
)
_DE_MERGER_COMMON_ASSOCIATE_DEFICIT_COVERED = re.compile(
    r"^Fusion:\s*Übernahme der Aktiven und Passiven\s*\(Fremdkapital\)\s+der\s+"
    r"[\"“](?P<absorbed_name>.+?)[\"”]\s*"
    r"\((?P<absorbed_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+mit Sitz in\s+"
    r"(?P<absorbed_place>[^,.;]+),\s*gemäss Fusionsvertrag vom\s+"
    r"(?P<agreement_date>\d{2}\.\d{2}\.\d{4})\s+und Fusionsbilanz per\s+"
    r"(?P<balance_date>\d{2}\.\d{2}\.\d{4})\.\s*Aktiven von CHF\s+"
    r"(?P<assets>[\d'.]+)\s+und Passiven\s*\(Fremdkapital\)\s+von CHF\s+"
    r"(?P<liabilities>[\d'.]+)\s+gehen auf die übernehmende Gesellschaft über\.\s*"
    r"Da dieselbe Gesellschafterin sämtliche Gesellschaftsanteile der an der "
    r"Fusion beteiligten Gesellschaften hält,\s*findet weder eine Kapitalerhöhung "
    r"noch eine Zuteilung von Gesellschaftsanteilen statt\.\s*Die übernehmende "
    r"Gesellschaft verfügt gemäss Bestätigung der zugelassenen Revisionsexpertin "
    r"vom\s+(?P<confirmation_date>\d{2}\.\d{2}\.\d{4})\s+über frei verwendbares "
    r"Eigenkapital im Umfang des Kapitalverlustes der übertragenden Gesellschaft\.?$",
    re.I | re.UNICODE,
)
_FR_SOLE_ADMINISTRATOR_NAME_CORRECTED = re.compile(
    r"^Rectificatif:\s*l['’]inscription\s+n°\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s*\(FOSC du\s+"
    r"(?P<notice_date>\d{2}\.\d{2}\.\d{4}),\s*p\.\s*"
    r"(?P<notice_ref>[\d/]+)\)\s+est rectifiée en ce sens que l['’]unique "
    r"administrateur se nomme\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^,)]+),\s*comme publié\)\.?$",
    re.I | re.UNICODE,
)
_FR_ERRONEOUS_ENTRY_AND_OWNER_BANKRUPTCY_REMOVED = re.compile(
    r"^L['’]inscription\s+no\s*(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+ayant été opérée à tort,\s*"
    r"elle est annulée\.\s*Par conséquent,\s*la mention relative à la faillite "
    r"du titulaire est radiée\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_MORATORIUM_LIFTED = re.compile(
    r"^Mit Verfügung vom\s+(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+der\s+"
    r"(?P<authority>.+?)\s+wurde die Nachlassstundung aufgehoben\.?$",
    re.I | re.UNICODE,
)
_DE_ADMINISTRATIVE_DOMICILE_REMOVED = re.compile(
    r"^\[gestrichen:\s*Verwaltungsdomizil:\s*(?P<address>.+?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^\].]+)\.?\]\.?$",
    re.I | re.UNICODE,
)
_FR_SHARES_TRANSFERRED_BY_MERGER_TO_NEW_ASSOCIATE = re.compile(
    r"^Par suite de fusion,\s*les\s+(?P<count>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+de\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"(?P<seller_form>société anonyme),\s*sont transférées à\s+"
    r"(?P<buyer>.+?)\s*\((?P<buyer_uid>CHE-\d{3}\.\d{3}\.\d{3})\),\s*"
    r"à\s+(?P<buyer_place>[^,.;]+),\s*nouvelle associée\.?$",
    re.I | re.UNICODE,
)
_FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT = re.compile(
    r"^Nouveau membre du conseil de fondation avec le/la président\(e\) ou le/la "
    r"vice-président\(e\):\s*(?P<name>[^,.;]+),\s*"
    r"(?:du|de la|des|de|d['’])(?P<origin>[^,.;]+),\s*à\s+"
    r"(?P<place>[^,.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_DIRECTOR_NAME_CORRECTED = re.compile(
    r"^L['’]inscription\s+(?P<entry>[\d']+)\s+du\s+"
    r"(?P<entry_date>\d{2}\.\d{2}\.\d{4})\s+est rectifiée en ce sens que le "
    r"directeur porte le nom de\s+(?P<name>[^()]+?)\s*\(et non\s+"
    r"(?P<previous_name>[^)]+)\)\.?$",
    re.I | re.UNICODE,
)
_DE_FOUNDATION_DISSOLVED_BY_AUTHORITY = re.compile(
    r"^(?:Name neu:\s*(?P<name>.+? in Liquidation)\.\s*)?"
    r"Die Stiftung ist gemäss Verfügung der\s+(?P<authority>.+?)\s+vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+aufgehoben\.?$",
    re.I | re.UNICODE,
)
_FR_SEAT_ADDRESS_AND_CONTRIBUTION_CLAUSE_REPEALED = re.compile(
    r"^Nouveau siège:\s*(?P<seat>[^,.;]+),\s*"
    r"(?P<street>.+?)\s+(?P<house>\d+[A-Za-z]?),\s*"
    r"(?P<postal_code>\d{4})\s+(?P<locality>[^.]+)\.\s*"
    r"La clause statutaire relative à l['’]apport en nature effectué[e]?\s+"
    r"[aà]\s+la constitution est abrogée conformément à l['’]art\.\s*"
    r"628\s+al\.\s*4\s+CO\.?$",
    re.I | re.UNICODE,
)
_FR_COUNCIL_COMPOSITION_MENTION_REMOVED = re.compile(
    r"^La mention relative à la composition du conseil n['’]étant plus "
    r"sou(?:m|sm)ise à inscription,\s*elle est radiée d['’]office\.?$",
    re.I | re.UNICODE,
)
_DE_COMPOSITION_MORATORIUM_EXTENDED = re.compile(
    r"^Mit Entscheid des\s+(?P<authority>.+?),\s*vom\s+"
    r"(?P<decision_date>\d{2}\.\d{2}\.\d{4})\s+wurde eine Verlängerung der "
    r"Nachlassstundung von\s+(?P<duration>\d+|ein(?:e|en)?|zwei|drei|vier|fünf|sechs)\s+"
    r"Monaten bis zum\s+(?P<until>\d{2}\.\d{2}\.\d{4})\s+bewilligt\.?$",
    re.I | re.UNICODE,
)
_FR_FIRST_NAME_CHANGED = re.compile(
    r"^(?P<surname>\S+)\s+(?P<previous_first_name>[^.;]+?)\s+porte désormais "
    r"le prénom de\s+(?P<first_name>[^.;]+)\.?$",
    re.I | re.UNICODE,
)
_FR_CORPORATE_ASSOCIATE_TRANSFER_TO_MANAGER = re.compile(
    r"^L['’]associée\s+(?P<seller>.+?)\s*"
    r"\((?P<seller_uid>CHE-\d{3}\.\d{3}\.\d{3})\)\s+cède\s+"
    r"(?P<transferred>[\d']+)\s+de ses\s+(?P<before>[\d']+)\s+parts de CHF\s+"
    r"(?P<nominal>[\d'.]+)\s+à l['’]associée-gérante\s+"
    r"(?P<buyer>[^,.;]+),\s*désormais titulaire de\s+"
    r"(?P<buyer_count>[\d']+)\s+parts de CHF\s+(?P<buyer_nominal>[\d'.]+);\s*"
    r"(?P=seller)\s*\((?P=seller_uid)\)\s+reste titulaire de\s+"
    r"(?P<seller_count>[\d']+)\s+parts de CHF\s+"
    r"(?P<seller_nominal>[\d'.]+)\.?$",
    re.I | re.UNICODE,
)


_DE_NUMBERS = {
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


def _count(raw: str) -> int:
    return int(raw.replace("'", ""))


def _duration(raw: str) -> int:
    normalized = raw.lower()
    return int(normalized) if normalized.isdigit() else _DE_NUMBERS[normalized]


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


def extract_parser152_leftovers(
    text: str,
    language: str | None,
    publication_id: str,
    published_at: str,
    org_uid: str | None,
    plz: str | None,
    canton: str | None,
) -> tuple[list[Event], str]:
    """Parse the bounded HR leftover families introduced with parser 152."""
    del language  # Historical publications can contain another language.
    events: list[Event] = []
    leftover = text.strip()

    def consume(match: re.Match[str]) -> None:
        nonlocal leftover
        leftover = f"{leftover[:match.start()]} {leftover[match.end():]}"

    match = _DE_BRANCH_PREVIOUS_PLACE_GISWIL.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "branch_changed", "de.text.branch_previous_place_giswil.v1",
            {
                "action": "previous_place_recorded",
                "previous_place": match.group("previous_place"),
            },
        ))

    match = _FR_AUDITOR_IDENTIFIER_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.auditor_identifier_corrected.v1",
            match.group("name"), uid=match.group("uid"), role="organe de révision",
            extra={
                "action": "identifier_corrected",
                "previous_uid": match.group("previous_uid"),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_MERGER_COMMON_ASSOCIATE_DEFICIT_COVERED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "company_merged", "de.text.merger_common_associate_deficit_covered.v1",
            {
                "kind": "absorption",
                "absorbed_name": match.group("absorbed_name").strip(),
                "absorbed_place": match.group("absorbed_place").strip(),
                "absorbed_uid": match.group("absorbed_uid"),
                "agreement_date": _iso_date(match.group("agreement_date")),
                "balance_date": _iso_date(match.group("balance_date")),
                "assets": match.group("assets"),
                "liabilities": match.group("liabilities"),
                "currency": "CHF",
                "liabilities_kind": "third_party_capital",
                "common_associate": True,
                "capital_increase": False,
                "share_allocation": False,
                "deficit_covered_by_freely_available_equity": True,
                "expert_confirmation_date": _iso_date(
                    match.group("confirmation_date")
                ),
            },
        ))

    match = _FR_SOLE_ADMINISTRATOR_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.sole_administrator_name_corrected.v1",
            match.group("name"), role="administrateur unique",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
                "notice_date": _iso_date(match.group("notice_date")),
                "notice_ref": match.group("notice_ref"),
            },
        ))

    match = _FR_ERRONEOUS_ENTRY_AND_OWNER_BANKRUPTCY_REMOVED.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.text.erroneous_entry_owner_bankruptcy_removed.v1"
        reference = {
            "entry": match.group("entry"),
            "entry_date": _iso_date(match.group("entry_date")),
        }
        events.extend([
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "publication_corrected", rule_id,
                {"kind": "registry_entry", "action": "cancelled", **reference},
            ),
            _event(
                publication_id, published_at, org_uid, plz, canton,
                "status_changed", rule_id,
                {
                    "kind": "bankruptcy_entry_removed",
                    "scope": "owner",
                    "action": "removed",
                    "reason": "erroneous_entry",
                    **reference,
                },
            ),
        ])

    match = _DE_COMPOSITION_MORATORIUM_LIFTED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.composition_moratorium_lifted.v1",
            {
                "kind": "composition_moratorium_revoked",
                "action": "lifted",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
            },
        ))

    match = _DE_ADMINISTRATIVE_DOMICILE_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "address_changed", "de.text.administrative_domicile_removed.v1",
            {
                "kind": "administrative_domicile",
                "action": "removed",
                "address": (
                    f"{match.group('address').strip()}, "
                    f"{match.group('postal_code')} {match.group('locality').strip()}"
                ),
                "postal_code": match.group("postal_code"),
                "locality": match.group("locality").strip(),
            },
        ))

    match = _FR_SHARES_TRANSFERRED_BY_MERGER_TO_NEW_ASSOCIATE.search(leftover)
    if match:
        consume(match)
        rule_id = "fr.persons.shares_transferred_by_merger_new_associate.v1"
        seller = match.group("seller").strip()
        buyer = match.group("buyer").strip()
        count = _count(match.group("count"))
        common = {
            "shares_count": count,
            "share_nominal": match.group("nominal"),
            "currency": "CHF",
            "transfer_reason": "merger",
        }
        events.extend([
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, seller,
                uid=match.group("seller_uid"), role="associée",
                extra={
                    "action": "shares_transferred",
                    "counterparty": buyer,
                    "counterparty_uid": match.group("buyer_uid"),
                    "legal_form": match.group("seller_form"),
                    **common,
                },
            ),
            _person_event(
                publication_id, published_at, org_uid, plz, canton,
                "officer_changed", rule_id, buyer,
                place=match.group("buyer_place"), uid=match.group("buyer_uid"),
                role="associée",
                extra={
                    "action": "shares_received",
                    "counterparty": seller,
                    "counterparty_uid": match.group("seller_uid"),
                    "new_associate": True,
                    **common,
                },
            ),
        ])

    match = _FR_FOUNDATION_MEMBER_WITH_PRESIDENT_OR_VICE_PRESIDENT.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed",
            "fr.persons.foundation_member_with_president_or_vice_president.v1",
            match.group("name"), place=match.group("place"),
            role="membre du conseil de fondation",
            signing="Kollektivunterschrift zu zweien",
            extra={
                "action": "appointed",
                "heimat": match.group("origin").strip(),
                "signing_with": "président ou vice-président",
            },
        ))

    match = _FR_DIRECTOR_NAME_CORRECTED.search(leftover)
    if match:
        consume(match)
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.director_name_corrected.v1",
            match.group("name"), role="directeur",
            extra={
                "action": "name_corrected",
                "previous_name": match.group("previous_name").strip(),
                "entry": match.group("entry"),
                "entry_date": _iso_date(match.group("entry_date")),
            },
        ))

    match = _DE_FOUNDATION_DISSOLVED_BY_AUTHORITY.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.foundation_dissolved_by_authority_short.v1",
            {
                "kind": "dissolution",
                "scope": "foundation",
                "action": "dissolved",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                **(
                    {"company_name": match.group("name").strip()}
                    if match.group("name") else {}
                ),
            },
        ))

    match = _FR_SEAT_ADDRESS_AND_CONTRIBUTION_CLAUSE_REPEALED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "statutes_changed",
            "fr.text.seat_address_contribution_clause_repealed_art_628.v1",
            {
                "kind": "contribution_in_kind",
                "action": "removed",
                "at_incorporation": True,
                "legal_basis": "Art. 628 al. 4 CO",
                "related_seat": match.group("seat").strip(),
                "related_address": (
                    f"{match.group('street').strip()} {match.group('house')}, "
                    f"{match.group('postal_code')} {match.group('locality').strip()}"
                ),
            },
        ))

    match = _FR_COUNCIL_COMPOSITION_MENTION_REMOVED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "organization_changed", "fr.text.council_composition_mention_removed.v1",
            {
                "kind": "council_composition_mention",
                "action": "removed_ex_officio",
                "reason": "no_longer_subject_to_registration",
            },
        ))

    match = _DE_COMPOSITION_MORATORIUM_EXTENDED.search(leftover)
    if match:
        consume(match)
        events.append(_event(
            publication_id, published_at, org_uid, plz, canton,
            "status_changed", "de.text.composition_moratorium_extended_short.v1",
            {
                "kind": "composition_moratorium_extended",
                "action": "extended",
                "decision_date": _iso_date(match.group("decision_date")),
                "authority": match.group("authority").strip(),
                "duration_months": _duration(match.group("duration")),
                "until": _iso_date(match.group("until")),
            },
        ))

    match = _FR_FIRST_NAME_CHANGED.search(leftover)
    if match:
        consume(match)
        name = f"{match.group('surname')} {match.group('first_name').strip()}"
        events.append(_person_event(
            publication_id, published_at, org_uid, plz, canton,
            "officer_changed", "fr.persons.first_name_changed.v1", name,
            extra={
                "action": "first_name_changed",
                "previous_name": (
                    f"{match.group('surname')} "
                    f"{match.group('previous_first_name').strip()}"
                ),
                "previous_first_name": match.group("previous_first_name").strip(),
                "first_name": match.group("first_name").strip(),
            },
        ))

    match = _FR_CORPORATE_ASSOCIATE_TRANSFER_TO_MANAGER.search(leftover)
    if match and len({
        match.group("nominal"),
        match.group("buyer_nominal"),
        match.group("seller_nominal"),
    }) == 1:
        before = _count(match.group("before"))
        transferred = _count(match.group("transferred"))
        seller_count = _count(match.group("seller_count"))
        if before - transferred == seller_count:
            consume(match)
            rule_id = "fr.persons.corporate_associate_transfer_to_manager.v1"
            seller = match.group("seller").strip()
            buyer = match.group("buyer").strip()
            common = {
                "share_nominal": match.group("nominal"),
                "currency": "CHF",
            }
            events.extend([
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, seller,
                    uid=match.group("seller_uid"), role="associée",
                    extra={
                        "action": "shares_transferred",
                        "counterparty": buyer,
                        "shares_before": before,
                        "shares_transferred": transferred,
                        "shares_count": seller_count,
                        **common,
                    },
                ),
                _person_event(
                    publication_id, published_at, org_uid, plz, canton,
                    "officer_changed", rule_id, buyer, role="associée-gérante",
                    extra={
                        "action": "shares_received",
                        "counterparty": seller,
                        "counterparty_uid": match.group("seller_uid"),
                        "shares_received": transferred,
                        "shares_count": _count(match.group("buyer_count")),
                        **common,
                    },
                ),
            ])

    return events, re.sub(r"\s+", " ", leftover).strip(" .,;")
